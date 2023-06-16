#!/usr/bin/env python3
"""
A simple vttttv processor
"""

from io import BytesIO
from gtts import gTTS as talk
from dotenv import load_dotenv
import speech_recognition as sr
import pygame
import openai
import os
import logging

load_dotenv()  # take environment variables from .env.

openai.api_key = os.getenv("OPENAI_API_KEY")

initial_text = "Hello! How are you?"

pygame.init()
pygame.mixer.init()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

def speak(input_text: str, language = "en", tld="us"):
    """Speaks the provided text"""
    logging.debug('Received text length %s', len(input_text))
    obj = talk(text=input_text, tld=tld, lang=language, slow=False)
    output = BytesIO()
    obj.write_to_fp(output)
    logging.debug('Received audio length is %s bytes, playing audio', output.tell())
    output.seek(0)
    pygame.mixer.music.load(output)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    logging.debug('Completed audio')

speak(initial_text)

r = sr.Recognizer()
r.pause_threshold = 2

messages = [{"role": "assistant", "content": initial_text}]

while True:
    # Exception handling to handle
    # exceptions at the runtime
    try:
        # use the microphone as source for input.
        with sr.Microphone() as source2:
            # wait for a second to let the recognizer
            # adjust the energy threshold based on
            # the surrounding noise level
            r.adjust_for_ambient_noise(source2, duration=0.5)
            #listens for the user's input
            logging.debug("Listening...")
            audio2 = r.listen(source2)
            logging.debug("Received audio from user, processing")
            # Using google to recognize audio
            text = r.recognize_google(audio2)
            logging.debug("VTT %s, sending to ChatGPT", text)
            messages.append({"role": "user", "content": text})
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
            response = completion.choices[0].message.content
            messages.append({"role": "assistant", "content": response})
            speak(response)
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    except sr.UnknownValueError:
        print("unknown error occurred")
