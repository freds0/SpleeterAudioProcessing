#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import argparse
from os.path import join, exists, isdir
from os import listdir, makedirs
from tqdm import tqdm
from config import Config
from shutil import rmtree

from conversion_tools import AudioConverter
from moises_tools import MoisesAPI
from spleeter_tools import SpleeterAPI
from acustic_tools import SilenceRemover
from segment_tools import  AudioSegmenter
from normalization_tools import AudioNormalizer

def moises_api_runner(input_dir, output_dir):
    '''
    Extract vocals and transcriptions from audio files in a folder
    '''
    moises_api = MoisesAPI(
        moises_id=Config.moises_id,
        audio_format=Config.input_audio_format,
        waiting_time=Config.waiting_time,
        verbose=Config.verbose
    )
    moises_api.process_folder(
        input_dir=input_dir, 
        output_dir=output_dir, 
    )


def spleeter_api_runner(input_dir, output_dir):
    '''
    Extract vocals from audio files in a folder
    '''
    spleeter_api = SpleeterAPI(
        audio_format=Config.input_audio_format,
        sample_rate=Config.vad_sample_rate,
        verbose=Config.verbose
    )
    spleeter_api.process_folder(
        input_dir=input_dir,
        output_dir=output_dir
    )


def converter_runner(input_dir, output_dir):
    '''
    Convert audio files in a folder to wav
    '''
    converter = AudioConverter(
        input_format=Config.input_audio_format, 
        output_format=Config.output_audio_format,
        target_sr=Config.vad_sample_rate,
        verbose=Config.verbose
    )
    converter.process_folder(
        input_dir=input_dir, 
        output_dir=output_dir           
    )


def silence_remover_runner(input_dir, output_dir):
    '''
    Remove silence from audio files in a folder
    '''
    silence_remover = SilenceRemover(
        sample_rate=Config.vad_sample_rate,
        frame_duration_ms=Config.frame_duration_ms,
        padding_duration_ms=Config.padding_duration_ms,
        aggressiveness=Config.aggressiveness,
        audio_format=Config.output_audio_format,
        verbose=Config.verbose
    )
    silence_remover.process_folder(
        input_dir=input_dir, 
        output_dir=output_dir           
    )   


def audio_segmenter_runner(input_dir, output_dir):
    segmenter = AudioSegmenter(
        audio_format=Config.output_audio_format,
        sample_rate=Config.vad_sample_rate,
        min_duration=Config.min_duration,
        max_duration=Config.max_duration,
        max_gap_duration=Config.max_gap_duration,
        threshold_db=Config.threshold_db,
        segment_extension=Config.segment_extension,
        frame_length=Config.frame_length,
        hop_length=Config.hop_length,
        verbose=Config.verbose
    )
    segmenter.build_segments(
        input_dir=input_dir, 
        output_dir=output_dir           
    )


def audio_normalizer_runner(input_dir, output_dir):
    '''
    Normalize audio files in a folder
    '''
    normalizer = AudioNormalizer(
        audio_format = Config.output_audio_format,
        target_dbfs = Config.target_dbfs,
        verbose = Config.verbose
    )
    normalizer.normalize_folder(
        input_dir=input_dir, 
        output_dir=output_dir           
    )


def execute_pileline(input_dir, output_dir):

    for songs_folder in tqdm(listdir(input_dir)):
        
        input_folder = join(input_dir, songs_folder)
        output_folder = join(output_dir, songs_folder.replace(' ', '_'))
        temp_folder = join(output_folder, Config.temp_dir)
        
        print("> Running pipeline for: " + input_folder + "...")

        if not isdir(input_folder):
            continue

        print("--> Extracting vocals and transcriptions... ")
        moises_temp_folder = join(temp_folder, 'moises')
        if not (exists(moises_temp_folder)):
            makedirs(moises_temp_folder)
        spleeter_api_runner(input_folder, moises_temp_folder)

        print("--> Converting audio files to wav... ")
        converted_temp_folder = join(temp_folder, 'converted')
        if not (exists(converted_temp_folder)):
            makedirs(converted_temp_folder)
        converter_runner(input_dir=moises_temp_folder, output_dir=converted_temp_folder)
        
        print("--> Removing silence... ")
        vad_temp_folder = join(temp_folder, 'vad')
        if not (exists(vad_temp_folder)):
            makedirs(vad_temp_folder)
        silence_remover_runner(input_dir=converted_temp_folder, output_dir=vad_temp_folder)

        print("--> Building target segments... ")
        segments_temp_folder = join(temp_folder, 'segments')
        if not (exists(segments_temp_folder)):
            makedirs(segments_temp_folder)     
        audio_segmenter_runner(input_dir=converted_temp_folder, output_dir=segments_temp_folder)

        print("--> Normalizing audio files... ")
        audio_normalizer_runner(input_dir=segments_temp_folder, output_dir=output_folder)

        
        if isdir(segments_temp_folder)  and Config.delete_temp:
            rmtree(moises_temp_folder)

        rmtree(converted_temp_folder)
        rmtree(vad_temp_folder)
        rmtree(segments_temp_folder)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', default='input', help='Input folder.')
    parser.add_argument('-o', '--output', default='output', help='Output folder.')
    args = parser.parse_args()

    execute_pileline(args.input, args.output)


if __name__ == "__main__":
    main()
