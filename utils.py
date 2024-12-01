import os
import sys
import csv
import requests
from pydub import AudioSegment
from io import BytesIO
from datetime import datetime
from pydub.playback import play

params = {
    'key': '4QZ4D8ufYnwWF&t1eJ#ar9X#$avrsa&$jKh8erfZrsSjT#A2qvzpRLwSRBtm',
    'version': '0.0'
}

def record_interaction(interactions_path, target, written, correctness, time, mf, voice):
    # Check if the file exists
    file_exists = os.path.isfile(interactions_path)
    
    # Open the file in append mode
    with open(interactions_path, 'a', newline='') as csvfile:
        fieldnames = ['target', 'written', 'correctness', 'time', 'mf', 'voice']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # If the file doesn't exist, write the header
        if not file_exists:
            writer.writeheader()
        
        # Write the row
        writer.writerow({'target': target, 'written': written, 'correctness': correctness, 
                         'time': time, 'mf': mf, 'voice': voice})

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def init_request():
    response = requests.get("https://lukasuz.uber.space/tones/init", params=params)
    data = response.json()
    message = data['message']
    code = response.status_code

    return message, code

def get_syllable(syllable, variant):
    url = "https://lukasuz.uber.space/tones/files/" + syllable + "_" + variant + "_MP3.mp3"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        audio_segment = AudioSegment.from_file(BytesIO(response.content), format="mp3")
    else:
        print("Failed to download the file:", response.status_code, response.text)
        return None

    return audio_segment

def suppress_stdout_stderr():
    null_fds = [os.open(os.devnull, os.O_RDWR) for _ in range(2)]
    save_fds = (os.dup(1), os.dup(2))
    os.dup2(null_fds[0], 1)
    os.dup2(null_fds[1], 2)
    return save_fds, null_fds

def restore_stdout_stderr(save_fds, null_fds):
    os.dup2(save_fds[0], 1)
    os.dup2(save_fds[1], 2)
    os.close(null_fds[0])
    os.close(null_fds[1])

def play_audio(audio_segment):
    save_fds, null_fds = suppress_stdout_stderr()
    play(audio_segment)
    restore_stdout_stderr(save_fds, null_fds)