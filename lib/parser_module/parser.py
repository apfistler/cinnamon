import re
import yaml

class Parser:
    def __init__(self, input_obj, template_obj, config_filename, output_obj, metadata):
        self.input_obj = input_obj
        self.template_obj = template_obj
        self.config = self.load_config(config_filename)
        self.output_obj = output_obj
        self.metadata = metadata  # Metadata dictionary passed from main.py

    def load_config(self, config_filename):
        with open(config_filename, 'r') as config_file:
            config = yaml.safe_load(config_file)
        return config

    def parse_template(self):
        input_lines = self.input_obj.read_lines()  # Assuming read_lines() reads lines from the input file
        input_keywords = self.input_obj.extract_keywords()  # Extract keywords from input file
        template_lines = self.template_obj.read_lines()

        # Use metadata title as the HTML title
        title = self.metadata['title']

        # Assuming self.config and self.metadata are dictionaries
        if 'keywords' in self.config and 'keywords' in self.metadata:
          keywords = ', '.join(set(self.config['keywords']) | set(self.metadata['keywords']) | set(input_keywords))
        else:
          # Handle the case where either self.config['keywords'] or self.metadata['keywords'] is missing
          keywords = ', '.join(set(input_keywords))

#        keywords = ', '.join(set(self.config['keywords']) | set(self.metadata['keywords']) | set(input_keywords))
#        keywords = keywords.sort()

        keywords = ', '.join(set(self.config['keywords']) | set(self.metadata['keywords']) | set(input_keywords))
        keywords_list = keywords.split(', ')
        keywords_list.sort()
        keywords = ', '.join(keywords_list)


        # Get CSS links from metadata YAML
        css_links = self.metadata.get('css', [])  # Assuming 'css' is the key in your YAML containing CSS file paths
        css_tags = "\n".join([f'<link rel="stylesheet" href="{css_link}">' for css_link in css_links])

        html_lines = []
        menu_items = self.config.get('menu', {})  # Get menu items from metadata

        for template_line in template_lines:
            template_line = re.sub('\n', '', template_line)

            if '<!-- TITLE -->' in template_line:
                html_lines.append(template_line.replace('<!-- TITLE -->', title))
            elif '<!-- KEYWORDS -->' in template_line:
                html_lines.append(template_line.replace('<!-- KEYWORDS -->', keywords))
            elif '<!-- MENU_DIV -->' in template_line:
                leading_whitespace = template_line[:len(template_line) - len(template_line.lstrip())]
                menu_html = self.generate_menu(leading_whitespace)
                html_lines.append(menu_html)
            elif '<!-- CSS -->' in template_line:
                # Preserve the leading whitespace (indentation) from the template line
                leading_whitespace = template_line[:len(template_line) - len(template_line.lstrip())]
                indented_css_tags = "\n".join([f'{leading_whitespace}<link rel="stylesheet" href="{css_link}">' for css_link in css_links])
                html_lines.append(indented_css_tags)
            elif '<!-- CONTENT_DIV -->' in template_line:
                padding = template_line[:len(template_line) - len(template_line.lstrip())]
                html_lines.append(self.get_input(padding, input_lines))  # Pass input_lines to get_input method
            else:
                html_lines.append(template_line)

        html = '\n'.join(html_lines)
        self.output_obj.write(html)

    def generate_menu(self, indent):
        menu_items = self.config.get('menu', {})  # Get the menu items from the configuration as a dictionary
 
        menu_html = []
        for label, link in menu_items.items():  # Iterate through the dictionary
            if isinstance(link, dict):  # Check if the item is a hash (dictionary)
                menu_html.append(f'{indent}<li><a class="menu-item parent active" href="javascript:void(0)">{label}</a>')
                menu_html.append(f'{indent}  <ul class="child-menu hidden">')
                for child_label, child_link in link.items():  # Iterate through child items without sorting
                    menu_html.append(f'{indent}    <li><a class="menu-item child active" href="{child_link}">{child_label}</a></li>')
                menu_html.append(f'{indent}  </ul>')
                menu_html.append(f'{indent}</li>')
            else:
                menu_html.append(f'{indent}<li><a class="menu-item" href="{link}">{label}</a></li>')
 
        return '\n'.join(menu_html)

    def get_input(self, padding, input_lines):

        processed_lines = []
        for line in input_lines:
            # Replace specific hard-coded placeholder
            if '<!-- HYPNOSIS_ISSUES -->' in line:
                hypnosis_list_html = self.generate_hypnosis_list()
                line = line.replace('<!-- HYPNOSIS_ISSUES -->', hypnosis_list_html)
            # Handle table data replacement
            elif '<!-- DISPLAY_TABLE name=' in line:
                table_directive = re.search(r'<!-- DISPLAY_TABLE name=["\'](.*?)["\'] -->', line)
                if table_directive:
                    table_name = table_directive.group(1)
                    table_data = self.metadata.get('display_table', {}).get(table_name, [])
 
                    if table_data:
                        table_html = self.construct_table_from_data(table_data)
                        processed_lines.append(table_html)
                        continue  # Skip processing the current line further
                    else:
                        processed_lines.append('<!-- Invalid table name: {} -->'.format(table_name))
                        continue  # Skip processing the current line further 
            # Find and replace all other placeholders dynamically from the config
            placeholders = re.findall(r'<!-- (.*?) -->', line)

            for placeholder in placeholders:
                placeholder_lower = placeholder.lower()
                keys = placeholder_lower.split('.')
                value = self.config

                for key in keys:
                    value = value.get(key, None)
                    if value is None:
                        break

                if value is not None:
                    line = line.replace(f'<!-- {placeholder} -->', str(value))
                else:
                    line = line.replace(f'<!-- {placeholder} -->', '')

            # Add padding and add processed line to the result
            processed_line = f'{padding}{line}'
            processed_lines.append(processed_line)

        return '\n'.join(processed_lines)

    def construct_table_from_data(self, table_data):
        table_html = '<table class="display-table">'
        num_columns = 2  # Number of columns in the table
    
        for i in range(0, len(table_data), num_columns):
            item1 = table_data[i]
            item2 = table_data[i + 1] if i + 1 < len(table_data) else None
    
            table_html += '<tr>'
            table_html += self.construct_table_cell(item1)
            if item2:
                table_html += self.construct_table_cell(item2)
            table_html += '</tr>'
    
        table_html += '</table>'
        return table_html
    
    def construct_table_cell(self, item):
        image_url = item.get('image', '')
        caption = item.get('caption', '')
        title = item.get('title', '')
        content = item.get('content', '')
        link = item.get('link', '')  # Check for the link field in metadata
 
        if link:
            # Wrap the image with <a> tag if link field exists
            #image_tag = f'<a href="{link}"><img src="{image_url}" alt="{caption}" /></a>'
            image_tag = f'<img src="{image_url}" alt="{caption}" />'
            title_tag = f'<span class="highlight"><a href="{link}">{title}</a></span>'
            figure_class = f'<a href="{link}">' \
                           f'<figure class="content-img caption left link">' \
                           f'{image_tag}' \
                           f'<figcaption>{caption}</figcaption>' \
                           f'</figure>' \
                           f'</a>'
        else:
            image_tag = f'<img src="{image_url}" alt="{caption}" />'
            title_tag = f'<span class="highlight">{title}</span>'
            figure_class = f'<figure class="content-img caption left">' \
                           f'{image_tag}' \
                           f'<figcaption>{caption}</figcaption>' \
                           f'</figure>'
 
        cell_html = f'<td>' \
                    f'<div class="display-table">' \
                    f'<div class="display-table left">' \
                    f'{figure_class}' \
                    f'</div>' \
                    f'<div class="display-table right">' \
                    f'{title_tag}{content}' \
                    f'</div>' \
                    f'</div>' \
                    f'</td>'
 
        return cell_html
  
    def generate_hypnosis_list(self):
        hypnosis_issues = self.config.get('hypnosis', {}).get('issues', [])
        num_columns = self.config.get('hypnosis', {}).get('issue_columns', 1)
        items_per_column = max(len(hypnosis_issues) // num_columns, 1)

        hypnosis_list_html = ['<div class="hypnosis-list-container">']

        for i in range(num_columns):
            start_idx = i * items_per_column
            end_idx = start_idx + items_per_column
            column_items = hypnosis_issues[start_idx:end_idx]
            column_items.sort()

            hypnosis_list_html.append('  <ul class="hypnosis-issue-list">')
            for issue in column_items:
                hypnosis_list_html.append(f'    <li class="hypnosis-issue">{issue}</li>')
            hypnosis_list_html.append('  </ul>')

        hypnosis_list_html.append('</div>')
        return '\n'.join(hypnosis_list_html)

