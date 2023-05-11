import argparse
from pathlib import Path
import sys
import typing as t
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv

import deco.gcloud_adapter as g
import deco.openai_adapter as o
from deco.utils import APP_CONFIG, load_config

load_dotenv()


def build_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    input_mutex = parser.add_mutually_exclusive_group()
    input_mutex.add_argument(
        '-i', '--in-file',
        type=str,
        help='Input file. (If not given, STDIN is used.) Supported formats: ' + ', '.join(o.TRANSCRIBE_FORMATS),
        )
    input_mutex.add_argument(
        '-t', '--transcribe',
        action='store_true',
        help='Transcribe binary audio from STDIN. Cannot be used with --in_file. If omitted, STDIN is assumed to carry text.',
    )
    parser.add_argument(
        '-o', '--out-file',
        type=str,
        help='Output file. (If not given, STDOUT is used.) Recommend using appropriate suffix for output format: .mp3 or .txt.',
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
    return parser.parse_args()


def override_app_config() -> None:
    
    if CLI.config_file:
        load_config(CLI.config_file)
    
    if CLI.extra_outputs:
        in_file = Path(CLI.input)
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


def ingest() -> str:
    
    if CLI.in_file:
        in_file = Path(CLI.in_file)
    else:
        # STDIN - However, o.transcribe() requires a file on disk as input 
        if CLI.transcribe:
            stream = sys.stdin.buffer.read()
            suffix = o.detect_audio_format(stream)
            temp = NamedTemporaryFile(mode='wb', delete=False, suffix=suffix)
            temp.write(stream)
        else:
            temp = NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            try:
                temp.write(sys.stdin.read())
            except UnicodeDecodeError as e:
                raise RuntimeError('Expected UTF-8 text at STDIN but got binary data instead.') from e

        temp.close()
        in_file = Path(temp.name)
        
    if in_file.suffix.lstrip('.').lower() in (o.TRANSCRIBE_FORMATS):
        # Transcribe
        t_out_file = APP_CONFIG['transcription']['output_file']

        if t_out_file:
            o.transcribe_to_file(in_file, t_out_file, APP_CONFIG['transcription']['model'])
            in_text = Path(t_out_file).read_text()
        else:
            in_text = o.transcribe(in_file, APP_CONFIG['transcription']['model'])
        
        if not CLI.in_file:
            # Delete temporary file  
            Path.unlink(in_file)
            
    else:
        # Ingest
        in_text = in_file.read_text()
        
    return in_text


def write_text_output(text: str) -> None:
    
    if CLI.out_file:
        with open(CLI.out_file, mode='w') as f:
            f.write(text)
    else:
        sys.stdout.write(text)


def stream_binary_output(first_block: bytes, remainder: t.Generator) -> None:
    
    if CLI.out_file:
        with open(CLI.out_file, mode='wb') as f:
            f.write(first_block)
            for block in remainder:
                f.write(block)
    else:
        sys.stdout.buffer.write(first_block)
        for block in remainder:
            sys.stdout.buffer.write(block)


if __name__ == '__main__':
    CLI = build_cli()
    override_app_config()
    in_text = ingest()
        
    # Cleanup
    if CLI.no_cleanup:
        c_text = in_text  
    else:
        c_text = cleanup(in_text)
        c_out_file = APP_CONFIG['cleanup']['output_file']
        
        if c_out_file:        
            with open(c_out_file, mode='w') as f:
                f.write(c_text)
    
    # Optimization
    if CLI.no_optimize:
        o_text = c_text
    else:
        o_text = optimize(c_text)
        o_out_file = APP_CONFIG['optimization']['output_file']
        
        if o_out_file:        
            with open(o_out_file, mode='w') as f:
                f.write(o_text)
    
    # Speech synthesis
    if CLI.no_speech:
        write_text_output(o_text)
    else:
        tts = g.GCloudTTS()
        audio_stream = tts.synthesize_stream(
            o_text,
            chunk_size=APP_CONFIG['speech_synthesis']['chunk_size'],
            )
        try:
            chunk0 = next(audio_stream)
            
            if len(chunk0):
                stream_binary_output(chunk0, audio_stream)
            else:
                raise ValueError('First chunk of audio stream was size 0.')
            
        except (StopIteration, ValueError) as e:
            raise RuntimeError('Speech synthesis output size was zero. \
                Possible problem with input. Use "-x" option to view \
                    intermediate outputs.') from e
