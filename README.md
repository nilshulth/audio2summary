# audio2summary
Uses OpenAI's whisper-1 model and gpt-3.5-turbo / gpt-4 to summarise audio recordings of meetings

## Installation
Create a file `secret_variables` and add this line
```
openai_api_key = "sk-...."
```
where you replace the `"sk-...."` with your OpenAI API-key.

You call the program with:
```python
python audio2summary your_audio_file.mp4
```
Wav files work too.