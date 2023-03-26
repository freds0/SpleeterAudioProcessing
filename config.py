class Config:
    # audio format settings
    input_audio_format = 'flac'
    output_audio_format = 'wav'

    # conversion settings
    sample_rate = 24000

    # remove silence settings
    aggressiveness = 2

    # moises settings
    moises_id = ""
    waiting_time = 5
    
    # segments settings
    min_duration = 10
    max_duration = 20
    max_gap_duration = 3
    segment_extension = 0.2
    threshold_db = 28
    frame_length = 1024
    hop_length = 256    

    # VAD settings
    frame_duration_ms = 30
    padding_duration_ms = 300
    aggressiveness = 2
    vad_sample_rate = 32000

    # normalization settings
    target_dbfs = -25

    # Pipeline settings
    temp_dir = 'tmp'
    delete_temp = False
    verbose = 2
