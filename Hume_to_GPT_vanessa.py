import hume
import openai
import numpy as np
import re
from colorama import Fore, Style
import threading
import asyncio
import os
import cv2
import time
import traceback
import websockets

from pynput import keyboard
from pvrecorder import PvRecorder
from whispercpp import Whisper
from chat import message, store_emotions
from playsound import playsound
from hume import HumeStreamClient, HumeClientException
from hume.models.config import FaceConfig
from gtts import gTTS


# Configurations
openai.api_key = ""
HUME_API_KEY = "wpcWMr5ejrfR0ztQyDhdMhsLaNaBIrL5FoUlTiLva3zgkEXU"
HUME_FACE_FPS = 1 / 3  # 3 FPS

TEMP_FILE = 'temp.jpg'
TEMP_WAV_FILE = 'temp.wav'

THRESHOLD = 0.6

# Initialize whisper model, pyttsx3 engine, and pv recorder
w = Whisper.from_pretrained("tiny.en")
recorder = PvRecorder(device_index=-1, frame_length=512)

# Global variables
recording = False
recording_data = []
prompt1 = "while I am teaching {planned_subjects[0]} right now. \
             Can you give me advice to make my students feel like they should \
             pay attention more and engage them more in the next 2 minutes? \
             What other teaching methods can I use to immediately improve classroom \
             engagement in this topic? Please list 4 multiple choice options."

# Webcam setup
cam = cv2.VideoCapture(0)


EMOTIONS = np.array([
    'Admiration', 'Adoration', 'Aesthetic Appreciation', 'Amusement', 'Anger', 'Anxiety', 'Awe', 
    'Awkwardness', 'Boredom', 'Calmness', 'Concentration', 'Contemplation', 'Confusion', 'Contempt', 
    'Contentment', 'Craving', 'Determination', 'Disappointment', 'Disgust', 'Horror', 'Interest', 
    'Joy', 'Love', 'Nostalgia', 'Pain', 'Pride', 'Realization', 'Relief', 'Romance', 'Sadness', 'Satisfaction', 
    'Desire', 'Shame', 'Surprise (negative)', 'Surprise (positive)', 'Sympathy', 'Tiredness', 'Triumph'
])
NEGATIVE_EMOTIONS = np.array([
    'Boredom', 'Confusion', 'Disappointment', 'Disgust', 'Horror', 'Sadness', 'Shame', 'Tiredness'
])
#TODO: add support for student vs teacher mode
prompt = "In this moment, I am a teacher,"

#TODO: add support for easy addition of subject, perhaps feeding a slide deck to gpt and having it summarize it
planned_subjects = ["Dijkstra's Algorithm", "Prim's Algorithm", "Kruskal's Algorithm", "Shortest path on a graph"]
# keyboard_input = input('Please enter "n" to progress to the next subject, \
#                        or "a", "b", "c", or "d" to select an option when prompted')

emotional_response_to_subjects = {}
cumulative_Hume_data = {}
for emotions in EMOTIONS:
    cumulative_Hume_data[emotions] = 0
num_iter = 0

async def webcam_loop():
    global planned_subjects, cumulative_Hume_data, emotional_response_to_subjects, num_iter, THRESHOLD, prompt
    while len(planned_subjects) != 0: #might want to add a wait clause
        try:
            client = HumeStreamClient(HUME_API_KEY)
            config = FaceConfig(identify_faces=True)
            async with client.connect([config]) as socket:
                print("(Connected to Hume API!)")
                while True:
                    if not recording:
                        _, frame = cam.read()
                        cv2.imwrite(TEMP_FILE, frame)
                        result = await socket.send_file(TEMP_FILE)
                        print(result)
                        #while len(planned_subjects) != 0: #might want to add a wait clause
                        print(f"current subject is {planned_subjects[0]}")
                        #TODO: check Hume emotions
                        emotion = "bored"
                        percent = 0.65
                        Hume_data = {emotion: percent}
                        result['face']['predictions'][0]['emotions']
                        for key, value in Hume_data.items():
                            try:
                                cumulative_Hume_data[key] += value
                                num_iter += 1
                            except Exception:
                                cumulative_Hume_data[key] = value
                                num_iter +=1
                        
                        for emotion in NEGATIVE_EMOTIONS:
                            threshold_exceeded = False
                            if Hume_data[emotion] > THRESHOLD:
                                prompt += f"and {percent * 100}% of my students are {emotion},"
                                threshold_exceeded = True
                                
                        if threshold_exceeded:
                            prompt += "while I am teaching {planned_subjects[0]} right now. \
                                Can you give me advice to make my students feel like they should \
                                pay attention more and engage them more in the next 2 minutes? \
                                What other teaching methods can I use to immediately improve classroom \
                                engagement in this topic? Please list 4 multiple choice options with examples and breakdowns of the examples in 5 bullet points"
                            response = "example text"
                            #TODO: OpenAI API call, send prompt
                            #TODO: Display buttons, need 4 buttons + timer + escape option
                            #TODO: allow button interaction --> generate new ideas
                        keyboard_input = "n" 
                        if keyboard_input == "n":
                            #print(planned_subjects[0])
                            #print(cumulative_Hume_data)
                            cumulative_Hume_data["num_iter"] = num_iter
                            emotional_response_to_subjects[planned_subjects[0]] = cumulative_Hume_data
                            #TODO: Store emotional_response_to_subjects
                            planned_subjects = planned_subjects[1:]
                            cumulative_Hume_data = {}
                            await asyncio.sleep(1 / 3)
        except websockets.exceptions.ConnectionClosedError:
            print("Connection lost. Attempting to reconnect in 1 seconds.")
            time.sleep(1)
        except HumeClientException:
            print(traceback.format_exc())
            break
        except Exception:
            print(traceback.format_exc())


def start_asyncio_event_loop(loop, asyncio_function):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(asyncio_function)

def recording_loop():
    global recording_data, recording
    while recording:
        frame = recorder.read()
        recording_data.append(frame)

    recorder.stop()
    print("(Recording stopped...)")

    recording_data = np.hstack(recording_data).astype(np.int16).flatten().astype(np.float32) / 32768.0
    transcription = w.transcribe(recording_data)
    response = message(transcription)
    tts = gTTS(text=response, lang='en')
    tts.save(TEMP_WAV_FILE)
    playsound(TEMP_WAV_FILE)
    os.remove(TEMP_WAV_FILE)

def on_press(key):
    global recording, recording_data, recorder
    if key == keyboard.Key.space:
        if recording:
            recording = False
        else:
            recording = True
            recording_data = []
            recorder.start()
            print("(Recording started...)")
            threading.Thread(target=recording_loop).start()

new_loop = asyncio.new_event_loop()

threading.Thread(target=start_asyncio_event_loop, args=(new_loop, webcam_loop())).start()

with keyboard.Listener(on_press=on_press) as listener:
    print("Speak to Joaquin!")
    print("(Press spacebar to speak. To finish speaking, press spacebar again)")
    listener.join()

    # while len(planned_subjects) != 0: #might want to add a wait clause
#     print(f"current subject is {planned_subjects[0]}")
#     #TODO: check Hume emotions
#     emotion = "bored"
#     percent = 0.65
#     Hume_data = {emotion: percent}
    
#     for key, value in Hume_data.items():
#         try:
#             cumulative_Hume_data[key] += value
#             num_iter += 1
#         except Exception:
#             cumulative_Hume_data[key] = value
#             num_iter +=1
    
#     for emotion in NEGATIVE_EMOTIONS:
#         threshold_exceeded = False
#         if Hume_data[emotion] > THRESHOLD:
#             prompt += f"and {percent * 100}% of my students are {emotion},"
#             threshold_exceeded = True
            
#     if threshold_exceeded:
#         prompt += "while I am teaching {planned_subjects[0]} right now. \
#             Can you give me advice to make my students feel like they should \
#             pay attention more and engage them more in the next 2 minutes? \
#             What other teaching methods can I use to immediately improve classroom \
#             engagement in this topic? Please list 4 multiple choice options."
#         response = "example text"
#         #TODO: OpenAI API call, send prompt
#         #TODO: Display buttons, need 4 buttons + timer + escape option
#         #TODO: allow button interaction --> generate new ideas

#     if keyboard_input == "n":
#         print(planned_subjects[0])
#         print(cumulative_Hume_data)
#         cumulative_Hume_data["num_iter"] = num_iter
#         emotional_response_to_subjects[planned_subjects[0]] = cumulative_Hume_data
#         #TODO: Store emotional_response_to_subjects
#         planned_subjects = planned_subjects[1:]
#         cumulative_Hume_data = {}

{'face': 
 {'predictions':[
      {'frame': 0, 
       'time': None, 
       'bbox': {'x': 573.3207397460938, 'y': 133.79055786132812, 'w': 345.2607421875, 'h': 462.9244079589844}, 
       'prob': 0.9999077320098877, 
       'face_id': '0', 
       'emotions': [
           {'name': 'Admiration', 'score': 0.12929004430770874}, 
           {'name': 'Adoration', 'score': 0.1693800687789917}, 
           {'name': 'Aesthetic Appreciation', 'score': 0.07234063744544983}, 
           {'name': 'Amusement', 'score': 0.30553102493286133}, 
           {'name': 'Anger', 'score': 0.028918087482452393}, 
           {'name': 'Anxiety', 'score': 0.1758086085319519}, 
           {'name': 'Awe', 'score': 0.07308340072631836}, 
           {'name': 'Awkwardness', 'score': 0.21045222878456116}, 
           {'name': 'Boredom', 'score': 0.2906133532524109}, 
           {'name': 'Calmness', 'score': 0.36906856298446655}, 
           {'name': 'Concentration', 'score': 0.2673038840293884}, 
           {'name': 'Contemplation', 'score': 0.16162244975566864}, 
           {'name': 'Confusion', 'score': 0.22738023102283478}, 
           {'name': 'Contempt', 'score': 0.07895644754171371}, 
           {'name': 'Contentment', 'score': 0.21148957312107086}, 
           {'name': 'Craving', 'score': 0.049950286746025085}, 
           {'name': 'Determination', 'score': 0.05880940333008766}, 
           {'name': 'Disappointment', 'score': 0.2668962776660919}, 
           {'name': 'Disgust', 'score': 0.05269285663962364}, 
           {'name': 'Distress', 'score': 0.24539561569690704}, 
           {'name': 'Doubt', 'score': 0.17646366357803345}, 
           {'name': 'Ecstasy', 'score': 0.07516681402921677}, 
           {'name': 'Embarrassment', 'score': 0.21434852480888367}, 
           {'name': 'Empathic Pain', 'score': 0.10106328874826431}, 
           {'name': 'Entrancement', 'score': 0.11452777683734894}, 
           {'name': 'Envy', 'score': 0.02844512090086937}, 
           {'name': 'Excitement', 'score': 0.13788136839866638}, 
           {'name': 'Fear', 'score': 0.08543292433023453}, 
           {'name': 'Guilt', 'score': 0.12718112766742706}, 
           {'name': 'Horror', 'score': 0.035674482583999634}, 
           {'name': 'Interest', 'score': 0.27523553371429443}, 
           {'name': 'Joy', 'score': 0.28825369477272034}, 
           {'name': 'Love', 'score': 0.31841906905174255}, 
           {'name': 'Nostalgia', 'score': 0.09779185801744461}, 
           {'name': 'Pain', 'score': 0.19082464277744293}, 
           {'name': 'Pride', 'score': 0.0632292702794075}, 
           {'name': 'Realization', 'score': 0.16011226177215576}, 
           {'name': 'Relief', 'score': 0.15509483218193054}, 
           {'name': 'Romance', 'score': 0.12925462424755096}, 
           {'name': 'Sadness', 'score': 0.2801573574542999}, 
           {'name': 'Satisfaction', 'score': 0.2536880075931549}, 
           {'name': 'Desire', 'score': 0.09516432881355286}, 
           {'name': 'Shame', 'score': 0.1488841474056244}, 
           {'name': 'Surprise (negative)', 'score': 0.03798443451523781}, 
           {'name': 'Surprise (positive)', 'score': 0.03677542135119438}, 
           {'name': 'Sympathy', 'score': 0.08205775171518326}, 
           {'name': 'Tiredness', 'score': 0.3124815821647644}, 
           {'name': 'Triumph', 'score': 0.03641732782125473}
        ]
      }
    ]
 }
}