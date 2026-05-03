function $(id) {
  return document.getElementById(id);
}

function safeText(el, text) {
  if (!el) return;
  el.textContent = text == null ? "" : String(text);
}

function setProgress(barEl, percent) {
  if (!barEl) return;
  const p = Math.max(0, Math.min(100, Number(percent) || 0));
  barEl.style.setProperty("--progress", p + "%");
}

function getSessionId() {
  return localStorage.getItem("session_id") || "";
}

function setSessionId(id) {
  if (id) localStorage.setItem("session_id", id);
}

function clearSession() {
  localStorage.removeItem("session_id");
}

async function jsonGet(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error("Request failed");
  return await res.json();
}

async function jsonPost(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  });
  if (!res.ok) throw new Error("Request failed");
  return await res.json();
}

function pageName() {
  const p = window.location.pathname;
  if (p === "/" || p.endsWith("/index.html")) return "index";
  if (p.startsWith("/interview")) return "interview";
  if (p.startsWith("/result")) return "result";
  return "";
}

async function initIndex() {
  const roleSelect = $("role");
  const fieldSelect = $("field");
  const form = document.getElementById("start-form");

  if (roleSelect) {
    const data = await jsonGet("/get_roles");
    roleSelect.innerHTML = '<option value="">Select Role</option>';
    (data.roles || []).forEach((role) => {
      const opt = document.createElement("option");
      opt.value = role;
      opt.textContent = role;
      roleSelect.appendChild(opt);
    });
  }

  if (roleSelect && fieldSelect) {
    roleSelect.addEventListener("change", async () => {
      const role = roleSelect.value;
      fieldSelect.innerHTML = '<option value="">Loading...</option>';
      const data = await jsonGet(`/get_fields?role=${encodeURIComponent(role)}`);
      fieldSelect.innerHTML = "";
      (data.fields || []).forEach((f) => {
        const opt = document.createElement("option");
        opt.value = f;
        opt.textContent = f;
        fieldSelect.appendChild(opt);
      });
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const name = (fd.get("name") || "").toString();
      const role = (fd.get("role") || "").toString();
      const field = (fd.get("field") || "").toString();
      const difficulty = (fd.get("difficulty") || "medium").toString();
      const numQuestions = Number(fd.get("num_questions") || 5);

      const data = await jsonGet(
        `/start-interview?name=${encodeURIComponent(name)}` +
          `&role=${encodeURIComponent(role)}` +
          `&field=${encodeURIComponent(field)}` +
          `&difficulty=${encodeURIComponent(difficulty)}` +
          `&num_questions=${encodeURIComponent(String(numQuestions))}`
      );

      setSessionId(data.session_id);
      window.location.href = "/interview";
    });
  }
}

async function initInterview() {
  const sid = getSessionId();
  if (!sid) {
    window.location.href = "/";
    return;
  }

  const qBox = $("question-box");
  const qIndex = $("q-index");
  const qTotal = $("q-total");
  const submitBtn = $("submitBtn");
  const answerEl = $("answer");

  const q = await jsonGet(`/get-question?session_id=${encodeURIComponent(sid)}`);
  if (q.done) {
    window.location.href = "/result";
    return;
  }

  safeText(qBox, q.question_text);
  safeText(qIndex, (q.index || 0) + 1);
  safeText(qTotal, q.total);

  document.body.dataset.total = String(q.total || 1);

  if (submitBtn) {
    submitBtn.addEventListener("click", async () => {
      const ans = (answerEl && answerEl.value ? answerEl.value : "").trim();
      if (!ans) {
        alert("Answer cannot be empty.");
        return;
      }

      const res = await jsonPost("/submit-answer", { session_id: sid, answer: ans });

      if (res.done) {
        window.location.href = "/result";
        return;
      }

      const next = await jsonGet(`/get-question?session_id=${encodeURIComponent(sid)}`);
      safeText(qBox, next.question_text);
      safeText(qIndex, (next.index || 0) + 1);
      safeText(qTotal, next.total);

      if (answerEl) answerEl.value = "";
    });
  }
}

function drawHistoryChart(canvas, scores) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const pad = 18;
  const minY = 0;
  const maxY = 10;

  function xAt(i) {
    if (scores.length <= 1) return pad;
    return pad + (i * (w - pad * 2)) / (scores.length - 1);
  }

  function yAt(v) {
    const t = (v - minY) / (maxY - minY);
    return (h - pad) - t * (h - pad * 2);
  }

  ctx.globalAlpha = 0.6;
  ctx.strokeStyle = "#8aa7ff";
  ctx.lineWidth = 1;
  for (let y = 0; y <= 10; y += 2) {
    const yy = yAt(y);
    ctx.beginPath();
    ctx.moveTo(pad, yy);
    ctx.lineTo(w - pad, yy);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;

  ctx.strokeStyle = "#6ee7b7";
  ctx.lineWidth = 3;
  ctx.beginPath();
  scores.forEach((s, i) => {
    const x = xAt(i);
    const y = yAt(s);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#ffffff";
  ctx.strokeStyle = "#6ee7b7";
  ctx.lineWidth = 2;
  scores.forEach((s, i) => {
    const x = xAt(i);
    const y = yAt(s);
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "rgba(255,255,255,0.85)";
    ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
    const txt = (Math.round(s * 10) / 10).toFixed(1);
    ctx.fillText(txt, x + 8, y - 8);
    ctx.fillStyle = "#ffffff";
  });
}

async function initResult() {
  const sid = getSessionId();
  if (!sid) {
    window.location.href = "/";
    return;
  }

  const data = await jsonGet(`/get-feedback?session_id=${encodeURIComponent(sid)}`);

  safeText($("res-name"), data.name || "");
  safeText($("res-time"), data.time_taken || 0);
  safeText($("res-total"), data.total_questions || 0);

  const score = Number(data.average_score_10 || 0);
  safeText($("res-score"), score.toFixed(1));
  safeText($("res-feedback"), data.summary || "");
  setProgress($("res-progress"), score * 10);

  const perq = $("res-perq");
  if (perq) {
    perq.innerHTML = "";
    (data.per_question || []).forEach((pq, i) => {
      const s = Number(pq.score_10 || 0);
      const li = document.createElement("li");
      li.style.marginBottom = "10px";
      li.innerHTML =
        `<div>Question ${i + 1} → <strong>${s.toFixed(1)}/10</strong></div>` +
        `<div class="progress-bar" style="--progress:${s * 10}%;"><div class="progress"></div></div>`;
      perq.appendChild(li);
    });
  }

  const tipsEl = $("res-tips");
  if (tipsEl) {
    tipsEl.innerHTML = "";
    const tips = [];
    const weaknesses = ((data.final_feedback || {}).weaknesses || []).slice(0, 5);

    if (score >= 8.0) {
      tips.push("Level-up: add 1 example and 1 trade-off in every answer.");
      tips.push("Use a crisp 15-second summary first, then expand.");
    } else if (score >= 5.0) {
      tips.push("Blueprint: Definition → How it works → Example → Edge case.");
      tips.push("After answering, add a quick ‘why it matters’ sentence.");
    } else {
      tips.push("Start with fundamentals: define the term in one sentence.");
      tips.push("Use Problem → Solution → Result to stay concrete.");
    }

    if (weaknesses.length) {
      tips.push("Focus keywords next time: " + weaknesses.join(", ") + ".");
    }

    tips.forEach((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      tipsEl.appendChild(li);
    });
  }

  const historyScores = (data.history && data.history.scores) ? data.history.scores : [];
  const attemptsCount = (data.history && typeof data.history.attempts === "number") ? data.history.attempts : historyScores.length;
  safeText($("res-attempts"), "Attempts: " + (attemptsCount || 0));

  const canvas = $("historyChart");
  if (historyScores.length) {
    drawHistoryChart(canvas, historyScores);
  } else if (canvas) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const page = pageName();
  if (page === "index") initIndex();
  if (page === "interview") initInterview();
  if (page === "result") initResult();
});
