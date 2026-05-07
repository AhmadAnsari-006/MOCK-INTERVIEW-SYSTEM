function authSetError(msg) {
  const el = document.getElementById("auth-error");
  if (el) el.textContent = msg || "";
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  });

  const ct = res.headers.get("content-type") || "";
  const data = ct.includes("application/json") ? await res.json() : {};

  if (!res.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function setupThemeLogoSwap() {
  const logo = document.getElementById("theme-logo");
  if (!logo) return;

  function apply() {
    const theme = document.body.dataset.theme || "dark";
    logo.src = theme === "light" ? "/assets/img/brain_byte_light_theme.png" : "/assets/img/brain_byte_darktheme.png";
  }

  apply();
  const observer = new MutationObserver(apply);
  observer.observe(document.body, { attributes: true, attributeFilter: ["data-theme"] });
}

document.addEventListener("DOMContentLoaded", () => {
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

  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      authSetError("");

      const fd = new FormData(loginForm);
      const email = (fd.get("email") || "").toString();
      const password = (fd.get("password") || "").toString();

      try {
        const data = await postJson("/api/login", { email, password });
        window.location.href = data.redirect || "/";
      } catch (err) {
        authSetError(err.message || "Login failed");
      }
    });
  }

  const signupForm = document.getElementById("signup-form");
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      authSetError("");

      const fd = new FormData(signupForm);
      const name = (fd.get("name") || "").toString();
      const email = (fd.get("email") || "").toString();
      const password = (fd.get("password") || "").toString();

      try {
        const data = await postJson("/api/signup", { name, email, password });
        window.location.href = data.redirect || "/";
      } catch (err) {
        authSetError(err.message || "Signup failed");
      }
    });
  }
});
