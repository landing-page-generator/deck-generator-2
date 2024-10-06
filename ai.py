import os
import requests

from pathlib import Path
from dotenv import load_dotenv

from ai21 import AI21Client
from ai21.models.chat import ChatMessage

_ = load_dotenv(Path(__file__).parent / ".env")


def gemini(prompt):
    api_key = os.environ["GEMINI_API_KEY"]
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    api_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }

    # Making the POST request
    try:
        response = requests.post(api_endpoint, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad responses (4XX, 5XX)

        # Handle the response
        response_data = response.json()
        return response_data["candidates"][0]["content"]["parts"][0]["text"]

    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
        return None


def ai21(prompt):
    api_key = os.environ["AI21_API_KEY"]
    model = os.environ.get("AI21_MODEL", "jamba-1.5-mini")
    ai21_client = AI21Client(api_key)

    # system = "You're a sales manager in a SaaS company"
    messages = [
        # ChatMessage(content=system, role="system"),
        ChatMessage(content=prompt, role="user"),
    ]

    chat_completions = ai21_client.chat.completions.create(
        messages=messages,
        model=model,
    )

    return chat_completions.choices[0].message.content
