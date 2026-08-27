import os
import re
import html
import yaml


class Parser:

    def __init__(
            self,
            input_dir,
            template_obj,
            config_filename,
            output_obj
        ):

        self.input_dir = os.path.normpath(input_dir)
        self.template_obj = template_obj
        self.output_obj = output_obj

        # Page name is the directory name
        self.page_name = os.path.basename(
            self.input_dir
        )

        # Page files
        self.input_filename = os.path.join(
            self.input_dir,
            f'{self.page_name}.html'
        )

        self.metadata_filename = os.path.join(
            self.input_dir,
            f'{self.page_name}.yaml'
        )

        # Snippet directory
        self.snippet_dir = os.path.join(
            self.input_dir,
            'snippet'
        )

        # Global configuration
        self.config = self.load_config(
            config_filename
        )

        # Page-specific metadata
        self.metadata = self.load_config(
            self.metadata_filename
        )

        # Merge page metadata over global configuration
        self.config = self.merge_config(
            self.config,
            self.metadata
        )


    # ==========================================================
    # CONFIGURATION
    # ==========================================================

    def load_config(self, config_filename):

        if not os.path.isfile(
                config_filename
            ):

            return {}

        with open(
                config_filename,
                'r',
                encoding='utf-8'
            ) as config_file:

            config = yaml.safe_load(
                config_file
            )

        return config or {}


    def merge_config(self, base, override):

        result = base.copy()

        for key, value in override.items():

            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):

                result[key] = self.merge_config(
                    result[key],
                    value
                )

            else:

                result[key] = value

        return result


    # ==========================================================
    # INPUT
    # ==========================================================

    def read_input(self):

        with open(
                self.input_filename,
                'r',
                encoding='utf-8'
            ) as input_file:

            return input_file.readlines()


    # ==========================================================
    # TEMPLATE
    # ==========================================================

    def parse_template(self):

        input_lines = self.read_input()
        template_lines = self.template_obj.read_lines()

        title = self.metadata.get(
            'title',
            ''
        )


        tagline = self.config.get(
           'tagline',
           ''
        )

        if tagline:
            title = f'{title} | {tagline}'

        input_keywords = self.extract_keywords(
            input_lines
        )

        config_keywords = self.config.get(
            'keywords',
            []
        )

        metadata_keywords = self.metadata.get(
            'keywords',
            []
        )

        keywords = set(
            config_keywords
            + metadata_keywords
            + input_keywords
        )

        keywords = sorted(
            keywords
        )

        keywords = ', '.join(
            keywords
        )

        css_links = self.metadata.get(
            'css',
            []
        )

        html_lines = []

        for template_line in template_lines:

            template_line = (
                template_line.rstrip('\n')
            )

            if '<!-- TITLE -->' in template_line:

                html_lines.append(
                    template_line.replace(
                        '<!-- TITLE -->',
                        title
                    )
                )

            elif '<!-- KEYWORDS -->' in template_line:

                html_lines.append(
                    template_line.replace(
                        '<!-- KEYWORDS -->',
                        keywords
                    )
                )

            elif '<!-- MENU_DIV -->' in template_line:

                leading_whitespace = (
                    template_line[
                        :len(template_line)
                        - len(template_line.lstrip())
                    ]
                )

                menu_html = self.generate_menu(
                    leading_whitespace
                )

                html_lines.append(
                    menu_html
                )

            elif '<!-- CSS -->' in template_line:

                leading_whitespace = (
                    template_line[
                        :len(template_line)
                        - len(template_line.lstrip())
                    ]
                )

                css_tags = []

                for css_link in css_links:

                    css_tags.append(
                        f'{leading_whitespace}'
                        f'<link rel="stylesheet" '
                        f'href="{css_link}">'
                    )

                html_lines.append(
                    '\n'.join(css_tags)
                )

            elif '<!-- CONTENT_DIV -->' in template_line:

                padding = (
                    template_line[
                        :len(template_line)
                        - len(template_line.lstrip())
                    ]
                )

                content = self.get_input(
                    padding,
                    input_lines
                )

                html_lines.append(
                    content
                )

            else:

                html_lines.append(
                    template_line
                )

        output_html = '\n'.join(
            html_lines
        )

        self.output_obj.write(
            output_html
        )


    # ==========================================================
    # KEYWORDS
    # ==========================================================

    def extract_keywords(self, input_lines):

        keywords = []

        for line in input_lines:

            matches = re.findall(
                r'<meta[^>]+keywords\s*=\s*["\']([^"\']*)["\']',
                line,
                re.IGNORECASE
            )

            for match in matches:

                keywords.extend(
                    keyword.strip()
                    for keyword in match.split(',')
                    if keyword.strip()
                )

        return keywords


    # ==========================================================
    # MENU
    # ==========================================================

    def generate_menu(self, indent):

        menu_items = self.config.get(
            'menu',
            {}
        )

        menu_html = []

        for label, item in menu_items.items():

            # --------------------------------------------------
            # Parent menu item
            #
            # YAML:
            #
            # Hypnosis:
            #   url: /html/hypnosis/landing.html#hypnosis
            #   children:
            #     About Hypnosis: /html/hypnosis/about_hypnosis.html
            #
            # --------------------------------------------------

            if isinstance(item, dict):

                parent_url = item.get(
                    'url',
                    'javascript:void(0)'
                )

                children = item.get(
                    'children',
                    {}
                )

                menu_html.append(
                    f'{indent}<li>'
                )

                menu_html.append(
                    f'{indent}  '
                    f'<a class="menu-item parent active" '
                    f'href="{parent_url}">'
                    f'{label}</a>'
                )

                if children:

                    menu_html.append(
                        f'{indent}  '
                        f'<ul class="child-menu hidden">'
                    )

                    for child_label, child_link in children.items():

                        menu_html.append(
                            f'{indent}    '
                            f'<li>'
                            f'<a class="menu-item child active" '
                            f'href="{child_link}">'
                            f'{child_label}</a>'
                            f'</li>'
                        )

                    menu_html.append(
                        f'{indent}  </ul>'
                    )

                menu_html.append(
                    f'{indent}</li>'
                )

            # --------------------------------------------------
            # Normal menu item
            #
            # YAML:
            #
            # Home:
            #   /html/main/home.html
            #
            # --------------------------------------------------

            else:

                menu_html.append(
                    f'{indent}<li>'
                    f'<a class="menu-item" '
                    f'href="{item}">'
                    f'{label}</a>'
                    f'</li>'
                )

        return '\n'.join(
            menu_html
        )


    # ==========================================================
    # CONTENT PROCESSING
    # ==========================================================

    def get_input(self, padding, input_lines):

        processed_lines = []

        for line in input_lines:

            line = line.rstrip('\n')

            # --------------------------------------------------
            # HTML SNIPPETS
            # --------------------------------------------------

            snippet_directive = re.search(
                r'<!--\s*SNIPPET\s+([A-Za-z0-9_-]+)\s*-->',
                line
            )

            if snippet_directive:

                snippet_name = (
                    snippet_directive.group(1)
                )

                snippet_html = (
                    self.load_snippet(
                        snippet_name
                    )
                )

                line_indent = (
                    line[
                        :len(line)
                        - len(line.lstrip())
                    ]
                )

                snippet_lines = (
                    snippet_html.splitlines()
                )

                for snippet_line in snippet_lines:

                    if snippet_line.strip():

                        processed_lines.append(
                            line_indent
                            + snippet_line
                        )

                    else:

                        processed_lines.append(
                            ''
                        )

                continue


            # --------------------------------------------------
            # FAQ
            # --------------------------------------------------

            faq_directive = re.search(
                r'<!--\s*FAQ(?:\s+([A-Za-z0-9_-]+))?\s*-->',
                line,
                re.IGNORECASE
            )

            if faq_directive:

                faq_name = (
                    faq_directive.group(1)
                )

                faq_html = (
                    self.generate_faq(
                        faq_name
                    )
                )

                line_indent = (
                    line[
                        :len(line)
                        - len(line.lstrip())
                    ]
                )

                faq_lines = (
                    faq_html.splitlines()
                )

                for faq_line in faq_lines:

                    if faq_line.strip():

                        processed_lines.append(
                            line_indent
                            + faq_line
                        )

                    else:

                        processed_lines.append(
                            ''
                        )

                continue


            # --------------------------------------------------
            # PRACTICE AREAS
            # --------------------------------------------------

            if '<!-- PRACTICE_AREAS -->' in line:

                practice_html = (
                    self.generate_practice_areas()
                )

                line = line.replace(
                    '<!-- PRACTICE_AREAS -->',
                    practice_html
                )

                processed_lines.append(
                    f'{padding}{line}'
                )

                continue


            # --------------------------------------------------
            # HYPNOSIS ISSUES
            # --------------------------------------------------

            if '<!-- HYPNOSIS_ISSUES -->' in line:

                hypnosis_list_html = (
                    self.generate_hypnosis_list()
                )

                line = line.replace(
                    '<!-- HYPNOSIS_ISSUES -->',
                    hypnosis_list_html
                )

                processed_lines.append(
                    f'{padding}{line}'
                )

                continue


            # --------------------------------------------------
            # DISPLAY TABLES
            # --------------------------------------------------

            elif '<!-- DISPLAY_TABLE name=' in line:

                table_directive = re.search(
                    r'<!-- DISPLAY_TABLE name=["\'](.*?)["\'] -->',
                    line
                )

                if table_directive:

                    table_name = (
                        table_directive.group(1)
                    )

                    table_data = (
                        self.metadata
                        .get('display_table', {})
                        .get(table_name, [])
                    )

                    if table_data:

                        table_html = (
                            self.construct_table_from_data(
                                table_data
                            )
                        )

                        processed_lines.append(
                            table_html
                        )

                        continue

                    else:

                        processed_lines.append(
                            '<!-- Invalid table name: '
                            f'{table_name} -->'
                        )

                        continue


            # --------------------------------------------------
            # GENERIC CONFIGURATION PLACEHOLDERS
            # --------------------------------------------------

            placeholders = re.findall(
                r'<!-- (.*?) -->',
                line
            )

            for placeholder in placeholders:

                placeholder_lower = (
                    placeholder.lower()
                )

                keys = (
                    placeholder_lower.split('.')
                )

                value = self.config

                for key in keys:

                    if not isinstance(
                            value,
                            dict
                        ):

                        value = None
                        break

                    value = value.get(
                        key,
                        None
                    )

                    if value is None:
                        break

                if value is not None:

                    line = line.replace(
                        f'<!-- {placeholder} -->',
                        str(value)
                    )

                else:

                    line = line.replace(
                        f'<!-- {placeholder} -->',
                        ''
                    )

            processed_lines.append(
                f'{padding}{line}'
            )

        return ''.join(
            processed_lines
        )


    # ==========================================================
    # FAQ
    # ==========================================================

    def generate_faq(self, faq_name=None):

        if not faq_name:

            faq_name = self.metadata.get(
                'faq',
                ''
            )

        if not faq_name:

            return (
                '<!-- FAQ: no FAQ name specified -->'
            )

        faq_filename = os.path.join(
            self.input_dir,
            f'{faq_name}.yaml'
        )

        if not os.path.isfile(
                faq_filename
            ):

            return (
                '<!-- FAQ file not found: '
                f'{faq_filename} -->'
            )

        faq_data = self.load_config(
            faq_filename
        )

        if not faq_data:

            return (
                '<!-- FAQ file is empty: '
                f'{faq_filename} -->'
            )

        html_output = []

        faq_title = faq_data.get(
            'title',
            ''
        )

        faq_description = faq_data.get(
            'description',
            ''
        )

        html_output.append(
            '<section class="faq">'
        )

        if faq_title:

            html_output.append(
                f'  <h2 class="faq-title">'
                f'{html.escape(str(faq_title))}'
                f'</h2>'
            )

        if faq_description:

            description_paragraphs = (
                self.format_faq_paragraphs(
                    faq_description
                )
            )

            for paragraph in description_paragraphs:

                html_output.append(
                    f'  <p class="faq-description">'
                    f'{paragraph}'
                    f'</p>'
                )

        topic_areas = faq_data.get(
            'topic_areas',
            []
        )

        for topic in topic_areas:

            topic_title = topic.get(
                'title',
                ''
            )

            questions = topic.get(
                'questions',
                []
            )

            html_output.append(
                '  <section class="faq-topic">'
            )

            if topic_title:

                html_output.append(
                    f'    <h3 class="faq-topic-title">'
                    f'{html.escape(str(topic_title))}'
                    f'</h3>'
                )

            for item in questions:

                question = item.get(
                    'question',
                    ''
                )

                response = item.get(
                    'response',
                    ''
                )

                if not question:

                    continue

                html_output.append(
                    '    <div class="faq-item">'
                )

                html_output.append(
                    '      '
                    '<button '
                    'class="faq-question" '
                    'type="button" '
                    'aria-expanded="false">'
                )

                html_output.append(
                    f'        '
                    f'{html.escape(str(question))}'
                )

                html_output.append(
                    '        '
                    '<span class="faq-question-icon">'
                    '+'
                    '</span>'
                )

                html_output.append(
                    '      </button>'
                )

                html_output.append(
                    '      '
                    '<div class="faq-answer" '
                    'hidden>'
                )

                paragraphs = (
                    self.format_faq_paragraphs(
                        response
                    )
                )

                for paragraph in paragraphs:

                    html_output.append(
                        f'        '
                        f'<p>{paragraph}</p>'
                    )

                html_output.append(
                    '      </div>'
                )

                html_output.append(
                    '    </div>'
                )

            html_output.append(
                '  </section'
            )

        html_output.append(
            '</section>'
        )

        return '\n'.join(
            html_output
        )


    def format_faq_paragraphs(self, text):

        if text is None:

            return []

        if isinstance(
                text,
                list
            ):

            text = '\n\n'.join(
                str(item)
                for item in text
            )

        else:

            text = str(text)

        text = text.replace(
            '\r\n',
            '\n'
        )

        text = text.replace(
            '\r',
            '\n'
        )

        raw_paragraphs = re.split(
            r'\n+',
            text.strip()
        )

        paragraphs = []

        for paragraph in raw_paragraphs:

            paragraph = (
                paragraph.strip()
            )

            if not paragraph:

                continue

            paragraph = re.sub(
                r'\s+',
                ' ',
                paragraph
            )

            paragraph = html.escape(
                paragraph
            )

            paragraphs.append(
                paragraph
            )

        return paragraphs


    # ==========================================================
    # SNIPPETS
    # ==========================================================

    def load_snippet(self, snippet_name):

        snippet_filename = os.path.join(
            self.snippet_dir,
            f'{snippet_name}.html'
        )

        if not os.path.isfile(
                snippet_filename
            ):

            raise FileNotFoundError(
                f"Snippet '{snippet_filename}' "
                f"not found."
            )

        with open(
                snippet_filename,
                'r',
                encoding='utf-8'
            ) as snippet_file:

            return snippet_file.read()


    # ==========================================================
    # PRACTICE AREAS
    # ==========================================================

    def generate_practice_areas(self):

        practice_areas = self.config.get(
            'practice_areas',
            []
        )

        html_output = []

        html_output.append(
            '<section class="practice-areas">'
        )

        html_output.append(
            '  <div class="practice-grid">'
        )

        for practice in practice_areas:

            practice_id = practice.get(
                'id',
                ''
            )

            title = practice.get(
                'title',
                ''
            )

            description = practice.get(
                'description',
                ''
            )

            url = practice.get(
                'url',
                '#'
            )

            svg_filename = os.path.join(
                self.input_dir,
                'svg',
                f'{practice_id}.svg'
            )

            svg_html = ''

            if os.path.isfile(
                    svg_filename
                ):

                with open(
                        svg_filename,
                        'r',
                        encoding='utf-8'
                    ) as svg_file:

                    svg_html = svg_file.read()

            html_output.append(
                f'    <a '
                f'class="practice-card" '
                f'href="{url}">'
            )

            html_output.append(
                '      '
                '<div class="practice-card__content">'
            )

            if svg_html:

                html_output.append(
                    '        '
                    '<div class="practice-card__icon">'
                )

                html_output.append(
                    f'          {svg_html}'
                )

                html_output.append(
                    '        </div>'
                )

            html_output.append(
                f'        <h2>{title}</h2>'
            )

            html_output.append(
                f'        <p>{description}</p>'
            )

            html_output.append(
                '        '
                '<span class="practice-card__link">'
                'Explore →'
                '</span>'
            )

            html_output.append(
                '      </div>'
            )

            html_output.append(
                '    </a>'
            )

        html_output.append(
            '  </div>'
        )

        html_output.append(
            '</section>'
        )

        return '\n'.join(
            html_output
        )

    # ==========================================================
    # DISPLAY TABLES
    # ==========================================================

    def construct_table_from_data(self, table_data):

        table_html = (
            '<table class="display-table">'
        )

        num_columns = 2

        for i in range(
                0,
                len(table_data),
                num_columns
            ):

            item1 = table_data[i]

            item2 = (
                table_data[i + 1]
                if i + 1 < len(table_data)
                else None
            )

            table_html += '<tr>'

            table_html += (
                self.construct_table_cell(
                    item1
                )
            )

            if item2:

                table_html += (
                    self.construct_table_cell(
                        item2
                    )
                )

            table_html += '</tr>'

        table_html += '</table>'

        return table_html


    def construct_table_cell(self, item):

        image_url = item.get(
            'image',
            ''
        )

        caption = item.get(
            'caption',
            ''
        )

        title = item.get(
            'title',
            ''
        )

        content = item.get(
            'content',
            ''
        )

        link = item.get(
            'link',
            ''
        )

        if link:

            image_tag = (
                f'<img src="{image_url}" '
                f'alt="{caption}" />'
            )

            title_tag = (
                f'<span class="highlight">'
                f'<a href="{link}">'
                f'{title}'
                f'</a>'
                f'</span>'
            )

            figure_class = (
                f'<a href="{link}">'
                f'<figure class="content-img '
                f'caption left link">'
                f'{image_tag}'
                f'<figcaption>{caption}'
                f'</figcaption>'
                f'</figure>'
                f'</a>'
            )

        else:

            image_tag = (
                f'<img src="{image_url}" '
                f'alt="{caption}" />'
            )

            title_tag = (
                f'<span class="highlight">'
                f'{title}'
                f'</span>'
            )

            figure_class = (
                f'<figure class="content-img '
                f'caption left">'
                f'{image_tag}'
                f'<figcaption>{caption}'
                f'</figcaption>'
                f'</figure>'
            )

        cell_html = (
            f'<td>'
            f'<div class="display-table">'
            f'<div class="display-table left">'
            f'{figure_class}'
            f'</div>'
            f'<div class="display-table right">'
            f'{title_tag}{content}'
            f'</div>'
            f'</div>'
            f'</td>'
        )

        return cell_html


    # ==========================================================
    # HYPNOSIS ISSUES
    # ==========================================================

    def generate_hypnosis_list(self):

        hypnosis_issues = (
            self.config
            .get('hypnosis', {})
            .get('issues', [])
        )

        num_columns = (
            self.config
            .get('hypnosis', {})
            .get('issue_columns', 1)
        )

        items_per_column = max(
            len(hypnosis_issues)
            // num_columns,
            1
        )

        hypnosis_list_html = [
            '<div class="hypnosis-list-container">'
        ]

        for i in range(
                num_columns
            ):

            start_idx = (
                i * items_per_column
            )

            end_idx = (
                start_idx + items_per_column
            )

            column_items = (
                hypnosis_issues[
                    start_idx:end_idx
                ]
            )

            column_items.sort()

            hypnosis_list_html.append(
                '  <ul class="hypnosis-issue-list">'
            )

            for issue in column_items:

                hypnosis_list_html.append(
                    f'    <li class="hypnosis-issue">'
                    f'{issue}'
                    f'</li>'
                )

            hypnosis_list_html.append(
                '  </ul>'
            )

        hypnosis_list_html.append(
            '</div>'
        )

        return '\n'.join(
            hypnosis_list_html
        )
