"""Generate noisy audio files and noisy manifests for all SNR levels."""
import argparse
import json
import os
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from add_noise import add_noise_to_file


def utterance_seed(utt_id: str, snr_db: int, base_seed: int) -> int:
    return (base_seed + hash(utt_id + str(snr_db))) % (2**31)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    with open("params.yaml") as f:
        params = yaml.safe_load(f)

    lang = args.lang
    snr_levels = params["snr_levels"]
    noise_seed = params["noise_seed"]

    manifest_dir = f"data/manifests/{lang}"
    in_path = os.path.join(manifest_dir, "clean.jsonl")

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    for snr_db in snr_levels:
        noisy_dir = f"data/noisy/{lang}/snr_{snr_db}"
        os.makedirs(noisy_dir, exist_ok=True)

        out_manifest = os.path.join(manifest_dir, f"noisy_snr{snr_db}.jsonl")
        tmp_fd, tmp_path = tempfile.mkstemp(dir=manifest_dir, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fout:
                for rec in records:
                    utt_id = rec["utt_id"]
                    out_wav = os.path.join(noisy_dir, f"{utt_id}.flac").replace("\\", "/")
                    seed = utterance_seed(utt_id, snr_db, noise_seed)
                    add_noise_to_file(
                        input_wav=rec["wav_path"],
                        output_wav=out_wav,
                        snr_db=snr_db,
                        seed=seed,
                    )
                    noisy_rec = dict(rec)
                    noisy_rec["wav_path"] = out_wav
                    noisy_rec["snr_db"] = snr_db
                    fout.write(json.dumps(noisy_rec, ensure_ascii=False) + "\n")
            os.replace(tmp_path, out_manifest)
        except Exception:
            os.unlink(tmp_path)
            raise

        print(f"SNR {snr_db:+d} dB: {len(records)} files -> {noisy_dir}")


if __name__ == "__main__":
    main()
