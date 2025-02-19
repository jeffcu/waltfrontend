# walt/walt.py
from flask import Blueprint, render_template, request, jsonify, session
import os
import openai
import logging
import json  # Import the json module

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
        logging.error(f"Error reading walt_prompt.txt: {str(e)}") #Added logging here
        return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

@walt_bp.route('/walt_analyze', methods=['POST'])
def walt_analyze():
    user_input = request.form.get('user_query')
    uploaded_content = request.form.get('uploaded_content', '')

    if not user_input:
        return jsonify({"error": "No user query provided"}), 400

    try:
        with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
            walt_prompt = f.read()
        except FileNotFoundError:
            return jsonify({"error": "walt_prompt.txt not found!"}), 500
    except Exception as e:
        return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

    if 'conversation' not in session:
        initial_greeting = "Hi I'm Walt. What's your name?"
        session['conversation'] = [{"role": "system", "content": walt_prompt},
                                     {"role": "assistant", "content": initial_greeting}]

    if uploaded_content:
        session['conversation'].append({"role": "system", "content": f"Here is context from your biography: {uploaded_content}"})
        print(f"UPLOADED CONTENT TO OPEN API:{uploaded_content}")
    else:
        print("NO UPLOADED CONTENT!")

    session['conversation'].append({"role": "user", "content": user_input + ". Pick another chapter and let's discuss it."})

    try:
        client = openai.Client()
        logging.info(f"OpenAI Request Messages: {session['conversation']}")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[session['conversation']],
            temperature=0.7,
            max_tokens=256,
            top_p=1
        )
        api_response = response.choices[0].message.content.strip()

        session['conversation'].append({"role": "assistant", "content": api_response})
        session.modified = True

        return jsonify({"response": api_response})

    except Exception as e:
        logging.error(f"OpenAI API Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/walt_session_summary', methods=['POST'])
def walt_session_summary():
    session_content = ""
    try:
        client = openai.Client()
        session_info = session.get('conversation', [])
        session_content = ""
        if 'file_content' in session:
            file_content = session['file_content']
        else:
            file_content = "No story started"

        session_content = session_info if session_info else "No story started"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Your job is to deliver the status and summary of the session, the outline of sections written, the conversation history and the prompt.  Do not add anything else."},
                      {"role": "user", "content": f"Return all known story with with outline, sections written, session prompts, system_info and the conversation for {session_content}."}],
            temperature=0.7,
            max_tokens=2000,
            top_p=1
        )
        api_response = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"session_summary": f"{api_response}"})

@walt_bp.route('/load_checkpoint', methods=['POST'])
def load_checkpoint():
    checkpoint_data = request.form.get('checkpoint_data')
    if not checkpoint_data:
        return jsonify({"error": "No checkpoint data received"}), 400

    try:
        # Load the Walt Prompt
        try:
            with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
                walt_prompt = f.read()
        except FileNotFoundError:
            return jsonify({"error": "walt_prompt.txt not found!"}), 500
        except Exception as e:
            logging.error(f"Error reading walt_prompt.txt in load_checkpoint: {str(e)}")
            return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

        # Restore the session - treat as a simple string.  NO JSON PARSING
        session['file_content'] = checkpoint_data #ADDED:  Load this first
        session['conversation'] = [{"role": "system", "content": walt_prompt},
                                     {"role": "user", "content": checkpoint_data}]#Treat as input not JSON

        session.modified = True

        # Extract user's name (from the loaded session or use a default)
        user_name = "User"  # Default
        #Welcome them back
        welcome_phrase = f"Welcome back, {user_name}! Hi, I am Walt. Let's continue your story."

        #Update the conversation history with the new state
        session['conversation'].append({"role": "assistant", "content":welcome_phrase}) #Update initial phrase

        return jsonify({"response": welcome_phrase})

    except Exception as e:
        print(f"Error processing checkpoint: {e}")
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/create_checkpoint', methods=['POST'])
def create_checkpoint():
    try:
        # Create a dictionary to hold the session data and file content
        checkpoint_data = {
            'conversation': session.get('conversation', []),
            'file_content': session.get('file_content', '')
        }

        # Serialize the dictionary to JSON
        checkpoint_json = json.dumps(checkpoint_data)

        # Return the JSON string
        return jsonify({"checkpoint_data": checkpoint_json})

    except Exception as e:
        logging.error(f"Error creating checkpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/saveTextAsFile', methods=['POST'])
def saveTextAsFile():
    try:
        data = request.get_json()
        checkpoint_data = data.get('checkpoint_data')

        if not checkpoint_data:
            return jsonify({"error": "No checkpoint data to save"}), 400

        # Return the checkpoint data directly (it's already a JSON string)
        logging.info(f"Checkpoint data being sent: {checkpoint_data}") #Debug log
        return jsonify({"fileContent": checkpoint_data})

    except Exception as e:
        logging.error(f"Error return and saving checkpoint from saveTextAsFile: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
