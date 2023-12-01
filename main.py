from pathlib import Path
from openai import OpenAI
#from playsound import playsound
import openai
import http.client
import json
import os
import pyaudio
import math
import struct
import wave
import time
import pygame

openai.api_key = os.getenv("OPENAI_API_KEY")
Threshold = 30

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
swidth = 2

TIMEOUT_LENGTH = 5

f_name_directory = r'.'


class Recorder:

    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=chunk)

    def record(self):
        print('Noise detected, recording beginning')
        rec = []
        current = time.time()
        end = time.time() + TIMEOUT_LENGTH

        while current <= end:

            data = self.stream.read(chunk)
            if self.rms(data) >= Threshold: end = time.time() + TIMEOUT_LENGTH

            current = time.time()
            rec.append(data)
        self.write(b''.join(rec))
        print('Saved')
        audio_file = open("speech.mp3", "rb")
        client = OpenAI()
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        text = translate(transcript)
        print(text)
        text2speech(text)
        speak()
        print('Returning to listening')

    def write(self, recording):
        filename = os.path.join(f_name_directory, 'speech.mp3')

        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(recording)
        wf.close()
        print('Written to file: {}'.format(filename))




    def listen(self):
        print('Listening beginning')
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)
            if rms_val > Threshold:
                self.record()


def speak():
#  current_dir = os.getcwd()
#  filename = current_dir + "\speech.mp3"
  #filename = "speech.mp3"
  #playsound(filename)
    pygame.mixer.init()
    pygame.mixer.music.load("speech.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        # Check if the music is still playing
        pygame.time.Clock().tick(10)  # Adjust the tick value as needed
    pygame.mixer.quit()

def translate(text):
  conn = http.client.HTTPSConnection("api.openai.com")
  headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + openai.api_key,
  }
  data = {
    "prompt": "Translate the following English text to French: '{" + text + "}'",
    "max_tokens": 60
  }
  data_json = json.dumps(data)
  conn.request("POST", "/v1/engines/text-davinci-003/completions", headers=headers, body=data_json)
  res = conn.getresponse()
  data = res.read()
  response_dict = json.loads(data.decode("utf-8"))
  generated_text = response_dict['choices'][0]['text'].strip()
  return generated_text

def text2speech(text):
  client = OpenAI()
  speech_file_path = Path(__file__).parent / "speech.mp3"
  response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=text
  )
  response.stream_to_file(speech_file_path)

a = Recorder()

a.listen()








