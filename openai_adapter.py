import pathlib
import typing as t

import openai

from utils import APP_CONFIG

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


if __name__ == '__main__':
    """
    This area is for interactive developer debugging
    """
    
    TEST_INPUT = pathlib.Path.cwd().joinpath("test-files/A big idea.mp3")
    
    # Transcribe
    t_model = APP_CONFIG['transcription']['model']
    t_output = TEST_INPUT.parent.joinpath(TEST_INPUT.stem + f'-openai({t_model}).txt')
    transcribe_to_file(TEST_INPUT, t_output, t_model)
    
    # Cleanup
    messages = create_chat_messages(APP_CONFIG['cleanup']['prompt'], t_output.read_text(), '')
    c_output = t_output.parent.joinpath(f'{t_output.stem}-clean.txt')
    completion, tokens = basic_chat(messages, APP_CONFIG['cleanup']['model'])
    with open(c_output, mode='w') as f:
        f.write(completion)
    
    # Optimization
    messages = create_chat_messages(APP_CONFIG['optimization']['prompt'], c_output.read_text(), '')
    o_output = c_output.parent.joinpath(f'{c_output.stem}-optim.txt')
    completion, tokens = basic_chat(messages, APP_CONFIG['cleanup']['model'])
    with open(o_output, mode='w') as f:
        f.write(completion)
