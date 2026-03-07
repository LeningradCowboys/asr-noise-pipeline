"""Convert ref_text -> ref_phon using espeak-ng; outputs clean.jsonl."""
import argparse
import json
import os
import subprocess
import tempfile

import yaml


def text_to_phonemes(text: str, lang: str) -> str:
    result = subprocess.run(
        ["espeak-ng", "--ipa", "-q", "-v", lang, text],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # Strip stress marks and normalize whitespace
    ipa = result.stdout.strip()
    ipa = ipa.replace("ˈ", "").replace("ˌ", "").replace("\n", " ")
    # Collapse multiple spaces
    ipa = " ".join(ipa.split())
    return ipa


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    with open("params.yaml") as f:
        params = yaml.safe_load(f)

    lang = args.lang
    in_path = f"data/manifests/{lang}/clean_raw.jsonl"
    out_dir = f"data/manifests/{lang}"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "clean.jsonl")

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    tmp_fd, tmp_path = tempfile.mkstemp(dir=out_dir, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fout:
            for rec in records:
                rec["ref_phon"] = text_to_phonemes(rec["ref_text"], lang)
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp_path, out_path)
    except Exception:
        os.unlink(tmp_path)
        raise

    print(f"Added phonemes for {len(records)} utterances -> {out_path}")


if __name__ == "__main__":
    main()
