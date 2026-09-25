from flask import Flask, render_template, request, jsonify
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

import re  # Add this import at the top of app.py


def sanitise_input(message):
    """
    Clean and validate user input.
    Returns cleaned message or None if invalid.
    """
    if not message:
        return None

    # Remove leading/trailing whitespace
    message = message.strip()

    # Check if message is empty after stripping
    if not message:
        return None

    # Remove HTML tags (prevents script injection)
    message = re.sub(r"<[^>]+>", "", message)

    # Check length after cleaning
    if len(message) > 500:
        return None

    return message


# Create the Flask application
app = Flask(__name__)

# Initialize the chatbot
chatbot = ChatBot(
    "VladBot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri="sqlite:///chatbot_database.sqlite3",
)

# Train the chatbot with English conversations
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")

# Custom training for school-related topics
from chatterbot.trainers import ListTrainer

list_trainer = ListTrainer(chatbot)

# Train on school-related conversations
list_trainer.train(
    [
        "What subjects do you like?",
        "I find all subjects interesting, but I really enjoy helping with coding!",
        "Can you help with homework?",
        "I can try to help explain concepts, but you should do your own work!",
        "Who made you?",
        "I was created by a talented Year 9 student at Tempe High School!",
    ]
)

# Train on greetings
list_trainer.train(
    [
        "Good morning!",
        "Good morning! How can I help you today?",
        "Good afternoon!",
        "Good afternoon! What would you like to chat about?",
    ]
)

# Safety: Keywords that should trigger a mental health response
CRISIS_KEYWORDS = [
    "suicide",
    "kill myself",
    "end my life",
    "self harm",
    "self-harm",
    "dont want to live",
    "don't want to live",
    "want to die",
]

CRISIS_RESPONSE = """I'm concerned about what you've shared. Please know that you're not alone.

If you're in crisis, please reach out for support:

- Lifeline: 13 11 14 (24/7)
- Kids Helpline: 1800 55 1800
- Beyond Blue: 1300 22 4636

I'm just a chatbot and can't provide the support you need, but these services have trained counselors ready to help right now."""


def check_for_crisis(message):
    """Check if message contains crisis keywords."""
    message_lower = message.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in message_lower:
            return True
    return False


@app.route("/")
def home():
    """Serve the main chat page."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    raw_message = data.get("message", "")

    user_message = sanitise_input(raw_message)

    if user_message is None:
        if not raw_message or not raw_message.strip():
            return jsonify({"response": "Please enter a message!"})
        else:
            return jsonify(
                {"response": "Message too long! Please keep it under 500 characters."}
            )

    # Safety check for crisis keywords
    if check_for_crisis(raw_message):
        return jsonify({"response": CRISIS_RESPONSE})

    bot_response = chatbot.get_response(raw_message)
    return jsonify({"response": str(bot_response)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
