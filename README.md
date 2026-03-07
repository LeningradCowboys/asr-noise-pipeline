# asr-noise-pipeline

Effect of additive Gaussian noise on wav2vec2 phoneme recognition across four languages.

## Prerequisites

These must be installed at the system level before running the pipeline.

**Python >= 3.10**

**espeak-ng** (used by `src/add_phonemes.py` to generate phoneme transcripts):

> **Windows note:** Download the installer from the [espeak-ng releases page](https://github.com/espeak-ng/espeak-ng/releases). The Windows installer does not always add `espeak-ng` to `PATH`
> automatically. After installing, verify with `espeak-ng --version` in a new terminal.
> If the command is not found, add the install directory (e.g.
> `C:\Program Files\eSpeak NG`) to your `PATH` manually.

**libsndfile** (required by the `soundfile` Python package):

| OS | Command |
|----|---------|
| Ubuntu/Debian | `sudo apt install libsndfile1` |
| macOS | `brew install libsndfile` |
| Windows | Bundled in the `soundfile` wheel — no action needed |

Dependencies declaration is in `pyproject.toml` and the actual resolution is in `uv.lock`.

## Data

Pull the raw audio tracked by DVC:

```bash
dvc pull data.raw.dvc
```
If you need more audio files, https://www.openslr.org/12 is for English, and https://www.openslr.org/94/ is for other languages. Download the files you need, save it to data/raw/{language code}/wav. Name the {language code} folder using ISO 639-1 Code (e.g., data/raw/fr/wav)

## Run

Reproduce the full pipeline:

```bash
dvc repro
```

## Inspect results

```bash
dvc metrics show   # WER / PER numbers
dvc plots show     # noise-level vs. error-rate curves
```

Plot for English, Polish, Portuguese, and Italien looks like:

<img width="500" alt="per_vs_snr_en-pl-pt-it" src="https://github.com/user-attachments/assets/b7f77da1-0030-4a60-a31b-b4a54e637588" />

The data folder originally has 5 subfolders
  data/
    manifests/
    metrics
    noisy
    plots/
    raw/
Raw data are saved on Google Drive. Other four folders are reproducible, which should not be commited as they are fully reproducible. I copy `manifests`, `metrics`, and `plots` to the `results` folder for reviewing convenience. 
