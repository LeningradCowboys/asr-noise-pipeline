"""Generate PER-vs-SNR curve per language and a cross-language mean curve."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml


def main():
    with open("params.yaml") as f:
        params = yaml.safe_load(f)

    languages = params["languages"]
    os.makedirs("data/plots", exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    all_snrs = None
    mean_per = None

    for lang in languages:
        summary_path = f"data/metrics/{lang}/per_all.json"
        with open(summary_path) as f:
            results = json.load(f)

        results_sorted = sorted(results, key=lambda x: x["snr_db"])
        snrs = [r["snr_db"] for r in results_sorted]
        pers = [r["per"] for r in results_sorted]

        ax.plot(snrs, pers, marker="o", label=lang)

        if all_snrs is None:
            all_snrs = snrs
            mean_per = list(pers)
        else:
            for i, p in enumerate(pers):
                mean_per[i] += p

    if len(languages) > 1 and all_snrs is not None:
        mean_per = [p / len(languages) for p in mean_per]
        ax.plot(all_snrs, mean_per, marker="s", linestyle="--", color="black", label="mean")

    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel("PER")
    ax.set_title("PER vs. SNR")
    ax.legend()
    ax.grid(True, alpha=0.3)

    langs_suffix = "-".join(languages)
    out_path = f"data/plots/per_vs_snr_{langs_suffix}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Plot saved to {out_path}")


if __name__ == "__main__":
    main()
