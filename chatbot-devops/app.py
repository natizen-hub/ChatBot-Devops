from flask import Flask, request, jsonify, render_template, send_file
import ollama
import os
import json

app = Flask(__name__)

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
    mode = request.json.get("mode", "chat")  # chat, interview, cv
    
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    messages = [{"role": "user", "content": SYSTEM_PROMPT + "\n\nMode: " + mode}]
    messages += conversation_history
    
    response = ollama.chat(
        model="llama3.2",
        messages=messages
    )
    
    bot_reply = response["message"]["content"]
    
    conversation_history.append({
        "role": "assistant",
        "content": bot_reply
    })
    
    return jsonify({"reply": bot_reply})

@app.route("/generate-cv", methods=["POST"])
def generate_cv():
    user_info = request.json.get("info")
    
    prompt = f"""Generate a professional CV in the same language as the following information.
Format it clearly with sections: Personal Info, Summary, Experience, Education, Skills.
User information: {user_info}
Make it ATS-friendly and professional."""
    
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )
    
    cv_content = response["message"]["content"]
    
    cv_path = os.path.join(UPLOAD_FOLDER, "cv_generated.txt")
    with open(cv_path, "w", encoding="utf-8") as f:
        f.write(cv_content)
    
    return jsonify({"cv": cv_content, "download": "/download-cv"})

@app.route("/download-cv")
def download_cv():
    cv_path = os.path.join(UPLOAD_FOLDER, "cv_generated.txt")
    return send_file(cv_path, as_attachment=True, download_name="my_cv.txt")

@app.route("/upload-cv", methods=["POST"])
def upload_cv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"})
    
    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    response = ollama.chat(
        model="llama3.2",
        messages=[{
            "role": "user",
            "content": f"Analyze this CV and give detailed feedback to improve it. Be specific and constructive:\n\n{content}"
        }]
    )
    
    return jsonify({"analysis": response["message"]["content"]})

@app.route("/reset", methods=["POST"])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    app.run(debug=True)