# Filename: walt/walt.py
# Location: walt/walt.py (inside the walt directory)

from flask import Blueprint, render_template, request, jsonify, session
import os
import openai  # Import the OpenAI library
from flask import current_app

walt_bp = Blueprint('walt', __name__, template_folder='templates')

@walt_bp.route('/walt')
def walt_window():
    return render_template('walt_window.html')

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

# New Route for Walt-Specific Analysis
@walt_bp.route('/walt_analyze', methods=['POST'])
def walt_analyze():
    user_input = request.form.get('user_query')
    if not user_input:
        return jsonify({"error": "No user query provided"}), 400

    # Initialize conversation history in session if it doesn't exist
    if 'conversation' not in session:
        try:
            with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            return jsonify({"error": "walt_prompt.txt not found!"}), 500
        except Exception as e:
            return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

        session['conversation'] = [{"role": "system", "content": system_prompt}]

    # Add the user's message to the conversation
    session['conversation'].append({"role": "user", "content": user_input})

    try:
        client = openai.Client()  # Use your preferred method to initialize the OpenAI client

        response = client.chat.completions.create(
            model="gpt-4o",  # Specify the model you want to use
            messages=session['conversation'],
            temperature=0.7,  # Adjust as needed
            max_tokens=256,
            top_p=1
        )
        api_response = response.choices[0].message.content.strip()

        # Add the assistant's response to the conversation
        session['conversation'].append({"role": "assistant", "content": api_response})
        session.modified = True  # Mark the session as modified

        return jsonify({"response": api_response})

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return jsonify({"error": str(e)}), 500

# Route to generate and return a session summary
@walt_bp.route('/walt_session_summary', methods=['POST'])
def walt_session_summary():
    session_content=""
    try:
        client = openai.Client()  # Use your preferred method to initialize the OpenAI client
        # Get session information
        session_info = session.get('conversation', [])
        #Get the story content if uploaded.
        session_file=""
        if 'file_content' in session:
           session_content= session['file_content']
        else:
            session_content = "No story started"

        # Generate Summary from API
        response = client.chat.completions.create(
            model="gpt-4o",  # Specify the model you want to use
            messages=[{"role": "system", "content": "Your job is to deliver the status and summary of the session, the outline of sections written, the conversation history and the prompt.  Do not add anything else."},
                      {"role": "user", "content": f"Return all known story with with outline, sections written, session prompts, system_info and the conversation."}],
            temperature=0.7,  # Adjust as needed
            max_tokens=2000, # up to 2000 tokes
            top_p=1
        )
        api_response = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"session_summary": f"{api_response}"})
