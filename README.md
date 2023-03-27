# Audio Processing with Spleeter API

This python script executes an audio processing pipeline to extract and normalize audio segments from songs.

The script consists of several audio processing steps including:

- Extraction of vocals using the Spleeter API
- Conversion of audio files to the wav format
- Silence removal
- Building of target audio segments
- Normalization of audio files

The pipeline is executed for each music folder within the specified input directory. The specified output directory will contain the normalized files for each music.

## Dependencies

This script requires the following libraries:

- torch==2.0.0
- torchaudio==2.0.1
- webrtcvad==2.0.10
- pydub==0.25.1
- librosa==0.8.0
- tqdm==4.65.0
- spleeter==2.3.2

## Install 

I recommend using a virtual conda environment:

```bash
$ conda create -n audio_processing python=3.9 pip
$ conda activate audio_processing
```

To install dependencies, run the command:

```bash
$ sudo apt-get update; sudo apt-get install ffmpeg
```
And install the requirements:

```bash
$ pip install -r requirements.txt
```

## How to use

To execute the audio processing pipeline, run the following command:

```bash
$ python main.py --input=input_folder --output=output_folder
```

## Settings

The config.py file contains the default settings for the audio processing pipeline and can be modified to customize the script's behavior.

```bash
    # audio format settings
    input_audio_format = 'mp3'
    output_audio_format = 'wav'

    # conversion settings
    temp_folder = 'tmp'
    sample_rate = 24000

    # remove silence settings
    aggressiveness = 2
    
    # segments settings
    min_duration = 10
    max_duration = 20
    max_gap_duration = 3
    threshold_db = 28

    # VAD settings
    frame_duration_ms = 30
    padding_duration_ms = 300
    aggressiveness = 2
    vad_sample_rate = 32000 # vad_sample_rate > sample rate in [8000, 16000, 32000, 48000]

    # normalization settings
    target_dbfs = -25

    # Pipeline settings
    remove_temp_folder = True
```

## Notes

This script was written in Python 3.9 and has been tested on Ubuntu 20.04.
