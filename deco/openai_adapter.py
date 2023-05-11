import pathlib
import typing as t

import openai

TRANSCRIBE_FORMATS = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']


def check_api_up():
    """
    Touches the OpenAI API to make sure everything is configured correctly.
    """
    openai.Model.list()  # Relying on an exception to be thrown if access key not configured or invalid


def choose_model(model_name: str='') -> None:
    global chat_model

    if model_name != '':
        chat_model = model_name

    mlist = openai.Model.list()
    models = sorted([i.id for i in mlist.data if i.object == 'model'])

    once = False
    while chat_model not in models:
        if not once:
            print('Available models:', *models, sep='\n- ')  # Reminder: * unpacks a list or tuple
            once = True
        chat_model = input('Pick one > ' ).strip()


def create_chat_messages(prompt: str, text: str, user: str='') -> list[dict]:

    messages = [
        {
            'role': 'system',
            'content': prompt,
        },
        {
            'role': 'user',
            'content': text,
        }
    ]

    if user:
        messages[1]['name'] = user

    return messages


def basic_chat(messages: list[dict], model_name: str, temperature: float=0.0, ) -> t.Tuple[str, int]:
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        temperature=0.0,
        stream=False,
    )
    return response.choices[0].message.content, response.usage.prompt_tokens


def adv_chat(messages: list[dict], model_name: str, temperature: float=0.0, ) -> t.Any:
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        stream=False,
    )
    return response


def transcribe(source_file: str|pathlib.Path, model_name: str) -> str:

    if isinstance(source_file, str):
        source_file = pathlib.Path(source_file)
    
    ret = openai.Audio.transcribe(
        model_name,
        source_file.open(mode='rb'),
        )
    return ret.text


def transcribe_to_file(source_file: str|pathlib.Path, output_file: str|pathlib.Path, model_name: str) -> None:
    with open(output_file, mode='w') as f:
        f.write(transcribe(source_file, model_name))


def is_mpeg_audio(data: bytes) -> bool:
    """Check if the data represents an MPEG (MPEG-1, MPEG-2) Layer III audio."""
    return data.startswith(b'\xff', 0) and (data[1] & 0b11100000) == 0b11100000


def detect_audio_format(data: bytes) -> t.Optional[str]:
    """Detect the audio container format based on the data's signature."""
    signatures = {
        b'ID3': ('.mp3', 0),
        b'\x00\x00\x00 ftypmp4': ('.mp4', 4),
        b'\x00\x00\x00 ftypM4A': ('.m4a', 4),
        b'RIFF': ('.wav', 0),
        b'\x1aE\xdf\xa3': ('.webm', 0),
        b'fLaC': ('.flac', 0),
    }

    if is_mpeg_audio(data):
        signatures[b'\xff'] = ('.mpga', 0)

    for signature, (extension, offset) in signatures.items():
        if data.startswith(signature, offset):
            return extension

    return None
