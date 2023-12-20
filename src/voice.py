import os
import numpy as np
import speech_recognition as sr
import whisper
import torch

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform


class Transcriber:
    def __init__(self):
        self.phrase_time = None
        self.data_queue = Queue()
        self.recorder = sr.Recognizer()
        self.recorder.dynamic_energy_threshold = False

        self.source = sr.Microphone(sample_rate=16000)
        self.audio_model = whisper.load_model("base")
        self.record_timeout = 2
        self.phrase_timeout = 1
        self.running = True

        self.transcription = ['']

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

    def transcribe(self, mode):
        while self.running:
            try:
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
                        print(text)

                    # Clear the console to reprint the updated transcription.
                    for line in self.transcription:
                        print(line)

                    sleep(0.25)
            except KeyboardInterrupt:
                self.running = False

        print("\n\nTranscription:")
        for line in self.transcription:
            print(line)

    def process_modes(self, text, mode):
        words = text.split()
        words = [word.lower() for word in words]
        print(words)
        if mode == "move":
            if "move" in words:
                # Implement your decode_move_to_uci function here
                # decode_move_to_uci(words_after_move)
                print(words)
                self.running = False
        else:
            if any(color in words for color in self.colors):
                # Find and return the nearest color
                found_colors = [color for color in self.colors if color in words]
                if found_colors:
                    print(f"Detected color(s): {', '.join(found_colors)}")
                    # You can implement additional processing here
                    self.running = False

if __name__ == "__main__":
    transcriber = Transcriber()
    transcriber.transcribe("move")