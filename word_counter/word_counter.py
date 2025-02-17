# word_counter/word_counter.py
from flask import Blueprint, render_template, request
import re  # For word splitting
from collections import Counter
import logging

wc_bp = Blueprint('wc', __name__, template_folder='templates')  # Corrected name

@wc_bp.route('/word_counter', methods=['GET', 'POST'])
def word_counter():
    word_counts = None # Initialize to None for the initial GET request.
    if request.method == 'POST':
        try:
            file = request.files['file_upload']
            if file:
                text = file.read().decode('utf-8')

                # Clean and split the text into words:  Lowercase and split by spaces and punctuation
                words = re.findall(r'\b\w+\b', text.lower())

                # Count the words using Counter
                word_counts = Counter(words)
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return render_template('word_counter.html', error=str(e))

    return render_template('word_counter.html', word_counts=word_counts)  # Pass word_counts to the template
