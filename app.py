import json

from dotenv import load_dotenv
from flask import Flask, request
import os
from twilio.rest import Client
import google.generativeai as genai

load_dotenv(".env")

account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
client = Client(account_sid, auth_token)
genai.configure(api_key=os.getenv("AI_API_KEY"))

# Create the model
generation_config = genai.GenerationConfig(
    temperature=1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="text/plain",
)

with open("system_instruction.txt", "r") as f:
    system_instruction = f.read()

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash",
  generation_config=generation_config,
  system_instruction=system_instruction
)

chat_session = model.start_chat(
  history=[
  ]
)


app = Flask(__name__)


@app.route("/hook/incoming_message", methods=["POST"])
def on_incoming_message():
    phone_number = request.form['From']
    incoming_message = request.form['Body']

    print(f"Received message: {incoming_message} from e{phone_number}e")  # Add logging
    # process message
    ai_response = chat_session.send_message(incoming_message)

    print(f"AI Response: {ai_response.text}")  # Log AI the response
    if "[FOR_BACKEND]" in ai_response.text:
        user_confirmation, be_data = ai_response.text.split("[FOR_BACKEND]")
        try:
            message = client.messages.create(
                body=user_confirmation.split("[USER]")[1],
                from_=f'whatsapp:{os.getenv("TWILIO_PHONE")}',
                to=phone_number
            )
            print(f"Message sent to {phone_number}. SID: {message.sid}")  # Log message SID for tracking
        except Exception as e:
            print(f"Error sending message via Twilio: {e}")
        be_data = json.loads(be_data)

        return ""

    try:
        message = client.messages.create(
            body=ai_response.text,
            from_=f'whatsapp:{os.getenv("TWILIO_PHONE")}',
            to=phone_number
        )
        print(f"Message sent to {phone_number}. SID: {message.sid}")  # Log message SID for tracking
    except Exception as e:
        print(f"Error sending message via Twilio: {e}")

    return "" # endpoint has to return something valid other than None


if __name__ == "__main__":
    app.run(port=5000)
