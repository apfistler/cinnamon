/* ==========================================================
   CONTACT ADAM FORM
   ========================================================== */


/* ==========================================================
   INITIALIZE FORM
   ========================================================== */

document.addEventListener(
  'DOMContentLoaded',
  function () {

    const form = document.querySelector(
      '.contact-form'
    );

    if (!form) {
      return;
    }


    /* ------------------------------------------------------
       Phone number formatting
       ------------------------------------------------------ */

    const phone = document.getElementById(
      'phone'
    );

    if (phone) {

      phone.addEventListener(
        'input',
        function () {

          let digits = phone.value.replace(
            /\D/g,
            ''
          );

          /*
           * Limit to a standard US phone number.
           */

          digits = digits.substring(
            0,
            10
          );


          /*
           * Format progressively:
           *
           * 6
           * 609
           * (609) 2
           * (609) 200
           * (609) 200-0
           * (609) 200-0230
           */

          if (digits.length <= 3) {

            phone.value = digits;

          } else if (digits.length <= 6) {

            phone.value =
              '(' +
              digits.substring(0, 3) +
              ') ' +
              digits.substring(3);

          } else {

            phone.value =
              '(' +
              digits.substring(0, 3) +
              ') ' +
              digits.substring(3, 6) +
              '-' +
              digits.substring(6);

          }

        }
      );

    }


    /* ------------------------------------------------------
       Form validation
       ------------------------------------------------------ */

    form.addEventListener(
      'submit',
      function (event) {

        /*
         * Let the browser perform its normal
         * required-field and email validation first.
         */

        if (!form.checkValidity()) {

          event.preventDefault();

          form.reportValidity();

          return;
        }


        /* --------------------------------------------------
           Validate email address
           -------------------------------------------------- */

        const email =
          document.getElementById('email');

        if (email) {

          const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

          if (
            !emailPattern.test(
              email.value.trim()
            )
          ) {

            event.preventDefault();

            email.setCustomValidity(
              'Please enter a valid email address.'
            );

            email.reportValidity();

            return;

          } else {

            email.setCustomValidity('');

          }

        }


        /* --------------------------------------------------
           Validate subject
           -------------------------------------------------- */

        const subject =
          document.getElementById('subject');

        if (subject) {

          if (!subject.value.trim()) {

            event.preventDefault();

            subject.setCustomValidity(
              'Please select a subject.'
            );

            subject.reportValidity();

            return;

          } else {

            subject.setCustomValidity('');

          }

        }


        /* --------------------------------------------------
           Validate message
           -------------------------------------------------- */

        const message =
          document.getElementById('message');

        if (message) {

          if (!message.value.trim()) {

            event.preventDefault();

            message.setCustomValidity(
              'Please enter a message.'
            );

            message.reportValidity();

            return;

          } else {

            message.setCustomValidity('');

          }

        }

      }
    );


    /* ------------------------------------------------------
       Clear custom validation messages when fields change
       ------------------------------------------------------ */

    const email =
      document.getElementById('email');

    if (email) {

      email.addEventListener(
        'input',
        function () {

          email.setCustomValidity('');

        }
      );

    }


    const subject =
      document.getElementById('subject');

    if (subject) {

      subject.addEventListener(
        'change',
        function () {

          subject.setCustomValidity('');

        }
      );

    }


    const message =
      document.getElementById('message');

    if (message) {

      message.addEventListener(
        'input',
        function () {

          message.setCustomValidity('');

        }
      );

    }

  }
);
