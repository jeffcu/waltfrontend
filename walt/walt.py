# walt/walt.py
from flask import Blueprint, render_template, request, jsonify, session
import os
import openai
import logging
import json
from werkzeug.utils import secure_filename

walt_bp = Blueprint('walt', __name__, template_folder='templates')

@walt_bp.route('/walt')
def walt_window():
    if 'conversation' not in session:
        # New session (new user)
        initial_greeting = "Hi, I'm Walt!  It's wonderful to meet you. I'm excited to help you write your biography. To get started, could you tell me your name?"
        session['conversation'] = [{"role": "system", "content": get_walt_prompt()},
                                     {"role": "assistant", "content": initial_greeting}]
        session['biography_outline'] = get_biography_outline()
        session.modified = True # Important for session modifications to be saved
        return render_template('walt_window.html', biography_outline=get_biography_outline(), initial_message=initial_greeting) # Pass initial message
    else:
        # Existing session (returning user - less common direct /walt access, but handling)
        return render_template('walt_window.html', biography_outline=get_biography_outline(), initial_message=None) # No initial message needed


@walt_bp.route('/get_walt_prompt')
def get_walt_prompt():
    try:
        with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
            prompt_text = f.read()
        return prompt_text
    except FileNotFoundError as e:
        logging.error(f"Error reading walt_prompt.txt: {str(e)}")
        return jsonify({"error": "walt_prompt.txt not found!"}), 404
    except Exception as e:
        logging.error(f"General error in get_walt_prompt: {str(e)}")
        return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

@walt_bp.route('/walt_analyze', methods=['POST'])
def walt_analyze():
    user_input = request.form.get('user_query')
    uploaded_content = request.form.get('uploaded_content', '')
    desired_tone = request.form.get('tone', 'default') # Get tone from request

    if not user_input:
        return jsonify({"error": "No user query provided"}), 400

    try:
        with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
            walt_prompt_base = f.read()

        # Incorporate tone into prompt (Improvement #4)
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
        session['biography_outline'] = get_biography_outline() # Initialize outline in session (Improvement #5)


    if uploaded_content:
        session['conversation'].append({"role": "system", "content": f"Here is context from your biography: {uploaded_content}"})
        print(f"UPLOADED CONTENT TO OPEN API:{uploaded_content}")
    else:
        print("NO UPLOADED CONTENT!")

    # Improvement #2: Dynamic Chapter Suggestion - Removed fixed chapter selection in prompt
    session['conversation'].append({"role": "user", "content": user_input + ".  Continue to help me build my biography."})


    try:
        client = openai.Client()
        logging.info(f"OpenAI Request Messages: {session['conversation']}")

        # --- FIRST OPENAI CALL: Get Walt's normal response ---
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=session['conversation'],
            temperature=0.7,
            max_tokens=256,
            top_p=1
        )
        api_response = response.choices[0].message.content.strip()

        # --- SECOND OPENAI CALL: Get Walt's Fact-Check Question (Improvement #3) ---
        verification_prompt_text = f"From our last exchange: '{user_input}' and Walt's response: '{api_response}', please list 2-3 key facts Walt has gathered about the person in this chapter so far. Ask the user to verify if these facts are correct in a friendly and natural tone, as Walt would." # More natural tone in fact-check prompt
        verification_prompt = [{"role": "system", "content": "You are Walt, fact-checking biographer.  Your goal is to create a short, friendly question to the user to verify 2-3 key facts from the conversation."},
                              {"role": "user", "content": verification_prompt_text}] # Define prompt as list of dicts

        verification_response = client.chat.completions.create(
            model="gpt-4o",
            messages=verification_prompt, # Use the defined verification_prompt
            temperature=0.5, # Lower temp for fact-checking
            max_tokens=150
        )
        verification_message = verification_response.choices[0].message.content.strip()
        api_response_with_verification = api_response + "\n\n" + verification_message


        session['conversation'].append({"role": "assistant", "content": api_response_with_verification}) # Use combined response
        session.modified = True

        return jsonify({"response": api_response_with_verification, "biography_outline": session['biography_outline']}) # Include outline in response

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
        except FileNotFoundError as e:
            logging.error(f"Error reading walt_prompt.txt: {str(e)}")
            return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500
        except Exception as e:
            logging.error(f"General error in get_walt_prompt: {str(e)}")
            return jsonify({"error": str(e)}), 500

        # Restore the session - treat as a simple string.  NO JSON PARSING
        session['file_content'] = checkpoint_data
        session['conversation'] = [{"role": "system", "content": walt_prompt}]
        session['biography_outline'] = get_biography_outline()

        session.modified = True

        # Try to extract user's name from conversation history (basic approach)
        user_name = "friend"  # Default if name not found
        for message in reversed(session['conversation']): # Check conversation history for name
            if message['role'] == 'assistant' and "What's your name?" in message['content']:
                previous_user_message = session['conversation'][session['conversation'].index(message) -1] if session['conversation'].index(message) > 0 else None # Get user's message before "What's your name?"
                if previous_user_message and previous_user_message['role'] == 'user':
                     user_name_potential = previous_user_message['content'].strip()
                     if user_name_potential: #Basic name validation
                        user_name = user_name_potential
                        break # Exit once name found


        # Generate a simple progress summary (basic example - improve later)
        chapters_discussed = 0
        for chapter_data in session['biography_outline']:
            if chapter_data['status'] == 'Complete': # Assuming you'll have a 'status' field and update it elsewhere
                chapters_discussed += 1
        progress_summary = f"So far, we've made progress on {chapters_discussed} chapters of your biography." if chapters_discussed > 0 else "We're ready to pick up where we left off."


        #Welcome them back with personalized message and summary
        welcome_phrase = f"Welcome back, {user_name}! Hi, I am Walt. It's great to continue your story. {progress_summary} Ready to jump back in?"

        #Update the conversation history with the new state
        session['conversation'].append({"role": "assistant", "content":welcome_phrase})

        return jsonify({"response": welcome_phrase, "biography_outline": session['biography_outline']})

    except Exception as e:
        print(f"Error processing checkpoint: {e}")
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/create_checkpoint', methods=['POST'])
def create_checkpoint():
    try:
        checkpoint_data_text = session.get('file_content', '') # Get file_content directly as text
        bio_prompt_content = ""
        try:
            with open('walt/bio_creator_prompt.txt', 'r', encoding='utf-8') as f: # ADDED: Read bio_creator_prompt.txt
                bio_prompt_content = f.read()
        except Exception as e:
            logging.error(f"Error reading bio_prompt.txt: {e}")
            bio_prompt_content = "Error loading bio creator prompt." # Fallback if file not read

        combined_checkpoint_content = bio_prompt_content + "\n\n" + checkpoint_data_text # Combined content

        logging.info(f"Checkpoint data being created: {combined_checkpoint_content[:100]}...") # Log start of data

        return jsonify({"checkpoint_data": combined_checkpoint_content}) # Return combined text

    except Exception as e:
        logging.error(f"Error creating checkpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/walt_process_checkpoint', methods=['POST']) # RENAME saveTextAsFile to walt_process_checkpoint
def walt_process_checkpoint(): # RENAME function as well
    try:
        checkpoint_data_text = session.get('file_content', '') # Get file_content directly as text
        bio_prompt_content = ""
        try:
            with open('walt/bio_creator_prompt.txt', 'r', encoding='utf-8') as f: # Read bio_creator_prompt.txt
                bio_prompt_content = f.read()
        except Exception as e:
            logging.error(f"Error reading bio_prompt.txt: {e}")
            bio_prompt_content = "Error loading bio creator prompt." # Fallback if file not read

        conversation_text = "" # Get conversation text for API call
        current_conversation = session.get('conversation', [])
        for message in current_conversation:
            if message['role'] in ['user', 'assistant']: # Filter for user and assistant roles
                conversation_text += f"{message['role']}: {message['content']}\n"

        # Improvement #4: Tone aware biography creation
        desired_tone = request.form.get('tone', 'default')
        tone_instruction = ""
        if desired_tone != 'default':
            tone_instruction = f" Write the biography in a {desired_tone} tone."


        api_input_text = bio_prompt_content + tone_instruction + "\n\n" + checkpoint_data_text + "\n\n--- CONVERSATION ---\n\n" + conversation_text # Combine for API

        client = openai.Client() # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": api_input_text}], # Send combined text prompt
            temperature=0.7,
            max_tokens=700, # Increased max tokens
        )
        api_response_text = response.choices[0].message.content.strip() # API response

        api_response_text_safe = api_response_text.replace("<", "<").replace(">", ">") # Escape HTML

        # File content for download is now set to the API biography draft - CHANGED
        file_content_for_download = api_response_text_safe # File content for download is NOW API Response - CHANGED

        # Output window displays the downloaded file content - CHANGED to match file
        combined_output_content = api_response_text_safe # Output window displays the same API Response - CHANGED

        # --- FIX: UPDATE SESSION['file_content'] with the new biography draft ---
        session['file_content'] = file_content_for_download
        session.modified = True # Ensure session is marked as modified

        return jsonify({ # Return checkpoint data (for file) and api response (for display)
            "checkpoint_data": file_content_for_download, #<-- CHANGED - Now sending API Response for download
            "api_response": combined_output_content # Return API Response for display - CHANGED
        })


    except Exception as e:
        logging.error(f"Error processing checkpoint and calling API: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@walt_bp.route('/saveTextAsFileDownload', methods=['POST']) # Keep old route for file download part only
def saveTextAsFileDownload(): # Keep separate function for actual download - UNCHANGED
    try:
        data = request.get_json()
        checkpoint_data = data.get('checkpoint_data') # Expect plain text directly

        if not checkpoint_data:
            return jsonify({"error": "No checkpoint data to save"}), 400

        # Return the checkpoint data directly as text
        logging.info(f"Checkpoint data being sent for download: {checkpoint_data[:50]}...") #Debug log start of data
        return jsonify({"fileContent": checkpoint_data}) # Return text directly for download

    except Exception as e:
        logging.error(f"Error return and saving checkpoint from saveTextAsFileDownload: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# Helper function to get biography outline (Improvement #5 - Data Driven Outline)
def get_biography_outline():
    return [
        {"chapter": 1, "title": "Hook – A Defining Moment", "status": "TBD"},
        {"chapter": 2, "title": "Origins – Early Life & Influences", "status": "TBD"},
        {"chapter": 3, "title": "Call to Action – The First Big Life Decision", "status": "TBD"},
        {"chapter": 4, "title": "Rising Conflict – Struggles & Growth", "status": "TBD"},
        {"chapter": 5, "title": "The Climax – Defining Achievements", "status": "TBD"}
