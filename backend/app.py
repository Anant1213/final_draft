from flask import Flask, render_template, request, jsonify, session
import openai
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from flask_session import Session
from backend.pdf_processing import extract_text_from_pdf
import re  # Import the re module for name validation

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / '.env')
openai.api_key = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).parent.parent
# Initialize Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'Frontend', 'Template'),  # Corrected 'Frontend'
    static_folder=os.path.join(BASE_DIR, 'Frontend', 'static')
)

app.secret_key = "your_secret_key"

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize session
sess = Session()
sess.init_app(app)

USER_DATA_FILE = Path(__file__).parent / 'user_data.json'

# PDF Mapping (Update with correct paths)
PDF_MAP = {
    "amity": "/Users/anant/projects/deployment_testing/1st_test/pdfs/amity.pdf",
    "chandigarh": "/Users/anant/projects/deployment_testing/1st_test/pdfs/chandigarh.pdf",
    "woxsen": "/Users/anant/projects/deployment_testing/1st_test/pdfs/woxsen.pdf",
    "dbs": "/Users/anant/projects/deployment_testing/1st_test/pdfs/dbs.pdf",
    "jklu": "/Users/anant/projects/deployment_testing/1st_test/pdfs/jklu.pdf"
}

# Save user info function
def save_user_info(name, phone):
    user_data = {"name": name, "phone": phone}
    try:
        with open(USER_DATA_FILE, 'r') as file:
            contacts = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        contacts = []

    contacts.append(user_data)
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(contacts, file, indent=4)

# GPT answer function
def get_answer_from_gpt(pdf_text, query, user_name):
    system_prompt = (
        f"You are an empathetic and knowledgeable college admissions assistant. You help students find their respective university and provide concise, personalized advice."
        f"Your role is to assist {user_name} with their college application and provide clear, helpful responses."
    )

    user_prompt = (
        f"Here is some information from the university:\n\n{pdf_text}\n\n{user_name}'s Question: {query}\n\nProvide a concise answer. If you don't have any information, state 'I'm sorry, I don't have that information, our counselors will call.'"
    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        answer = completion['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        print(f"Error in OpenAI API request: {e}")
        return f"Error communicating with OpenAI API: {str(e)}"



@app.route('/')
def index():
    print("Template folder:", app.template_folder)
    print("Static folder:", app.static_folder)
    print("Index file exists:", os.path.exists(os.path.join(app.template_folder, 'index.html')))
    return render_template('index.html')

@app.route('/greet', methods=['GET'])
def greet():
    return jsonify({"message": "Hi, I am Gaurav , you can ask me about college stuff."})

@app.route('/amity')
def amity_page():
    session['university'] = 'amity'
    reset_session()
    return render_template('amity.html')

@app.route('/chandigarh')
def chandigarh_page():
    session['university'] = 'chandigarh'
    reset_session()
    return render_template('chandigarh.html')

@app.route('/woxsen')
def woxsen_page():
    session['university'] = 'woxsen'
    reset_session()
    return render_template('woxsen.html')

@app.route('/dbs')
def dbs_page():
    session['university'] = 'dbs'
    reset_session()
    return render_template('dbs.html')

@app.route('/jklu')
def jklu_page():
    session['university'] = 'jklu'
    reset_session()
    return render_template('jklu.html')

# Reset session state when switching between universities
def reset_session():
    if 'university' in session:
        session_key = f"session_{session['university']}"
        if session_key in session:
            session.pop(session_key)

@app.route('/chat', methods=['POST'])
@app.route('/chat', methods=['POST'])
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()

    print(f"Current session: {session}")

    if not user_input:
        return jsonify({"error": "Please provide a query."}), 400

    user_university = session.get('university')

    if user_university not in PDF_MAP:
        return jsonify({"error": "Invalid university."}), 400

    pdf_path = PDF_MAP[user_university]
    session_key = f"session_{user_university}"

    if session_key not in session:
        print(f"Initializing new session for {user_university}")
        session[session_key] = {
            'state': 'greeted',
            'pdf_text': None,
            'pending_query': None,
            'name': None,
            'phone': None,
            'questions_asked': 0  # Counter for queries
        }

    current_session = session[session_key]
    response = {}

    # Handle the greeting state and initial query
    if current_session['state'] == 'greeted':
        current_session['pdf_text'] = extract_text_from_pdf(pdf_path)[:2000]  # Save PDF text
        current_session['pending_query'] = user_input
        current_session['state'] = 'awaiting_name'
        session[session_key] = current_session
        response['message'] = "Please enter your name:"
        return jsonify(response)

    # Ask for and validate the name
    elif current_session['state'] == 'awaiting_name':
        if not validate_name(user_input):
            response['message'] = "Please provide a valid first and last name."
            return jsonify(response)

        current_session['name'] = user_input
        current_session['state'] = 'awaiting_phone'
        session[session_key] = current_session
        response['message'] = "Please enter your phone number:"
        return jsonify(response)

    # Ask for and validate the phone number
    elif current_session['state'] == 'awaiting_phone':
        if not user_input.isdigit() or len(user_input) != 10:
            response['message'] = "Please provide a valid 10-digit phone number."
            return jsonify(response)

        current_session['phone'] = user_input
        save_user_info(current_session['name'], current_session['phone'])
        answer = get_answer_from_gpt(current_session['pdf_text'], current_session['pending_query'], current_session['name'])
        current_session['questions_asked'] = 1  # Count the initial query
        current_session['state'] = 'chatting'
        session[session_key] = current_session

        response['message'] = answer  # Answer the initial query
        return jsonify(response)

    # Handle subsequent queries
    elif current_session['state'] == 'chatting':
        if current_session['questions_asked'] >= 3:
            response['message'] = "We know that your questions are important. We will call you on the phone number provided for further assistance."
            return jsonify(response)

        user_name = current_session['name']
        answer = get_answer_from_gpt(current_session['pdf_text'], user_input, user_name)
        current_session['questions_asked'] += 1
        session[session_key] = current_session

        if current_session['questions_asked'] == 3:
            response['message'] = answer + "\nYou have reached the query limit. We will call you for further assistance."
        else:
            response['message'] = answer
        return jsonify(response)



def validate_name(name):
    name_pattern = r"^[A-Za-z]+(?: [A-Za-z]+){0,2}$"
    return bool(re.match(name_pattern, name))

if __name__ == "__main__":
    app.run(debug=True)
