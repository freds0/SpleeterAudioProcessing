class Config:
    # audio format settings
    input_audio_format = 'flac'
    output_audio_format = 'wav'

    # conversion settings
    temp_folder = 'tmp'
    sample_rate = 24000

    # remove silence settings
    aggressiveness = 2

    # moises settings
    moises_id = ""
    
    # segments settings
    min_duration = 10
    max_duration = 20
    max_gap_duration = 3
    threshold_db = 28

    # VAD settings
    frame_duration_ms = 30
    padding_duration_ms = 300
    aggressiveness = 2
    vad_sample_rate = 32000

    # normalization settings
    target_dbfs = -25

    # Pipeline settings
    remove_temp_folder = True
