import pathlib
import signal
from time import sleep

import ffmpeg
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

    def record_apple_mic(file_name: pathlib.Path) -> None:
        global interrupted
        
        """
        What the flags mean
        -f = "force format". In this case we're forcing the use of AVFoundation
        -i = input source [handled by input() method]. Typically it's a file, but you can use devices.
            "0:1" = Record both audio and video from FaceTime camera and built-in mic
            "0" = Record just video from FaceTime camera
            ":1" = Record just audio from built-in mic
        -t = time in seconds. If you want it to run indefinitely until you stop it (ControlC) omit this value
        """
        # TODO (probably): Write a function to get the correct input source using 'ffmpeg -f avfoundation -list_devices true -i ""'
        process = (
            ffmpeg
            .input(
                ':0',
                f='avfoundation',
                )
            .output(
                str(file_name),
                acodec='mp3',
                # ac=1, 
                # ar=16000,
                )
            .overwrite_output()
            .run_async(
                # pipe_stdout=True,
                # pipe_stderr=True,
                quiet=True,  # NB: True sets `pipe_` parameters to null STDOUT and map STDERR->STDOUT
                )
        )

        while process.poll() is None:
            if interrupted:
                process.terminate()
                break
            else:
                sleep(1)

        if process.returncode is not None:
            raise RuntimeError(str(process.stdout.read()).replace('\\n', '\n'))

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