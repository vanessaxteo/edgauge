from hume import HumeStreamClient, HumeClientException
from hume.models.config import FaceConfig
import openai
from terminal_gpt import get_completion, get_completion_fast
import numpy as np
import threading
import asyncio
import cv2
import time
import traceback
import websockets
import copy
from pynput import keyboard

# Configurations
OPENAI_API_KEY = "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"
HUME_API_KEY = "T46iFimyuk6sPJqfdWz3thRyo3U3y5RbfH1H5T16FETzF5va"
HUME_FACE_FPS = 1 / 2  # 2 FPS
TEMP_FILE = 'temp.jpg'
THRESHOLD = 0.6
# Webcam setup
cam = cv2.VideoCapture(0)

# Input your lesson plan here!
planned_subjects = ["Left-Leaning Red Black Trees", "Dijkstra's Algorithm", "Prim's Algorithm", "Kruskal's Algorithm", "Shortest path on a graph"]


EMOTIONS = np.array([
    'Admiration', 'Adoration', 'Aesthetic Appreciation', 'Amusement', 'Anger', 'Annoyance', 'Anxiety', 'Awe', 
    'Awkwardness', 'Boredom', 'Calmness', 'Concentration', 'Contemplation', 'Confusion', 'Contemplation', 'Contempt', 
    'Contentment', 'Craving', 'Desire', 'Determination', 'Disappointment', 'Disapproval', 'Disgust', 'Distress', 'Doubt', 
    'Ecstasy', 'Embarrassment', 'Empathic Pain', 'Enthusiasm', 'Entrancement', 'Envy', 'Excitement', 'Fear', 'Gratitude', 'Guilt',
    'Horror', 'Interest', 'Joy', 'Love', 'Nostalgia', 'Pain', 'Pride', 'Realization', 'Relief', 'Romance', 'Sadness', 
    'Satisfaction', 'Shame', 'Surprise (negative)', 'Surprise (positive)', 'Sympathy', 'Tiredness', 'Triumph'
])
NEGATIVE_EMOTIONS = np.array([
    'Boredom', 'Confusion', 'Distress', 'Disappointment', 'Disgust', 'Horror', 'Sadness', 'Shame', 'Tiredness'
])
prompt = "In this moment, I am a teacher, "

emotional_response_to_subjects = {}
cumulative_Hume_data = {}
for emotions in EMOTIONS:
    cumulative_Hume_data[emotions] = 0
zerod_dictionary = copy.deepcopy(cumulative_Hume_data)
num_iter = 0
next_subject = False
end_loop = False
test_prompting = False
global option
option = ""
awaiting_option = False
responses = ""

async def webcam_loop():
    global planned_subjects, cumulative_Hume_data, emotional_response_to_subjects, num_iter
    global THRESHOLD, prompt, next_subject, end_loop, test_prompting, option, awaiting_option, responses
    while len(planned_subjects) != 0:
        try:
            client = HumeStreamClient(HUME_API_KEY)
            config = FaceConfig(identify_faces=True)
            async with client.connect([config]) as socket:
                print("(Connected to Hume API!)")
                while True:
                    if len(planned_subjects) == 0:
                        break
                    _, frame = cam.read()
                    cv2.imwrite(TEMP_FILE, frame)
                    result = await socket.send_file(TEMP_FILE)
                    Hume_data = copy.deepcopy(zerod_dictionary)
                    do_nothing = False
                    try:
                        processed_result = result['face']['predictions'][0]['emotions']
                        for emotion in processed_result:
                            Hume_data[emotion['name']] = emotion['score']
                            cumulative_Hume_data[emotion['name']] += emotion['score']
                        num_iter += 1
                    except:
                        do_nothing = True
                    #print(num_iter)
                    threshold_exceeded = False
                    for emotion in NEGATIVE_EMOTIONS:
                        if not do_nothing and Hume_data[emotion] > THRESHOLD:
                            prompt += f"and {round(Hume_data[emotion] * 100, 2)}% of my students are experiencing the emotion of {emotion}, "
                            threshold_exceeded = True

                    if (threshold_exceeded or test_prompting) and (not awaiting_option):
                        if test_prompting:
                            print(Hume_data['Boredom'] * 100)
                            prompt += f"and {round(Hume_data['Boredom'] * 100, 2)}% of my students are experiencing the emotion of Boredom, "
                        test_prompting = False
                        threshold_exceeded = False
                        prompt_part_2 = f"while I am teaching {planned_subjects[0]} right now. Can you give me advice to make my students feel like they should pay attention more and engage them more in the next 2 minutes? What other teaching methods can I use to immediately improve classroom engagement in this topic? Please list 4 multiple choice options with examples and breakdowns of the examples in 5 bullet points"
                        prompt += prompt_part_2
                        
                        print("prompt1: ", prompt)
                        prompt_response = get_completion_fast(prompt, OPENAI_API_KEY=OPENAI_API_KEY)
                        await asyncio.sleep(1 / 3)
                        print("prompt_response", prompt_response)
                        responses += prompt_response
                        prompt = "In this moment, I am a teacher, "
                        awaiting_option = True
                    
                    if option == "x":
                        awaiting_option = False
                        option = ""
                    if awaiting_option and option in ["a", "b", "c", "d"]:
                        option_selection_prompt = f"""
                        given the options: {responses} Let us say that I want to use option {option}.
                        give me an example of this idea and thoroughly explain the 4 steps for me to execute
                        this idea surrounding {planned_subjects[0]} using one bullet point per step to take to show my students this example within 5 minutes.
                        """
                        print("prompt2:", option_selection_prompt)
                        option_selection_response = get_completion_fast(option_selection_prompt, OPENAI_API_KEY=OPENAI_API_KEY)
                        await asyncio.sleep(1 / 3)
                        print("option_selection_response", option_selection_response)
                        responses = option_selection_response
                        option = ""

                    if next_subject:
                        next_subject = False
                        awaiting_option = False
                        option = ""
                        responses = ""
                        cumulative_Hume_data["num_iter"] = num_iter
                        cumulative_Hume_data["subject"] = planned_subjects[0]
                        emotional_response_to_subjects[planned_subjects[0]] = cumulative_Hume_data
                        print(f"just finished {planned_subjects[0]}")
                        print("")
                        planned_subjects = planned_subjects[1:]
                        await asyncio.sleep(1 / 3)
                        if num_iter > 0:
                            for key, value in cumulative_Hume_data.items():
                                if key in NEGATIVE_EMOTIONS:
                                    print(f"{key}: {value / num_iter}")
                        else:
                            for key, value in zerod_dictionary.items():
                                if key in NEGATIVE_EMOTIONS:
                                    print(f"{key}: {value}")
                        cumulative_Hume_data = copy.deepcopy(zerod_dictionary)
                        num_iter = 0
                    if end_loop:
                        print("caught end")
                        cumulative_Hume_data["num_iter"] = num_iter
                        cumulative_Hume_data["subject"] = planned_subjects[0]
                        emotional_response_to_subjects[planned_subjects[0]] = cumulative_Hume_data
                        planned_subjects = []
                        if num_iter > 0:
                            for key, value in cumulative_Hume_data.items():
                                if key in NEGATIVE_EMOTIONS:
                                    print(f"{key}: {value / num_iter}")
                        else:
                            for key, value in zerod_dictionary.items():
                                if key in NEGATIVE_EMOTIONS:
                                    print(f"{key}: {value}")
                        cumulative_Hume_data = copy.deepcopy(zerod_dictionary)
                        num_iter = 0
                        break
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

def on_press(key):
    global option
    if key == keyboard.Key.right or key == keyboard.Key.space:
        global next_subject
        next_subject = True
    #if key ==  keyboard.Key.left: SCRAPPING THE IDEA OF GOING BACK TO PREVIOUS TOPIC.
        #previous_subject = True
    if key == keyboard.KeyCode.from_char("1") or key == keyboard.KeyCode.from_char("a"):
        option = "a"
        print(option)
    if key == keyboard.KeyCode.from_char("2") or key == keyboard.KeyCode.from_char("b"):
        option = "b"
        print(option)
    if key == keyboard.KeyCode.from_char("3") or key == keyboard.KeyCode.from_char("c"):
        option = "c"
        print(option)
    if key == keyboard.KeyCode.from_char("4") or key == keyboard.KeyCode.from_char("d"):
        option = "d"
        print(option)
    if key == keyboard.KeyCode.from_char("x"):
        option = "x"
        print(option)
    if key == keyboard.Key.esc or key == keyboard.Key.backspace:
        print("escape worked")
        global end_loop
        end_loop = True
    if key == keyboard.KeyCode.from_char("t"):
        global test_prompting
        test_prompting = True

new_loop = asyncio.new_event_loop()

threading.Thread(target=start_asyncio_event_loop, args=(new_loop, webcam_loop())).start()

with keyboard.Listener(on_press=on_press) as listener:
    print("Press right arrow or space to advance to the next subject")
    print("Press 1 / a, 2 / b, 3 / c, or 4 / d in order to select an option when prompted")
    listener.join()
