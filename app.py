import os
from langchain.tools import Tool
from plyer import notification
import time
import threading
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import smtplib
from email.mime.text import MIMEText
from langchain.agents import initialize_agent, Tool
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import speech_recognition as sr
from serpapi import GoogleSearch

load_dotenv()

def set_alarm_tool(time_str: str, message: str):
    """
    Sets an alarm.
    Args:
        time_str (str): Alarm time in HH:MM format.
        message (str): Alarm message.
    """
    def alarm_thread():
        alarm_time = time.strptime(time_str, "%H:%M")
        current_time = time.localtime()
        seconds_until_alarm = (
            (alarm_time.tm_hour - current_time.tm_hour) * 3600
            + (alarm_time.tm_min - current_time.tm_min) * 60
        )
        if seconds_until_alarm < 0:
            return "Alarm time must be in the future!"
        time.sleep(seconds_until_alarm)
        notification.notify(
            title="Alarm Notification",
            message=message,
            app_name="Desktop Alarm",
            timeout=10,
        )
        return "Alarm set successfully!"

    threading.Thread(target=alarm_thread).start()
    return "Alarm is being set."

alarm_tool = Tool(
    name="Set Alarm",
    description="Sets a desktop alarm for a specific time. Input format: HH:MM and a message.",
    func=lambda input: set_alarm_tool(input.split(";")[0], input.split(";")[1])
)

def create_calendar_event(summary: str, start_time: str, end_time: str):
    """
    Creates a calendar event.
    Args:
        summary (str): Event title.
        start_time (str): Start time in ISO format.
        end_time (str): End time in ISO format.
    """
    
    creds = Credentials.from_authorized_user_file('credentials.json', ['https://www.googleapis.com/auth/calendar'])
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": "UTC"},
        "end": {"dateTime": end_time, "timeZone": "UTC"},
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    return f"Event created: {event.get('htmlLink')}"

calendar_tool = Tool(
    name="Create Calendar Event",
    description="Creates a Google Calendar event. Input format: 'summary;start_time;end_time' (ISO time format).",
    func=lambda input: create_calendar_event(*input.split(";"))
)

def send_email_tool(recipient: str, subject: str, body: str):
    """
    Sends an email.
    Args:
        recipient (str): Recipient email address.
        subject (str): Subject of the email.
        body (str): Body of the email.
    """
    sender_email = os.environ["SENDER_EMAIL"]
    sender_password = os.environ["SENDER_PASSWORD"]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())

    return "Email sent successfully!"

email_tool = Tool(
    name="Send Email",
    description="Sends an email. Input format: 'recipient;subject;body'.",
    func=lambda input: send_email_tool(*input.split(";"))
)

def voice_input_tool():
    """
    Captures and processes voice input to generate commands for the agent.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your command (say 'stop' to quit)...")
        try:
            audio = recognizer.listen(source,timeout=5, phrase_time_limit=10)
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand what you said.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""

def google_search(query: str) -> str:
    """Perform a Google search using SerpAPI and return the top results."""
    serpapi_key = os.environ["SERP_API_KEY"]
    search = GoogleSearch({
        "q": query,
        "api_key": serpapi_key
    })
    results = search.get_dict()
    
    search_results = results.get("organic_results", [])
    response = "\n".join([f"{i+1}. {result['title']}: {result['link']}" for i, result in enumerate(search_results[:5])])
    return response or "No results found."

google_search_tool = Tool(
    name="Google Search",
    func=google_search,
    description="Use this tool to search Google for information."
)

llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile")

# Add tools to the agent
tools = [alarm_tool, calendar_tool, email_tool, google_search_tool]

# Initialize the agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

# Run the agent
#response = agent.run("Set an alarm at 15:30 with the message 'Meeting with Bob'.")
# response = agent.run("Send Email to MilindKapile at Yahoo about Testing of App")
# #response = agent.run("Set a Calender Event for 11th January 2025 at 3 pm  to 5 pm Pacific Time Zone for Testing")
# print(response)

if __name__ == "__main__":
    print("Starting voice assistant. Say 'stop' to exit.")
    while True:
        voice_command = voice_input_tool()
        if voice_command:
            if "stop" in voice_command:
                print("Stopping the assistant. Goodbye!")
                break
            response = agent.run(voice_command)
            print(response)