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

    print("Checking sound file server...")
    message, code = init_request()
    print(message)
    if code != 200:
        print("Try again later.")
        return
    
    stats = SyllableStats(syllables=SYLLABLES, variants=VARIANTS, interactions_path=args.interactions_path)
    fetch_new = True
    while True:
        if fetch_new:
            current_target, variant = stats.get_rnd_syllable(1, advanced=args.worst_100_only, non_sampled_boost=args.non_sampled_boost)
            current_target, variant = current_target[0], variant[0]
            mf, voice = variant.split('V')
            current_audio_segment = get_syllable(current_target, variant)
            if current_audio_segment is None:
                continue
            play_audio(current_audio_segment)
            fetch_new = False
        
        current_written = input().strip().lower()
        
        skip = False
        if current_written == 'exit':
            print('  exiting.')
            break

        elif current_written == 'give up' or current_written == 'giveup':
            print(f'  Solution was: {current_target}.')
            play_audio(current_audio_segment)
            sleep(0.3)
            correct = 2
            fetch_new = True

        elif current_written == 'break':
            skip = True
            play_audio(current_audio_segment)

        elif current_written == '':
            print('  repeating syllable ... 🔊.')
            play_audio(current_audio_segment)
            correct = 0

        elif current_written != current_target:
            if current_written in stats.possible_syllables:
                print('  wrong, that would be ... 🔊')
                current_written_audio_segment = get_syllable(current_written, variant)
                play_audio(current_written_audio_segment)
                sleep(0.3)
                print('  but it is the following instead ... 🔊')
            else:
                print('  syllable does not exists.')
            play_audio(current_audio_segment)
            correct = 0

        elif current_written == current_target:
            print('  correct.')
            correct = 1
            fetch_new = True
        
        else:
            print('  something unexpected happend.')

        if not skip:
            record_interaction(args.interactions_path, current_target, current_written, correct, get_time(), mf, voice)
            stats.update_stats(current_target, current_written, correct)

if __name__ == '__main__':
    run()