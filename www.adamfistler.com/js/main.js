function init() {

  const menuVisibility =
    document.getElementById("menu_visibility");

  const menu =
    document.getElementById("menu");

  const content =
    document.getElementById("content");


  /*
   * ==========================================================
   * CLOSE OTHER MENU PARENTS
   * ==========================================================
   *
   * Close every parent menu except the specified parent.
   *
   */

  window.closeOtherMenuParents = function (parent) {

    if (!menu) {
      return;
    }

    const parents =
      menu.querySelectorAll(".menu-item.parent");


    parents.forEach(function (otherParent) {

      if (otherParent === parent) {
        return;
      }


      otherParent.classList.remove("active");


      const otherChildMenu =
        otherParent.nextElementSibling;


      if (
        otherChildMenu &&
        otherChildMenu.classList.contains("child-menu")
      ) {

        otherChildMenu.classList.add("hidden");

      }

    });

  };


  /*
   * ==========================================================
   * OPEN MENU PARENT
   * ==========================================================
   *
   * Open the child menu belonging to a parent.
   *
   */

  window.openMenuParent = function (parent) {

    if (!parent) {
      return;
    }


    const childMenu =
      parent.nextElementSibling;


    if (
      !childMenu ||
      !childMenu.classList.contains("child-menu")
    ) {

      return;

    }


    closeOtherMenuParents(parent);


    childMenu.classList.remove("hidden");

    parent.classList.add("active");

  };


  /*
   * ==========================================================
   * TOGGLE MENU PARENT
   * ==========================================================
   *
   * Legacy/manual menu toggle support.
   *
   * This remains available if we ever need it again.
   *
   */

  window.toggleMenuParent = function (parent) {

    if (!parent) {
      return false;
    }


    const childMenu =
      parent.nextElementSibling;


    if (
      !childMenu ||
      !childMenu.classList.contains("child-menu")
    ) {

      return false;

    }


    if (
      !childMenu.classList.contains("hidden")
    ) {

      childMenu.classList.add("hidden");

      parent.classList.remove("active");

      return false;

    }


    openMenuParent(parent);

    return true;

  };


  /*
   * ==========================================================
   * OPEN MENU PARENT FROM URL
   * ==========================================================
   *
   * Parent menu links are now normal URLs.
   *
   * Example:
   *
   *     /html/hypnosis/landing.html#hypnosis
   *
   * After the browser loads the page, use the URL hash to
   * determine which parent menu should be expanded.
   *
   */

  function openMenuParentFromUrl() {

    if (!menu) {
      return;
    }


    const hash =
      window.location.hash;


    if (!hash) {
      return;
    }


    const menuId =
      hash.substring(1);


    if (!menuId) {
      return;
    }


    const parent =
      menu.querySelector(
        '.menu-item.parent[href$="#' +
        CSS.escape(menuId) +
        '"]'
      );


    if (!parent) {
      return;
    }


    openMenuParent(parent);

  };


  /*
   * ==========================================================
   * HIDE MENU
   * ==========================================================
   */

  function hideMenu() {

    if (!menu || !content) {
      return;
    }


    menu.style.display = "none";


    if (menuVisibility) {

      const hamburger =
        menuVisibility.querySelector(
          ".hamburger-icon"
        );

      const closeIcon =
        menuVisibility.querySelector(
          ".close-icon"
        );


      if (hamburger) {
        hamburger.style.display = "inline";
      }


      if (closeIcon) {
        closeIcon.style.display = "none";
      }

    }


    content.classList.add("hidden-menu");

    content.style.marginRight = "0";

    document.body.classList.remove("visible");

  };


  /*
   * ==========================================================
   * SHOW MENU
   * ==========================================================
   */

  function showMenu() {

    if (!menu || !content) {
      return;
    }


    menu.style.display = "block";


    if (menuVisibility) {

      const hamburger =
        menuVisibility.querySelector(
          ".hamburger-icon"
        );

      const closeIcon =
        menuVisibility.querySelector(
          ".close-icon"
        );


      if (hamburger) {
        hamburger.style.display = "none";
      }


      if (closeIcon) {
        closeIcon.style.display = "inline";
      }

    }


    content.classList.remove("hidden-menu");

    content.style.marginRight =
      menu.offsetWidth + "px";

    document.body.classList.add("visible");

  };


  /*
   * ==========================================================
   * RESPONSIVE LAYOUT MANAGEMENT
   * ==========================================================
   */

  function handleViewportChange() {

    if (window.innerWidth < 1280) {

      hideMenu();

    } else {

      showMenu();

    }

  };


  /*
   * ==========================================================
   * INITIALIZE MENU
   * ==========================================================
   */

  handleViewportChange();

  openMenuParentFromUrl();


  /*
   * ==========================================================
   * RESPONSIVE RESIZE
   * ==========================================================
   */

  window.addEventListener(
    "resize",
    function () {

      if (window.innerWidth < 1280) {

        hideMenu();

      } else if (
        menu &&
        menu.style.display === "block"
      ) {

        content.style.marginRight =
          menu.offsetWidth + "px";

      }

    }
  );


  /*
   * ==========================================================
   * MENU VISIBILITY BUTTON
   * ==========================================================
   */

  if (menuVisibility) {

    menuVisibility.addEventListener(
      "click",
      function (event) {

        event.preventDefault();


        if (
          !menu ||
          menu.style.display === "none" ||
          menu.style.display === ""
        ) {

          showMenu();

        } else {

          hideMenu();

        }

      }
    );

  }


  /*
   * ==========================================================
   * MESSAGE BOX
   * ==========================================================
   */

  const messageBox =
    document.querySelector(".message-box");

  const closeButton =
    document.querySelector(".close-btn");


  if (
    messageBox &&
    closeButton
  ) {

    messageBox.style.display = "flex";


    closeButton.addEventListener(
      "click",
      function () {

        messageBox.style.display = "none";

      }
    );

  }

}


document.addEventListener(
  "DOMContentLoaded",
  init
);
