"""
Intention: Make a CLI-driven app that works with files on disk
"""
import argparse
import pathlib

import gcloud_adapter as g
import openai_adapter as o
from utils import APP_CONFIG, load_config


def override_app_config(namespace: argparse.Namespace) -> None:
    
    if namespace.config_file:
        load_config(namespace.config_file)
    
    if namespace.extra_outputs:
        in_file = pathlib.Path(namespace.input)
        out_trunk = str(in_file.parent.joinpath(in_file.stem).resolve())
        APP_CONFIG['transcription']['output_file'] = out_trunk + '-trans.txt'
        APP_CONFIG['cleanup']['output_file'] = out_trunk + '-clean.txt'
        APP_CONFIG['optimization']['output_file'] = out_trunk + '-optim.txt'


def cleanup(text, ) -> str:
    # TODO Return token count to user for monitoring
    messages = o.create_chat_messages(
        APP_CONFIG['cleanup']['prompt'],
        text,
        )
    completion, tokens = o.basic_chat(
        messages,
        APP_CONFIG['cleanup']['model'],
        )
    return completion


def optimize(text: str) -> str:
    # TODO Return token count to user for monitoring
    messages = o.create_chat_messages(
        APP_CONFIG['optimization']['prompt'],
        text,
        )
    completion, tokens = o.basic_chat(
        messages,
        APP_CONFIG['optimization']['model'],
        )
    
    output = ''
    lines = completion.splitlines()
    for i, line in enumerate(lines):
        # These strings are taken from the prompt.
        # TODO Something more robust, since prompt is configurable and
        #  AI doesn't follow instructions perfectly.
        if line.startswith('###') and '3' in line:
            output = '\n'.join(lines[i+1:])
            break
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # TODO Add mutex option to input from STDIN instead of file
    parser.add_argument(
        'input',
        type=str,
        help='Input file. Supported formats: ' + ', '.join(o.TRANSCRIBE_FORMATS),
        )
    # TODO Add mutex option to output to STDOUT instead of file
    parser.add_argument(
        '-o', '--output-file',
        type=str,
        help='Output file. (Recommend using appropriate suffix for output format: .mp3 or .txt.)',
    )
    parser.add_argument(
        '-c', '--config-file',
        type=str,
        help='Path to custom config file',
        )
    parser.add_argument(
        '-C', '--no-cleanup',
        action='store_true',
        help='Do not cleanup the transcription (if input is audio)',
    )
    parser.add_argument(
        '-O', '--no-optimize',
        action='store_true',
        help='Do not optimize the input',
    )
    parser.add_argument(
        '-S', '--no-speech',
        action='store_true',
        help='Do not generate speech output. Will output text instead. \
            MIND THE SUFFIX OF THE OUTPUT FILE, IF YOU SPECIFIED THE "-o" OPTION!',
    )
    parser.add_argument(
        '-x', '--extra-outputs',
        action='store_true',
        help='Generate extra outputs from intermediate steps in the processing chain. \
            Will be stored in the alongside final output file. \
            Overrides config file settings.',
    )
    cli = parser.parse_args()
    override_app_config(cli)
    
    in_file = pathlib.Path(cli.input)
    
    # Transcription or ingestion
    if in_file.suffix.lstrip('.').lower() in o.TRANSCRIBE_FORMATS:
        t_out_file = APP_CONFIG['transcription']['output_file']

        if t_out_file:
            o.transcribe_to_file(in_file, t_out_file, APP_CONFIG['transcription']['model'])
            in_text = pathlib.Path(t_out_file).read_text()
        else:
            in_text = o.transcribe(in_file, APP_CONFIG['transcription']['model'])
            
    else:
        in_text = in_file.read_text()
        
    # Cleanup
    if cli.no_cleanup:
        c_text = in_text  
    else:
        c_text = cleanup(in_text)
        c_out_file = APP_CONFIG['cleanup']['output_file']
        
        if c_out_file:        
            with open(c_out_file, mode='w') as f:
                f.write(c_text)
    
    # Optimization
    if cli.no_optimize:
        o_text = c_text
    else:
        o_text = optimize(c_text)
        o_out_file = APP_CONFIG['optimization']['output_file']
        
        if o_out_file:        
            with open(o_out_file, mode='w') as f:
                f.write(o_text)
    
    # Speech synthesis
    if cli.no_speech:
        with open(cli.output_file, mode='w') as f:
            f.write(o_text)
    else:
        tts = g.GCloudTTS()
        audio_stream = tts.synthesize_stream(
            o_text,
            chunk_size=APP_CONFIG['speech_synthesis']['chunk_size'],
            )
        with open(cli.output_file, mode='wb') as f:
            for chunk in audio_stream:
                f.write(chunk)
