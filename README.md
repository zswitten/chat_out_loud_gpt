# Chat Out Loud with GPT
Title says it all. No typing required. Reasonably fast thanks to async + stream=true. 

## Usage
```
export OPENAI_API_KEY={your key}
export CHARACTR_CLIENT_KEY={your key}
export CHARACTR_API_KEY={your key}
pip install -r requirements.txt
python chat_out_loud.py
```

## Mods
- By default it pretends to be Snoop Dogg. Feel free to change the system message to your liking. Or to change the GPT model from 3.5 to 4.

- You may need to tweak the silence_threshold in the `record` function depending on the sensitivity of your mic and the environment you're in. The higher it is, the louder you need to talk, but if it's too low the background noise may keep it from ever turning off.

- You can choose different voices from charactr (throw a breakpoint and call `charactr_api.get_voices()` to see available, or swap in a different TTS system entirely if you want to clone your own voice or Snoop's voice or whatever.








#### Credits
Written by [me](http://twitter.com/zswitten) and my buddy [Alec](https://github.com/thatperson42).
