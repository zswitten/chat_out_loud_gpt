# Chat Out Loud with GPT
Hands-free companionship on demand. Reasonably non-laggy thanks to async + stream=true. 

## Usage
```
brew install portaudio
export OPENAI_API_KEY={your key}
export CHARACTR_CLIENT_KEY={your key}
export CHARACTR_API_KEY={your key}
pip install -r requirements.txt
python chat_out_loud.py
```

If the recording is acting wonky (either hanging forever, or not starting), run `python chat_out_loud.py --calibrate` to find your ideal threshold. Then you can set it in the file and run it without the --calibrate flag.

Only tested on Mac for now. Please LMK if you get it to work on Windows or Linux.

## Mods
- By default it pretends to be Snoop Dogg. Feel free to change the system message to your liking. Or to change the GPT model from 3.5 to 4.

- You can change the silence threshold (the higher it is, the louder you need to talk, but if it's too low the background noise may keep it from ever turning off), and how long it tolerates silence for (silence_limit, currently set to 1, shorter = snappier but more demanding).

- You can choose different voices from charactr (throw a breakpoint and call `charactr_api.get_voices()` to see available, or swap in a different TTS system entirely if you want to clone your own voice or Snoop's voice or whatever.

## How does it work?

1. Pyaudio listens until it hears a sound, then listens until it stops hearing a sound, then writes to a file.
2. The file is sent to [Whisper](https://openai.com/blog/introducing-chatgpt-and-whisper-apis) for transcription.
3. The transcription is appended to the system message + any previous messages in the convo and sent to [ChatGPT](https://openai.com/blog/introducing-chatgpt-and-whisper-apis).
4. ChatGPT's response is streamed back; when it finishes a sentence, the sentence is sent to [Charactr](https://charactr.com/) for TTS
5. The resulting TTS plays out loud while 3 and 4 continue in the background
6. Repeat!





#### Contributors note
My buddy [Alec](https://github.com/thatperson42) wrote some of the code. This originated as a [hackathon project](https://twitter.com/zswitten/status/1632640801850425344) involving a stuffed teddy bear.
