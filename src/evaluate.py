"""Compute PER per SNR level and write metrics JSON files."""
import argparse
import json
import os
import tempfile

import yaml


def levenshtein(ref: list, hyp: list) -> tuple[int, int, int]:
    """Return (substitutions, deletions, insertions)."""
    n, m = len(ref), len(hyp)
    # dp[i][j] = (edits, S, D, I)
    dp = [[(0, 0, 0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = (i, 0, i, 0)
    for j in range(1, m + 1):
        dp[0][j] = (j, 0, 0, j)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                sub = (dp[i - 1][j - 1][0] + 1, dp[i - 1][j - 1][1] + 1, dp[i - 1][j - 1][2], dp[i - 1][j - 1][3])
                dele = (dp[i - 1][j][0] + 1, dp[i - 1][j][1], dp[i - 1][j][2] + 1, dp[i - 1][j][3])
                ins = (dp[i][j - 1][0] + 1, dp[i][j - 1][1], dp[i][j - 1][2], dp[i][j - 1][3] + 1)
                dp[i][j] = min(sub, dele, ins, key=lambda x: x[0])
    return dp[n][m][1], dp[n][m][2], dp[n][m][3]


def compute_per(ref_phon: str, hyp_phon: str) -> tuple[float, int, int, int, int]:
    ref_tokens = ref_phon.split()
    hyp_tokens = hyp_phon.split()
    S, D, I = levenshtein(ref_tokens, hyp_tokens)
    N = len(ref_tokens)
    per = (S + D + I) / N if N > 0 else 0.0
    return per, S, D, I, N


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    with open("params.yaml") as f:
        params = yaml.safe_load(f)

    lang = args.lang
    snr_levels = params["snr_levels"]
    manifest_dir = f"data/manifests/{lang}"
    metrics_dir = f"data/metrics/{lang}"
    os.makedirs(metrics_dir, exist_ok=True)

    all_results = []

    for snr_db in snr_levels:
        in_path = os.path.join(manifest_dir, f"preds_snr{snr_db}.jsonl")

        total_S = total_D = total_I = total_N = 0
        with open(in_path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                _, S, D, I, N = compute_per(rec["ref_phon"], rec["hyp_phon"])
                total_S += S
                total_D += D
                total_I += I
                total_N += N

        per = (total_S + total_D + total_I) / total_N if total_N > 0 else 0.0
        result = {"snr_db": snr_db, "per": round(per, 4), "lang": lang}

        # Write per-SNR metric file
        per_snr_path = os.path.join(metrics_dir, f"per_snr{snr_db}.json")
        tmp_fd, tmp_path = tempfile.mkstemp(dir=metrics_dir, suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w") as fout:
                json.dump(result, fout, indent=2)
            os.replace(tmp_path, per_snr_path)
        except Exception:
            os.unlink(tmp_path)
            raise

        all_results.append(result)
        print(f"SNR {snr_db:+d} dB: PER = {per:.4f}")

    # Write summary file
    summary_path = os.path.join(metrics_dir, "per_all.json")
    tmp_fd, tmp_path = tempfile.mkstemp(dir=metrics_dir, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w") as fout:
            json.dump(all_results, fout, indent=2)
        os.replace(tmp_path, summary_path)
    except Exception:
        os.unlink(tmp_path)
        raise

    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
