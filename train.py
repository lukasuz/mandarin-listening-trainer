import os
from time import sleep
from stats import SyllableStats
import argparse
from utils import *
from data import *

def run():
    parser = argparse.ArgumentParser(description="Mandarin listening trainer.")
    parser.add_argument('--non_sampled_boost', type=float, default=0.25, help='Additive boosting scalar for not-yet sampled syllables.')
    parser.add_argument('--interactions_path', type=str, default='interactions.csv', help='Path to interactions.csv.')
    parser.add_argument('--worst_100_only', action='store_true', help='Strictly sample from the 100 syllables with the worst performance.')
    args = parser.parse_args()

    if not os.path.exists(args.interactions_path):
        with open(args.interactions_path, 'w'): pass
    
    CLIWriter.print("Checking sound file server.")
    CLIWriter.print("Do not forget that you need an active internet connection.")
    message, code = Request.init_request()
    CLIWriter.print(message)
    if code != 200:
        CLIWriter.print("Try again later.")
        return
    
    stats = SyllableStats(syllables=SYLLABLES, variants=VARIANTS, interactions_path=args.interactions_path)
    fetch_new = True
    while True:
        if fetch_new:
            current_target, variant = stats.get_rnd_syllable(1, advanced=args.worst_100_only, non_sampled_boost=args.non_sampled_boost)
            current_target, variant = current_target[0], variant[0]
            mf, voice = variant.split('V')
            try:
                current_audio_segment = Request.get_syllable(current_target, variant)
                Request.set_initial_time()
            except DownloadException:
                sys.exit()
            play_audio(current_audio_segment)
            fetch_new = False
        
        current_written = input().strip().lower()
        
        skip = False
        if current_written == 'exit':
            CLIWriter.print('exiting.', indent=True)
            break

        elif current_written == 'give up' or current_written == 'giveup':
            CLIWriter.print(f'Solution was: {current_target}.', indent=True)
            play_audio(current_audio_segment)
            sleep(0.3)
            correct = 2
            fetch_new = True

        elif current_written == 'break':
            skip = True
            play_audio(current_audio_segment)

        elif current_written == '':
            CLIWriter.print('repeating syllable ... 🔊.', indent=True)
            play_audio(current_audio_segment)
            correct = 0

        elif current_written != current_target:
            if current_written in stats.possible_syllables:
                CLIWriter.print('wrong, that would be ... 🔊', indent=True)
                current_written_audio_segment = Request.get_syllable(current_written, variant)
                play_audio(current_written_audio_segment)
                sleep(0.3)
                CLIWriter.print('but it is the following instead ... 🔊', indent=True)
            else:
                CLIWriter.print('syllable does not exists.', indent=True)
            play_audio(current_audio_segment)
            correct = 0

        elif current_written == current_target:
            CLIWriter.print('correct.', indent=True)
            correct = 1
            fetch_new = True
        
        else:
            CLIWriter.print('something unexpected happend.', indent=True)

        if not skip:
            record_interaction(args.interactions_path, current_target, current_written, correct, get_time(), mf, voice)
            stats.update_stats(current_target, current_written, correct)

if __name__ == '__main__':
    run()