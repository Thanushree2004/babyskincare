// static/lang.js
// 🌍 Shared multilingual manager for Smart Baby Skin Scanner

document.addEventListener("DOMContentLoaded", () => {
  const switcher = document.getElementById("languageSwitcher");
  if (!switcher) return;

  function setLanguage(lang) {
    // Normal text
    document.querySelectorAll("[data-en]").forEach(el => {
      el.textContent = el.getAttribute("data-" + lang);
    });

    // Placeholders
    document.querySelectorAll("[data-en-placeholder]").forEach(el => {
      el.placeholder = el.getAttribute("data-" + lang + "-placeholder");
    });

    // Buttons
    document.querySelectorAll("button[data-en]").forEach(btn => {
      btn.textContent = btn.getAttribute("data-" + lang);
    });

    localStorage.setItem("lang", lang);
  }

  // Load saved language or default to English
  const savedLang = localStorage.getItem("lang") || "en";
  switcher.value = savedLang;
  setLanguage(savedLang);

  switcher.addEventListener("change", () => {
    const lang = switcher.value;
    setLanguage(lang);
    // Notify backend for requests (if needed)
    document.dispatchEvent(new CustomEvent("languageChanged", { detail: lang }));
  });
});
