from flask import Blueprint, render_template, request, jsonify, session
import os
import openai  # Import the OpenAI library
from flask import current_app
import logging #Import logging tool for debugging

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
    uploaded_content = request.form.get('uploaded_content', '')  # Get the file content

    if not user_input:
        return jsonify({"error": "No user query provided"}), 400

    try:
        with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
            walt_prompt = f.read()  # Read the walt_prompt.txt
    except FileNotFoundError:
        return jsonify({"error": "walt_prompt.txt not found!"}), 500
    except Exception as e:
        return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

    # Initialize conversation history in session if it doesn't exist
    if 'conversation' not in session:
        # Load initial greeting
        initial_greeting = "Hi I'm Walt. What's your name?"

        session['conversation'] = [{"role": "system", "content": walt_prompt}, #Get prompt
                                     {"role": "assistant", "content": initial_greeting}] #Default state

    # Add the uploaded content (if any) as context
    #Debug Code
    if uploaded_content:
         session['conversation'].append({"role": "system", "content": f"Here is context from your biography: {uploaded_content}"})
         print(f"UPLOADED CONTENT TO OPEN API:{uploaded_content}")
    else:
        print ("NO UPLOADED CONTENT!")


    # Add the user's message to the conversation
    session['conversation'].append({"role": "user", "content": user_input + ". Pick another chapter and let's discuss it."}) # Force chapter selection

    try:
        client = openai.Client()  # Use your preferred method to initialize the OpenAI client

        # Log the messages being sent to OpenAI for debugging
        logging.info(f"OpenAI Request Messages: {session['conversation']}")

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
        # Log the full error for debugging.  You can also return this to Walt but might not be desired.
        logging.error(f"OpenAI API Error: {e}", exc_info=True) # Log the full stack trace
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/walt_session_summary', methods=['POST'])
def walt_session_summary():
    session_content=""
    try:
        client = openai.Client()  # Use your preferred method to initialize the OpenAI client
        # Get session information
        session_info = session.get('conversation', [])
        #Get the story content if uploaded.
        session_content=""
        if 'file_content' in session:
           file_content= session['file_content']
        else:
            file_content = "No story started"

        # Generate Summary from API
        session_content=""
        #if session info exists add it.
        if session_info:
             session_content=session_info
        else:
             session_content = "No story started"


        response = client.chat.completions.create(
            model="gpt-4o",  # Specify the model you want to use
            messages=[{"role": "system", "content": "Your job is to deliver the status and summary of the session, the outline of sections written, the conversation history and the prompt.  Do not add anything else."},
                      {"role": "user", "content": f"Return all known story with with outline, sections written, session prompts, system_info and the conversation for {session_content}."}],
            temperature=0.7,  # Adjust as needed
            max_tokens=2000, # up to 2000 tokes
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
        # Extract user's name (crude, but functional for demonstration)
        if "Name:" in checkpoint_data:
           user_name = checkpoint_data.split("Name:")[1].split("\n")[0].strip()
        else:
            user_name = "User"

        #Call OpenAPI to get summary
        client = openai.Client()
        response = client.chat.completions.create(
            model="gpt-4o",  # Or your preferred model
            messages=[
                {"role": "system", "content": "You are a biography assistant. Summarize the provided checkpoint file and return the users name and what parts of their biography are in the file."},
                {"role": "user", "content": checkpoint_data}
            ],
            temperature=0.7,
            max_tokens=256,
            top_p=1,
        )
        api_response = response.choices[0].message.content.strip()

        # Load the Walt Prompt
        try:
            with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
                walt_prompt = f.read()  # Read the walt_prompt.txt
        except FileNotFoundError:
                return jsonify({"error": "walt_prompt.txt not found!"}), 500
        except Exception as e:
                return jsonify({"error": f"Error reading walt_prompt.txt: {str(e)}"}), 500

        #Update the conversation history with the new state
        session['conversation'] = [{"role": "system", "content": walt_prompt}, #Load walt prompt
                                   {"role": "assistant", "content":f"Welcome back, {user_name}! Hi, I am Walt. Let's continue your story."}]#Update initial phrase

        return jsonify({"response": f"Welcome back, {user_name}! Hi, I am Walt. Let's continue your story."}) #Update the user

    except Exception as e:
        print(f"Error processing checkpoint: {e}")
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/create_checkpoint', methods=['POST']) #New route
def create_checkpoint():
    try:
        client = openai.Client()  # Use your preferred method to initialize the OpenAI client
        # 1. Load the three files
        try:
            with open('walt_prompt.txt', 'r', encoding='utf-8') as f:
                walt_prompt = f.read()
            with open('walt/bio_creator_prompt.txt', 'r', encoding='utf-8') as f: #Load the new prompt
                bio_creator_prompt = f.read()
        except FileNotFoundError as e:
            return jsonify({"error": f"Required prompt file not found: {e}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error reading prompt file: {e}"}), 500

        # 2. Get the session
        session_info = session.get('conversation', [])

        # 3. Consolidate content
        consolidated_content = bio_creator_prompt #Start here
        consolidated_content += "\n --- Previous Checkpoint Data --- \n"
        #Get the story content if uploaded.
        if 'file_content' in session:
             consolidated_content+= session['file_content'] #Tack file content
        else:
             consolidated_content+= "No Checkpoint Data Found"
        consolidated_content += "\n --- Begin Walt Session Data --- \n"
        consolidated_content += str(session_info) #Load Session data for this run

        # 4. Call OpenAPI

        response = client.chat.completions.create(
            model="gpt-4o",  # Or your preferred model
            messages=[
                {"role": "system", "content": walt_prompt}, #Use basic instruction
                {"role": "user", "content": f"Create the next version of the Checkpoint file. Please consolidate and organize this information: {consolidated_content}"}
            ],
            temperature=0.7,
            max_tokens=2000, #Up the ante
            top_p=1,
        )
        revised_content = response.choices[0].message.content.strip()

        # 5. Return the Prompted Results
        return jsonify({"checkpoint_data": revised_content})
    except Exception as e:
        logging.error(f"Error creating checkpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@walt_bp.route('/saveTextAsFile', methods=['POST']) #Updated route to send value for create checkpoint.
def saveTextAsFile():
        # Get the content from create checkpoint and display
       try:
            data = request.get_json() #Get from Ajax not function
            checkpoint_data = data.get('checkpoint_data') #Get the string

            if not checkpoint_data: #Trap potential issue
                return jsonify({"error": "No checkpoint data to save"}), 400

            # Create the new file with checkpoint_data from OpenAPI
            textFileAsBlob = checkpoint_data.encode('utf-8') #Encode data.
            fileNameToSaveAs = "sessionStory.txt"

            # 5. Return data (to front end)
            return jsonify({"fileContent": f"{textFileAsBlob.decode()}"}) #All set

       except Exception as e:
            logging.error(f"Error return and saving checkpoint from saveTextAsFile: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500 #Shot error
