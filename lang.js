// static/lang.js
// 🌍 Shared multilingual manager for Smart Baby Skin Scanner

document.addEventListener("DOMContentLoaded", () => {
  // Support pages that use either #languageSwitcher or #lang (legacy)
  const switcher1 = document.getElementById("languageSwitcher");
  const switcher2 = document.getElementById("lang");

  function setLanguage(lang) {
    // Normal text
    document.querySelectorAll("[data-en]").forEach(el => {
      const val = el.getAttribute("data-" + lang) || el.getAttribute("data-en");
      if (val !== null) el.textContent = val;
    });

    // Placeholders
    document.querySelectorAll("[data-en-placeholder]").forEach(el => {
      const ph = el.getAttribute("data-" + lang + "-placeholder") || el.getAttribute("data-en-placeholder");
      if (ph !== null) el.placeholder = ph;
    });

    // Buttons (some pages use button[data-en])
    document.querySelectorAll("button[data-en]").forEach(btn => {
      const txt = btn.getAttribute("data-" + lang) || btn.getAttribute("data-en");
      if (txt !== null) btn.textContent = txt;
    });

    // Sync any language selects on the page
    if (switcher1) switcher1.value = lang;
    if (switcher2) switcher2.value = lang;

    localStorage.setItem("lang", lang);
  }

  // Global helper for other scripts to set language
  window.setAppLanguage = function(lang) {
    setLanguage(lang);
    document.dispatchEvent(new CustomEvent("languageChanged", { detail: lang }));
  };

  // Load saved language or default to English
  const savedLang = localStorage.getItem("lang") || "en";
  setLanguage(savedLang);

  // Attach change listeners to both selects (if present)
  if (switcher1) switcher1.addEventListener("change", () => {
    const lang = switcher1.value;
    setLanguage(lang);
    document.dispatchEvent(new CustomEvent("languageChanged", { detail: lang }));
  });
  if (switcher2) switcher2.addEventListener("change", () => {
    const lang = switcher2.value;
    setLanguage(lang);
    document.dispatchEvent(new CustomEvent("languageChanged", { detail: lang }));
  });
});
