#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import argparse
from glob import glob
from os.path import join, exists, basename
from os import makedirs
from tqdm import tqdm
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter

class SpleeterAPI:
    def __init__(self, audio_format='wav', sample_rate=24000, verbose=1):
        self.audio_format = audio_format
        self.sample_rate = sample_rate
        # Using embedded configuration.
        self.separator = Separator('spleeter:2stems')
        self.audio_adapter = AudioAdapter.default()
        self.verbose = verbose
    
    def process_folder(self, input_dir, output_dir):
        for input_filepath in tqdm(glob(input_dir + "/*.{}".format(self.audio_format))):
            if self.verbose: print("----> Converting file {}".format(basename(input_filepath)))
            output_filename = basename(input_filepath).replace('.{}'.format(self.audio_format), '.{}'.format(self.audio_format))
            output_filepath = join(output_dir, output_filename)
            self._convert_file(input_filepath, output_filepath)
    
    def _convert_file(self, input_filepath, output_filepath):
        waveform, _ = self.audio_adapter.load(input_filepath, sample_rate=self.sample_rate)

        # Perform the separation :
        prediction = self.separator.separate(waveform)
        # Save the prediction :
        self.audio_adapter.save(output_filepath, prediction['vocals'], self.sample_rate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert audio files.')
    parser.add_argument('-i', '--input', default='input', help='Input folder.')
    parser.add_argument('-o', '--output', default='output', help='Output folder.')
    parser.add_argument('--audio_format', default='wav', help='Input audio format.')
    parser.add_argument('--sample_rate', type=int, default=24000, help='Sample rate.')
    parser.add_argument('--verbose', default=1, help="Verbosity level: 0 or 1.")    
    args = parser.parse_args()

    if not exists(args.output):
        makedirs(args.output)

    converter = SpleeterAPI(
        audio_format = args.audio_format,
        sample_rate = args.sample_rate,
        verbose=args.verbose
    )
    converter.process_folder(args.input, args.output)
