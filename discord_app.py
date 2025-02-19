import json
import pdfkit
from typing import Final
from dotenv import load_dotenv
import os
import google.generativeai as genai
import re
from discord import Intents, Client as DiscordClient, File, DMChannel
from vacancies import Vacancies
from jinja2 import Environment, FileSystemLoader

load_dotenv(".env")


# discord
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
intents = Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True
discord_client = DiscordClient(intents=intents)


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


@discord_client.event
async def on_ready():
    print(f'✅ Bot is online as {discord_client.user}!')


@discord_client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == discord_client.user:
        return

    # Check if it's a DM (private message)
    if isinstance(message.channel, DMChannel):
        print(f"📩 DM from {message.author}: {message.content}")
        ai_response = chat_session.send_message(message.content)
        print(f"AI Response: {ai_response.text}")

        if "[FOR_BACKEND]" in ai_response.text:
            user_confirmation, person_data = extract_user_and_json(ai_response.text)
            await message.channel.send(user_confirmation)
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
            await message.channel.send(jobs_text)

            pdf_path = "resume.pdf"
            env = Environment(loader=FileSystemLoader("templates"))
            template = env.get_template("resume.html")
            context = {
                "person": person_data
            }
            processed_html = template.render(context)
            print(processed_html)
            pdfkit.from_string(processed_html, "resume.pdf")
            if os.path.exists(pdf_path):  # Check if the file exists
                await message.channel.send("📄 Resume:", file=File(pdf_path))
            return
        # Respond to the user
        await message.channel.send(ai_response.text)


def extract_user_and_json(text):
    pattern = r"\[USER\]\s*(.*?)\s*\[FOR_BACKEND\]\s*```json\s*(\{.*\})\s*```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        user_response = match.group(1).strip()
        backend_json = match.group(2).strip()
        return user_response, backend_json
    return None, None


# Run bot
if __name__ == "__main__":
    discord_client.run(DISCORD_TOKEN)
