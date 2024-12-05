import requests

url = "http://127.0.0.1:5000/chat"
data = {
    "chat_history": [
        {"role": "user", "content": "Tell me about real estate trends in 2024."},
        {"role": "assistant", "content": "Sure! The 2024 real estate market is expected to be shaped by several factors..."}
    ],
    "buffer_memory": [
        "Interest rates are expected to remain stable in 2024, favoring buyers."
    ]
}

response = requests.post(url, json=data)

print("Response:", response.json())
