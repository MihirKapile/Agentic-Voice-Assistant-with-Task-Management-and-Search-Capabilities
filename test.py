from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# Define the scope for the Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Initialize the flow using the client secrets JSON
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json', SCOPES)

# Run the local server to get the user's authorization
creds = flow.run_local_server(port=0)

# Save the credentials to a file for future use
with open('credentials.json', 'w') as token_file:
    token_file.write(creds.to_json())

# Test API call (optional)
service = build('calendar', 'v3', credentials=creds)
calendars = service.calendarList().list().execute()
print(calendars)
