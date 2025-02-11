from flask import Blueprint, render_template, request
import os

walt_bp = Blueprint('walt', __name__, template_folder='templates')

@walt_bp.route('/walt')
def walt_window():
    prompt_text = ""
    try:
        with open('walt_prompt.txt', 'r', encoding='utf-8') as f:  # Assuming walt_prompt.txt is in the project root
            prompt_text = f.read()
    except FileNotFoundError:
        prompt_text = "Error: walt_prompt.txt not found!"
    except Exception as e:
        prompt_text = f"Error reading walt_prompt.txt: {str(e)}"

    return render_template('walt_window.html', prompt_text=prompt_text)
