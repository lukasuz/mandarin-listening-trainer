import os
import sys
import csv
import requests
from pydub import AudioSegment
from io import BytesIO
from datetime import datetime
from pydub.playback import play
import time
import threading
import itertools

class DownloadException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class CLIWriter:
    indent = '  '
    clean_prev = False
    loading = False
    loading_thread = None
    @staticmethod
    def print(text, indent=False, clean=False):    
        if CLIWriter.loading:
            CLIWriter.stop_loading_animation()
    
        if CLIWriter.clean_prev:
            CLIWriter._clean()

        if indent:
            text = CLIWriter.indent + text

        CLIWriter.clean_prev = clean
        print(text)

    @staticmethod
    def _clean():
        sys.stdout.write('\033[F')
        sys.stdout.write('\033[K')
        
    @staticmethod
    def animate():
        for c in itertools.cycle(['|', '/', '-', '\\']):
            if not CLIWriter.loading:
                break
            sys.stdout.write('\rFetching data ' + c)
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\n')
        sys.stdout.flush()
        CLIWriter._clean()

    @staticmethod
    def start_loading_animation():
        CLIWriter.loading_thread = threading.Thread(target=CLIWriter.animate)
        CLIWriter.loading_thread.daemon = True
        CLIWriter.loading = True
        CLIWriter.loading_thread.start()
    
    @staticmethod
    def stop_loading_animation():
        CLIWriter.loading = False
        CLIWriter.loading_thread.join(0.1)
        CLIWriter.loading_thread = None

class Request():
    params = {
        'key': '4QZ4D8ufYnwWF&t1eJ#ar9X#$avrsa&$jKh8erfZrsSjT#A2qvzpRLwSRBtm',
        'version': '0.0'
    }
    prev_time = None
    client_limit = 3

    def set_initial_time():
        Request.prev_time = time.time()

    def check_time():
        if Request.prev_time is None:
            return
        current_time = time.time()
        time_sime_last_request = current_time - Request.prev_time
        if time_sime_last_request < Request.client_limit:
            waiting_time = Request.client_limit - time_sime_last_request
            time.sleep(waiting_time)
        Request.prev_time = time.time()

    def init_request():
        CLIWriter.start_loading_animation()
        Request.check_time()
        response = requests.get("https://lukasuz.uber.space/tones/init", params=Request.params)
        CLIWriter.stop_loading_animation()
        data = response.json()
        message = data['message']
        code = response.status_code

        return message, code

    def get_syllable(syllable, variant):
        url = "https://lukasuz.uber.space/tones/files/" + syllable + "_" + variant + "_MP3.mp3"
        CLIWriter.start_loading_animation()
        Request.check_time()
        response = requests.get(url, params=Request.params)
        CLIWriter.stop_loading_animation()

        if response.status_code == 200:
            audio_segment = AudioSegment.from_file(BytesIO(response.content), format="mp3")
        else:
            CLIWriter.print(f"Failed to download the file, try again later.\nCode: {response.status_code}\nResponse: {response.text}")
            raise DownloadException('Failed download.')

        return audio_segment


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
    CLIWriter.print('Playing audio ... 🔊')
    save_fds, null_fds = suppress_stdout_stderr()
    play(audio_segment)
    restore_stdout_stderr(save_fds, null_fds)