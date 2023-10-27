class Input:
    def __init__(self, filename):
        self.filename = filename

    def read_lines(self):
        try:
            with open(self.filename, 'r') as file:
                lines = file.readlines()
            return lines
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file '{self.filename}' not found.")

    def read_title(self):
        with open(self.filename, 'r') as input_file:
            return input_file.readline().strip()

    def read_content(self):
        with open(self.filename, 'r') as input_file:
            return input_file.readlines()[1:]

