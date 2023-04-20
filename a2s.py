import openai
from pydub import AudioSegment
import argparse
import io
import hashlib
import os
import shutil
import sys

from secret_variables import openai_api_key

openai.api_key = openai_api_key


def split_audio(file_path, segment_length=300000):
    """Splits an audio file into smaller segments.

    Args:
        file_path (str): Path to the audio file to split.
        segment_length (int, optional): Length of the segments in milliseconds. Defaults to 300000.

    Returns:
        List[AudioSegment]: List of smaller audio segments.
    """
    audio = AudioSegment.from_file(file_path)

    segments = []
    for i in range(0, len(audio), segment_length):
        segments.append(audio[i:i + segment_length])

    return segments


def transcribe_audio_segments(segments, file_extension):
    """Transcribes the audio content of a list of audio segments.

    Args:
        segments (List[AudioSegment]): List of audio segments to transcribe.
        file_extension (str): File extension of the audio file, e.g. "wav" or "mp3".

    Returns:
        str: Transcription corresponding to the concatenation of all segments' audio content.
    """
    transcriptions = ''
    total_segments = len(segments)

    for i, segment in enumerate(segments):
        print(f"Transcribing segment {i + 1} of {total_segments}...")
        sys.stdout.flush()

        audio_file = io.BytesIO()
        audio_file.name = f"segment_{i + 1}.{file_extension}"
        segment.export(audio_file, format=file_extension)
        audio_file.seek(0)
        print(f"Exported segment {i + 1} to {audio_file.name}.")
        sys.stdout.flush()

        if file_extension == "wav":
            transcript = openai.Audio.transcribe("whisper-1", audio_file, format="wav").text
        else:
            transcript = openai.Audio.transcribe("whisper-1", audio_file).text

        transcriptions += transcript + ' '
        print(f"Transcription for segment {i + 1} of {total_segments} complete.")
        sys.stdout.flush()

    print("Transcription complete.")
    sys.stdout.flush()
    return transcriptions


def split_transcript(transcript, max_length=3000):
    """Splits a long transcript into smaller chunks.

    Args:
        transcript (str): Long transcript to split.
        max_length (int, optional): Maximum length of each chunk. Defaults to 3000.

    Returns:
        List[str]: List of transcript chunks.
    """
    chunks = []
    words = transcript.split()

    while words:
        chunk = words[:max_length]
        words = words[max_length:]
        chunks.append(" ".join(chunk))

    return chunks


def summarize_text(chunks, max_size_per_message=4096):
    """Summarizes a list of text chunks using OpenAI's GPT-3.5 model.

    Args:
        chunks (List[str]): List of text chunks to summarize.
        max_size_per_message (int, optional): Maximum size of each GPT-3 output message. Defaults to 4096.

    Returns:
        str: Concatenated summary of all the text chunks.
    """
    summaries = []
    command = f"Give a very long and detailed summary, but keep it to max {max_size_per_message} characters."

    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i + 1} out of {total_chunks}, characters: {len(chunk)}")
        sys.stdout.flush()

        messages = [{"role": "user", "content": chunk}]
        messages.append({"role": "user", "content": command})

        output = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        summary = output.choices[0].message.content
        summaries.append(summary.strip())

        print(f"Summary for chunk {i + 1} of {total_chunks} complete: {len(summary)} characters")
        sys.stdout.flush()

    return " ".join(summaries)


def query_mode(summary):
    """Interactively answers user's questions using OpenAI's GPT-4 model.

    Args:
        summary (str): Summary of the audio file content.
    """
    while True:
        user_question = input("\nAsk a question (type 'exit' to quit): ")

        if user_question.lower() == "exit":
            break

        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages.append({"role": "user", "content": summary})
        messages.append({"role": "user", "content": user_question})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )

        answer = response.choices[0].message.content
        print("\nAnswer:", answer.strip())
        sys.stdout.flush()


def calculate_audio_file_hash(file_path):
    """Calculates the SHA-256 hash of an audio file.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        str: SHA-256 hash of the audio file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main(audio_file_path, clear_cache=False, debug=False):
    """Main function that processes an audio file.

    Args:
        audio_file_path (str): Path to the audio file to process.
        clear_cache (bool, optional): Whether or not to clear the cache before processing. Defaults to False.
        debug (bool, optional): Whether or not to print debug statements. Defaults to False.
    """
    if debug:
        openai.api_request_debug = True
        sys.tracebacklimit = None

    cache_dir = 'cache'
    if clear_cache and os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        return

    os.makedirs(cache_dir, exist_ok=True)
    file_hash = calculate_audio_file_hash(audio_file_path)
    cached_transcript_file = f"{cache_dir}/{file_hash}_transcript.txt"
    cached_summary_file = f"{cache_dir}/{file_hash}_summary.txt"

    if os.path.exists(cached_transcript_file):
        with open(cached_transcript_file, 'r') as f:
            transcript = f.read()
        print("Using cached transcription.")
        sys.stdout.flush()
    else:
        file_extension = audio_file_path.split('.')[-1].lower()
        segments = split_audio(audio_file_path)
        transcript = transcribe_audio_segments(segments, file_extension)
        with open(cached_transcript_file, 'w') as f:
            f.write(transcript)

    if os.path.exists(cached_summary_file):
        with open(cached_summary_file, 'r') as f:
            summary = f.read()
        print("Using cached summary.")
        sys.stdout.flush()
    else:
        chunks = split_transcript(transcript)
        summary = summarize_text(chunks)
        with open(cached_summary_file, 'w') as f:
            f.write(summary)

    query_mode(summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process an audio file.")
    parser.add_argument("audio_file", help="The path to the audio file.")
    parser.add_argument("--clear-cache", action="store_true", help="Clear the cache and exit.")
    parser.add_argument("--debug", action="store_true", help="Print debug statements.")
    args = parser.parse_args()

    main(args.audio_file, clear_cache=args.clear_cache, debug=args.debug)