import json
import pdfkit
from typing import Final
from dotenv import load_dotenv
from flask import Flask, request, send_file, render_template
import os
from twilio.rest import Client
import google.generativeai as genai
import re
from vacancies import Vacancies

load_dotenv(".env")

# twilio
ACCOUNT_SID: Final[str] = os.getenv("ACCOUNT_SID")
TWILIO_AUTH_TOKEN: Final[str] = os.getenv("AUTH_TOKEN")
client = Client(ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Gemini AI
genai.configure(api_key=os.getenv("AI_API_KEY"))

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

# Server

app = Flask(__name__)

@app.route("/resume")
def serve_pdf():
    """host generated pdf file"""
    return send_file("resume.pdf", mimetype="application/pdf")


@app.route("/hook/incoming_message", methods=["POST"])
def on_incoming_message():
    phone_number = request.form['From']
    incoming_message = request.form['Body']

    print(f"Received message: {incoming_message} from {phone_number}")  # logging
    ai_response = chat_session.send_message(incoming_message) # Process message
    print(f"AI Response: {ai_response.text}") # logging

    if "[FOR_BACKEND]" in ai_response.text:
        user_confirmation, person_data = extract_user_and_json(ai_response.text)
        send(user_confirmation, phone_number)
        person_data = json.loads(person_data)

        data = person_data["job_interest"]

        # Jobs
        vac = Vacancies(
            job_title=data["job_title"],
            city_or_state=data["city_or_state"],
            country=data["country"],
            keyword_description=None
        )
        jobs = Vacancies.get_vacancies_info_list(vac.get_vacancies_id_list())
        jobs_text = ""
        if type(jobs) == list:
            for job in jobs:
                jobs_text += f"*Job Title:* \n{job["title"]}\n"
                jobs_text += f"*Company:* \n{job["company_name"]}\n"
                jobs_text += f"*Seniority:* \n{job["seniority"]}\n"
                jobs_text += f"*URL:* \n{job["url"]}\n"
                jobs_text += f"\n\n"
        else:
            jobs_text = jobs
        print(jobs_text)
        send(jobs_text, phone_number)

        # Resume PDF
        processed_html = render_template("resume.html", person=person_data)
        print(processed_html)
        pdfkit.from_string(processed_html, "resume.pdf")
        send(
            msg="Here is finished your Resume :)",
            phone_number=phone_number,
            media_url="https://90f0-92-213-83-47.ngrok-free.app/resume")
        return "", 204 # return no content

    send(ai_response.text, phone_number)
    return "", 204 # return no content


def extract_user_and_json(text):
    pattern = r"\[USER\]\s*(.*?)\s*\[FOR_BACKEND\]\s*```json\s*(\{.*\})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        user_response = match.group(1).strip()
        backend_json = match.group(2).strip()
        return user_response, backend_json
    return None, None


def send(msg, phone_number, media_url=None):
    try:
        message = client.messages.create(
            body=msg,
            media_url=media_url if media_url is not None else [media_url],
            from_=f'whatsapp:{os.getenv("TWILIO_PHONE")}',
            to=phone_number
        )
        #print(f"Message sent to {phone_number}. SID: {message.sid}")  # Log message SID for tracking
    except Exception as e:
        print(f"Error sending message via Twilio: {e}")


if __name__ == "__main__":
    app.run(port=5000)
