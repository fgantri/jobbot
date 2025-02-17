from dotenv import load_dotenv
from utility import send_message
from flask import Flask, request
import os
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv(".env")

account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
client = Client(account_sid, auth_token)

def main():
    send_message(client=client, message="Initial Message")


app = Flask(__name__)


@app.route("/hook/incoming_message", methods=["POST"])
def on_incoming_message():
    incoming_message = request.form['Body']

    # TODO process message

    # generate response
    response = MessagingResponse()
    response.message(f"You told me: \"{incoming_message}\". I'll reach out to you soon.")
    return str(response)


if __name__ == "__main__":
    main()
    app.run(port=5000)
