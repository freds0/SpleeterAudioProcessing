#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import argparse
from os.path import exists, join, basename
from os import makedirs
from tqdm import tqdm
import numpy as np
from pydub import AudioSegment
from glob import glob


class AudioNormalizer:
    def __init__(self, target_dbfs=False, audio_format= 'wav', verbose=0):
        self.audio_format = audio_format
        self.target_dbfs = target_dbfs
        self.verbose = verbose

    def __calculate_mean_dbfs(self, input_dir):
        dbfs_list = []
        for input_filepath in tqdm(glob(input_dir + '/*.{}'.format(self.audio_format))):
            dbfs_list.append(AudioSegment.from_file(input_filepath).dBFS)

        target_dbfs = np.array(dbfs_list).mean()
        return target_dbfs
    

    def normalize_folder(self, input_dir, output_dir):
        if not self.target_dbfs:
            if self.verbose: print("----> Calculating average dBFS from files at: {}".format(input_dir))
            self.target_dbfs = self.__calculate_mean_dbfs(input_dir)

        for input_filepath in tqdm(glob(input_dir + '/*.{}'.format(self.audio_format))):
            if self.verbose: print("----> Normalizing file {}".format(basename(input_filepath)))
            filename = basename(input_filepath)
            output_filepath = join(output_dir, filename)
            audio = AudioSegment.from_file(input_filepath)
            change_in_dBFS = self.target_dbfs - audio.dBFS
            normalized_sound = audio.apply_gain(change_in_dBFS)
            normalized_sound.export(output_filepath, format=self.audio_format)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input folder.')
    parser.add_argument('-o', '--output', required=True, help='Output folder.')
    parser.add_argument('--audio_format', default='wav', help="Audio format: wav, flac, mp3, etc.")
    parser.add_argument('--dbfs_target', default=False, help="Sugestion: -25.0")
    parser.add_argument('--verbose', default=1, help="Verbosity level: 0 or 1.")
    args = parser.parse_args()

    if not exists(args.output):
        makedirs(args.output)

    audio_normalizer = AudioNormalizer(args.dbfs_target, args.audio_format, args.verbose)
    audio_normalizer.normalize_folder(args.input, args.output)


if __name__ == "__main__":
    main()
