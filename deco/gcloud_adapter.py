# Using gcloud REST API rather than Python API because of the latter's dependency constraints

import json
import re
import subprocess
import typing as t
from base64 import b64decode
from enum import Enum

import requests
from .utils import APP_CONFIG


class SsmlVoiceGender(str, Enum):
    UNSPECIFIED = 'SSML_VOICE_GENDER_UNSPECIFIED'
    MALE = 'MALE'
    FEMALE = 'FEMALE'
    NEUTRAL = 'NEUTRAL'


class ReportedUsage(str, Enum):
    REALTIME = 'REALTIME'
    OFFLINE = 'OFFLINE'


class AudioEncoding(str, Enum):
    LINEAR16 = 'LINEAR16'   # 16-bit signed little-endian samples (Linear PCM)
    MP3 = 'MP3'             # 32kbps
    OGG_OPUS = 'OGG_OPUS'   # Opus encoded audio wrapped in an ogg container. 
    MULAW = 'MULAW'         # 8-bit samples that compand 14-bit audio samples using G.711 PCMU/mu-law.
    ALAW = 'ALAW'           # 8-bit samples that compand 14-bit audio samples using G.711 PCMU/A-law.


class SentenceTokenizer:
    """
    Lifted from StackOverflow at https://stackoverflow.com/a/31505798/2539684
    on 5/1/23, with license CC-BY-SA-4.0: https://creativecommons.org/licenses/by-sa/4.0/
    """

    # -*- coding: utf-8 -*-
    alphabets= "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov|edu|me)"
    digits = "([0-9])"

    def __call__(self, text: str) -> str:
        text = " " + text + "  "
        text = text.replace("\n"," ")
        text = re.sub(self.prefixes,"\\1<prd>",text)
        text = re.sub(self.websites,"<prd>\\1",text)
        text = re.sub(self.digits + "[.]" + self.digits,"\\1<prd>\\2",text)
        if "..." in text: text = text.replace("...","<prd><prd><prd>")
        if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
        text = re.sub("\s" + self.alphabets + "[.] "," \\1<prd> ",text)
        text = re.sub(self.acronyms+" "+self.starters,"\\1<stop> \\2",text)
        text = re.sub(self.alphabets + "[.]" + self.alphabets + "[.]" + self.alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
        text = re.sub(self.alphabets + "[.]" + self.alphabets + "[.]","\\1<prd>\\2<prd>",text)
        text = re.sub(" "+self.suffixes+"[.] "+self.starters," \\1<stop> \\2",text)
        text = re.sub(" "+self.suffixes+"[.]"," \\1<prd>",text)
        text = re.sub(" " + self.alphabets + "[.]"," \\1<prd>",text)
        if "”" in text: text = text.replace(".”","”.")
        if "\"" in text: text = text.replace(".\"","\".")
        if "!" in text: text = text.replace("!\"","\"!")
        if "?" in text: text = text.replace("?\"","\"?")
        if "..." in text: text = text.replace("...","<prd><prd><prd>")
        text = text.replace(".",".<stop>")
        text = text.replace("?","?<stop>")
        text = text.replace("!","!<stop>")
        text = text.replace("<prd>",".")
        sentences = text.split("<stop>")
        sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]
        return sentences


class GCloudTTS():

    GTTS_MAX_LENGTH = 5000  # https://cloud.google.com/text-to-speech/quotas
    sentencizer = SentenceTokenizer()

    def __init__(self) -> None:
        MODULE_CONFIG: dict = APP_CONFIG['speech_synthesis']
        self.load_gcloud_sdk_config()
        self.__synthesis_input = {
            'text': ''
            }
        self.__custom_voice_params = {
            "model": '',
            "reportedUsage": ReportedUsage.REALTIME,
            }
        self.__voice_selection_params = {
            "languageCode": MODULE_CONFIG['voice']['languageCode'],
            "name": MODULE_CONFIG['voice']['name'],  
            "ssmlGender": SsmlVoiceGender.UNSPECIFIED,
            # "customVoice": {custom_voice_params},
            }
        self.__audio_config = {
            "audioEncoding": MODULE_CONFIG['voice']['audioEncoding'],
            "speakingRate": max(0.25, min(4.0, MODULE_CONFIG['voice']['speakingRate'])),
            "pitch": max(-20.0, min(20.0, MODULE_CONFIG['voice']['pitch'])),
            "volumeGainDb": max(-96.0, min(16.0, MODULE_CONFIG['voice']['volumeGainDb'])),
            "sampleRateHertz": MODULE_CONFIG['voice']['sampleRateHertz'],
            # "effectsProfileId": [''],  # elects 'audio effects' profiles that are applied
            }

    @property
    def __request_body(self) -> dict:
        return {
            'input': self.__synthesis_input,
            'voice': self.__voice_selection_params,
            'audioConfig': self.__audio_config
            }
    
    @property
    def __request_headers(self) -> dict:
        return {
            # NB: These headers let the app use my personal GCloud account
            "Authorization": f'Bearer {self.__sdk_token}',
            "X-Goog-User-Project": self.__sdk_project,
            }
    
    @property
    def __request_endpoint(self) -> str:
        api_url = 'https://texttospeech.googleapis.com/v1/'
        api_endpoint = 'text:synthesize'
        return api_url + api_endpoint

    def load_gcloud_sdk_config(self) -> None:
        # TODO Add method to authenticate without SDK
        # TODO Move gcloud authentication out of this class, into the module
        cmd_bin = APP_CONFIG['speech_synthesis']['gcloud_sdk_bin']
        cmd_params = 'auth application-default print-access-token'
        self.__sdk_token = subprocess.run(
            f'{cmd_bin} {cmd_params}',
            capture_output=True,
            text=True,
            shell=True,
            ).stdout.strip()

        if APP_CONFIG['speech_synthesis']['gcloud_project'] == '':
            cmd_params = 'config get-value project'
            self.__sdk_project = subprocess.run(
                f'{cmd_bin} {cmd_params}',
                capture_output=True,
                text=True,
                shell=True,
                ).stdout.strip()
        else:
            self.__sdk_project = APP_CONFIG['speech_synthesis']['gcloud_project']

    def synthesize(self, text: str) -> bytes:

        if not isinstance(text, str):
            raise ValueError('Text must be a string. For chunked text, use the other method.')
        
        if len(text.encode('utf-8')) > self.GTTS_MAX_LENGTH:
            raise ValueError('Text must be <= 5000 bytes in utf-8 encoding. Use other method to chunk it.')

        req_body = self.__request_body
        req_body['input']['text'] = text
        rep = requests.post(
            url=self.__request_endpoint,
            json=req_body,
            headers=self.__request_headers,
        )

        if not rep.status_code == 200:
            raise Exception(
                    (
                        f'GCloud API returned with code {rep.status_code}. Response body:\n' +
                        json.dumps(json.loads(rep.content), indent=4)
                        )
                    )
        else:
            ret_str = json.loads(rep.content)

        return b64decode(ret_str['audioContent'])

    def synthesize_stream(self, text: str|t.Generator, chunk_size: int) -> t.Generator:
        
        chunk_size = min(chunk_size, self.GTTS_MAX_LENGTH)
        
        if isinstance(text, t.Generator):
            raise NotImplementedError
        elif isinstance(text, str):

            if len(text) > chunk_size:
                chunks = self.sentencizer(text)

                if len(sorted(chunks, key=lambda _: len(_), reverse=True)[0]) > chunk_size:
                    for i, chunk in enumerate(chunks):
                        if len(chunk) > chunk_size:
                            sub_chunks = []
                            j = 0
                            while j < len(chunk):
                                sub_chunks.append(chunk[j : j + chunk_size])
                                j = j + chunk_size
                            chunks[i] = sub_chunks 
            else:
                chunks = [text]
                
        else:
            raise ValueError('Text must be type str or Generator')
        
        for chunk in chunks:

            if isinstance(chunk, list):
                for c in chunk:
                    yield self.synthesize(c)
            else:
                yield self.synthesize(chunk)
