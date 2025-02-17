import os

def send_message(client, message):
    message = client.messages.create(
        from_=f"whatsapp:{os.getenv("TWILIO_PHONE")}",
        body=message,
        to=f"whatsapp:{os.getenv("MY_PHONE")}"
    )
    return message.sid