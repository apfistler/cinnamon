import os
import yaml


class Metadata:
    def __init__(self, input_dir):
        self.input_dir = os.path.normpath(input_dir)

        # Page name is the directory name
        self.name = os.path.basename(self.input_dir)

        # Metadata lives inside the page directory
        self.metadata_file = os.path.join(
            self.input_dir,
            f'{self.name}.yaml'
        )

        self.metadata = self.load_metadata()

    def load_metadata(self):
        try:
            with open(self.metadata_file, 'r') as file:
                metadata = yaml.safe_load(file) or {}

                required = [
                    'title',
                    'keywords',
                    'category',
                    'name'
                ]

                missing = [
                    key for key in required
                    if key not in metadata
                ]

                if missing:
                    raise ValueError(
                        'Missing required metadata: '
                        + ', '.join(missing)
                    )

                return metadata

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Metadata file '{self.metadata_file}' not found."
            )

        except yaml.YAMLError:
            raise ValueError(
                f"Invalid YAML format in '{self.metadata_file}'."
            )

    def generate_output_filename(self, output_dir):
        category = self.metadata.get(
            'category',
            'default_category'
        )

        name = self.metadata.get(
            'name',
            'default_name'
        )

        output_directory = os.path.join(
            output_dir,
            'html',
            category
        )

        os.makedirs(
            output_directory,
            exist_ok=True
        )

        return os.path.join(
            output_directory,
            f'{name}.html'
        )
