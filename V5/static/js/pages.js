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

function postJson(url, body) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  }).then(async (res) => {
    const ct = res.headers.get("content-type") || "";
    const data = ct.includes("application/json") ? await res.json() : {};
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  });
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

function setupThemeLogoSwap() {
  const logo = document.getElementById("theme-logo");
  if (!logo) return;

  function apply() {
    const theme = document.body.dataset.theme || "dark";
    logo.src = theme === "light" ? "/assets/img/lighttheme_logo.png" : "/assets/img/darktheme_logo.png";
  }

  apply();
  const observer = new MutationObserver(apply);
  observer.observe(document.body, { attributes: true, attributeFilter: ["data-theme"] });
}

async function loadMe() {
  try {
    return await jsonGet("/api/me");
  } catch {
    return { authenticated: false };
  }
}

function randomChoice(arr, fallback) {
  if (!arr || !arr.length) return fallback;
  return arr[Math.floor(Math.random() * arr.length)];
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
  if (p.startsWith("/settings")) return "settings";
  if (p.startsWith("/tips")) return "tips";
  return "";
}

async function initSettings() {
  setupThemeLogoSwap();

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        const data = await jsonGet("/logout");
        clearSession();
        window.location.href = data.redirect || "/";
      } catch {
        clearSession();
        window.location.href = "/";
      }
    });
  }

  const switchUserBtn = document.getElementById("switch-user-btn");
  if (switchUserBtn) {
    switchUserBtn.addEventListener("click", async () => {
      try {
        const data = await jsonGet("/logout");
        clearSession();
        window.location.href = data.redirect || "/";
      } catch {
        clearSession();
        window.location.href = "/";
      }
    });
  }

  const cpForm = document.getElementById("change-password-form");
  if (cpForm) {
    cpForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = document.getElementById("settings-msg");
      if (msg) msg.textContent = "";

      const fd = new FormData(cpForm);
      const current_password = (fd.get("current_password") || "").toString();
      const new_password = (fd.get("new_password") || "").toString();

      try {
        await postJson("/api/change-password", { current_password, new_password });
        if (msg) msg.textContent = "Password updated.";
        cpForm.reset();
      } catch (err) {
        if (msg) msg.textContent = err.message || "Failed to change password";
      }
    });
  }

  const homeFab = document.getElementById("home-fab");
  if (homeFab) {
    homeFab.addEventListener("click", () => {
      window.location.href = "/";
    });
  }

  const settingsFab = document.getElementById("settings-fab");
  if (settingsFab) {
    settingsFab.addEventListener("click", () => {
      window.location.href = "/settings";
    });
  }
}

async function initTips() {
  setupThemeLogoSwap();

  const homeFab = document.getElementById("home-fab");
  if (homeFab) {
    homeFab.addEventListener("click", () => {
      window.location.href = "/";
    });
  }

  const settingsFab = document.getElementById("settings-fab");
  if (settingsFab) {
    settingsFab.addEventListener("click", () => {
      window.location.href = "/settings";
    });
  }
}

async function initIndex() {
  setupThemeLogoSwap();

  const me = await loadMe();
  if (me && me.authenticated) {
    safeText($("user-name"), me.name || "User");
  }

  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        const data = await jsonGet("/logout");
        clearSession();
        window.location.href = data.redirect || "/";
      } catch {
        clearSession();
        window.location.href = "/";
      }
    });
  }

  const switchUserBtn = document.getElementById("switch-user-btn");
  if (switchUserBtn) {
    switchUserBtn.addEventListener("click", async () => {
      try {
        const data = await jsonGet("/logout");
        clearSession();
        window.location.href = data.redirect || "/";
      } catch {
        clearSession();
        window.location.href = "/";
      }
    });
  }

  const cpForm = document.getElementById("change-password-form");
  if (cpForm) {
    cpForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = document.getElementById("settings-msg");
      if (msg) msg.textContent = "";

      const fd = new FormData(cpForm);
      const current_password = (fd.get("current_password") || "").toString();
      const new_password = (fd.get("new_password") || "").toString();

      try {
        await postJson("/api/change-password", { current_password, new_password });
        if (msg) msg.textContent = "Password updated.";
        cpForm.reset();
      } catch (err) {
        if (msg) msg.textContent = err.message || "Failed to change password";
      }
    });
  }

  const homeFab = document.getElementById("home-fab");
  if (homeFab) {
    homeFab.addEventListener("click", () => {
      window.location.href = "/";
    });
  }

  const settingsFab = document.getElementById("settings-fab");
  if (settingsFab) {
    settingsFab.addEventListener("click", () => {
      window.location.href = "/settings";
    });
  }

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

      localStorage.setItem("interview_difficulty", difficulty);

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
  setupThemeLogoSwap();

  const homeFab = document.getElementById("home-fab");
  if (homeFab) {
    homeFab.addEventListener("click", () => {
      window.location.href = "/";
    });
  }

  const settingsFab = document.getElementById("settings-fab");
  if (settingsFab) {
    settingsFab.addEventListener("click", () => {
      window.location.href = "/settings";
    });
  }
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

  const prog = document.querySelector(".progress-bar");
  setProgress(prog, (((q.index || 0) + 1) / (q.total || 1)) * 100);

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

      setProgress(prog, (((next.index || 0) + 1) / (next.total || 1)) * 100);

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
  setupThemeLogoSwap();

  const homeFab = document.getElementById("home-fab");
  if (homeFab) {
    homeFab.addEventListener("click", () => {
      window.location.href = "/";
    });
  }

  const settingsFab = document.getElementById("settings-fab");
  if (settingsFab) {
    settingsFab.addEventListener("click", () => {
      window.location.href = "/settings";
    });
  }
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
  const scoreInt = Math.max(0, Math.min(10, Math.round(score)));
  const scoreFeedbackMap = {
    0: ["Let’s reboot from the basics—start small, build confidence.", "A fresh start. Focus on the core definitions first."],
    1: ["You’ve started. Next: add key terms to every answer.", "Step 1 done—now build structure."],
    2: ["Some signals are there—improve clarity and correctness.", "Good attempt—tighten your fundamentals."],
    3: ["You’re warming up—add examples and correct terminology.", "Progress noted—cover missing concepts."],
    4: ["Fair—now aim for precision and completeness.", "You’re close—focus on weak areas."],
    5: ["Decent—make answers more structured and confident.", "Solid base—add depth and trade-offs."],
    6: ["Good—push for sharper explanations and stronger keywords.", "Nice work—add real-world scenarios."],
    7: ["Strong—polish delivery and include edge cases.", "Good performance—improve conciseness."],
    8: ["Very strong—add trade-offs and performance considerations.", "Great—make it interview-ready with crisp summaries."],
    9: ["Excellent—keep consistency and refine storytelling.", "Outstanding—add more architecture-level thinking."],
    10: ["Perfect run—mentor-level clarity.", "Flawless—keep this consistency under pressure."]
  };
  const dynamicBelowScore = randomChoice(scoreFeedbackMap[scoreInt], "Good effort—keep improving.");

  safeText($("res-feedback"), dynamicBelowScore);
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
    const per = data.per_question || [];

    const lowScore = per
      .map((pq, idx) => ({ idx, score: Number(pq.score_10 || 0), words: Number(pq.answer_words || 0), hit: Number(pq.keyword_hit_count || 0), total: Number(pq.keyword_total || 0) }))
      .sort((a, b) => a.score - b.score)[0];

    if (lowScore && Number.isFinite(lowScore.score)) {
      const cov = lowScore.total ? Math.round((lowScore.hit / lowScore.total) * 100) : 0;
      if (lowScore.words < 25) tips.push(`Q${lowScore.idx + 1}: Your answer was too short (${lowScore.words} words). Aim for 40–80 words.`);
      if (cov < 60) tips.push(`Q${lowScore.idx + 1}: Keyword coverage was low (${cov}%). Include more expected terms.`);
      if (lowScore.score < 6) tips.push(`Q${lowScore.idx + 1}: Score ${lowScore.score.toFixed(1)}/10. Improve with definition + example + trade-off.`);
    }

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
    drawHistoryChartAxes(canvas, historyScores);
  } else if (canvas) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  if (canvas && historyScores.length) {
    const observer = new MutationObserver(() => drawHistoryChartAxes(canvas, historyScores));
    observer.observe(document.body, { attributes: true, attributeFilter: ["data-theme"] });
  }
}

function drawHistoryChartAxes(canvas, scores) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const isLight = (document.body.dataset.theme || "dark") === "light";
  const axis = isLight ? "rgba(15,23,42,0.35)" : "rgba(255,255,255,0.25)";
  const label = isLight ? "rgba(15,23,42,0.75)" : "rgba(255,255,255,0.7)";
  const grid = isLight ? "rgba(15,23,42,0.10)" : "rgba(255,255,255,0.18)";
  const text = isLight ? "rgba(15,23,42,0.75)" : "rgba(255,255,255,0.65)";
  const line = isLight ? "rgba(16,185,129,1)" : "#6ee7b7";
  const pointFill = isLight ? "#ffffff" : "#ffffff";
  const pointStroke = line;

  const padL = 34;
  const padR = 12;
  const padT = 14;
  const padB = 26;
  const minY = 0;
  const maxY = 10;

  function xAt(i) {
    if (scores.length <= 1) return padL;
    return padL + (i * (w - padL - padR)) / (scores.length - 1);
  }
  function yAt(v) {
    const t = (v - minY) / (maxY - minY);
    return (h - padB) - t * (h - padT - padB);
  }

  ctx.globalAlpha = 1;
  ctx.strokeStyle = axis;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padL, padT);
  ctx.lineTo(padL, h - padB);
  ctx.lineTo(w - padR, h - padB);
  ctx.stroke();

  ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
  ctx.fillStyle = label;
  ctx.fillText("Score", 6, padT + 10);
  ctx.fillText("Attempts", w / 2 - 22, h - 6);

  ctx.globalAlpha = 1;
  ctx.strokeStyle = grid;
  for (let y = 0; y <= 10; y += 2) {
    const yy = yAt(y);
    ctx.beginPath();
    ctx.moveTo(padL, yy);
    ctx.lineTo(w - padR, yy);
    ctx.stroke();
    ctx.fillStyle = text;
    ctx.fillText(String(y), 10, yy + 4);
  }
  ctx.globalAlpha = 1;

  ctx.strokeStyle = line;
  ctx.lineWidth = 3;
  ctx.beginPath();
  scores.forEach((s, i) => {
    const x = xAt(i);
    const y = yAt(s);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = pointFill;
  ctx.strokeStyle = pointStroke;
  ctx.lineWidth = 2;
  scores.forEach((s, i) => {
    const x = xAt(i);
    const y = yAt(s);
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = isLight ? "rgba(15,23,42,0.8)" : "rgba(255,255,255,0.85)";
    ctx.fillText((Math.round(s * 10) / 10).toFixed(1), x + 8, y - 8);
    ctx.fillStyle = pointFill;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const page = pageName();
  if (page === "index") initIndex();
  if (page === "interview") initInterview();
  if (page === "result") initResult();
  if (page === "settings") initSettings();
  if (page === "tips") initTips();
});
