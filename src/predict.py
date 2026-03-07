"""Run facebook/wav2vec2-lv-60-espeak-cv-ft on noisy manifests; outputs preds_snr*.jsonl."""
import argparse
import json
import os
import tempfile

import numpy as np
import soundfile as sf
import torch
import yaml
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

MODEL_ID = "facebook/wav2vec2-lv-60-espeak-cv-ft"
TARGET_SR = 16000

def load_audio_16k(wav_path: str) -> np.ndarray:
    signal, sr = sf.read(wav_path)
    if signal.ndim != 1:
        signal = signal.mean(axis=1)
    if sr != TARGET_SR:
        # Resample using linear interpolation (avoids librosa dependency)
        import librosa
        signal = librosa.resample(signal, orig_sr=sr, target_sr=TARGET_SR)
    return signal.astype(np.float32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    with open("params.yaml") as f:
        params = yaml.safe_load(f)

    lang = args.lang
    snr_levels = params["snr_levels"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Loading model {MODEL_ID} on {device}...")
    processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID).to(device)
    model.eval()

    manifest_dir = f"data/manifests/{lang}"

    for snr_db in snr_levels:
        in_path = os.path.join(manifest_dir, f"noisy_snr{snr_db}.jsonl")
        out_path = os.path.join(manifest_dir, f"preds_snr{snr_db}.jsonl")

        records = []
        with open(in_path, encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))

        tmp_fd, tmp_path = tempfile.mkstemp(dir=manifest_dir, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fout:
                for rec in records:
                    signal = load_audio_16k(rec["wav_path"])
                    inputs = processor(
                        signal,
                        sampling_rate=TARGET_SR,
                        return_tensors="pt",
                        padding=True,
                    )
                    input_values = inputs.input_values.to(device)
                    with torch.no_grad():
                        logits = model(input_values).logits
                    pred_ids = torch.argmax(logits, dim=-1)
                    hyp_phon = processor.batch_decode(pred_ids)[0]
                    rec["hyp_phon"] = hyp_phon
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            os.replace(tmp_path, out_path)
        except Exception:
            os.unlink(tmp_path)
            raise

        print(f"SNR {snr_db:+d} dB: predicted {len(records)} utterances -> {out_path}")


if __name__ == "__main__":
    main()
