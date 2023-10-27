import re
import nltk
import yaml
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter

nltk.download('stopwords')
nltk.download('punkt')

class Input:
    def __init__(self, filename, config_filename):
        self.filename = filename
        self.config = self.load_config(config_filename)
        self.excluded_keywords = self.config.get('excluded_keywords', [])

    def load_config(self, config_filename):
        with open(config_filename, 'r') as config_file:
            config = yaml.safe_load(config_file)
        return config

    def read_lines(self):
        try:
            with open(self.filename, 'r') as file:
                lines = file.readlines()
            return lines
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file '{self.filename}' not found.")

    def extract_keywords(self):
        lines = self.read_lines()
        all_text = ''.join(lines)
 
        # Use regular expression to remove HTML tags
        cleaned_text = re.sub('<[^<]+?>', '', all_text)
 
        # Tokenize the cleaned text into words
        words = word_tokenize(cleaned_text.lower())  # Convert to lowercase for case insensitivity
 
        # Remove stopwords and digits
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words and not word.isdigit()]
 
        # Count the occurrences of each word
        word_counts = Counter(filtered_words)
 
        # Get words that appear more than 2 times
        keywords = [word for word, count in word_counts.items() if count > 2]
 
        # Return the keywords
        return keywords
