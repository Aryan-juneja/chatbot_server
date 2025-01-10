from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai
import logging
from dotenv import load_dotenv
import os
import boto3
import mysql.connector
# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
# === Hardcoded API Keys and MongoDB Credentials ===
try:
    openai.api_key = os.getenv('OPEN_AI_API_KEY')
    tavily_api_key = os.getenv('TAVILY_API_KEY')
    KENDRA_INDEX_ID = os.getenv('KENDRA_INDEX_ID')
    AWS_REGION = os.getenv('AWS_REGION')
    ROLE_ARN = os.getenv('ROLE_ARN')
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    host=os.getenv('HOST')
    database=os.getenv('DATABASE')
    user=os.getenv('USER')
    password=os.getenv('PASSWORD')
    kendra_client = boto3.client(
    "kendra",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=AWS_REGION,
)

except Exception as e:
    logger.error("Error initializing APIs or MongoDB: %s", e)
    exit(1)

# === Initialize Flask App ===
app = Flask(__name__)
CORS(app)

# === Routes ===

@app.route("/")
def home():
    """Root route for the application."""
    return jsonify({
        "message": "Welcome to the API!",
        "routes": [
            {"endpoint": "/", "description": "Root route with available endpoints"},
            {"endpoint": "/fetchip", "description": "Fetch the user's IP address"},
            {"endpoint": "/chat", "description": "Chat API (POST)"},
            {"endpoint": "/save-user-credentials", "description": "Save user credentials (POST)"},
            {"endpoint": "/api/v1/transcript", "description": "Transcript API (POST)"},
        ]
    }), 200

@app.route("/favicon.ico")
def favicon():
    """Avoid 404 errors for favicon."""
    return "", 204

@app.route("/fetchip", methods=["GET"])
def fetchip():
    """Fetch the user's IP address."""
    try:
        ip_add = request.headers.get("X-Forwarded-For", request.remote_addr)
        return jsonify({"ip": ip_add})
    except Exception as e:
        logger.error("Error fetching IP: %s", e)
        return jsonify({"error": "Unable to fetch IP"}), 500

@app.route("/save-user-credentials", methods=["POST"])
def save_user_credentials():
    """Save user credentials."""
    try:
        data = request.json
        user_id = data.get("user_id")
        name = data.get("name")
        email = data.get("email")
        if not user_id or not name or not email:
            return jsonify({"error": "Missing required field"}), 400
        
        # Save user credentials to the database
        connection = create_connection()
        cursor = connection.cursor()
        query = "INSERT INTO User (user_id, name, email) VALUES (%s, %s, %s)"
        cursor.execute(query, (user_id, name, email))
        connection.commit()
        connection.close()
        
        return jsonify({"message": "User credentials saved successfully"}), 201
    except Exception as e:
        logger.error("Error saving user credentials: %s", e)

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages."""
    try:
        data = request.json
        chat_history = data.get("chat_history")
        buffer_memory = data.get("buffer_memory")
        logger.info("buffer_memory: %s", buffer_memory)
        logger.info("chat_history: %s", chat_history)
        if not chat_history or buffer_memory is None:
            return jsonify({"error": "Invalid input"}), 400

        messages = [
            {"role": chat["role"], "content": chat["content"]} for chat in chat_history
        ]

        query = create_query(messages, buffer_memory)
        search_results = None

        if query not in ["'NONE'", "NONE", '"None"']:
            search_results = search_query(query)
            buffer_memory.append(search_results)

        bot_reply = chat_answer(messages, buffer_memory)
        buffer_memory.append(bot_reply)
        chat ={"role": "assistant", "content": bot_reply}
        chat_history.append(chat)
        return jsonify({"bot_reply": bot_reply})

    except Exception as e:
        logger.error("Error handling chat: %s", e)
        return jsonify({"error": "An error occurred"}), 500

@app.route("/api/v1/transcript", methods=["POST"])
def transcript():
    """Handle Transcription."""
    try:
        # Parse JSON input
        data = request.get_json()
        if not data or "userQuery" not in data or not isinstance(data["userQuery"], str):
            return jsonify({"error": "Invalid input: 'userQuery' is required and must be a string"}), 400

        user_query = data["userQuery"].strip()
        if not user_query:
            return jsonify({"error": "Invalid input: 'userQuery' cannot be empty"}), 400

        logger.info("Received userQuery: %s", user_query)

        # Construct the prompt
        prompt = (
    "You are a highly skilled assistant specializing in interpreting and refining user queries,"
    "particularly for real estate searches. Your goal is to take the provided 'userQuery' and transform it into "
    "a precise, complete, and actionable query that aligns with the user's intent. Please focus on providing "
    "a query that is specific, relevant to real estate, and ready for use in a property search engine."
    "\n\n"
    "Guidelines:\n"
    "1. Retain key details from the userQuery, such as location, type of property, price range, or specific needs.\n"
    "2. Ensure the query is formatted naturally and fully expresses the user's intent.\n"
    "3. Avoid including extraneous text or unrelated details—just the transformed query.\n"
    "4. Ensure clarity, e.g., if the user mentions a city, include it explicitly in the response.\n\n"
    f"userQuery: {user_query}"
)


        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0,
        )

        logger.info("Response from OpenAI: %s", response)

        # Safely extract the response content
        query = response.choices[0].message.content.strip() if response and response.choices else None
        if not query:
            logger.error("OpenAI response missing 'content'")
            return jsonify({"error": "Failed to generate query"}), 500

        # Return the refined query
        return jsonify({"query": query}), 200

    except openai.error.OpenAIError as oe:
        logger.error("OpenAI API error: %s", oe)
        return jsonify({"error": "OpenAI API error occurred"}), 500
    except Exception as e:
        logger.error("Unhandled exception: %s", e, exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500




# === Helper Functions ===


def create_connection():
    """Create a database connection."""
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    return connection

def create_query(chat_history, buffer_memory):
    """Generate an optimized search query based on chat history."""
    user_prompts = [
        {"content": chat["content"]} for chat in chat_history if chat["role"] == "user"
    ]
    prompt = f"""
    You are a Google search query generator for a real estate expert. Return:
    1. 'NONE' if the relevant data is in the buffer or the query is general.
    2. An optimized search query string if the needed information isn't in the buffer.

    Chat_history: {chat_history[1:]} 
    Buffer data: {buffer_memory}
    """
    prompt = [{"role": "system", "content": prompt}]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=prompt, max_tokens=100, temperature=0
        )
        logger.info("Response from query creation: %s", response)
        query = response.choices[0].message.content  # Correct way to access content
        print("Query-----------------------------------------------",query)
        return query
    except Exception as e:
        logger.error("Error generating query: %s", e)
        return "NONE"


def search_query(query):
    """Perform a search using Tavily API."""
    try:
        search_result = tavily.search(query.strip(), include_images=True)
        full_text = [
                        result["content"] + result["url"] for result in search_result["results"]
                    ] + search_result["images"]
        return full_text
    except Exception as e:
        logger.error("Error performing search: %s", e)
        return []

def kendra_search(query):
    """
    Query AWS Kendra for search results.
    """
    try:
        response = kendra_client.query(
            IndexId=KENDRA_INDEX_ID,
            QueryText=query,
            PageSize=3
        )
        results = []
        for item in response.get("ResultItems", []):
            content = item.get("DocumentExcerpt", {}).get("Text", "")
            image_link = item.get("DocumentAttributes", [{}])[0].get("Value", {}).get("TextWithLinksValue", "No image available")
            results.append({
                "content": content,
                "image_link": image_link
            })
        return results
    except Exception as e:
        print(f"Error querying Kendra: {e}")
        return []
def chat_answer(messages, buffer_memory):
    """Generate chatbot response."""
    try:
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, "prompt2.txt")
        with open(file_path, "r") as f:
            prompt = f.read()
        query=messages[0]["content"]
        search_results=kendra_search(query)
        messages[0]["content"] += f""" {prompt} Use this info: {search_results}."""

        response = openai.chat.completions.create(
            model="gpt-4o-mini", messages=messages, temperature=0
        )

        # Access the content of the first choice from the response
        bot_reply = response.choices[0].message.content.strip()  # Correct way to access content

        return bot_reply

    except Exception as e:
        logger.error("Error generating chatbot response: %s", e)
        return "An error occurred while generating the response."


# === Main ===

if __name__ == "__main__":
    app.run(port=5000)
