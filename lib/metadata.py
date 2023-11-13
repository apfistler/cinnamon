import os
import yaml

class Metadata:
    def __init__(self, input_filename):
        # Strip the extension and add .yaml
        base_filename = os.path.splitext(input_filename)[0]
        self.metadata_file = f'{base_filename}.yaml'
        self.metadata = self.load_metadata()

    def load_metadata(self):
        try:
            with open(self.metadata_file, 'r') as file:
                metadata = yaml.safe_load(file)
                if 'title' not in metadata or 'keywords' not in metadata or 'category' not in metadata or 'name' not in metadata:
                    raise ValueError("Title, keywords, category, and name must be present in the metadata YAML file.")
                return metadata
        except FileNotFoundError:
            raise FileNotFoundError(f"Metadata file '{self.metadata_file}' not found.")
        except yaml.YAMLError:
            raise ValueError(f"Invalid YAML format in '{self.metadata_file}'.")

    def generate_output_filename(self, output_dir):
        category = self.metadata.get('category', 'default_category')
        name = self.metadata.get('name', 'default_name')
        output_directory = os.path.join(output_dir, 'html', category)
        os.makedirs(output_directory, exist_ok=True)
        return os.path.join(output_directory, f'{name}.html')

