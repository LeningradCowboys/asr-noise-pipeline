"""Bootstrap: raw audio + .trans.txt -> clean_raw.jsonl manifest."""
import argparse
import glob
import hashlib
import json
import os
import tempfile

import soundfile as sf


def md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    data_dir = f"data/raw/{args.lang}/wav"
    trans_files = sorted(glob.glob(f"{data_dir}/*.trans.txt"))
    if not trans_files:
        raise FileNotFoundError(f"No *.trans.txt files found in {data_dir}")

    # Parse transcription files: "STEM TEXT"
    transcripts = {}
    for trans_file in trans_files:
        with open(trans_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                stem, text = line.split(None, 1)
                transcripts[stem] = text

    # Detect audio/transcript mismatches
    flac_files = sorted(glob.glob(f"{data_dir}/*.flac"))
    audio_stems = {os.path.splitext(os.path.basename(f))[0] for f in flac_files}
    trans_stems = set(transcripts)

    orphan_audio = audio_stems - trans_stems   # flac with no transcript
    orphan_trans = trans_stems - audio_stems   # transcript entry with no flac

    if orphan_audio:
        print(f"WARNING: {len(orphan_audio)} audio file(s) have no transcript — skipping:")
        for s in sorted(orphan_audio):
            print(f"  {s}.flac")
    if orphan_trans:
        print(f"WARNING: {len(orphan_trans)} transcript entry(ies) have no audio — skipping:")
        for s in sorted(orphan_trans):
            print(f"  {s}")

    valid_stems = trans_stems & audio_stems

    out_dir = f"data/manifests/{args.lang}"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "clean_raw.jsonl")

    tmp_fd, tmp_path = tempfile.mkstemp(dir=out_dir, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fout:
            for stem in sorted(valid_stems):
                ref_text = transcripts[stem]
                wav_path = os.path.join(data_dir, f"{stem}.flac").replace("\\", "/")
                info = sf.info(wav_path)
                record = {
                    "utt_id": f"{args.lang}_{stem}",
                    "lang": args.lang,
                    "wav_path": wav_path,
                    "ref_text": ref_text,
                    "ref_phon": None,
                    "sr": info.samplerate,
                    "duration_s": info.duration,
                    "audio_md5": md5(wav_path),
                    "snr_db": None,
                }
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.replace(tmp_path, out_path)
    except Exception:
        os.unlink(tmp_path)
        raise

    print(f"Wrote {len(valid_stems)} utterances to {out_path}")


if __name__ == "__main__":
    main()
