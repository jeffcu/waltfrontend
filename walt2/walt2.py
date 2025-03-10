
from flask import Blueprint, render_template, request, jsonify, session, send_file
import os
import openai
import logging
import json
from werkzeug.utils import secure_filename
from io import StringIO

walt2_bp = Blueprint('walt2', __name__, template_folder='templates')

def format_openai_text(text):
    formatted_text = text.replace("\n", "<br>")
    return formatted_text

@walt2_bp.route('/')
def walt_window_splash(): # Renamed to walt_window_splash to be more descriptive
    return render_template('walt_splash2.html')

@walt2_bp.route('/new_bio_start', methods=['GET'])
def new_bio_start():
    session.pop('conversation', None)
    session.pop('biography_outline', None)
    session.pop('file_content', None)
    session.pop('loaded_checkpoint_conversation', None)
    session.pop('previous_checkpoint_history_text', None) # Clear previous history

    try:
        with open('walt2/walt_prompts/welcome.txt', 'r', encoding='utf-8') as f:
            welcome_prompt = f.read()
    except FileNotFoundError:
        return jsonify({"error": "welcome.txt prompt not found!"}), 500

    try:
        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Walt, the biographer, starting a new biography."},
                {"role": "user", "content": welcome_prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        initial_message = response.choices[0].message.content.strip()
        session['conversation'] = [{"role": "system", "content": get_walt_prompt_content()}, {"role": "assistant", "content": initial_message}]
        session['biography_outline'] = get_biography_outline()
        session.modified = True
        return jsonify({
            "initial_message": initial_message,
            "biography_outline": session['biography_outline']
        })

    except Exception as e:
        logging.error(f"OpenAI API error on new bio start: {e}")
        logging.exception(e) # Log full exception details including traceback
        return jsonify({
            "error": f"Error starting new bio: {str(e)}",
            "biography_outline": session.get('biography_outline') # Still return outline if available
        })


@walt2_bp.route('/app')
def walt_window():
    return render_template('walt_window2.html', biography_outline=session.get('biography_outline'), initial_message=None)

@walt2_bp.route('/continue_bio_start', methods=['POST'])
def continue_bio_start():
    checkpoint_data = request.form.get('checkpoint_data')
    if not checkpoint_data:
        logging.warning("No checkpoint data received in continue_bio_start request.")
        return jsonify({"error": "No checkpoint data received"}), 400

    session.pop('conversation', None)
    session.pop('biography_outline', None)
    session.pop('file_content', None)
    session.pop('loaded_checkpoint_conversation', None)
    session.pop('previous_checkpoint_history_text', None) # Clear previous history

    logging.debug(f"Checkpoint data received:\n{checkpoint_data[:200]}...")

    try:
        try:
            with open('walt2/walt_prompts/continue.txt', 'r', encoding='utf-8') as f:
                continue_prompt_base = f.read()
        except FileNotFoundError:
            return jsonify({"error": "continue.txt prompt not found!"}), 500

        continue_prompt = continue_prompt_base + "\n\nCHECKPOINT FILE CONTENT:\n" + checkpoint_data

        initial_message = "Error: Could not get initial message from OpenAI." # <---- ADD DEFAULT VALUE HERE

        try: # OpenAI API call try block
            client = openai.Client()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are Walt, the biographer, continuing a biography from a checkpoint."},
                    {"role": "user", "content": continue_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            initial_message = response.choices[0].message.content.strip()  # <-- API response, overwrites default
            logging.debug(f"Initial message from OpenAI API: {initial_message}") # Log initial message

            parts = checkpoint_data.split("--- PREVIOUS CHECKPOINT CONVERSATION HISTORY ---\n\n") # Split for previous history FIRST
            main_part = parts[0] # Main part now excludes previous history
            if len(parts) > 1:
                previous_history_content = parts[1].strip() # Extract previous history - NEW
                session['previous_checkpoint_history_text'] = previous_history_content # Store previous history in session - NEW
            else:
                session['previous_checkpoint_history_text'] = "" # No previous history found - NEW


            conversation_parts = main_part.split("--- CURRENT CONVERSATION HISTORY ---\n\n") # Split main part for current history
            file_content_part = conversation_parts[0].strip()
            conversation_history_text = conversation_parts[1].strip() if len(conversation_parts) > 1 else ""


            session['file_content'] = file_content_part


            loaded_conversation_history = []
            if conversation_history_text:
                conversation_messages = []
                valid_roles = ['system', 'user', 'assistant']
                for line in conversation_history_text.strip().split('\n'):
                    if line.strip():
                        try:
                            role, content = line.split(':', 1)
                            role = role.strip()
                            if role in valid_roles:
                                conversation_messages.append({"role": role, "content": content.strip()})
                            else:
                                logging.warning(f"Skipping line with invalid role: {role}. Line: {line}")
                        except ValueError as ve:
                            logging.warning(f"Error parsing conversation history line: {line}. Error: {ve}")
                loaded_conversation_history = conversation_messages
            session['loaded_checkpoint_conversation'] = loaded_conversation_history


            session['conversation'] = [{"role": "system", "content": get_walt_prompt_content()}]
            session['conversation'].extend(loaded_conversation_history)


            session['biography_outline'] = get_biography_outline()
            session.modified = True

            return jsonify({
                "initial_message": initial_message, # SEND INITIAL MESSAGE FOR DISPLAY
                "biography_outline": session['biography_outline']
            })

        except Exception as openai_e: # SPECIFICALLY CATCH OPENAI EXCEPTIONS
            logging.error(f"OpenAI API error in continue_bio_start: {openai_e}", exc_info=True) # LOG OPENAI ERROR WITH TRACEBACK
            logging.exception(openai_e) # Log full exception details including traceback
            return jsonify({
                "error": f"Error continuing bio (OpenAI API): {str(openai_e)}",
                "biography_outline": session.get('biography_outline') # Still return outline if available
            })

    except Exception as e: # CATCH ALL OTHER EXCEPTIONS IN THE ROUTE
        logging.error(f"General error in continue_bio_start: {e}", exc_info=True) # LOG GENERAL ERROR WITH TRACEBACK
        logging.exception(e) # Log full exception details including traceback
        return jsonify({
            "error": f"Error processing checkpoint: {str(e)}"
        }) # RETURN JSON ERROR FOR AJAX CALL


def get_walt_prompt_content():
    try:
        with open('walt2/walt_prompts/walt_prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: walt_prompt.txt not found!"


@walt2_bp.route('/walt_analyze', methods=['POST'])
def walt_analyze():
    user_input = request.form.get('user_query')

    if not user_input:
        return jsonify({"error": "No user query provided"}), 400

    walt_prompt_base = get_walt_prompt_content()
    walt_prompt = walt_prompt_base


    if 'conversation' not in session:
        initial_greeting = "Hi I'm Walt. What's your name?"
        session['conversation'] = [{"role": "system", "content": walt_prompt},
                                     {"role": "assistant", "content": initial_greeting}]
        session['biography_outline'] = get_biography_outline()


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
        session['conversation'].append({"role": "assistant", "content": api_response})
        session.modified = True

        return jsonify({"response": api_response, "biography_outline": session['biography_outline']})

    except Exception as e:
        logging.error(f"OpenAI API Error in walt_analyze:", exc_info=True) # Added route name to log
        logging.exception(e) # Log full exception details including traceback
        return jsonify({"error": str(e)}), 500


@walt2_bp.route('/create_checkpoint', methods=['POST'])
def create_checkpoint():
    try:
        bio_prompt_content = ""
        try:
            with open('walt2/walt_prompts/bio_creator_prompt.txt', 'r', encoding='utf-8') as f:
                bio_prompt_content = f.read()
        except Exception as e:
            logging.error(f"Error reading bio_prompt.txt in create_checkpoint:", exc_info=True) # Added route name to log
            logging.exception(e) # Log full exception details including traceback
            bio_prompt_content = "Error loading bio creator prompt."

        conversation_text = ""
        current_conversation = session.get('conversation', [])

        extended_conversation = list(session.get('loaded_checkpoint_conversation', []))
        extended_conversation.extend(current_conversation)

        extended_conversation_text = ""
        for message in extended_conversation:
            if message['role'] in ['user', 'assistant']: # Only include user and assistant messages in history
                conversation_text += f"{message['role']}: {message['content']}\n"
                extended_conversation_text += f"{message['role']}: {message['content']}\n" # Current extended conv text - for CURRENT HISTORY SECTION


        previous_checkpoint_history_text = session.get('previous_checkpoint_history_text', "") # Retrieve previous history - NEW

        api_input_text = bio_prompt_content + "\n\n--- CONVERSATION HISTORY ---\n\n" + conversation_text # Combine prompt and conversation

        try: # Call OpenAI API to process and summarize checkpoint data
            client = openai.Client()
            response = client.chat.completions.create(
                model="gpt-4o", # Or desired model
                messages=[{"role": "user", "content": api_input_text}],
                temperature=0.7, # Adjust as needed
                max_tokens=500, # Adjust as needed
            )
            checkpoint_data_text = response.choices[0].message.content.strip() # Get processed summary
            session['file_content'] = checkpoint_data_text # Store processed summary in session
        except Exception as openai_error:
            logging.error(f"OpenAI API error during checkpoint processing in create_checkpoint:", exc_info=True) # Added route name to log
            logging.exception(openai_error) # Log full exception details including traceback
            checkpoint_data_text = "Error processing checkpoint data. Conversation history saved, but summary generation failed." # Informative error message in checkpoint
            session['file_content'] = checkpoint_data_text # Still store error in session


        file_content_for_download = checkpoint_data_text + "\n\n--- CURRENT CONVERSATION HISTORY ---\n\n" + extended_conversation_text + "\n\n--- PREVIOUS CHECKPOINT CONVERSATION HISTORY ---\n\n" + previous_checkpoint_history_text # Checkpoint file now contains PROCESSED data, then conversation history

        session.modified = True # Ensure session is saved

        logging.info(f"Checkpoint data being created (Processed Summary and History): {file_content_for_download[:100]}...")

        return jsonify({"checkpoint_data": file_content_for_download}) # Send the complete file content for download

    except Exception as e: # Catch any errors during checkpoint creation
        logging.error(f"Error processing checkpoint and calling API in create_checkpoint:", exc_info=True) # Added route name to log
        logging.exception(e) # Log full exception details including traceback
        return jsonify({"error": str(e)}), 500


@walt2_bp.route('/craft_biography', methods=['POST'])
def craft_biography():
    checkpoint_data_text = session.get('file_content', '')
    conversation_text = ""
    current_conversation = session.get('conversation', [])
    for message in current_conversation:
        if message['role'] in ['user', 'assistant']:
            conversation_text += f"{message['role']}: {message['content']}\n"

    try:
        with open('walt2/walt_prompts/write_bio.txt', 'r', encoding='utf-8') as f:
            write_bio_prompt = f.read()
    except FileNotFoundError:
        return jsonify({"error": "write_bio.txt prompt not found!"}), 500

    api_input_text = write_bio_prompt + "\n\n" + checkpoint_data_text + "\n\n--- CONVERSATION ---\n\n" + conversation_text

    try:
        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": api_input_text}],
            temperature=0.7,
            max_tokens=2048, # <-- INCREASED max_tokens here
        )
        biography_content = response.choices[0].message.content.strip()
        logging.info(f"Biography content length: {len(biography_content)}") # <-- Added length logging
        formatted_biography = format_openai_text(biography_content)

        formatted_biography_file = biography_content.replace("<br>", "\n")
        filename = "Full_biography.txt"
        with open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write(formatted_biography_file)

        session['file_content'] = biography_content
        session.modified = True

        return jsonify({"api_response": formatted_biography, "file_download_name": filename})

    except Exception as e:
        logging.error(f"Error crafting biography in craft_biography:", exc_info=True) # Added route name to log
        logging.exception(e) # Log full exception details including traceback
        error_message = f"Error crafting biography: {str(e)}"
        formatted_error = format_openai_text(error_message)
        return jsonify({"error": error_message, "api_response": formatted_error}), 500


@walt2_bp.route('/saveTextAsFileDownload', methods=['POST'])
def saveTextAsFileDownload():
    try:
        data = request.get_json()
        checkpoint_data = data.get('checkpoint_data')
        file_download_name = data.get('file_download_name', 'sessionStory.txt')

        if not checkpoint_data:
            return jsonify({"error": "No checkpoint data to save"}), 400

        logging.info(f"Checkpoint data being sent for download: {checkpoint_data[:50]}...")

        virtual_file = StringIO()
        virtual_file.write(checkpoint_data)
        virtual_file.seek(0)

        return send_file(
            virtual_file,
            mimetype='text/plain',
            download_name=file_download_name,
            as_attachment=True
        )


    except Exception as e:
        logging.error(f"Error return and saving checkpoint from saveTextAsFileDownload:", exc_info=True) # Added route name to log
        logging.exception(e) # Log full exception details including traceback
        return jsonify({"error": str(e)}), 500

def get_biography_outline():
    return [
        {"chapter": 1, "title": "Hook – Defining Moment", "status": "TBD"},
        {"chapter": 2, "title": "Origins – Early Life & Influences", "status": "TBD"},
        {"chapter": 3, "title": "Call to Action – First Big Decision", "status": "TBD"},
        {"chapter": 4, "title": "Rising Conflict – Struggles & Growth", "status": "TBD"},
        {"chapter": 5, "title": "The Climax – Defining Achievements", "status": "TBD"}
    ]
