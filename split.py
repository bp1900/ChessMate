from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

def split_audio(file_path, min_silence_len=1000, silence_thresh=-50, keep_silence=500):
    # Load the audio file
    audio = AudioSegment.from_mp3(file_path)

    # Split audio on silences
    chunks = split_on_silence(
        audio,
        # Experiment with these values for your specific use case
        min_silence_len=min_silence_len,  # Length of silence to consider it a split point
        silence_thresh=silence_thresh,    # Silence threshold
        keep_silence=keep_silence         # Keep some silence at the end of each chunk
    )

    # Create a folder to save the chunks
    output_folder = "chess_audio_chunks"
    os.makedirs(output_folder, exist_ok=True)

    # Export each chunk
    for i, chunk in enumerate(chunks):
        chunk_name = f"{output_folder}/chunk{i}.mp3"
        print(f"Exporting {chunk_name}...")
        chunk.export(chunk_name, format="mp3")

if __name__ == "__main__":
    split_audio("match.mp3")
