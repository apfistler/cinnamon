#!/usr/bin/env python3

import argparse
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

def clean_quotes(text):
    return text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")

def extract_subject_from_content(content):
    soup = BeautifulSoup(content, 'html.parser')
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    h2 = soup.find('h2')
    if h2:
        return h2.get_text(strip=True)
    return "New Substack Draft"

def send_to_substack(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Input file does not exist: '{file_path}'")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = clean_quotes(content)

    # Determine if input is Markdown or HTML
    if file_path.endswith('.md'):
        subject = "New Substack Draft"
        for line in content.splitlines():
            if line.startswith('# '):
                subject = line.lstrip('# ').strip()
                break
        html_body = f"<div style='font-family: sans-serif; line-height: 1.6;'><pre style='font-family: inherit; white-space: pre-wrap;'>{content}</pre></div>"
        plain_body = content
    else:
        subject = extract_subject_from_content(content)
        html_body = content
        # Strip tags for a clean plain-text fallback part
        soup = BeautifulSoup(content, 'html.parser')
        plain_body = soup.get_text()

    # Build a strict multipart/alternative message structure required by Substack's ingestion parser
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'adam@adamfistler.com'
    msg['To'] = 'adamfistler@substack.com'
    msg['Reply-To'] = 'adam@adamfistler.com'

    # Attach plain text and HTML alternatives explicitly
    part_plain = MIMEText(plain_body, 'plain', 'utf-8')
    part_html = MIMEText(html_body, 'html', 'utf-8')

    msg.attach(part_plain)
    msg.attach(part_html)

    smtp_host = 'localhost'
    smtp_port = 25

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.send_message(msg)
        print(f"Successfully sent '{file_path}' to Substack as a structured draft with subject: '{subject}'.")
    except Exception as e:
        print(f"Failed to send email via SMTP: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Publish generated HTML or Markdown files directly to Substack via SMTP as a clean draft'
    )
    parser.add_argument(
        'input_filename',
        type=str,
        help='Path to the HTML or MD file to publish'
    )

    args = parser.parse_args()
    send_to_substack(args.input_filename)

if __name__ == '__main__':
    main()
