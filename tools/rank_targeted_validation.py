#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True)
    parser.add_argument('--output-dir', default=None)
    args = parser.parse_args()

    summary = Path(args.summary)
    out = Path(args.output_dir) if args.output_dir else summary.parent
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(summary)
    for col in ['mean_abs_motor_delta', 'l2_motor_delta', 'top10_motor_shift']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    ranked = df.sort_values('mean_abs_motor_delta', ascending=False)
    ranked.to_csv(out / 'ranked_targeted_validation.csv', index=False)

    lines = ['Targeted validation ranked summary', '']
    for _, row in ranked.iterrows():
        lines.append(f"{row.get('input_context')} to {row.get('perturbation_target')}: mean_abs={row.get('mean_abs_motor_delta')}, l2={row.get('l2_motor_delta')}, top10={row.get('top10_motor_shift')}")
    (out / 'targeted_validation_readable_summary.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(out / 'ranked_targeted_validation.csv')
    print(out / 'targeted_validation_readable_summary.txt')


if __name__ == '__main__':
    main()
