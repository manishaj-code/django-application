// Small progressive enhancements. The site works fully without JavaScript.
(function () {
  "use strict";

  // Loading state: on submit, disable the submit button and show its
  // data-loading-text so users don't submit twice.
  document.querySelectorAll("form[data-loading-form]").forEach(function (form) {
    form.addEventListener("submit", function () {
      var button = form.querySelector("button[type=submit][data-loading-text]");
      if (!button || button.disabled) {
        return;
      }
      // Defer so the button's own value is still submitted with the form.
      window.setTimeout(function () {
        button.disabled = true;
        button.setAttribute("aria-busy", "true");
        var spinner = document.createElement("span");
        spinner.className = "spinner-border spinner-border-sm me-2";
        spinner.setAttribute("aria-hidden", "true");
        button.textContent = button.getAttribute("data-loading-text");
        button.prepend(spinner);
      }, 0);
    });
  });

  // Move focus to the first invalid field after a failed submission.
  var firstInvalid = document.querySelector(".is-invalid");
  if (firstInvalid) {
    firstInvalid.focus();
  }
})();
