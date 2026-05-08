from __future__ import annotations

from typing import Any, Dict, List, Optional

from evaluators.embedding_evaluator import cosine_similarity
from evaluators.text_metrics import confidence_score, keyword_coverage


class AiInterviewService:
    def __init__(self, *, llm_service, vector_store_service):
        self._llm = llm_service
        self._vs = vector_store_service

    def extract_resume_profile(self, *, resume_text: str) -> Dict[str, Any]:
        schema = (
            '{"candidate_summary": "string", "skills": ["string"], "projects": [{"name": "string", "highlights": ["string"]}], '
            '"experience": [{"company": "string", "role": "string", "highlights": ["string"]}]}'
        )
        system = "You extract structured profile data from resumes for interview personalization."
        user = (
            "Extract the candidate summary, skills, projects, and experience from this resume text. "
            "Keep it concise and factual.\n\nRESUME:\n" + (resume_text or "")[:15000]
        )
        return self._llm.chat_json(system=system, user=user, schema_hint=schema, max_output_tokens=1000)

    def generate_questions(
        self,
        *,
        resume_profile: Dict[str, Any],
        role: str,
        domain: str,
        difficulty: str,
        num_questions: int,
    ) -> List[Dict[str, Any]]:
        schema = '{"questions": [{"question_id": "string", "question_text": "string", "keywords": ["string"], "focus": "string"}]}'
        system = "You generate interview questions tailored to a candidate resume and target role/domain."
        user = (
            f"Generate {num_questions} {difficulty} interview questions for role={role} domain={domain}. "
            "Use resume details to personalize. Include keywords to evaluate. "
            "Return unique question_id values.\n\nRESUME_PROFILE_JSON:\n"
            + str(resume_profile)
        )
        data = self._llm.chat_json(system=system, user=user, schema_hint=schema, max_output_tokens=1400)
        qs = data.get("questions") or []
        out: List[Dict[str, Any]] = []
        for i, q in enumerate(qs):
            if not isinstance(q, dict):
                continue
            out.append(
                {
                    "question_id": q.get("question_id") or f"aiq{i}",
                    "question_text": q.get("question_text") or "",
                    "keywords": q.get("keywords") or [],
                    "role": role,
                    "field": domain,
                    "difficulty": difficulty,
                    "focus": q.get("focus") or "",
                }
            )
        return out[: max(1, int(num_questions or 1))]

    def evaluate_answer(
        self,
        *,
        question_text: str,
        answer_text: str,
        resume_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        retrieved = []
        if resume_id:
            q_emb = self._llm.embed_texts([question_text + "\n" + (answer_text or "")[:1200]])
            if q_emb:
                retrieved = self._vs.query(resume_id=resume_id, query_embedding=q_emb[0], top_k=4)

        context_docs = [d for d, _m in retrieved if d]
        context = "\n\n".join(context_docs)[:6000]

        # Local metrics (always available)
        kw_ratio, matched, missing, _counts = keyword_coverage(answer_text or "", [])
        # Use question keywords only if caller provides them via question_service; blueprint passes q.get("keywords") separately.
        # Here we compute them later if present in `question_text` prompt; keep as empty list for safety.
        conf_10 = confidence_score(answer_text or "")

        # Embedding relevance: similarity(answer, question) and similarity(answer, best retrieved chunk)
        relevance_0_1 = 0.0
        try:
            embs = self._llm.embed_texts(
                [
                    (question_text or "").strip(),
                    (answer_text or "").strip(),
                ]
            )
            if len(embs) == 2 and embs[0] and embs[1]:
                relevance_0_1 = max(relevance_0_1, max(0.0, min(1.0, cosine_similarity(embs[1], embs[0]))))
        except Exception:
            pass

        try:
            if context_docs:
                ctx_embs = self._llm.embed_texts([c[:1200] for c in context_docs[:4]])
                ans_emb = self._llm.embed_texts([(answer_text or "")[:1200]])
                if ctx_embs and ans_emb and ans_emb[0]:
                    best = 0.0
                    for ce in ctx_embs:
                        best = max(best, cosine_similarity(ans_emb[0], ce))
                    relevance_0_1 = max(relevance_0_1, max(0.0, min(1.0, float(best))))
        except Exception:
            pass

        schema = (
            '{"label": "Poor|Average|Good|Excellent", "overall_score": 0, '
            '"scores": {"technical_accuracy": 0, "communication": 0, "confidence": 0, "relevance": 0, "problem_solving": 0}, '
            '"feedback": "string", "improvements": ["string"]}'
        )

        system = (
            "You are an interview evaluator. Score answers from 0-10 in each category and provide concise feedback. "
            "Be strict about technical correctness."
        )

        user = (
            "Evaluate the candidate answer.\n\nQUESTION:\n"
            + (question_text or "")
            + "\n\nANSWER:\n"
            + (answer_text or "")
            + ("\n\nRESUME_CONTEXT (for relevance):\n" + context if context else "")
        )

        # LLM rubric (best-effort). If model isn't running, return metrics-only evaluation.
        try:
            data = self._llm.chat_json(system=system, user=user, schema_hint=schema, max_output_tokens=900)
        except Exception:
            overall = round((relevance_0_1 * 10.0 * 0.35) + (conf_10 * 0.35) + (kw_ratio * 10.0 * 0.30), 2)
            label = "Average"
            if overall >= 8.5:
                label = "Excellent"
            elif overall >= 6.5:
                label = "Good"
            elif overall < 4.0:
                label = "Poor"
            return {
                "label": label,
                "overall_score": max(0.0, min(10.0, float(overall))),
                "scores": {
                    "technical_accuracy": 0.0,
                    "communication": round(max(0.0, min(10.0, conf_10)), 2),
                    "confidence": round(max(0.0, min(10.0, conf_10)), 2),
                    "relevance": round(max(0.0, min(10.0, relevance_0_1 * 10.0)), 2),
                    "problem_solving": 0.0,
                },
                "feedback": "AI rubric unavailable; using local metrics (confidence + relevance).",
                "improvements": [
                    "Add a short 1-line summary first, then expand with an example.",
                    "Align your answer directly to the question and mention key terms explicitly.",
                ],
                "rag": {"used": bool(context), "relevance_0_1": relevance_0_1},
            }

        scores = data.get("scores") or {}
        def _num(x):
            try:
                return float(x)
            except Exception:
                return 0.0

        tech = _num(scores.get("technical_accuracy"))
        comm = _num(scores.get("communication"))
        conf = _num(scores.get("confidence"))
        rel = _num(scores.get("relevance"))
        prob = _num(scores.get("problem_solving"))
        overall = _num(data.get("overall_score"))

        if overall <= 0:
            overall = round((tech + comm + conf + rel + prob) / 5.0, 2)

        label = (data.get("label") or "Average").strip()
        if label not in {"Poor", "Average", "Good", "Excellent"}:
            if overall >= 8.5:
                label = "Excellent"
            elif overall >= 6.5:
                label = "Good"
            elif overall >= 4.0:
                label = "Average"
            else:
                label = "Poor"

        return {
            "label": label,
            "overall_score": max(0.0, min(10.0, float(overall))),
            "scores": {
                "technical_accuracy": max(0.0, min(10.0, float(tech))),
                "communication": max(0.0, min(10.0, float(comm))),
                "confidence": max(0.0, min(10.0, float(conf))),
                "relevance": max(0.0, min(10.0, float(rel))),
                "problem_solving": max(0.0, min(10.0, float(prob))),
            },
            "feedback": data.get("feedback") or "",
            "improvements": data.get("improvements") or [],
            "rag": {
                "used": bool(context),
                "relevance_0_1": relevance_0_1,
            },
        }
