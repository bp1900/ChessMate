import os
import torch
import whisper
import torchaudio
import pandas as pd

# https://github.com/ggerganov/whisper.cpp/tree/master/examples/command

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

class LibriSpeech(torch.utils.data.Dataset):
    def __init__(self, split="test-clean", device=DEVICE, limit=None):
        self.dataset = torchaudio.datasets.LIBRISPEECH(
            root=os.path.expanduser("~/.cache"),
            url=split,
            download=True,
        )
        self.device = device
        if limit:
            self.dataset = self.dataset

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, item):
        audio, sample_rate, text, _, _, _ = self.dataset[item]
        assert sample_rate == 16000
        audio = whisper.pad_or_trim(audio.flatten()).to(self.device)
        mel = whisper.log_mel_spectrogram(audio)
        return (mel, text)

class VoiceRecognition:
    def __init__(self, model_name="base.en"):
        self.model = whisper.load_model(model_name)
        print(
            f"Model is {'multilingual' if self.model.is_multilingual else 'English-only'} "
            f"and has {sum(p.numel() for p in self.model.parameters()):,} parameters."
        )

    def predict(self, loader, language="en", without_timestamps=True):
        options = whisper.DecodingOptions(language=language, without_timestamps=without_timestamps)
        hypotheses, references = [], []
        for mels, texts in loader:
            results = self.model.decode(mels, options)
            hypotheses.extend([result.text for result in results])
            references.extend(texts)
        return pd.DataFrame(dict(hypothesis=hypotheses, reference=references))

def create_loader(split="test-clean", limit=None):
    dataset = LibriSpeech(split, limit=limit)
    return torch.utils.data.DataLoader(dataset, batch_size=16)

def main():
    # Limit the dataset to 10 samples for testing
    loader = create_loader(limit=10)
    recognizer = VoiceRecognition()
    data = recognizer.predict(loader)
    print(data)

if __name__ == "__main__":
    main()
