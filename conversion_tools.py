import argparse
import torch
import torchaudio
from os import makedirs
from os.path import join, exists, basename
from tqdm import tqdm
from glob import glob

class AudioConverter:
    def __init__(self, input_format='flac', output_format='wav', target_sr=24000, verbose=1):
        self.input_format = input_format
        self.output_format = output_format
        self.target_sr = target_sr
        self.verbose = verbose
    
    def process_folder(self, input_dir, output_dir):
        for input_filepath in tqdm(glob(input_dir + "/*.{}".format(self.input_format))):
            if self.verbose: print("----> Converting file {}".format(basename(input_filepath)))
            output_filename = basename(input_filepath).replace('.{}'.format(self.input_format), '.{}'.format(self.output_format))
            output_filepath = join(output_dir, output_filename)
            self._convert_file(input_filepath, output_filepath)
    
    def _convert_file(self, input_filepath, output_filepath):
        waveform, sr = torchaudio.load(input_filepath)
        waveform_mono = torch.mean(waveform, dim=0).unsqueeze(0)

        fn_resample = torchaudio.transforms.Resample(orig_freq=sr, new_freq=self.target_sr, resampling_method='sinc_interp_hann')
        target_waveform = fn_resample(waveform_mono)
        torchaudio.save(output_filepath, target_waveform, self.target_sr, encoding="PCM_S", bits_per_sample=16, format=self.output_format)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert audio files.')
    parser.add_argument('-i', '--input', default='input', help='Input folder.')
    parser.add_argument('-o', '--output', default='output', help='Output folder.')
    parser.add_argument('--input_format', default='flac', help='Input audio format.')
    parser.add_argument('--output_format', default='wav', help='Output audio format.')
    parser.add_argument('--target_sr', type=int, default=24000, help='Target sample rate.')
    parser.add_argument('--verbose', default=1, help="Verbosity level: 0 or 1.")    
    args = parser.parse_args()

    if not exists(args.output):
        makedirs(args.output)

    converter = AudioConverter(
        input_format = args.input_format,
        output_format = args.output_format,
        target_sr = args.target_sr,
        verbose=args.verbose
    )
    converter.process_folder(args.input, args.output)
