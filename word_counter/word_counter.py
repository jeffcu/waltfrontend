from flask import Blueprint, render_template, request, session
import re
from collections import Counter
import logging
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import InputRequired

wc_bp = Blueprint('wc', __name__, template_folder='templates')  # Corrected name

class UploadFileForm(FlaskForm):
    file_upload = FileField('File', validators=[InputRequired()])
    submit = SubmitField('Upload File')

@wc_bp.route('/word_counter', methods=['GET', 'POST'])
def word_counter():
    form = UploadFileForm()
    word_counts = None

    if form.validate_on_submit():
        try:
            file = form.file_upload.data
            text = file.read().decode('utf-8')

            # Clean and split the text into words:  Lowercase and split by spaces and punctuation
            words = re.findall(r'\b\w+\b', text.lower())

            # Count the words using Counter
            word_counts = Counter(words)
            # word_counts = Counter(words)
            sorted_word_counts = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)  # Sort by count in descending order
            #session['word_counts'] = sorted_word_counts  #Store words in session
            session['word_counts'] = sorted_word_counts #Use sorted session.

        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return render_template('word_counter.html', form=form, error=str(e))

    return render_template('word_counter.html', form=form, word_counts=session.get('word_counts', None)) #Passes in the variable.
