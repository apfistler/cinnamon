#!/usr/bin/python3

import cgi
import html
import os
import re
import subprocess
import yaml


CONFIG_FILE = (
    '/etc/contact_adam.yaml'
)


# ==========================================================
# CONFIGURATION
# ==========================================================

def load_config():

    if not os.path.isfile(
            CONFIG_FILE
        ):

        raise RuntimeError(
            'Configuration file not found.'
        )

    with open(
            CONFIG_FILE,
            'r',
            encoding='utf-8'
        ) as config_file:

        config = yaml.safe_load(
            config_file
        )

    return config or {}


# ==========================================================
# VALIDATION
# ==========================================================

def clean(value):

    if value is None:
        return ''

    return str(value).strip()


def valid_email(email):

    pattern = (
        r'^[A-Za-z0-9._%+-]+'
        r'@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    )

    return bool(
        re.match(
            pattern,
            email
        )
    )


def valid_phone(phone):

    if not phone:
        return True

    digits = re.sub(
        r'\D',
        '',
        phone
    )

    return len(digits) == 10


# ==========================================================
# HTML RESPONSE
# ==========================================================

def response_page(title, message):

    print(
        'Content-Type: text/html; charset=utf-8'
    )

    print()

    print(
        '<!DOCTYPE html>'
    )

    print(
        '<html lang="en">'
    )

    print(
        '<head>'
    )

    print(
        '<meta charset="UTF-8">'
    )

    print(
        '<meta name="viewport" '
        'content="width=device-width, initial-scale=1.0">'
    )

    print(
        f'<title>{html.escape(title)}</title>'
    )

    print(
        '<link rel="stylesheet" '
        'href="/css/main.css">'
    )

    print(
        '<link rel="stylesheet" '
        'href="/css/form.css">'
    )

    print(
        '</head>'
    )

    print(
        '<body>'
    )

    print(
        '<main class="main">'
    )

    print(
        f'<h1>{html.escape(title)}</h1>'
    )

    print(
        '<p class="form-response">'
        f'{html.escape(message)}'
        '</p>'
    )

    print(
        '<p class="form-response">'
        '<a href="/html/main/contact_adam.html">'
        'Return to Contact Adam'
        '</a>'
        '</p>'
    )

    print(
        '</main>'
    )

    print(
        '</body>'
    )

    print(
        '</html>'
    )

def redirect_page(url):

    print(
        'Status: 302 Found'
    )

    print(
        f'Location: {url}'
    )

    print()


# ==========================================================
# SEND EMAIL
# ==========================================================

def send_message(
        destination,
        name,
        email,
        phone,
        subject,
        message
    ):

    # Prevent header injection.
    header_values = [
        name,
        email,
        phone,
        subject
    ]

    for value in header_values:

        if '\r' in value or '\n' in value:

            raise ValueError(
                'Invalid header data.'
            )

    email_message = (
        f'To: {destination}\n'
        f'From: {destination}\n'
        f'Reply-To: {email}\n'
        f'Subject: Contact Form: {subject}\n'
        f'Content-Type: text/plain; '
        f'charset="UTF-8"\n'
        f'\n'
        f'Name: {name}\n'
        f'Subject: {subject}\n'
        f'Email: {email}\n'
        f'Phone: {phone or "Not provided"}\n'
        f'\n'
        f'Message:\n'
        f'{message}\n'
    )

    process = subprocess.run(
        [
            '/usr/sbin/sendmail',
            '-t'
        ],
        input=email_message,
        text=True,
        capture_output=True
    )

    if process.returncode != 0:

        raise RuntimeError(
            'Mail delivery failed.'
        )


# ==========================================================
# MAIN
# ==========================================================

def main():

    try:

        config = load_config()

        destination = clean(
            config.get(
                'email',
                ''
            )
        )

        if not destination:

            raise RuntimeError(
                'No destination email configured.'
            )

        form = cgi.FieldStorage()

        name = clean(
            form.getfirst(
                'name',
                ''
            )
        )

        email = clean(
            form.getfirst(
                'email',
                ''
            )
        )

        phone = clean(
            form.getfirst(
                'phone',
                ''
            )
        )

        subject = clean(
            form.getfirst(
                'subject',
                ''
            )
        )

        message = clean(
            form.getfirst(
                'message',
                ''
            )
        )

        # --------------------------------------------------
        # Required fields
        # --------------------------------------------------

        if not name:

            response_page(
                'Message Not Sent',
                'Please enter your name.'
            )

            return

        if not email:

            response_page(
                'Message Not Sent',
                'Please enter your email address.'
            )

            return

        if not subject:

            response_page(
                'Message Not Sent',
                'Please select a subject.'
            )

            return

        if not message:

            response_page(
                'Message Not Sent',
                'Please enter a message.'
            )

            return

        # --------------------------------------------------
        # Email validation
        # --------------------------------------------------

        if not valid_email(email):

            response_page(
                'Message Not Sent',
                'Please enter a valid email address.'
            )

            return

        # --------------------------------------------------
        # Phone validation
        # --------------------------------------------------

        if not valid_phone(phone):

            response_page(
                'Message Not Sent',
                'Please enter a valid 10-digit phone number.'
            )

            return

        # --------------------------------------------------
        # Send
        # --------------------------------------------------

        send_message(
            destination,
            name,
            email,
            phone,
            subject,
            message
        )

        redirect_page(
            '/html/main/contact_adam_complete.html'
        )

    except Exception:

        response_page(
            'Message Not Sent',
            'Sorry, there was a problem sending your '
            'message. Please try again later.'
        )


if __name__ == '__main__':

    main()
