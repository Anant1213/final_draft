from flask import Flask, render_template, request, jsonify, session
import openai
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from flask_session import Session
from backend.pdf_processing import extract_text_from_pdf

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / '.env')
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(
    __name__,
    template_folder="Users/anant/projects/multi-link multi pdf/web_trial/frontend/templates",  # Absolute path
    static_folder="/Users/anant/projects/multi-link multi pdf/web_trial/frontend/static"        # Absolute path
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
    "amity": "/Users/anant/projects/multi-link multi pdf/web_trail/pdfs/Amity.pdf",
    "chandigarh": "/Users/anant/projects/multi-link multi pdf/web_trail/pdfs/chandigarh.pdf",
    "woxsen": "/Users/anant/projects/multi-link multi pdf/web_trail/pdfs/woxsen.pdf",
    "dbs": "/Users/anant/projects/multi-link multi pdf/web_trail/pdfs/dbs.pdf",
    "jklu": "/Users/anant/projects/multi-link multi pdf/web_trail/pdfs/jklu.pdf"
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
        f"You are an empathetic and knowledgeable college admissions assistant which help student find respective univeristy, you have a experience od decades. "
        f"Your role is to help {user_name} with their college application and provide concise, personalized advice for the admission ."
    )

    user_prompt = (
        f"Here is some information from the university:\n\n{pdf_text}\n\n{user_name}'s Question: {query}\n\nProvide a concise answer. Keep in mind that if you don't have any information about the question, you can say 'I'm sorry, I don't have that information, our counselors will call.'"

    )

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        answer = completion.choices[0].message.content.strip()
        return answer
    except Exception as e:
        return f"Error communicating with OpenAI API: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

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
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()

    # Debugging: Print current session state
    print(f"Current session: {session}")

    if not user_input:
        return jsonify({"error": "Please provide a query."}), 400

    # Automatically get the university from the session
    user_university = session.get('university')

    # Ensure valid university
    if user_university not in PDF_MAP:
        return jsonify({"error": "Invalid university."}), 400

    pdf_path = PDF_MAP[user_university]

    # Initialize session for this specific university if not present
    session_key = f"session_{user_university}"

    if session_key not in session:
        print(f"Initializing new session for {user_university}")
        session[session_key] = {
            'state': 'awaiting_query',
            'pdf_text': None,
            'pending_query': None,
            'name': None,
            'phone': None
        }

    current_session = session[session_key]
    response = {}

    if current_session['state'] == 'awaiting_query':
        pdf_text = extract_text_from_pdf(pdf_path)
        current_session['pdf_text'] = pdf_text[:2000]  # Save truncated PDF text
        current_session['pending_query'] = user_input
        current_session['state'] = 'awaiting_name'
        session[session_key] = current_session

        response['message'] = "Please enter your name:"
        return jsonify(response)

    elif current_session['state'] == 'awaiting_name':
        current_session['name'] = user_input
        current_session['state'] = 'awaiting_phone'
        session[session_key] = current_session

        response['message'] = "Please enter your phone number:"
        return jsonify(response)

    elif current_session['state'] == 'awaiting_phone':
        current_session['phone'] = user_input
        save_user_info(current_session['name'], current_session['phone'])

        answer = get_answer_from_gpt(current_session['pdf_text'], current_session['pending_query'], current_session['name'])
        current_session['state'] = 'chatting'
        session[session_key] = current_session

        response['message'] = answer + " Is there anything else you'd like to ask?"
        return jsonify(response)

    elif current_session['state'] == 'chatting':
        user_name = current_session['name']
        answer = get_answer_from_gpt(current_session['pdf_text'], user_input, user_name)
        response['message'] = answer
        return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
