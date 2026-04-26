from flask import Flask, request, jsonify, render_template, send_file
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SYSTEM_PROMPT = """You are an expert career coach and interview preparation assistant.
You help users prepare for job interviews in multiple languages (Arabic, French, English).
You can:
1. Simulate realistic job interviews by asking professional questions
2. Analyze and improve the user's answers
3. Generate professional CVs based on user information
4. Give tips and feedback on interview performance
5. Adapt to the language the user writes in

Always be encouraging, professional, and constructive.
If the user writes in Arabic, respond in Arabic.
If the user writes in French, respond in French.
If the user writes in English, respond in English.
When simulating an interview, ask one question at a time and wait for the answer."""

conversation_history = []

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global conversation_history
    user_message = request.json.get("message")
    mode = request.json.get("mode", "chat")

    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\nMode: " + mode}]
    messages += conversation_history

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024
    )

    bot_reply = response.choices[0].message.content

    conversation_history.append({
        "role": "assistant",
        "content": bot_reply
    })

    return jsonify({"reply": bot_reply})

@app.route("/upload-cv", methods=["POST"])
def upload_cv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"Analyze this CV and give detailed feedback: {content}"
        }],
        max_tokens=1024
    )

    return jsonify({"analysis": response.choices[0].message.content})

@app.route("/reset", methods=["POST"])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    app.run(debug=True)
