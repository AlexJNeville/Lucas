import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]



def add_event(service, summary, description, start_time, end_time):
    """
    Adds an event to the primary calendar.
    start_time and end_time should be in ISO format: 'YYYY-MM-DDTHH:MM:SSZ'
    """
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC', # Adjust to your timezone, e.g., 'America/New_York'
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except HttpError as error:
        print(f"An error occurred: {error}")






def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:



    # ... inside your try block ...
    service = build("calendar", "v3", credentials=creds)

    # Example: Create an event for tomorrow at 10:00 AM
    # Format: YYYY-MM-DDTHH:MM:SS
    start = "2026-04-05T10:00:00Z" 
    end = "2026-04-05T11:00:00Z"
    
    add_event(service, "Coffee with Gemini", "Discussing Python scripts", start, end)
  except:
    print("nah")

if __name__ == "__main__":
    
  main()
