# audio2summary
Uses OpenAI's whisper-1 model and gpt-3.5-turbo / gpt-4 to summarise audio recordings of meetings. If audio files are too big (over 25 MB) it automatically partitions them into smaller pieces.

When done it enters chat mode where you can ask the assistant about the contents of the meeting.

## Installation
Install python requirements as usual:
```bash
pip install -r requirements.txt
```
Create a file `secret_variables.py` and add this line
```python
openai_api_key = "sk-...."
```
where you replace the `"sk-...."` with your OpenAI API-key.

You call the program with:
```bash
python audio2summary your_audio_file.mp4
```
Wav files work too.