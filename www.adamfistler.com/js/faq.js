document.addEventListener("DOMContentLoaded", function () {

  const questions = document.querySelectorAll(".faq-question");

  questions.forEach(function (question) {

    question.addEventListener("click", function () {

      const item = question.closest(".faq-item");
      const answer = item.querySelector(".faq-answer");

      const isOpen = item.classList.contains("open");

      if (isOpen) {
        item.classList.remove("open");
        question.setAttribute("aria-expanded", "false");
        answer.setAttribute("aria-hidden", "true");
      } else {
        item.classList.add("open");
        question.setAttribute("aria-expanded", "true");
        answer.setAttribute("aria-hidden", "false");
      }

    });

  });

});

