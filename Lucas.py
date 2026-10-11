import pyaudio   #import for pyaudio
import speech_recognition as sr    #import for speech recogogogo
import google.genai as genai   #gemini install (for generations)
from google.genai import types
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
import os
import sys
import subprocess
import asyncio
import json
from playsound3 import playsound
from ddgs import DDGS
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client



# 1. Define the path clearly
mpv_path = r'C:\mpv-sdk'

# 2. Add it to the Windows DLL search (for Python 3.10)
if os.path.exists(mpv_path):
    os.add_dll_directory(mpv_path)
    
    # 3. Add it to the System PATH (this is what the 'mpv' library is looking for)
    # This satisfies the "raise OSError" check in the library's code
    os.environ['PATH'] = mpv_path + os.pathsep + os.environ['PATH']
else:
    print(f"Error: {mpv_path} not found!")

# 4. NOW import mpv
try:
    import mpv
    player = mpv.MPV()
except Exception as e:
    print(f"Library import failed: {e}")


from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError




prereq = """You are a helpful AI assistant like Alexa. Give short, direct, useful answers.
Be concise, your responses will be played out loud, so keep it in a format which is readable, so basic formatting, no punctutation other than !?.,
without preamble or footers. Use British English units (mph, Celsius)
. Speak naturally for text-to-speech, use base text. Search for real-time data when needed."""    #cheeky prerequesite for the AI assistant. It ensures it wont be like **** ---- diddy ---****


with open(os.path.join(os.path.dirname(__file__), "api_keys.txt"), "r", encoding="utf-8") as _f:
    _api_keys = [line.strip() for line in _f.readlines()]
api_key_gemini = _api_keys[0]  # api key for gem (secret) -- loaded from api_keys.txt (gitignored)
api_key_eleven = _api_keys[1]  # eleven labs api key -- loaded from api_keys.txt (gitignored)


client_eleven = ElevenLabs(api_key=api_key_eleven)
client = genai.Client(api_key=api_key_gemini)

# Generate and play the test audio


# Create a recognizer instance
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
#recognizer_instance.energy_threshold = 100
recognizer.dynamic_energy_adjustment_ratio = 1.3
# Example: Recognize speech from microphone


SCOPES = ["https://www.googleapis.com/auth/calendar"]

creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    print("here")
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

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
            'timeZone': 'Europe/London',
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


def web_search(query,number_of_searches):
    """Searches the web for real-time information, news, and research."""
    print("Searching... this may take a second")
    with DDGS() as ddgs:
        search_results = [r for r in ddgs.text(query, max_results=number_of_searches)]
        formatted_results = ""
        for x in range(0,len(search_results)):
            formatted_results += search_results[x]['body']


    return formatted_results


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
            data = json.loads(content_item.text)
            
            if isinstance(data, list):
                for chat in data:
                    name = chat.get("name") or ""
                    if target_name.lower() in name.lower():
                        jid = chat.get("jid") or chat.get("id")
                        print(f"Match Found: '{name}' [ID: {jid}]")
                        return jid
            
            elif isinstance(data, dict):
                name = data.get("name") or ""
                if target_name.lower() in name.lower():
                    jid = data.get("jid") or data.get("id")
                    print(f"✅ Match Found: '{name}' [ID: {jid}]")
                    return jid

        except Exception:
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
                
            jid = await find_chat_jid(session, response)
            
            if not jid:
                print(f"❌ Could not find a chat named '{target_name}'.")
                return

            try:
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
            try:
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

with open(os.path.join(os.path.dirname(__file__), "contacts.txt"), "r", encoding="utf-8") as _f:
    contact = _f.read()  # personal contact list -- loaded from contacts.txt (gitignored)


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


sound = playsound(r"C:\Users\alexn\Coding\Lucas\Snap Finger Echo Sound Effect.mp3", block=False)
while True: #creating a loop for recognising speech
    try: #simple try except loop
        with sr.Microphone() as source: #using default microphone (((set as connected microphone into speaker eventually")))
            print("Say something...")
            audio = recognizer.listen(source, phrase_time_limit = 2)
            text = recognizer.recognize_google(audio)
            if text.lower() == "lucas":  #wake word
                print("Yes")
        
                command = recognizer.recognize_google(recognizer.listen(source,phrase_time_limit = None))
                
                
                print(command)

                response = (chat.send_message(command))

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
                    audio_stream = client_eleven.text_to_speech.stream(
                        text=response.text.strip(),
                        voice_id="CwhRBWXzGAHq8TQ4Fs17",
                        model_id="eleven_turbo_v2"
                    )
                    stream(audio_stream)

                #response.text is the response from gemini


                

    except sr.UnknownValueError:
        print("Sorry, could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    except Exception as e:
        print(f"Actual error: {e}")
