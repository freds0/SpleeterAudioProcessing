#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Source https://gist.github.com/keithito/771cfc1a1ab69d1957914e377e65b6bd
#
from glob import glob
import argparse
from os import makedirs
from os.path import isdir, dirname, join, basename
from collections import OrderedDict
import librosa
import numpy as np
import sys
from scipy.io.wavfile import write

class Segment:
    '''
    Linked segments lists
    '''
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.next = None
        self.gap = 0 # gap between segments (current and next)

    def set_next(self, next):
        self.next = next
        self.gap = next.start - self.end

    def set_filename_and_id(self, filename, id):
        self.filename = filename
        self.id = id

    def merge_from(self, next):
        # merge two segments (current and next)
        self.next = next.next
        self.gap = next.gap
        self.end = next.end

    def duration(self, sample_rate):
        return (self.end - self.start - 1) / sample_rate


class AudioSegmenter:
    def __init__(self, audio_format='wav', sample_rate=24000, min_duration=5, max_duration=15, max_gap_duration=0.5, threshold_db=28, segment_extension=0.2, frame_length=1024, hop_length=256, verbose=1):
        self.audio_format = audio_format
        self.sample_rate = sample_rate
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.max_gap_duration = max_gap_duration
        self.threshold_db = threshold_db
        self.end_of_file_extension = segment_extension
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.verbose = verbose
        self.output_filename = False
        self.output_filename_id = 1


    def __segment_wav(self, wav):
        '''
        Segment audio file and return a segment linked list
        '''
        # Find gaps at a fine resolution:
        parts = librosa.effects.split(wav, top_db=self.threshold_db)

        # Build up a linked list of segments:
        head = None
        for start, end in parts:
            segment = Segment(start, end)
            if head is None:
                head = segment
            else:
                prev.set_next(segment)
            prev = segment
        return head


    def __find_best_merge(self, segments):
        '''
        Find small segments that can be merged by analyzing max_duration and max_gap_duration
        '''
        best = None
        best_score = 0
        s = segments
        while s.next is not None:
            gap_duration = s.gap / self.sample_rate
            merged_duration = (s.next.end - s.start) / self.sample_rate
            if gap_duration <= self.max_gap_duration and merged_duration <= self.max_duration:
                score = self.max_gap_duration - gap_duration
                if score > best_score:
                    best = s
                    best_score = score
            s = s.next
        return best


    def __find_segments(self, filename, wav):
        '''
        Given an audio file, creates the best possible segment list
        '''
        # Segment audio file
        segments = self.__segment_wav(wav)
        # Merge until we can't merge any more
        while True:
            best = self.__find_best_merge(segments)
            if best is None:
                break
            best.merge_from(best.next)

        # Convert to list
        result = []
        s = segments
        while s is not None:
            result.append(s)
            # Create a errors file
            if (s.duration(self.sample_rate) < self.min_duration and
                    s.duration(self.sample_rate) > self.max_duration):
                    with open(join(dirname(__file__), "errors.txt"), "a") as f:
                            f.write(filename+"\n")

            # Extend the end by 0.2 sec as we sometimes lose the ends of words ending in unvoiced sounds.
            s.end += int(self.end_of_file_extension * self.sample_rate)
            s = s.next

        return result


    def __load_filenames(self, input_dir):
        '''
        Given an folder, creates a wav file alphabetical order dict
        '''
        mappings = OrderedDict()
        for filepath in glob(join(input_dir + "/*.{}".format(self.audio_format))):
            filename = basename(filepath).replace('.{}'.format(self.audio_format), '')
            mappings[filename] = filepath
        return mappings


    def build_segments(self, input_dir, output_dir):
        '''
        Build best segments of wav files
        '''
        # Creates destination folder
        if not isdir(output_dir):
            makedirs(output_dir)
        # Initializes variables
        segment_max_duration, mean_duration = 0, 0
        all_segments = []
        total_duration = 0
        filenames = self.__load_filenames(input_dir)
        if len(filenames) == 0:
            if self.verbose: print('------> No files found in %s' % input_dir)
            return False
        
        for i, (filename, input_filepath) in enumerate(filenames.items()):
            if self.verbose: print('------> Loading %s: %s (%d of %d)' % (filename, input_filepath, i+1, len(filenames)))

            # Load audio
            audio_data, sample_rate = librosa.load(input_filepath, sr=self.sample_rate)
            if self.verbose > 1: print('------> Loaded %.1f min of audio. Splitting...' % (len(audio_data) / self.sample_rate / 60))

            # Find best segments
            segments = self.__find_segments(input_filepath, audio_data)
            duration = sum((s.duration(self.sample_rate) for s in segments))
            total_duration += duration

            # Create records for the segments
            j = int(self.output_filename_id)
            for s in segments:
                all_segments.append(s)
                s.set_filename_and_id(input_filepath, '%s-%04d' % (filename, j))
                j = j + 1

            if self.verbose > 1: print('------> Segmented into %d parts (%.1f min, %.2f sec avg)' % (
                len(segments), duration / 60, duration / len(segments)))

            # Write segments to disk:
            for s in segments:
                segment_wav = (audio_data[s.start:s.end] * 32767).astype(np.int16)
                out_path = join(output_dir, '%s.wav' % s.id)
                #librosa.output.write_wav(out_path, segment_wav, sample_rate)
                write(out_path, self.sample_rate, segment_wav)

                duration += len(segment_wav) / self.sample_rate
                duration_segment = len(segment_wav) / self.sample_rate
                if duration_segment > segment_max_duration:
                    segment_max_duration = duration_segment

                mean_duration = mean_duration + duration_segment
            if self.verbose > 1: print('------> Wrote %d segment wav files' % len(segments))
            if self.verbose > 1: print('------> Progress: %d segments, %.2f hours, %.2f sec avg' % (
                len(all_segments), total_duration / 3600, total_duration / len(all_segments)))

        if self.verbose: print('------> Writing metadata for %d segments (%.2f hours)' % (len(all_segments), total_duration / 3600))
        with open(join(output_dir, 'segments.csv'), 'w') as f:
            for s in all_segments:
                f.write('%s|%s|%d|%d\n' % (s.id, s.filename, s.start, s.end))
        if self.verbose > 1: print('------> Mean: %f' %( mean_duration / len(segments) ))
        if self.verbose > 1: print('------> Max: %d' %(segment_max_duration ))
        return True


def main():
    parser = argparse.ArgumentParser("Segments audio files into silent chunks")
    parser.add_argument('-i', '--input', default='input', help='Input folder.')
    parser.add_argument('-o', '--output', default='output', help='Output folder.')
    parser.add_argument('--audio_format', type=str, default='wav', help='Audio format: wav, mp3, flac, etc.')    
    parser.add_argument('--min_duration', type=float, default=3.0, help='In seconds')
    parser.add_argument('--max_duration', type=float, default=15.0, help='In seconds')
    parser.add_argument('--max_gap_duration', type=float, default=3.0, help='In seconds')
    parser.add_argument('--sample_rate', type=int, default=24000, help='Sampling rate')
    parser.add_argument('--output_filename', type=str, default=False, help='')
    parser.add_argument('--output_filename_id', type=int, default=1, help='Sequencial number used for id filename.')
    parser.add_argument('--threshold_db', type=float, default=28.0, help='The threshold (in decibels) below reference to consider as silence')
    parser.add_argument('--verbose', default=1, help="Verbosity level: 0, 1 or 2.")
    args = parser.parse_args()


    audio_segmenter = AudioSegmenter(
        audio_format=args.audio_format,
        sample_rate=args.sample_rate, 
        min_duration=args.min_duration, 
        max_duration=args.max_duration, 
        max_gap_duration=args.max_gap_duration, 
        threshold_db=args.threshold_db,
        verbose=args.verbose
    )

    audio_segmenter.build_segments(args.input, args.output)


if __name__ == "__main__":
    main()
