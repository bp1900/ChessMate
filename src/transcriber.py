import os
import re

import numpy as np
import speech_recognition as sr
import whisper
import torch
import chess

from datetime import datetime, timedelta
from queue import Queue
import time 
from sys import platform

from openai import OpenAI

class Transcriber:
    def __init__(self):
        self.phrase_time = None
        self.data_queue = Queue()
        self.recorder = sr.Recognizer()
        self.recorder.dynamic_energy_threshold = False

        self.source = sr.Microphone(sample_rate=16000)
        self.audio_model = whisper.load_model("medium.en")
        self.record_timeout = 2
        self.phrase_timeout = 3
        self.running = True

        self.transcription = ['']

        self.transfer_queue = Queue()

        self.colors = ["blue", "green", "red", "yellow", "purple", "orange"]
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)

        self.recorder.listen_in_background(self.source, self.record_callback, phrase_time_limit=self.record_timeout)

    def record_callback(self, _, audio:sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        self.data_queue.put(data)

    def transcribe(self, mode="move"):
        print("Listening for audio...")
        while self.running:
            if not self.data_queue.empty():
                now = datetime.utcnow()
                # Pull raw recorded audio from the queue.
                if not self.data_queue.empty():
                    phrase_complete = False
                    # If enough time has passed between recordings, consider the phrase complete.
                    # Clear the current working audio buffer to start over with the new data.
                    if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout):
                        phrase_complete = True
                    # This is the last time we received new audio data from the queue.
                    self.phrase_time = now
                    
                    # Combine audio data from queue
                    audio_data = b''.join(self.data_queue.queue)
                    self.data_queue.queue.clear()
                    
                    # Convert in-ram buffer to something the model can use directly without needing a temp file.
                    # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                    # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Read the transcription.
                    result = self.audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    text = result['text'].strip()

                    # If we detected a pause between recordings, add a new item to our transcription.
                    # Otherwise edit the existing one.
                    if phrase_complete:
                        self.transcription.append(text)
                        self.process_modes(text, mode)
                    else:
                        self.transcription[-1] = text

            time.sleep(0.2)

    def process_modes(self, text, mode):
        words = text.split()
        words = [word.lower() for word in words]
        if mode == "move":
            if "move" in words:
                self.transfer_queue.put(text)
            
    def stop(self):
        self.running = False

    def start(self):
        self.running = True

def parse_uci_move(transcription):
    transcription = transcription.lower()
    # Regular expression to find structured move commands like "Move E2 to E4"
    match = re.search(r"\bmove\s+([a-h][1-8])\s+to\s+([a-h][1-8])\b", transcription, re.I)
    if match:
        from_square, to_square = match.groups()
        if from_square.lower() != to_square.lower():
            return chess.Move.from_uci(f"{from_square.lower()}{to_square.lower()}")
        
def parse_moves_from_text(text):
    # Normalize the text to lower case for consistent parsing
    text = text.lower()

    # Initialize an empty list to hold all extracted UCI move strings
    uci_moves = []

    # Use regular expressions to find all UCI move patterns in the text
    uci_move_pattern = re.compile(r"\b[a-h][1-8][a-h][1-8](?:q|r|b|n)?\b")
    uci_moves_found = uci_move_pattern.findall(text)

    # Add all found UCI moves to the list
    for move in uci_moves_found:
        uci_moves.append(move)

    return uci_moves

def convert_uci_moves_to_chess_moves(uci_moves):
    # Convert each UCI move string to a chess.Move object using the current board.
    chess_moves = []
    for uci_move in uci_moves:
        try:
            move = chess.Move.from_uci(uci_move)
            chess_moves.append(move)
        except ValueError:
            print(f"Invalid UCI move: {uci_move}")
    return chess_moves

def generate_text_from_transcription(transcription, board):
    # Check that the transcription is in UTF-8 format
    if not isinstance(transcription, str):
        transcription = transcription.decode("utf-8")

    # First, try to parse the transcription directly into UCI format
    uci_move = parse_uci_move(transcription)
    if uci_move:
        return [uci_move]  # Return the move directly if successfully parsed
    
    # If the transcription only contains move, return an empty list
    if transcription.lower() in ["move"]:
        return []
    
    # Ensure the OPENAI_API_KEY environment variable is set
    api_key = os.getenv("OPENAI_API_KEY")  # Ensure you have this set in your environment variables
    client = OpenAI(api_key=api_key)

    # Send the transcription to the OpenAI API
    prompt = f"""
    I have a transcribed move from a chess player, the board is the following:
    {board.__str__()}

    I want you to output only the move in UCI format. Take into account that the transcription is automatic so consider possible misinterpretations, so consider possible homonyms. Return the most probable move in UCI format. If there are more than one possibility, return the most probable separated by commas. Here is the move I want you to transcribe:
    {transcription}
    Output:
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a chess assistant helping to interpret spoken chess moves into UCI format."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4",
        )

        # Extract and process the generated text from the response
        generated_text = response.choices[0].message.content.strip()
        print("Using GPT-4 to generate text...")
        print(f"Generated text: {generated_text}")
        print()
        uci_moves = parse_moves_from_text(generated_text)
        possible_chess_moves = convert_uci_moves_to_chess_moves(uci_moves)
        return possible_chess_moves

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    transcriber = Transcriber()
    transcriber.transcribe()