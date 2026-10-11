import pyaudio   #import for pyaudio
import speech_recognition as sr    #import for speech recogogogo
import google.genai as genai   #gemini install (for generations)
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
import os
import sys
import subprocess
from playsound3 import playsound



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


import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build




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
                
                
                full_text = ""
                sentence_buffer = ""
                print(command)
                # Stream from Gemini and buffer complete sentences for smoother audio
                for chunk in client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=prereq + command
                ):
                    if chunk.text:
                        full_text += chunk.text
                        sentence_buffer += chunk.text
                        
                        # Check if we have a complete sentence or paragraph
                        #           if any(punct in sentence_buffer for punct in ['. ', '! ', '? ', '\n']):
                        if len(sentence_buffer.split()) >= 5:
                            # Stream the complete sentence for smoother audio
                            audio_stream = client_eleven.text_to_speech.stream(
                                text=sentence_buffer.strip(),
                                voice_id="CwhRBWXzGAHq8TQ4Fs17",
                                model_id="eleven_turbo_v2"
                            )
                            stream(audio_stream)
                            sentence_buffer = "" 
                
                # Stream any remaining text that didn't end with punctuation
                if sentence_buffer.strip():
                    audio_stream = client_eleven.text_to_speech.stream(
                        text=sentence_buffer.strip(),
                        voice_id="CwhRBWXzGAHq8TQ4Fs17",
                        model_id="eleven_multilingual_v2"
                    )
                    stream(audio_stream)                        

                #response.text is the response from gemini


                

    except sr.UnknownValueError:
        print("Sorry, could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")

