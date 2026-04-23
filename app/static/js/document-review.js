document.addEventListener("DOMContentLoaded", () => {
  const reviewForms = document.querySelectorAll("[data-document-review-form]");
  for (const form of reviewForms) {
    form.addEventListener("submit", () => {
      form.dataset.state = "submitting";
    });
  }

  const autofocusTarget = document.querySelector("[data-document-review-form] input[name='supplier_guess']");
  if (autofocusTarget) {
    autofocusTarget.focus();
    autofocusTarget.select();
  }
});
