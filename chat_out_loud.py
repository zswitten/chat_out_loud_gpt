import openai
import json
import requests
import os
import wave
import pyaudio
import audioop
import math
from collections import deque
from typing import AsyncGenerator, Optional
from playsound import playsound
import asyncio

### Setting up sound recording. ###
### Credit https://kevinponce.com/blog/python/record-audio-on-detection/ ###

def record(file_name, silence_threshold, silence_limit=1,
            chunk=1024, rate=44100, prev_audio=1, channels=1):

    FORMAT = pyaudio.paInt16
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(2),
        channels=channels,
        rate=rate,
        input=True,
        output=False,
        frames_per_buffer=chunk,
    )

    listen = True
    started = False
    rel = rate/chunk
    frames = []
    prev_audio = deque(maxlen=int(prev_audio * rel))
    slid_window = deque(maxlen=int(silence_limit * rel))

    print('Recording.')
    while listen:
        data = stream.read(chunk)
        slid_window.append(math.sqrt(abs(audioop.avg(data, 4))))

        if(sum([x > silence_threshold for x in slid_window]) > 0):
            if(not started):
                print("Noise detected")
                started = True
        elif (started is True):
            started = False
            listen = False
            prev_audio = deque(maxlen=int(0.5 * rel))

        if (started is True):
            frames.append(data)
        else:
            prev_audio.append(data)

    stream.stop_stream()
    stream.close()

    p.terminate()
    print("Done recording")

    wf = wave.open(f'{file_name}', 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(rate)

    wf.writeframes(b''.join(list(prev_audio)))
    wf.writeframes(b''.join(frames))
    wf.close()

### Setting up TTS ###

openai.api_key = os.environ['OPENAI_API_KEY']
charactr_client_key = os.environ['CHARACTR_CLIENT_KEY']
charactr_api_key = os.environ['CHARACTR_API_KEY']

class CharactrAPI:
    VOICES_URL = 'https://api.charactr.com/v1/tts/voices'
    TTS_URL = 'https://api.charactr.com/v1/tts/convert'

    def __init__(self, client_key, api_key, voice_id=163):
        self.client_key = client_key
        self.api_key = api_key
        self.voice_id = voice_id

    def get_voices(self):
        headers = {
            'X-Client-Key': self.client_key,
            'X-Api-Key': self.api_key,
        }
        response = requests.get(self.VOICES_URL,
                                headers=headers)
        try:
            voices = json.loads(response.content)
        except Exception as e:
            raise Exception(e)
        return voices

    def text2speech(self, text):
        headers = {
            'X-Client-Key': self.client_key,
            'X-API-Key': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {'voiceId': self.voice_id, 'text': text}
        response = requests.post(self.TTS_URL,
                                 headers=headers,
                                 data=json.dumps(data))
        return response.content

charactr_api = CharactrAPI(charactr_client_key, charactr_api_key)

### Async methods for TTS + ChatGPT ###
### Whisper can't be async because it relies on full phrase ###

async def async_get_completion(messages):
    async def _call(messages) -> AsyncGenerator[str, None]:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
            max_tokens=1000,
            temperature=0,
            top_p=1,
            frequency_penalty=0.6,
            presence_penalty=0.6,
        )

        async def gen():
            async for chunk in response:  # type: ignore
                yield chunk

        return gen()

    return await _call(messages)

async def text2speech_async(text):
    return charactr_api.text2speech(text)

async def make_text2speech_file(text, output_path):
    audiob = await text2speech_async(text)
    with open(output_path, 'wb') as f:
        f.write(audiob)

### Some convenience methods ###

def make_messages(conversation_history):
    messages = [
        {"role": "system", "content": system_message},
    ]
    for i, message in enumerate(conversation_history['user_messages']):
        messages.append({'role': "user", "content": message})
        if i < len(conversation_history['elmo_messages']):
            messages.append(
                {'role': "assistant", "content": conversation_history['elmo_messages'][i]})
    return messages

def play_audio(path):
    playsound(path)

### Setup the system ###

conversation_history = {'user_messages': [], 'elmo_messages': []}
input_path = 'speech_input.wav'
output_path = 'speech_output.wav'

system_message = """
You are famous rapper Snoop Dogg. You answer questions lacksadaisically, like you're
too cool to care. You speak with a lot of attitude. 
"""

### Let's go ###
async def main(channels=1, rate=44100, chunk_val=1024):
    print('Calibrating silence threshold...')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(2),
        channels=CHANNELS,
        rate=rate,
        input=True,
        output=False,
        frames_per_buffer=chunk_val,
    )
    # Calibration step to determine the silence threshold based on the environment noise.
    calibrate_secs = 3
    silence_thresholds = []
    for _ in range(int(rate / chunk_val * calibrate_secs)):
        data = stream.read(chunk_val)
        silence_thresholds.append(math.sqrt(abs(audioop.avg(data, 4))))

    silence_threshold = sum(silence_thresholds)/len(silence_thresholds) * 2
    print(f'Silence threshold set to {silence_threshold}')
    stream.stop_stream()
    stream.close()
    p.terminate()

    while(True):
        os.system(f"rm {input_path}")
        record(input_path, silence_threshold, rate=rate, chunk=chunk_val, channels=channels)
        transcription = openai.Audio.transcribe("whisper-1", open(input_path, "rb"))
        # print("Transcription:", transcription)
        conversation_history['user_messages'].append(transcription['text'])
        completion = async_get_completion(make_messages(conversation_history))
        collected_messages = []
        current_sentence = ''
        collected_sentences = []
        chunk_idx = 0
        async for chunk in await completion:
            chunk_message = chunk['choices'][0]['delta']
            msg_chunk_txt = chunk_message.get('content', '')
            current_sentence += msg_chunk_txt
            delimiters = ['.', '!', '?', '\n']
            for d in delimiters:
                if d in msg_chunk_txt:
                    completed_sentence = current_sentence.split(d)[0] + d
                    # print('completed_sentence: ', completed_sentence)
                    collected_sentences.append(completed_sentence)
                    if len(completed_sentence.strip()) > 0:
                        _output_path = output_path + str(chunk_idx)
                        _ = await make_text2speech_file(
                            completed_sentence, _output_path)
                        play_audio(_output_path)
                        os.system(f'rm {_output_path}')
                    current_sentence = msg_chunk_txt.split(d)[1]
                    break
            collected_messages.append(chunk_message)
            chunk_idx += 1
        text = ''.join([m.get('content', '') for m in collected_messages])
        conversation_history['elmo_messages'].append(text)

if __name__ == '__main__':
    CHANNELS = 1
    rate = 44100
    chunk = 1024

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(
        channels=CHANNELS, rate=rate, chunk_val=chunk
    ))
    loop.close()
