from flask import Blueprint, render_template, request, jsonify, session
import os
import openai
import logging
import json
from werkzeug.utils import secure_filename

walt2_bp = Blueprint('walt2', __name__, template_folder='templates')

@walt2_bp.route('/walt2')
def walt_window():
    new_bio = request.args.get('new_bio')

    if 'conversation' not in session or new_bio == 'true':
        if 'conversation' in session:
            session.pop('conversation', None)
            session.pop('biography_outline', None)
            session.pop('file_content', None)

        return render_template('walt_splash2.html')
    else:
        return render_template('walt_window2.html', biography_outline=session['biography_outline'], initial_message=None)


@walt2_bp.route('/get_walt_prompt')
def get_walt_prompt():
    try:
        with open('walt2/walt_prompts/walt_prompt.txt', 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        return prompt_text
    except FileNotFoundError as e:
        logging.error(f"Error reading walt_prompt.txt: {str(e)}")
        return jsonify({"error": "walt_prompt.txt not found!"}), 404
    except Exception as e:
        logging.error(f"General error in get_walt_prompt: {str(e)}")
        return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

@walt2_bp.route('/walt_analyze', methods=['POST'])
def walt_analyze():
    user_input = request.form.get('user_query')
    uploaded_content = request.form.get('uploaded_content', '')
    desired_tone = request.form.get('tone', 'default')

    if not user_input:
        return jsonify({"error": "No user query provided"}), 400

    try:
        with open('walt2/walt_prompts/walt_prompt.txt', 'r', encoding='utf-8') as f:
            walt_prompt_base = f.read()

        if desired_tone != 'default':
            walt_prompt = walt_prompt_base + f"\nThe user prefers a biography with a {desired_tone} tone."
        else:
            walt_prompt = walt_prompt_base


    except FileNotFoundError:
        return jsonify({"error": "walt_prompt.txt not found!"}), 500
    except Exception as e:
        return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

    if 'conversation' not in session:
        initial_greeting = "Hi I'm Walt. What's your name?"
        session['conversation'] = [{"role": "system", "content": walt_prompt},
                                     {"role": "assistant", "content": initial_greeting}]
        session['biography_outline'] = get_biography_outline()

    if uploaded_content:
        session['conversation'].append({"role": "system", "content": f"Here is context from your biography: {uploaded_content}"})
        print(f"UPLOADED CONTENT TO OPEN API:{uploaded_content}")
    else:
        print("NO UPLOADED CONTENT!")

    session['conversation'].append({"role": "user", "content": user_input + ".  Continue to help me build my biography."})

    try:
        client = openai.Client()
        logging.info(f"OpenAI Request Messages: {session['conversation']}")

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=session['conversation'],
            temperature=0.7,
            max_tokens=256,
            top_p=1
        )
        api_response = response.choices[0].message.content.strip()

        verification_prompt_text = f"From our last exchange: '{user_input}' and Walt's response: '{api_response}', suggest 1-2 very natural, brief follow-up questions Walt might ask to clarify details or get more specific information about what the person just said.  Think of questions a friendly biographer would ask in a casual conversation, like 'Where did that happen?' or 'What year was that?' Keep the tone friendly and natural, like Walt."
        verification_prompt = [{"role": "system", "content": "You are Walt, a friendly biographer focused on getting accurate details. Your goal is to ask natural, short follow-up questions - think 'where', 'when', 'who' - to clarify the user's story."},
                              {"role": "user", "content": verification_prompt_text}]

        verification_response = client.chat.completions.create(
            model="gpt-4o",
            messages=verification_prompt,
            temperature=0.5,
            max_tokens=100
        )
        verification_message = verification_response.choices[0].message.content.strip()
        api_response_with_verification = api_response + "\n\n" + verification_message

        session['conversation'].append({"role": "assistant", "content": api_response_with_verification})
        session.modified = True

        return jsonify({"response": api_response_with_verification, "biography_outline": session['biography_outline']})

    except Exception as e:
        logging.error(f"OpenAI API Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@walt2_bp.route('/walt_session_summary', methods=['POST'])
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

@walt2_bp.route('/load_checkpoint', methods=['POST'])
def load_checkpoint():
    checkpoint_data = request.form.get('checkpoint_data')
    if not checkpoint_data:
        return jsonify({"error": "No checkpoint data received"}), 400

    try:
        try:
            with open('walt2/walt_prompts/walt_prompt.txt', 'r', encoding='utf-8') as f:
                walt_prompt = f.read()
        except FileNotFoundError as e:
            logging.error(f"Error reading walt_prompt.txt: {str(e)}")
            return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500
        except Exception as e:
            logging.error(f"General error in get_walt_prompt: {str(e)}")
            return jsonify({"error": str(e)}), 500

        parts = checkpoint_data.split("--- CONVERSATION HISTORY ---\n\n")
        file_content_part = parts[0].strip()
        conversation_history_text = parts[1].strip() if len(parts) > 1 else ""

        session['file_content'] = file_content_part

        session['conversation'] = [{"role": "system", "content": walt_prompt}]
        if conversation_history_text:
            conversation_messages = []
            for line in conversation_history_text.strip().split('\n'):
                if line.strip():
                    role, content = line.split(':', 1)
                    conversation_messages.append({"role": role.strip(), "content": content.strip()})
            session['conversation'].extend(conversation_messages)

        session['biography_outline'] = get_biography_outline()
        session.modified = True

        user_name = "friend"
        for message in reversed(session['conversation']):
            if message['role'] == 'assistant' and "What's your name?" in message['content']:
                previous_user_message = session['conversation'][session['conversation'].index(message) - 1] if session['conversation'].index(message) > 0 else None
                if previous_user_message and previous_user_message['role'] == 'user':
                    user_name_potential = previous_user_message['content'].strip()
                    if user_name_potential:
                        user_name = user_name_potential
                        break

        chapters_discussed = 0
        for chapter_data in session['biography_outline']:
            if chapter_data['status'] == 'Complete':
                chapters_discussed += 1
        progress_summary = f"So far, we've made progress on {chapters_discussed} chapters of your biography." if chapters_discussed > 0 else "We're ready to pick up where we left off."

        welcome_phrase = f"Welcome back, {user_name}! Hi, I am Walt. It's great to continue your story. {progress_summary} Ready to jump back in?"

        session['conversation'].append({"role": "assistant", "content": welcome_phrase})

        return jsonify({"response": welcome_phrase, "biography_outline": session['biography_outline']})

    except Exception as e:
        print(f"Error processing checkpoint: {e}")
        return jsonify({"error": str(e)}), 500

@walt2_bp.route('/create_checkpoint', methods=['POST'])
def create_checkpoint():
    try:
        checkpoint_data_text = session.get('file_content', '')
        bio_prompt_content = ""
        try:
            with open('walt2/walt_prompts/bio_creator_prompt.txt', 'r', encoding='utf-8') as f:
                bio_prompt_content = f.read()
        except Exception as e:
            logging.error(f"Error reading bio_prompt.txt: {e}")
            bio_prompt_content = "Error loading bio creator prompt."

        conversation_text = ""
        current_conversation = session.get('conversation', [])
        for message in current_conversation:
            if message['role'] in ['system', 'user', 'assistant']:
                conversation_text += f"{message['role']}: {message['content']}\n"

        combined_checkpoint_content = bio_prompt_content + "\n\n" + checkpoint_data_text + "\n\n--- CONVERSATION HISTORY ---\n\n" + conversation_text

        logging.info(f"Checkpoint data being created (with conversation): {combined_checkpoint_content[:100]}...")

        return jsonify({"checkpoint_data": combined_checkpoint_content})

    except Exception as e:
        logging.error(f"Error creating checkpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@walt2_bp.route('/walt_process_checkpoint', methods=['POST'])
def walt_process_checkpoint():
    checkpoint_data_text = session.get('file_content', '')
    bio_prompt_content = ""
    api_response_text_safe = ""

    try:
        try:
            with open('walt2/walt_prompts/bio_creator_prompt.txt', 'r', encoding='utf-8') as f:
                bio_prompt_content = f.read()
        except Exception as e:
            logging.error(f"Error reading bio_prompt.txt: {e}")
            return jsonify({"error": f"Error loading bio creator prompt: {str(e)}"}), 500

        conversation_text = ""
        current_conversation = session.get('conversation', [])
        for message in current_conversation:
            if message['role'] in ['user', 'assistant']:
                conversation_text += f"{message['role']}: {message['content']}\n"

        desired_tone = request.form.get('tone', 'default')
        tone_instruction = ""
        if desired_tone != 'default':
            tone_instruction = f" Write the biography in a {desired_tone} tone."

        api_input_text = bio_prompt_content + tone_instruction + "\n\n" + checkpoint_data_text + "\n\n--- CONVERSATION ---\n\n" + conversation_text

        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": api_input_text}],
            temperature=0.7,
            max_tokens=700,
        )
        api_response_text = response.choices[0].message.content.strip()

        api_response_text_safe = api_response_text.replace("<", "<").replace(">", ">")

        file_content_for_download = checkpoint_data_text + "\n\n" + api_response_text_safe

        combined_output_content = file_content_for_download

        session['file_content'] = file_content_for_download
        session.modified = True

        return jsonify({
            "checkpoint_data": file_content_for_download,
            "api_response": combined_output_content
        })

    except Exception as e:
        logging.error(f"Error processing checkpoint and calling API: {e}", exc_info=True)
        error_message = f"Error processing checkpoint and calling API: {str(e)}"
        api_response_text_safe = error_message
        return jsonify({"error": error_message, "api_response": api_response_text_safe}), 500

@walt2_bp.route('/saveTextAsFileDownload', methods=['POST'])
def saveTextAsFileDownload():
    try:
        data = request.get_json()
        checkpoint_data = data.get('checkpoint_data')

        if not checkpoint_data:
            return jsonify({"error": "No checkpoint data to save"}), 400

        logging.info(f"Checkpoint data being sent for download: {checkpoint_data[:50]}...")
        return jsonify({"fileContent": checkpoint_data})

    except Exception as e:
        logging.error(f"Error return and saving checkpoint from saveTextAsFileDownload: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def get_biography_outline():
    return [
        {"chapter": 1, "title": "Hook – Defining Moment", "status": "TBD"},
        {"chapter": 2, "title": "Origins – Early Life & Influences", "status": "TBD"},
        {"chapter": 3, "title": "Call to Action – First Big Decision", "status": "TBD"},
        {"chapter": 4, "title": "Rising Conflict – Struggles & Growth", "status": "TBD"},
        {"chapter": 5, "title": "The Climax – Defining Achievements", "status": "TBD"}
    ]
