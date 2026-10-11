#import pyaudio   #import for pyaudio
import speech_recognition as sr    #import for speech recogogogo
import google.genai as genai
from google.genai import types                          #gemini install (for generations)
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
import os
import sys
import subprocess
from playsound3 import playsound
from datetime import datetime



###### calendar ####

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError







SCOPES = ["https://www.googleapis.com/auth/calendar"]



#calendar token check

creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    print("here")
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

service = build("calendar", "v3", credentials=creds)






def add_event(service,summary, description, start_time, end_time):
    """
    Adds an event to the primary calendar.
    start_time and end_time should be in ISO format: 'YYYY-MM-DDTHH:MM:SS'
    """
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'Europe/London', # Adjust to your timezone, e.g., 'America/New_York'
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Europe/London',
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")
    except HttpError as error:
        print(f"An error occurred: {error}")






#### end calenrdar ####



#conversation mode#


def conversation(active):
    print("Conversation mode : Active, you dont need to say lucas anymore")
    while active:
        print("Conversation mode : Active, you dont need to say lucas anymore")
        try:
            prompt = str(input("-->"))


            response = chat.send_message(prompt)
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                if function_call.name == 'add_event':
                    add_event(service,**function_call.args)
                    print("Added event, check your calendar!")
                elif function_call.name == 'conversation':
                    active = function_call.args['active']
                elif function_call.name == 'web_search':
                    web_search(**function_call.args)
            else:
                print(response.text)
        except:
            print("Unable to process request")
 


### duck duck go search ###
from ddgs import DDGS

def web_search(query,number_of_searches):
    """Searches the web for real-time information, news, and research."""
    print("Searching... this may take a second")
    with DDGS() as ddgs:
        search_results = [r for r in ddgs.text(query, max_results=number_of_searches)]
        formatted_results = ""
        for x in range(0,len(search_results)):
            formatted_results += search_results[x]['body']


    return formatted_results



##whatsapp###

###whatsapp ###

import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- CONFIGURATION ---
SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=[r"C:\Users\alexn\whatsapp-mcp\whatsapp-mcp-server\main.py"],
    env=None
)




async def find_chat_jid(session, target_name):
    """
    Scans active chats and handles the specific string-list format 
    returned by your WhatsApp MCP server.
    """
    print(f"Scanning active chats for '{target_name}'...")
    
    chats_resp = await session.call_tool("list_chats", arguments={"limit": 100})
    
    if not chats_resp.content:
        print("No chat history found.")
        return None

    for content_item in chats_resp.content:
        try:
            # Your server sends back data in blocks. We check each block.
            # We try to load the text as JSON.
            data = json.loads(content_item.text)
            
            # If the server returned a list of chats at once:
            if isinstance(data, list):
                for chat in data:
                    name = chat.get("name") or ""
                    if target_name.lower() in name.lower():
                        jid = chat.get("jid") or chat.get("id")
                        print(f"Match Found: '{name}' [ID: {jid}]")
                        return jid
            
            # If the server returned a single chat object (as seen in your snippet):
            elif isinstance(data, dict):
                name = data.get("name") or ""
                if target_name.lower() in name.lower():
                    # Your snippet uses "jid", so we prioritize that
                    jid = data.get("jid") or data.get("id")
                    print(f"✅ Match Found: '{name}' [ID: {jid}]")
                    return jid

        except Exception:
            # If it's not JSON, we skip this block and keep looking
            continue
            
    return None

async def lookup(target_name, number_of_messages):
    print("1")
    async with stdio_client(SERVER_PARAMS) as (read, write):
        print("2")
        async with ClientSession(read, write) as session:
            print("3")
            await session.initialize()
            response = (chat.send_message(target_name+contact)).text
            print("4")
            print(response)
                
            # 1. Locate the Chat ID
            jid = await find_chat_jid(session, response)
            
            if not jid:
                print(f"❌ Could not find a chat named '{target_name}'.")
                return

            # 2. Fetch the messages
            try:
                # Using the JID we just found
                messages = await session.call_tool(
                    "list_messages", 
                    arguments={"chat_jid": jid, "limit": number_of_messages}
                )
                
                print(f"\n--- LAST {number_of_messages} MESSAGES IN '{target_name}' ---")
                
                if not messages.content:
                    print("No messages found.")
                    return
                completed_message = ""
                for msg in messages.content:
                    completed_message +=f"{msg.text}"
                return completed_message
                    
            except Exception as e:
                print(f"❌ Error fetching messages: {e}")


message_prompt =""" This prompt is going to have 3 parts. The first part is this instructionary preamble. Listen to it exactly. The Second part will be a
message, the third part will be chat logs from me. I want you to construct a message based on the message I sent in the second part, making it sound like
me, based on the chat logs from me. The chat logs will be contained in brackets so you can distinguish between log and message. Your output, I want no
preamble, no summary text, either. I just want your output to be the message you construct, influenced by the instructionary message in the second part,
reformed to sound like me
"""



                
async def send_message(target_name,message):
    print("1")
    print(target_name)
    async with stdio_client(SERVER_PARAMS) as (read, write):
        print("2")
        async with ClientSession(read, write) as session:
            print("3")
            await session.initialize()
            print("4")
            # 1. Locate the Chat ID
            with open('my_messages.txt', 'r', encoding='utf-8') as file:
                content = file.read()
                print("File Read")
            response = (chat.send_message(target_name+contact)).text
            print(response)
            jid = await find_chat_jid(session, response)
            
            
            if not jid:
                print(f"❌ Could not find a chat named '{target_name}'.")
                return
            response = (chat.send_message(f"{message_prompt} ,{message} , ({content})")).text
            # 2. Fetch the messages
            try:
                # Using the JID we just found
                result = await session.call_tool(
                    "send_message", 
                    arguments={
                        "recipient": jid,
                        "message": response
                    }
                )
                print(f"Message sent! Server response: {result.content[0].text}")
                return "Completed"
                    
            except Exception as e:
                print(f"❌ Error fetching messages: {e}")
                return "Error"
#whatsapp contact reference

with open(os.path.join(os.path.dirname(__file__), "contacts.txt"), "r", encoding="utf-8") as _f:
    contact = _f.read()  # personal contact list -- loaded from contacts.txt (gitignored)















### gemini tools ###

whatsapp_messages = {
    "name":"lookup",
    "description": "Looks up the last n messages from a specified person or group on whatsapp.",
    "parameters":{
        "type": "object",
        "properties":{
            "target_name":{
                "type":"string",
                "description":"The name of the person",
            },
            "number_of_messages":{
                "type":"integer",
                "description":"""The number of messages in the past to search for""",
            },
        },
        "required":["target_name","number_of_messages"]
    },
}


send_message_ = {
    "name":"send_message",
    "description":"sends a message to a person specified on whatsapp, using the whatsapp mcp server connected",
    "parameters":{
        "type": "object",
        "properties":{
            "target_name":{
                "type":"string",
                "description":"The name of the person",
            },
            "message":{
                "type":"string",
                "description":"The instruction for a later input into you on what the message sent must say",
            },
        },
        "required":["target_name","message"]
    },
}




online_web_search = {
    "name":"web_search",
    "description": "Searches the internet for an answer to the users question online, if it involves real data, which you can't look up yourself. Trigger at mentions of research or thinking or 'look at ...'",
    "parameters":{
        "type": "object",
        "properties":{
            "query":{
                "type":"string",
                "description":"Write a google search prompt in order to fetch data for the user on the recieving end.",
            },
            "number_of_searches":{
                "type":"integer",
                "description":"""Write a number of searches to search up the results needed. The higher number the more thorough and accurate the search will be
but it will take longer subsequently. Never go below 10, and never exceed 50 searches for the user"""
            },
        },
        "required":["query","number_of_searches"]
    },
}
                




add_event_function = {
    "name": "add_event",
    "description": "Adds an event to google calendar",
    "parameters": {
        "type": "object",
        "properties":{
            "summary":{
                "type": "string",
                "description":"Write a short summary within 5 words of the activity being added",
            },
            "description":{
                "type":"string",
                "description":"Write a longer summary of the task, include more information",
            },
            "start_time":{
                "type":"string",
                "description":"Put the start time and date, in the ISO format:: 'YYYY-MM-DDTHH:MM:SS, if no start time, or end time is given, list the  start time as 12:00:00 on the day specified'",
            },
            "end_time":{
                "type":"string",
                "description":"Put the end time and date, in the ISO format:: 'YYYY-MM-DDTHH:MM:SS. If no end time is given, just list it as the start time + 2 hours.'",
            },
        },
        "required":["summary","description","start_time","end_time"]
    },
}


conversation_mode = {
    "name": "conversation",
    "description":"""starts a seperate conversation
mode for quicker assistance in brainstorming, planning,
or anything with many responses, can use this function to turn it on or off.
To activate user must say both 'conversation' and 'active' or 'activate' and 'mode' in
any order.""",
    "parameters": {
        "type":"object",
        "properties":{
            "active":{
                "type": "boolean",
                "description":"True to activate conversation mode, false to deactivate it",
            },
        },
        "required":["active"]
    },
}















with open('api_keys.txt', 'r', encoding='utf-8') as file:
    line = file.readline()




api_key_gemini = line #api key for gem (secret)
client = genai.Client(api_key=api_key_gemini)
tools = types.Tool(function_declarations=[add_event_function,conversation_mode,online_web_search,whatsapp_messages,send_message_])

current_date = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

system_instruction=f"""You are a helpful AI assistant like Alexa named Lucas. Give short, direct answers.

Use British English units (Celsius, 24-hour time). 
IMPORTANT: Today's date and time is {current_date}. Use this to resolve relative dates like 'tomorrow'.
Be funny, creative and witty, to bring light into the situation. You can search online using the search tool given to you.
Always feel free to be critical and honest, and ask follow up questions. Be decisive and give answers when requested. For example
if the user says, "choose a restaurant" you pick the resturant. For context the user lives in Malvern, Worcestershire, England, use for
context in location 'e.g nearby...' If a task requires a tool (like searching the web or adding a calendar event),
you must call that tool before confirming the action to the user. Do not pretend to perform actions.

IMPORTANT:
You are being translated into text to speech so anything other than ?,!. Will be translated aswell. For example never use * as that will get
translated. Only ever speak in plain text, so I can turn it into speech"""


config = types.GenerateContentConfig(tools=[tools],system_instruction=system_instruction)
chat = client.chats.create(model="gemini-2.5-flash", config=config)
    

while True:
    try:
        print("Type in 'lucas' to use me!")
        wake = input(" -->")
        if wake.lower() == "lucas":
            print("\nHow can I help you")
            prompt = str(input("-->"))

            response = (chat.send_message(prompt))
            
            while response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                if function_call.name == 'add_event':
                    add_event(service,**function_call.args)
                    print("Added event, check your calendar!")
                    response = chat.send_message("I have added the event to the calendar. What's next?")
                elif function_call.name == 'conversation':
                    print("Starting conversation mode...")
                    conversation(**function_call.args)
                    print("Conversation mode ending...")
                    break
                elif function_call.name == 'web_search':
                    response = web_search(**function_call.args)
                elif function_call.name == 'lookup':
                    print("aqui")

                    response = asyncio.run(lookup(**function_call.args))
                elif function_call.name == 'send_message':
                    asyncio.run(send_message(**function_call.args))
                    response = "Sent message"
                response = (chat.send_message(response + "If you are planning to call another function, do it straight away, with this prompt"))
            else:
                print(response.text)

    except Exception as e:
        print(f"Actual error: {e}")  
                
            
