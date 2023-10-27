class Output:
    def __init__(self, filename):
        self.filename = filename

    def write(self, content):
        with open(self.filename, 'w') as output_file:
            output_file.write(content)

