/* ============================================
   Theme (persisted) + Micro-interactions + AJAX
   ============================================ */

const THEME_KEY = "theme";

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

function safeJson(response) {
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.includes("application/json")) return Promise.reject(new Error("Expected JSON response"));
    return response.json();
}

function submitAnswer() {
    const answerEl = document.getElementById("answer");
    if (!answerEl) return;

    const answer = answerEl.value || "";
    const submitBtn = document.querySelector("[data-submit-answer]");

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.loading = "1";
    }

    fetch("/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    })
        .then(safeJson)
        .then((data) => {
            if (data.next_question) {
                const box = document.getElementById("question-box");
                if (box) box.textContent = data.next_question;
                answerEl.value = "";
                answerEl.focus();
            } else if (data.redirect) {
                window.location.href = data.redirect;
            }
        })
        .catch(() => {
            // Keep UX simple for hackathon: re-enable button on any failure.
        })
        .finally(() => {
            if (submitBtn) {
                submitBtn.disabled = false;
                delete submitBtn.dataset.loading;
            }
        });
}

document.addEventListener("DOMContentLoaded", () => {
    document.body.dataset.theme = getPreferredTheme();
    setTheme(document.body.dataset.theme);

    const themeSwitch = document.getElementById("themeSwitch");
    if (themeSwitch) {
        themeSwitch.addEventListener("change", toggleTheme);
    }

    // Drawer (sidebar) toggle
    const drawerToggles = Array.from(document.querySelectorAll("[data-drawer-toggle]"));
    const drawerOverlay = document.querySelector("[data-drawer-overlay]");
    const drawer = document.querySelector("[data-drawer]");
    const screen = document.querySelector("[data-screen]");

    function setDrawerOpen(open) {
        if (open) document.body.classList.add("drawer-open");
        else document.body.classList.remove("drawer-open");

        drawerToggles.forEach((btn) => btn.setAttribute("aria-expanded", open ? "true" : "false"));
        if (drawer) drawer.setAttribute("aria-hidden", open ? "false" : "true");
    }

    // Ensure hidden by default on load
    setDrawerOpen(false);

    drawerToggles.forEach((btn) => {
        btn.addEventListener("click", () => {
            const next = !document.body.classList.contains("drawer-open");
            setDrawerOpen(next);
        });
    });

    if (drawerOverlay) {
        drawerOverlay.addEventListener("click", () => setDrawerOpen(false));
    }

    // Close drawer when navigating via menu items
    document.querySelectorAll("[data-drawer] a").forEach((el) => {
        el.addEventListener("click", () => setDrawerOpen(false));
    });

    if (screen) {
        screen.addEventListener("click", () => {
            if (document.body.classList.contains("drawer-open")) setDrawerOpen(false);
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") setDrawerOpen(false);
    });

    // Keyboard submit (Ctrl/Cmd + Enter) for textarea
    const answerEl = document.getElementById("answer");
    if (answerEl) {
        answerEl.addEventListener("keydown", (e) => {
            const isSubmitCombo = (e.ctrlKey || e.metaKey) && e.key === "Enter";
            if (isSubmitCombo) submitAnswer();
        });
    }
});

/* Motion suggestions (drop-in ideas for developers)
   - Use IntersectionObserver to stagger-in cards on scroll
   - Add “question change” crossfade + slide (CSS keyframes)
   - Add progress easing: update --progress inline based on question index
   - Add optimistic “sending…” state on buttons (data-loading)
*/
