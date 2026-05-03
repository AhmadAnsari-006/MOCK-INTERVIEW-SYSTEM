/* ============================================
   Theme + UI + AJAX + TIMER + PROGRESS + UX
   ============================================ */

const THEME_KEY = "theme";

/* ---------------- THEME ---------------- */
function getPreferredTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === "light" || saved === "dark") return saved;
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) return "light";
    return "dark";
}

function setTheme(theme) {
    document.body.dataset.theme = theme;
    localStorage.setItem(THEME_KEY, theme);

    const themeSwitch = document.getElementById("themeSwitch");
    if (themeSwitch) themeSwitch.checked = theme === "light";

    const themeLabel = document.querySelector("[data-theme-label]");
    if (themeLabel) themeLabel.textContent = theme === "light" ? "Light" : "Dark";
}

function toggleTheme() {
    const next = document.body.dataset.theme === "light" ? "dark" : "light";
    setTheme(next);
}

/* ---------------- SAFE JSON ---------------- */
function safeJson(response) {
    const contentType = response.headers.get("content-type") || "";

    if (!contentType.includes("application/json")) {
        console.error("❌ Invalid JSON response");
        return Promise.reject("Invalid JSON");
    }

    return response.json();
}

/* ---------------- TIMER ---------------- */
let timerInterval = null;

function startTimer(totalQuestions) {

    let timeLeft = totalQuestions * 60;
    const timerEl = document.getElementById("timer");

    if (!timerEl) return;

    timerInterval = setInterval(() => {

        timeLeft--;
        timerEl.textContent = `Time: ${timeLeft}s`;

        if (timeLeft <= 0) {
            clearInterval(timerInterval);

            console.warn("⏱ Time ended, forcing submission...");

            fetch("/answer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ answer: "" })
            }).then(() => {
                window.location.href = "/result";
            });
        }

    }, 1000);
}

/* ---------------- PROGRESS ---------------- */
function updateProgress(index, total) {

    const percent = ((index + 1) / total) * 100;

    const bar = document.querySelector(".progress-bar");
    if (bar) {
        bar.style.setProperty("--progress", percent + "%");
    }
}

/* ---------------- STATUS MESSAGE ---------------- */
function showStatus(msg, type = "info") {
    console.log(`[${type.toUpperCase()}] ${msg}`);
}

/* ---------------- RESET ANSWER BOX ---------------- */
function resetAnswerBox() {
    const answerEl = document.getElementById("answer");
    if (!answerEl) return;

    answerEl.value = "";
    answerEl.focus();
}

/* ---------------- SUBMIT ANSWER ---------------- */
function submitAnswer() {

    const answerEl = document.getElementById("answer");
    if (!answerEl) return;

    const answer = answerEl.value || "";
    const submitBtn = document.querySelector("[data-submit-answer]");

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.loading = "1";
    }

    showStatus("Submitting answer...", "info");

    fetch("/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    })
        .then(safeJson)
        .then((data) => {

            if (data.next_question) {

                const box = document.getElementById("question-box");

                if (box) {
                    box.style.opacity = 0;

                    setTimeout(() => {
                        box.textContent = data.next_question;
                        box.style.opacity = 1;
                    }, 200);
                }

                resetAnswerBox();

                if (data.index !== undefined && window.totalQuestions) {
                    updateProgress(data.index, window.totalQuestions);
                }

                showStatus("Next question loaded", "success");

            } else if (data.redirect) {

                showStatus("Redirecting to result...", "info");
                window.location.href = data.redirect;
            }
        })
        .catch((err) => {
            console.error("❌ Submission failed:", err);
            showStatus("Submission failed", "error");
        })
        .finally(() => {
            if (submitBtn) {
                submitBtn.disabled = false;
                delete submitBtn.dataset.loading;
            }
        });
}

/* ---------------- DRAWER ---------------- */
function setupDrawer() {

    const drawerToggles = Array.from(document.querySelectorAll("[data-drawer-toggle]"));
    const drawerOverlay = document.querySelector("[data-drawer-overlay]");
    const drawer = document.querySelector("[data-drawer]");
    const screen = document.querySelector("[data-screen]");

    function setDrawerOpen(open) {
        document.body.classList.toggle("drawer-open", open);
        drawerToggles.forEach(btn => btn.setAttribute("aria-expanded", open));
        if (drawer) drawer.setAttribute("aria-hidden", !open);
    }

    setDrawerOpen(false);

    drawerToggles.forEach(btn => {
        btn.addEventListener("click", () => {
            setDrawerOpen(!document.body.classList.contains("drawer-open"));
        });
    });

    if (drawerOverlay) drawerOverlay.addEventListener("click", () => setDrawerOpen(false));

    if (screen) screen.addEventListener("click", () => setDrawerOpen(false));

    document.addEventListener("keydown", e => {
        if (e.key === "Escape") setDrawerOpen(false);
    });
}

/* ---------------- KEYBOARD SHORTCUT ---------------- */
function setupKeyboardSubmit() {

    const answerEl = document.getElementById("answer");

    if (!answerEl) return;

    answerEl.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            submitAnswer();
        }
    });
}

/* ---------------- INIT ---------------- */
document.addEventListener("DOMContentLoaded", () => {

    /* Theme */
    document.body.dataset.theme = getPreferredTheme();
    setTheme(document.body.dataset.theme);

    const themeSwitch = document.getElementById("themeSwitch");
    if (themeSwitch) themeSwitch.addEventListener("change", toggleTheme);

    /* Drawer */
    setupDrawer();

    /* Keyboard */
    setupKeyboardSubmit();

    /* Timer */
    const total = document.body.dataset.total;

    if (total) {
        window.totalQuestions = parseInt(total);
        startTimer(window.totalQuestions);
    }

    showStatus("App initialized", "info");
});