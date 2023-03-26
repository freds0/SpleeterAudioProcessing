import argparse
import torch
import torchaudio
from os import makedirs
from os.path import join, exists, basename
from tqdm import tqdm
from glob import glob

class AudioConverter:
    def __init__(self, input_dir, output_dir, input_format='flac', output_format='wav', target_sr=24000):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.input_format = input_format
        self.output_format = output_format
        self.target_sr = target_sr
    
    def convert(self):
        for audio_filepath in tqdm(glob(self.input_dir + "/*.{}".format(self.input_format))):
            print(">>> Converting: " + audio_filepath + "...")
            output_filename = basename(audio_filepath).replace('.{}'.format(self.input_format), '.{}'.format(self.output_format))
            output_filepath = join(self.output_dir, output_filename)
            self._convert_file(audio_filepath, output_filepath)
    
    def _convert_file(self, input_filepath, output_filepath):
        waveform, sr = torchaudio.load(input_filepath)
        waveform_mono = torch.mean(waveform, dim=0).unsqueeze(0)

        fn_resample = torchaudio.transforms.Resample(orig_freq=sr, new_freq=self.target_sr, resampling_method='sinc_interp_hann')
        target_waveform = fn_resample(waveform_mono)
        torchaudio.save(output_filepath, target_waveform, self.target_sr, encoding="PCM_S", bits_per_sample=16, format=self.output_format)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert audio files.')
    parser.add_argument('--input', required=True, help='Directory containing input audio files.')
    parser.add_argument('--output', required=True, help='Directory to save output audio files.')
    parser.add_argument('--input_format', default='flac', help='Input audio file format.')
    parser.add_argument('--output_format', default='wav', help='Output audio file format.')
    parser.add_argument('--target_sr', type=int, default=24000, help='Target sample rate.')
    args = parser.parse_args()

    if not exists(args.output):
        makedirs(args.output)

    converter = AudioConverter(args.input, args.output, args.input_format, args.output_format, args.target_sr)
    converter.convert()
