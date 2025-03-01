from flask import Blueprint, render_template, request, jsonify, session, send_file
import os
import openai
import logging
import json
from werkzeug.utils import secure_filename
from io import StringIO

from .voice.config import voice_config  # Import VoiceConfig
from .voice.openai_voice import OpenAI_VoiceAPI  # Import OpenAI_VoiceAPI

waltx_bp = Blueprint('waltx', __name__, template_folder='templates')

def format_openai_text(text):
    formatted_text = text.replace("\n", "<br>")
    return formatted_text

# Initialize Voice API (based on config) - UNCONDITIONAL INITIALIZATION NOW
voice_api = None
if voice_config.default_voice_api == "openai":
    try:
        voice_api = OpenAI_VoiceAPI(openai_api_key=voice_config.openai_api_key)
        logging.info("OpenAI Voice API initialized.")
    except ValueError as e:
        logging.warning(f"OpenAI Voice API initialization error: {e}. Voice features may be partially disabled if API key is missing.") # Adjusted log message
        voice_api = None # Set to None if initialization fails
# ... (you can keep other voice API initializations here if you add them later)
else:
    logging.warning(f"Unknown voice API '{voice_config.default_voice_api}' configured. Voice features may be partially disabled.") # Adjusted log message
    voice_api = None


@waltx_bp.route('/')
def walt_window_splash(): # Renamed to walt_window_splash to be more descriptive
    return render_template('walt_splashx.html') # <-- RENAMED TEMPLATE FILE

@waltx_bp.route('/new_bio_start', methods=['GET'])
def new_bio_start():
    session.pop('conversation', None)
    session.pop('biography_outline', None)
    session.pop('file_content', None)

    try:
        with open('waltx/walt_prompts/welcome.txt', 'r', encoding='utf-8') as f:
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
        # Return JSON instead of rendering template for new_bio_start as well, for consistency.
        return jsonify({
            "initial_message": initial_message,
            "biography_outline": session['biography_outline']
        })

    except Exception as e:
        logging.error(f"OpenAI API error on new bio start: {e}")
        return jsonify({
            "error": f"Error starting new bio: {str(e)}",
            "biography_outline": session.get('biography_outline') # Still return outline if available
        })


@waltx_bp.route('/app') # NEW route for /waltx/app - serves main app window
def walt_window(): # Original walt_window function - now for /waltx/app
    return render_template('walt_windowx.html', biography_outline=session.get('biography_outline'), initial_message=None) # <-- RENAMED TEMPLATE FILE

@waltx_bp.route('/continue_bio_start', methods=['POST'])
def continue_bio_start():
    checkpoint_data = request.form.get('checkpoint_data')
    if not checkpoint_data:
        logging.warning("No checkpoint data received in continue_bio_start request.") # Enhanced logging
        return jsonify({"error": "No checkpoint data received"}), 400

    session.pop('conversation', None)
    session.pop('biography_outline', None)
    session.pop('file_content', None)

    logging.debug(f"Checkpoint data received:\n{checkpoint_data[:200]}...") # Log the beginning of checkpoint data

    try: # ADDED try...except BLOCK
        try:
            with open('waltx/walt_prompts/continue.txt', 'r', encoding='utf-8') as f:
                continue_prompt_base = f.read()
        except FileNotFoundError:
            return jsonify({"error": "continue.txt prompt not found!"}), 500

        continue_prompt = continue_prompt_base + "\n\nCHECKPOINT FILE CONTENT:\n" + checkpoint_data

        try:
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
            initial_message = response.choices[0].message.content.strip()
            logging.debug(f"Initial message from OpenAI API: {initial_message}") # Log initial message

            parts = checkpoint_data.split("--- CONVERSATION HISTORY ---\n\n")
            file_content_part = parts[0].strip()
            conversation_history_text = parts[1].strip() if len(parts) > 1 else ""

            session['file_content'] = file_content_part
            logging.debug(f"File content part extracted:\n{file_content_part[:200]}...") # Log file content part

            session['conversation'] = [{"role": "system", "content": get_walt_prompt_content()}]
            if conversation_history_text:
                logging.debug(f"Conversation history text found:\n{conversation_history_text[:200]}...") # Log conversation history text
                conversation_messages = []
                for line in conversation_history_text.strip().split('\n'):
                    if line.strip():
                        try: # Add try-except for line parsing
                            role, content = line.split(':', 1)
                            conversation_messages.append({"role": role.strip(), "content": content.strip()})
                            logging.debug(f"Parsed line - Role: {role.strip()}, Content: {content.strip()[:100]}...") # Log parsed line
                        except ValueError as ve:
                            logging.warning(f"Error parsing conversation history line: {line}. Error: {ve}") # Log parsing errors
                session['conversation'].extend(conversation_messages)
            else:
                logging.debug("No conversation history text found in checkpoint data.") # Log if no history

            session['conversation'].append({"role": "assistant", "content": initial_message})
            session['biography_outline'] = get_biography_outline()
            session.modified = True

            logging.debug(f"Session variables after checkpoint load: \nConversation: {session.get('conversation')}\nBiography Outline: {session.get('biography_outline')}\nFile Content (start): {session.get('file_content', '')[:200]}...") # Log session variables

            # Return JSON response with initial message and biography_outline
            return jsonify({
                "initial_message": initial_message,
                "biography_outline": session['biography_outline']
            })

        except Exception as openai_e: # SPECIFICALLY CATCH OPENAI EXCEPTIONS
            logging.error(f"OpenAI API error in continue_bio_start: {openai_e}", exc_info=True) # LOG OPENAI ERROR WITH TRACEBACK
            return jsonify({
                "error": f"Error continuing bio (OpenAI API): {str(openai_e)}",
                "biography_outline": session.get('biography_outline') # Still return outline if available
            })

    except Exception as e: # CATCH ALL OTHER EXCEPTIONS IN THE ROUTE
        logging.error(f"General error in continue_bio_start: {e}", exc_info=True) # LOG GENERAL ERROR WITH TRACEBACK
        return jsonify({
            "error": f"Error processing checkpoint: {str(e)}"
        }) # RETURN JSON ERROR FOR AJAX CALL


def get_walt_prompt_content():
    try:
        with open('waltx/walt_prompts/walt_prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: walt_prompt.txt not found!"

@waltx_bp.route('/transcribe_audio', methods=['POST']) # <-- ADDED ROUTE
def transcribe_audio():
    if not voice_api: # Keep this check for robustness
        return jsonify({"error": "Voice API not initialized. Please check server logs."}), 501 # More informative error

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected audio file"}), 400

    temp_audio_dir = os.path.join('/app', 'temp_audio') # ABSOLUTE PATH for directory
    temp_audio_path = os.path.join(temp_audio_dir, secure_filename(audio_file.filename)) # ABSOLUTE PATH for file

    try: # ADDED try...except for makedirs
        os.makedirs(temp_audio_dir, exist_ok=True) # Ensure temp_audio directory exists - ABSOLUTE PATH
    except FileExistsError:
        pass # Directory likely already exists due to concurrency - ignore error
    except OSError as e: # Catch other OS errors during directory creation
        logging.error(f"Error creating temp_audio directory: {e}", exc_info=True)
        return jsonify({"error": f"Could not create temp audio directory: {str(e)}"}), 500


    try:
        audio_file.save(temp_audio_path) # Save audio file FIRST - move here
        logging.info(f"Audio file saved to: {temp_audio_path}") # Log file path

        try: # Inner try-except for OpenAI transcription specifically
            transcription_text = voice_api.transcribe_audio(temp_audio_path)
            os.remove(temp_audio_path) # Delete temp audio file after transcription
            return jsonify({"transcription": transcription_text})
        except ValueError as openai_err: # Catch OpenAI specific errors
            os.remove(temp_audio_path) # Delete temp audio file even on OpenAI error
            logging.error(f"OpenAI Transcription API error: {openai_err}", exc_info=True) # Log OpenAI error with traceback
            return jsonify({"error": f"OpenAI Transcription error: {str(openai_err)}"}), 500 # Return JSON error to client

    except Exception as e: # Catch any other errors (file saving, etc.)
        logging.error(f"General error during audio transcription: {e}", exc_info=True) # Log general error with traceback
        return jsonify({"error": f"Error processing audio file: {str(e)}"}), 500 # Return JSON error


@waltx_bp.route('/synthesize_speech', methods=['POST']) # <-- ADDED ROUTE
def synthesize_speech():
    if not voice_api: # Keep this check for robustness
        return jsonify({"error": "Voice API not initialized. Please check server logs."}), 501 # More informative error

    text_data = request.get_json()
    if not text_data or 'text' not in text_data:
        return jsonify({"error": "No text provided for speech synthesis"}), 400

    text_to_synthesize = text_data['text']
    voice_id = voice_config.tts_voice_id # Get configured voice ID

    temp_audio_output_path = os.path.join("temp_audio", f"waltx_speech_{session.sid}.mp3") # Unique filename
    os.makedirs("temp_audio", exist_ok=True) # Ensure temp_audio directory exists

    try:
        audio_file_path = voice_api.synthesize_speech(text_to_synthesize, temp_audio_output_path, voice_id=voice_id)
        audio_url = f"/temp_audio_url/<filename>" # Corrected line: use <filename> for URL construction
        return jsonify({"audio_url": audio_url}) # Return audio URL
    except ValueError as e:
        os.remove(temp_audio_output_path) # Delete temp audio file even on error
        return jsonify({"error": str(e)}), 500


@waltx_bp.route('/temp_audio_url/<filename>') # <-- ADDED ROUTE to serve temp audio files
def temp_audio_url(filename):
    return send_file(os.path.join("temp_audio", filename))


@waltx_bp.route('/walt_analyze', methods=['POST'])
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
        api_response_text = response.choices[0].message.content.strip()
        session['conversation'].append({"role": "assistant", "content": api_response_text})
        session.modified = True

        response_data = {"response": api_response_text, "biography_outline": session['biography_outline']}

        if voice_api: # No more voice_config.voice_enabled check here - assume voice_api is intended to be used if initialized
            try:
                speech_data = {"text": api_response_text}
                speech_response = synthesize_speech() # Call synthesize_speech function directly
                if speech_response.status_code == 200:
                    speech_json = speech_response.get_json()
                    response_data["audio_url"] = speech_json.get("audio_url") # Add audio URL to response
                else:
                    logging.warning(f"Text-to-speech API failed: {speech_response.get_json()}") # Log TTS failure, but don't block main response
            except Exception as tts_e:
                logging.error(f"Error during text-to-speech synthesis: {tts_e}", exc_info=True) # Log TTS errors

        return jsonify(response_data) # Return response with or without audio URL


    except Exception as e:
        logging.error(f"OpenAI API Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@waltx_bp.route('/create_checkpoint', methods=['POST'])
def create_checkpoint():
    try:
        checkpoint_data_text = session.get('file_content', '')
        bio_prompt_content = ""
        try:
            with open('waltx/walt_prompts/bio_creator_prompt.txt', 'r', encoding='utf-8') as f:
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

@waltx_bp.route('/craft_biography', methods=['POST'])
def craft_biography():
    checkpoint_data_text = session.get('file_content', '')
    conversation_text = ""
    current_conversation = session.get('conversation', [])
    for message in current_conversation:
        if message['role'] in ['user', 'assistant']:
            conversation_text += f"{message['role']}: {message['content']}\n"

    try:
        with open('waltx/walt_prompts/write_bio.txt', 'r', encoding='utf-8') as f:
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
            max_tokens=1000,
        )
        biography_content = response.choices[0].message.content.strip()
        formatted_biography = format_openai_text(biography_content)

        formatted_biography_file = biography_content.replace("<br>", "\n")
        filename = "Full_biography.txt"
        with open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write(formatted_biography_file)

        session['file_content'] = biography_content
        session.modified = True

        return jsonify({"api_response": formatted_biography, "file_download_name": filename})

    except Exception as e:
        logging.error(f"Error crafting biography: {e}", exc_info=True)
        error_message = f"Error crafting biography: {str(e)}"
        formatted_error = format_openai_text(error_message)
        return jsonify({"error": error_message, "api_response": formatted_error}), 500


@waltx_bp.route('/saveTextAsFileDownload', methods=['POST'])
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
