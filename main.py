import argparse
from glob import glob
from os.path import join, exists, isdir, basename, dirname
from os import listdir, makedirs
from tqdm import tqdm
from config import Config
from shutil import rmtree

from conversion_tools import AudioConverter
from moises_tools import MoisesAPI
from acustic_tools import SilenceRemover
from segment_tools import  AudioSegmenter
from normalization_tools import AudioNormalizer

def execute_pileline(input_dir, output_dir):

    for songs_folder in glob(input_dir + "/**"):
        
        print("> Running pipeline for: " + songs_folder + "...")

        if not isdir(songs_folder):
            continue

        print("--> Extracting vocals and transcriptions... ")
        moises_temp_folder = join(output_dir, Config.temp_folder, 'moises')
        if not (exists(moises_temp_folder)):
            makedirs(moises_temp_folder)

        moises_api = MoisesAPI(Config.moises_id)
        moises_api.process_folder(songs_folder, moises_temp_folder, Config.input_audio_format)

        print("--> Converting audio files to wav... ")
        converted_temp_folder = join(output_dir, Config.temp_folder, 'converted')
        if not (exists(converted_temp_folder)):
            makedirs(converted_temp_folder)

        converter = AudioConverter(
            input_dir=moises_temp_folder, 
            output_dir=converted_temp_folder, 
            input_format=Config.input_audio_format, 
            output_format=Config.output_audio_format,
            target_sr=Config.vad_sample_rate
        )
        converter.convert()
        
        print("--> Removing silence... ")
        vad_temp_folder = join(output_dir, Config.temp_folder, 'vad')
        if not (exists(vad_temp_folder)):
            makedirs(vad_temp_folder)

        silence_remover = SilenceRemover(
            sample_rate=Config.vad_sample_rate, 
            frame_duration_ms=Config.frame_duration_ms, 
            padding_duration_ms=Config.padding_duration_ms, 
            aggressiveness=Config.aggressiveness,
            audio_format=Config.output_audio_format
        )
        silence_remover.proccess_folder(converted_temp_folder, vad_temp_folder, force=True)
                

        print("--> Building target segments... ")
        segments_temp_folder = join(output_dir, Config.temp_folder, 'segments')
        if not (exists(segments_temp_folder)):
            makedirs(segments_temp_folder)     

        audio_segmenter = AudioSegmenter(
            audio_format=Config.output_audio_format,
            sample_rate=Config.sample_rate, 
            min_duration=Config.min_duration, 
            max_duration=Config.max_duration, 
            max_gap_duration=Config.max_gap_duration, 
            threshold_db=Config.threshold_db
        )
        audio_segmenter.build_segments(vad_temp_folder, segments_temp_folder)

        print("--> Normalizing audio files... ")
        audio_normalizer = AudioNormalizer(Config.target_dbfs, Config.output_audio_format)
        audio_normalizer.normalize_files(segments_temp_folder, output_dir)


        temp_dir = join(output_dir, Config.temp_folder)
        if isdir(temp_dir)  and Config.remove_temp_folder:
            rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', default='input', help='Input folder')
    parser.add_argument('-o', '--output', default='output', help='Output folder')
    args = parser.parse_args()

    execute_pileline(args.input, args.output)


if __name__ == "__main__":
    main()
