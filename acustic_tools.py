# Source: https://github.com/WeberJulian/TTS-1/blob/multilingual/TTS/bin/remove_silence_using_vad.py
from os.path import basename, exists, join
from tqdm import tqdm
from glob import glob
import argparse
import pathlib
import collections
import contextlib
import wave
import webrtcvad
from itertools import chain


class FrameGenerator(object):
    class Frame(object):
        """Represents a "frame" of audio data."""
        def __init__(self, bytes, timestamp, duration):
            self.bytes = bytes
            self.timestamp = timestamp
            self.duration = duration

            
    def __init__(self, frame_duration_ms, audio, sample_rate):
        self.frame_duration_ms = frame_duration_ms
        self.audio = audio
        self.sample_rate = sample_rate
        
    def __iter__(self):
        n = int(self.sample_rate * (self.frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        duration = (float(n) / self.sample_rate) / 2.0
        while offset + n < len(self.audio):
            yield self.Frame(self.audio[offset:offset + n], timestamp, duration)
            timestamp += duration
            offset += n

class SilenceRemover:
    def __init__(self, sample_rate=32000, frame_duration_ms=30, padding_duration_ms=300, aggressiveness=2, audio_format='wav'):  
        assert sample_rate in (8000, 16000, 32000, 48000)
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.padding_duration_ms = padding_duration_ms
        self.vad = webrtcvad.Vad(aggressiveness)
        self.num_padding_frames = int(padding_duration_ms / frame_duration_ms)
        self.ring_buffer = collections.deque(maxlen=self.num_padding_frames)
        self.triggered = False
        self.voiced_frames = []  
        self.audio_format=audio_format 
        self.frame_generator = FrameGenerator

    def read_wave(self, filepath):
        """Reads a .wav file.
        Returns PCM audio data and sample rate.
        """
        with contextlib.closing(wave.open(filepath, 'rb')) as wf:
            num_channels = wf.getnchannels()
            assert num_channels == 1
            sample_width = wf.getsampwidth()
            assert sample_width == 2
            sample_rate = wf.getframerate()
            assert sample_rate in (8000, 16000, 32000, 48000)
            pcm_data = wf.readframes(wf.getnframes())
            return pcm_data, sample_rate


    def write_wave(self, audio_data, filepath):
        """Writes a .wav file.
        Takes PCM audio data and sample rate.
        """
        with contextlib.closing(wave.open(filepath, 'wb')) as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)


    def vad_collector(self, frames):
        '''
        Filters out non-voiced audio frames. Given a webrtcvad.Vad and a source of audio frames, yields only the voiced audio. Uses a padded, sliding window algorithm over the audio frames.
        When more than 90% of the frames in the window are voiced (as reported by the VAD), the collector triggers and begins yielding
        audio frames. Then the collector waits until 90% of the frames in the window are unvoiced to detrigger.
        The window is padded at the front and back to provide a small amount of silence or the beginnings/endings of speech around the
        voiced frames.
        Arguments:
            sample_rate - The audio sample rate, in Hz.
            frame_duration_ms - The frame duration in milliseconds.
            padding_duration_ms - The amount to pad the window, in milliseconds.
            vad - An instance of webrtcvad.Vad.
        frames - a source of audio frames (sequence or generator).
            Returns: A generator that yields PCM audio data.                
        '''

        num_padding_frames = int(self.padding_duration_ms / self.frame_duration_ms)
        # We use a deque for our sliding window/ring buffer.
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
        # NOTTRIGGERED state.
        triggered = False

        voiced_frames = []
        for frame in frames:
            is_speech = self.vad.is_speech(frame.bytes, self.sample_rate)

            # sys.stdout.write('1' if is_speech else '0')
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                # If we're NOTTRIGGERED and more than 90% of the frames in
                # the ring buffer are voiced frames, then enter the
                # TRIGGERED state.
                if num_voiced > 0.9 * ring_buffer.maxlen:
                    triggered = True
                    # sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))
                    # We want to yield all the audio we see from now until
                    # we are NOTTRIGGERED, but we have to start with the
                    # audio that's already in the ring buffer.
                    for f, s in ring_buffer:
                        voiced_frames.append(f)
                    ring_buffer.clear()
            else:
                # We're in the TRIGGERED state, so collect the audio data
                # and add it to the ring buffer.
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                # If more than 90% of the frames in the ring buffer are
                # unvoiced, then enter NOTTRIGGERED and yield whatever
                # audio we've collected.
                if num_unvoiced > 0.9 * ring_buffer.maxlen:
                    #sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                    triggered = False
                    yield b''.join([f.bytes for f in voiced_frames])
                    ring_buffer.clear()
                    voiced_frames = []
        # If we have any leftover voiced audio when we run out of input,
        # yield it.
        if voiced_frames:
            yield b''.join([f.bytes for f in voiced_frames])


    def proccess_file(self, input_filepath, output_filepath, force=False):

        filename = basename(input_filepath)
        # ignore if the file exists 
        if not force and exists(output_filepath):
            return False
        # create all directory structure
        pathlib.Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
        audio_data, sample_rate = self.read_wave(input_filepath)
        frames = self.frame_generator(self.frame_duration_ms, audio_data, sample_rate)
        frames = list(frames)
        segments = self.vad_collector(frames)
        flag = False
        segments = list(segments)
        num_segments = len(segments)

        if num_segments != 0:
            for i, segment in reversed(list(enumerate(segments))):
                if i >= 1:
                    if flag == False:
                        concat_segment = segment
                        flag = True
                    else:
                        concat_segment = segment + concat_segment
                else:
                    if flag:
                        segment = segment + concat_segment
                    self.write_wave(segment, output_filepath)
                    return True
        else:
            print("> Just Copying the file to:", output_filepath)
            # if fail to remove silence just write the file
            self.write_wave(audio_data, output_filepath)


    def proccess_folder(self, input_dir, output_dir, force=False):

        for input_filepath in tqdm(glob(input_dir + '/*.{}'.format(self.audio_format))):
            filename = basename(input_filepath)
            output_filepath = join(output_dir, filename)
            self.proccess_file(input_filepath, output_filepath, force=False)


if __name__ == "__main__":
    """
    usage
    python remove_silence.py -i=input -o=output -g=/*.wav -a=2 
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default='input',
                        help='Input dir')
    parser.add_argument('-o', '--output', type=str, default='output',
                        help='Output dir')
    parser.add_argument('--audio_format', type=str, default='wav',
                        help='Audio codec. Ex: wav, mp3, flac, etc.')
    parser.add_argument('--sr', type=int, default=32000)    
    parser.add_argument('-a', '--aggressiveness', type=int, default=2,
                        help='set its aggressiveness mode, which is an integer between 0 and 3. 0 is the least aggressive about filtering out non-speech, 3 is the most aggressive.')
    parser.add_argument('-f', '--force', type=bool, default=False,
                        help='Overwrite if the file already exists.')    

    args = parser.parse_args()

    silence_remover = SilenceRemover(
        sample_rate=args.sr, 
        frame_duration_ms=30, 
        padding_duration_ms=300, 
        audio_format=args.audio_format
    )
    silence_remover.proccess_folder(args.input, args.output, args.force)
