document.addEventListener('DOMContentLoaded', function () {

  const cards = document.querySelectorAll('.practice-card');
  const details = document.querySelectorAll('.practice-detail');


  /*
   * ==========================================================
   * SHOW PRACTICE AREA
   * ==========================================================
   *
   * Legacy/internal navigation.
   *
   * This remains available in case practice areas are ever
   * switched back to internal page behavior.
   *
   * openMenu = true
   *     Open the corresponding menu parent.
   *
   * openMenu = false
   *     Do not modify the menu.
   *
   */

  window.showPracticeArea = function (practiceId, openMenu) {

    if (!practiceId) {
      return;
    }


    /*
     * Find the practice-area detail.
     */

    const target = document.getElementById(
      'practice-detail-' + practiceId
    );

    if (!target) {

      console.error(
        'Practice detail not found:',
        'practice-detail-' + practiceId
      );

      return;
    }


    /*
     * Hide every practice-area detail.
     */

    details.forEach(function (detail) {

      detail.classList.remove('active');

    });


    /*
     * Remove selected state from every card.
     */

    cards.forEach(function (card) {

      card.classList.remove('selected');

    });


    /*
     * Show the requested practice area.
     */

    target.classList.add('active');


    /*
     * Select the corresponding card, if one exists.
     */

    cards.forEach(function (card) {

      if (
        card.dataset.practice === practiceId
      ) {

        card.classList.add('selected');

      }

    });


    /*
     * If requested, open the corresponding menu parent.
     */

    if (openMenu) {

      const parent =
        document.querySelector(
          '.menu-item.parent[href$="#' +
          CSS.escape(practiceId) +
          '"]'
        );

      if (parent) {

        if (
          typeof window.openMenuParent === 'function'
        ) {

          window.openMenuParent(parent);

        }

      }

    }


    /*
     * Scroll to the practice-area detail.
     */

    target.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });

  };


  /*
   * ==========================================================
   * PRACTICE CARD CLICK
   * ==========================================================
   *
   * NEW BEHAVIOR:
   *
   * Practice cards generated as <a> elements are normal links.
   * We deliberately do NOT intercept those clicks.
   *
   * LEGACY BEHAVIOR:
   *
   * Practice cards generated as <button> elements continue
   * to use showPracticeArea().
   *
   */

  cards.forEach(function (card) {

    card.addEventListener('click', function (event) {

      /*
       * --------------------------------------------------------
       * URL NAVIGATION
       * --------------------------------------------------------
       *
       * <a class="practice-card" href="...">
       *
       * Let the browser follow the URL normally.
       *
       */

      if (
        card.tagName.toLowerCase() === 'a'
      ) {

        return;
      }


      /*
       * --------------------------------------------------------
       * LEGACY INTERNAL NAVIGATION
       * --------------------------------------------------------
       *
       * <button class="practice-card"
       *         data-practice="hypnosis">
       *
       */

      event.preventDefault();

      const practiceId =
        card.dataset.practice;

      showPracticeArea(
        practiceId,
        true
      );

    });

  });


  /*
   * ==========================================================
   * INITIAL HASH
   * ==========================================================
   *
   * LEGACY INTERNAL PRACTICE-AREA SUPPORT
   *
   * If a page contains:
   *
   *     #hypnosis
   *
   * and also contains:
   *
   *     id="practice-detail-hypnosis"
   *
   * then the old practice-area functionality is activated.
   *
   * This does not interfere with the new landing-page
   * navigation model.
   *
   */

  const hash =
    window.location.hash;

  if (!hash) {
    return;
  }


  const practiceId =
    hash.substring(1);

  if (!practiceId) {
    return;
  }


  const target =
    document.getElementById(
      'practice-detail-' + practiceId
    );

  if (!target) {

    /*
     * This is expected on landing pages that use the hash
     * only as a URL/menu identifier.
     */

    return;
  }


  /*
   * Legacy internal behavior.
   */

  showPracticeArea(
    practiceId,
    false
  );

});
