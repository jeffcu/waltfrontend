from flask import Blueprint, render_template, request, jsonify
import os

walt_bp = Blueprint('walt', __name__, template_folder='templates')

@walt_bp.route('/walt')
def walt_window():
    from flask_wtf.csrf import generate_csrf
    csrf_token = generate_csrf()
    return render_template('walt_window.html', csrf_token=csrf_token)

@walt_bp.route('/get_walt_prompt')
def get_walt_prompt():
    try:
        with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        return prompt_text
    except FileNotFoundError:
        return jsonify({"error": "walt_prompt.txt not found!"}), 404
    except Exception as e:
        return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500
