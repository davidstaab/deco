import pathlib
import signal
from time import sleep

import yaml

APP_CONFIG = {}

def load_config(file: pathlib.Path) -> None:
    global APP_CONFIG
    
    if isinstance(file, str):
        file = pathlib.Path(file)
    
    APP_CONFIG = yaml.safe_load(file.read_text())

default_config_file = pathlib.Path('./config.yaml')

if default_config_file.exists():
    load_config(default_config_file)


if __name__ == '__main__':
    """
    This area is for interactive developer debugging
    """
    
    interrupted = False
    
    def signal_handler(signal, frame) -> None:
        global interrupted
        interrupted = True

    def generate_config() -> None:
        """
        Generates a new config file using these hard-coded values
        """
        
        import gcloud_adapter
        import openai_adapter

        config = {
            'recording': {
                'output_file': './recording.mp3',
                'sample_rate_Hz': 16000,
                'channels': 1,
                'ffmpeg': {
                    'i': ':0',
                    'f': 'avfoundation',
                    'acodec': 'mp3',
                },
            },
            'transcription': {
                'output_file': '',
                'model': 'whisper-1',
            },
            'completion_model': openai_adapter.chat_model,
            'cleanup': {
                'output_file': '',
                'prompt': '',
            },
            'optimization': {
                'output_file': '',
                'prompt': '',
            },
            'speech_synthesis': {
                'gcloud_sdk_bin': '~/google-cloud-sdk/bin/gcloud',
                'gcloud_project': '',
                'voice': {
                "languageCode": 'en-US',
                "name": 'en-US-Studio-M',
                "audioEncoding": gcloud_adapter.AudioEncoding.MP3.value,
                "speakingRate": 1.0,
                "pitch": 0.0,
                "volumeGainDb": 0.0,
                "sampleRateHertz": 16000,
                },
                'chunk_size': 1000,
            },
        }
        
        with open('./config.yaml', 'w') as f:
            f.write(yaml.safe_dump(config, default_flow_style=False))
    
    # Record something
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    output = str(pathlib.Path.cwd().joinpath('testfiles/recording.mp3'))
    record_apple_mic(output)