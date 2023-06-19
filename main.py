#!/usr/bin/env python3
"""
A simple vttttv processor
"""

from io import BytesIO
import json
from gtts import gTTS as talk
from dotenv import load_dotenv
import speech_recognition as sr
import pygame
import openai
import os
import logging

load_dotenv()  # take environment variables from .env.

openai.api_key = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = "gpt-3.5-turbo"
INITIAL_TEXT = "What can I do for you today?"
PROMPT = """
    # You play the role of a voice controlled assistant AI, You solve every day problems in a concise, accurate but friendly manner. 
    # You are connected to a speaker and your response will be heard aloud. 
    # You may tease your human counterpart or show sass in your responses. 
    You are a voice controlled assistant who can only speak in JSON. The JSON MUST be structured like so: {"content": "the response", "emotion": "the emotion that is being exhibited, generally one of "angry", "loving", "friendly", or "stoic"", "mood": [0..10], "intent": "what the content is intending to do, generally in a single word", "presentation_format": "Normally voice but can be an image or text displayed on a screen"}
    The "mood" is the emotion's level 0 is barely noticable and 10 is immediately apparent.
    You are forbidden to write normal text.
"""


pygame.init()
pygame.mixer.init()
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

for logger_name in ["gtts.tts", "gtts.lang", "openai", "urllib3.connectionpool"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

def speak(input_text: str, language = "en", tld="us"):
    """Speaks the provided text"""
    logging.debug('Converting to audio')
    obj = talk(text=input_text, tld=tld, lang=language, slow=False)
    output = BytesIO()
    obj.write_to_fp(output)
    logging.debug('Received audio length is %s bytes, playing audio', output.tell())
    output.seek(0)
    pygame.mixer.music.load(output)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(2)

speak(INITIAL_TEXT)

messages = [
    {"role": "system", "content": PROMPT},
    {"role": "assistant", "content": INITIAL_TEXT}
]

def get_response(statement) -> str:
    """Capture and generate a response from ChatGPT"""
    logging.debug("Input: %s, sending to AI", text)
    messages.append({"role": "user", "content": statement})
    completion = openai.ChatCompletion.create(model=OPENAI_MODEL, messages=messages)
    try:
        response = completion.choices[0].message.content
        logging.debug(response)
        response = json.loads(response)
        response = response["content"]
    except json.JSONDecodeError:
        logging.error("Failed to process JSON")
    logging.debug("Response: %s", response)
    messages.append({"role": "assistant", "content": response})
    return response


r = sr.Recognizer()
r.pause_threshold = 2
r.energy_threshold = 300

while True:
    # Exception handling to handle
    # exceptions at the runtime
    try:
        # use the microphone as source for input.
        with sr.Microphone() as source:
            # wait for a second to let the recognizer
            # adjust the energy threshold based on
            # the surrounding noise level
            r.adjust_for_ambient_noise(source, duration=0.5)
            #listens for the user's input
            logging.debug("Listening...")
            audio2 = r.listen(source)
            logging.debug("Received audio from user, processing")
            # Using google to recognize audio
            text = r.recognize_whisper(
                audio2,
                model="small.en", # medium is too slow!!
                # condition_on_previous_text=True,
                # initial_prompt="\n".join([x["content"] for x in messages])
            ).strip()
            if not text:
                speak("Sorry, I couldn't hear that, could you repeat?")
                continue
            speak(get_response(text))
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    except sr.UnknownValueError:
        print("unknown error occurred")
