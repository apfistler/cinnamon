#!/usr/bin/env python3

import argparse
import os
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString


BASE_URL = 'https://www.adamfistler.com/'


def derive_output_filename(input_filename, extension):
    input_path = os.path.abspath(input_filename)
    output_dir = os.path.abspath('output')

    try:
        relative_path = os.path.relpath(
            input_path,
            output_dir
        )
    except ValueError:
        raise ValueError(
            f"Input file must be located under '{output_dir}': "
            f"'{input_filename}'"
        )

    if (
        relative_path == '..'
        or relative_path.startswith('..' + os.sep)
    ):
        raise ValueError(
            f"Input file must be located under '{output_dir}': "
            f"'{input_filename}'"
        )

    relative_path = os.path.splitext(
        relative_path
    )[0] + extension

    return os.path.join(
        output_dir,
        'substack',
        relative_path
    )


def extract_title(soup):
    title_tag = soup.find('title')

    if title_tag is None:
        raise ValueError(
            'No <title> element found in input HTML'
        )

    title = title_tag.get_text(
        strip=True
    )

    title = title.split(
        '|',
        1
    )[0].strip()

    if not title:
        raise ValueError(
            'Page title is empty'
        )

    return title


def make_urls_absolute(content):
    for tag in content.find_all(
        ['a', 'img', 'source', 'video', 'audio']
    ):

        if tag.name == 'a':
            attribute = 'href'
        else:
            attribute = 'src'

        value = tag.get(attribute)

        if not value:
            continue

        if value.startswith(
            (
                'http://',
                'https://',
                '//',
                'data:',
                'mailto:',
                'tel:',
                '#'
            )
        ):
            continue

        tag[attribute] = urljoin(
            BASE_URL,
            value
        )


def clean_content(soup):
    content = soup.find(
        'div',
        id='content'
    )

    if content is None:
        raise ValueError(
            'No <div id="content"> element found in input HTML'
        )

    # ---------------------------------------------------------------
    # Remove website-only navigation and footers
    # ---------------------------------------------------------------

    breadcrumb = content.find(
        'nav',
        class_='breadcrumb'
    )
    if breadcrumb:
        breadcrumb.decompose()

    footer = content.find(
        'footer',
        id='footer'
    )
    if footer:
        footer.decompose()

    # Optional: Remove bottom site-navigation sections if they shouldn't be in the email/Substack post
    for section in content.find_all('section'):
        heading = section.find(['h2', 'h3'])
        if heading and 'Explore my Technology' in heading.get_text():
            section.decompose()

    # ---------------------------------------------------------------
    # Convert custom image wrappers to Substack-compatible figures
    # ---------------------------------------------------------------

    for img_div in content.find_all('div', class_='content-img'):
        img = img_div.find('img')
        if img:
            figure = soup.new_tag('figure', **{'class': 'image'})
            figure.append(img.extract())
            
            # Preserve alt text as a caption if present
            alt_text = img.get('alt')
            if alt_text:
                figcaption = soup.new_tag('figcaption')
                figcaption.string = alt_text
                figure.append(figcaption)
                
            img_div.replace_with(figure)

    # ---------------------------------------------------------------
    # Remove trailing whitespace and <br> elements left behind
    # ---------------------------------------------------------------

    while content.contents:
        last = content.contents[-1]

        if getattr(last, 'name', None) == 'br':
            last.extract()
            continue

        if isinstance(last, NavigableString) and not last.strip():
            last.extract()
            continue

        break

    # ---------------------------------------------------------------
    # Convert relative URLs
    # ---------------------------------------------------------------

    make_urls_absolute(
        content
    )

    return content


def generate_html(content):
    return ''.join(
        str(element)
        for element in content.contents
    ).strip() + '\n'


def inline_to_markdown(element):
    if isinstance(element, NavigableString):
        return str(element)

    if not getattr(element, 'name', None):
        return ''

    tag = element.name

    if tag in ('strong', 'b'):
        return '**' + ''.join(
            inline_to_markdown(child)
            for child in element.children
        ) + '**'

    if tag in ('em', 'i'):
        return '*' + ''.join(
            inline_to_markdown(child)
            for child in element.children
        ) + '*'

    if tag == 'code':
        return '`' + element.get_text() + '`'

    if tag == 'a':
        text = ''.join(
            inline_to_markdown(child)
            for child in element.children
        ).strip()

        href = element.get('href', '')

        if not href:
            return text

        return f'[{text}]({href})'

    if tag == 'br':
        return '  \n'

    if tag == 'img':
        alt = element.get('alt', '').strip()
        src = element.get('src', '').strip()

        if not src:
            return ''

        return f'![{alt}]({src})'

    if tag in ('span', 'small', 'sub', 'sup'):
        return ''.join(
            inline_to_markdown(child)
            for child in element.children
        )

    return ''.join(
        inline_to_markdown(child)
        for child in element.children
    )


def block_to_markdown(element, list_level=0):
    if isinstance(element, NavigableString):
        return str(element).strip()

    if not getattr(element, 'name', None):
        return ''

    tag = element.name

    if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        level = int(tag[1])
        text = ''.join(
            inline_to_markdown(child)
            for child in element.children
        ).strip()

        return '#' * level + ' ' + text + '\n\n'

    if tag == 'p':
        text = ''.join(
            inline_to_markdown(child)
            for child in element.children
        ).strip()

        if not text:
            return ''

        return text + '\n\n'

    if tag == 'blockquote':
        text = ''.join(
            block_to_markdown(child)
            for child in element.children
        ).strip()

        if not text:
            return ''

        lines = text.splitlines()

        return ''.join(
            '> ' + line + '\n'
            for line in lines
        ) + '\n'

    if tag == 'ul':
        output = ''

        for item in element.find_all(
            'li',
            recursive=False
        ):
            text = ''.join(
                inline_to_markdown(child)
                for child in item.children
                if getattr(child, 'name', None) not in ('ul', 'ol')
            ).strip()

            output += '- ' + text + '\n'

            for nested in item.find_all(
                ['ul', 'ol'],
                recursive=False
            ):
                nested_text = block_to_markdown(
                    nested,
                    list_level + 1
                )

                nested_lines = nested_text.rstrip().splitlines()

                output += ''.join(
                    '  ' + line + '\n'
                    for line in nested_lines
                )

        return output + '\n'

    if tag == 'ol':
        output = ''
        number = 1

        for item in element.find_all(
            'li',
            recursive=False
        ):
            text = ''.join(
                inline_to_markdown(child)
                for child in item.children
                if getattr(child, 'name', None) not in ('ul', 'ol')
            ).strip()

            output += f'{number}. {text}\n'
            number += 1

        return output + '\n'

    if tag == 'hr':
        return '---\n\n'

    if tag == 'figure':
        return ''.join(
            block_to_markdown(child)
            if getattr(child, 'name', None)
            else str(child)
            for child in element.children
        ) + '\n'

    return ''.join(
        block_to_markdown(child, list_level)
        if getattr(child, 'name', None)
        else str(child)
        for child in element.children
    )


def generate_markdown(content):
    markdown = ''.join(
        block_to_markdown(element)
        for element in content.children
    )

    markdown = re.sub(
        r'[ \t]+\n',
        '\n',
        markdown
    )

    markdown = re.sub(
        r'\n{3,}',
        '\n\n',
        markdown
    )

    return markdown.strip() + '\n'


def main():
    parser = argparse.ArgumentParser(
        description='Generate Substack-ready HTML and Markdown from rendered HTML'
    )

    parser.add_argument(
        'input_filename',
        type=str,
        help='Rendered HTML file'
    )

    args = parser.parse_args()

    input_filename = os.path.abspath(
        args.input_filename
    )

    if not os.path.isfile(input_filename):
        parser.error(
            f"input file does not exist: '{args.input_filename}'"
        )

    try:
        with open(
            input_filename,
            'r',
            encoding='utf-8'
        ) as input_file:
            html = input_file.read()

        soup = BeautifulSoup(
            html,
            'html.parser'
        )

        title = extract_title(
            soup
        )

        content = clean_content(
            soup
        )

        html_output = generate_html(
            content
        )

        markdown_output = generate_markdown(
            content
        )

        html_filename = derive_output_filename(
            input_filename,
            '.html'
        )

        markdown_filename = derive_output_filename(
            input_filename,
            '.md'
        )

        html_directory = os.path.dirname(
            html_filename
        )

        os.makedirs(
            html_directory,
            exist_ok=True
        )

        with open(
            html_filename,
            'w',
            encoding='utf-8'
        ) as output_file:
            output_file.write(
                html_output
            )

        with open(
            markdown_filename,
            'w',
            encoding='utf-8'
        ) as output_file:
            output_file.write(
                markdown_output
            )

    except ValueError as error:
        parser.error(
            str(error)
        )

    print(
        f'Title: {title}'
    )

    print(
        f'HTML:  {html_filename}'
    )

    print(
        f'MD:    {markdown_filename}'
    )


if __name__ == '__main__':
    main()
