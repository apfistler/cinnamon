class Template:
    def __init__(self, filename):
        self.filename = filename

    def read_lines(self):
        with open(self.filename, 'r') as template_file:
            return template_file.readlines()

