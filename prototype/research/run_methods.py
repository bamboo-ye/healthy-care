#!/usr/bin/env python3
"""Descriptive trajectories and hypothetical base rates. No clinical model or labels."""
import argparse
import json
import math
from pathlib import Path
from run_analysis import run, validate

VERSION = 'research-methods-2026.10.18.1'


def trajectory(subjects):
    records = []
    insufficient = 0
    for subject in subjects:
        scores = sorted([o for o in subject['observations'] if isinstance(o.get('score'), (int, float))
                         and not isinstance(o['score'], bool) and math.isfinite(o['score'])
                         and 0 <= o['score'] <= 10 and o['day'] < subject['expected_days']], key=lambda o: o['day'])
        if len(scores) < 2:
            insufficient += 1
            continue
        first, last = scores[0], scores[-1]
        change = last['score'] - first['score']
        closed = subject.get('closed_day')
        records.append({'participant_id': subject['id'], 'topic': subject['topic'],
                        'first_day': first['day'] + 1, 'last_day': last['day'] + 1,
                        'first_score': first['score'], 'last_score': last['score'], 'change': change,
                        'direction': 'decrease' if change < 0 else 'increase' if change > 0 else 'same',
                        'first_source_id': first['source_id'], 'last_source_id': last['source_id'],
                        'baseline_observed': first['day'] == 0, 'score_observations': len(scores),
                        'unmeasured_score_days': subject['expected_days'] - len(scores),
                        'archived_in_window': closed is not None and closed < subject['expected_days'],
                        'recovery_event': 'not_defined'})
    return {'method_version': VERSION, 'participants': len(subjects), 'paired': len(records),
            'insufficient': insufficient, 'baseline_observed': sum(r['baseline_observed'] for r in records),
            'directions': {key: sum(r['direction'] == key for r in records) for key in ('decrease', 'same', 'increase')},
            'archived_in_window': sum(r['archived_in_window'] for r in records), 'records': records,
            'interpretation': 'First/last available self-scores only; no interpolation, causal drug effect or recovery event.'}


def base_rate(prevalence, sensitivity, specificity, population=10000):
    if not all(math.isfinite(x) and 0 <= x <= 100 for x in (prevalence, sensitivity, specificity)) or not math.isfinite(population) or population <= 0:
        raise ValueError('Assumed percentages must be between 0 and 100.')
    p, se, sp = prevalence / 100, sensitivity / 100, specificity / 100
    tp, fn = population * p * se, population * p * (1 - se)
    fp, tn = population * (1 - p) * (1 - sp), population * (1 - p) * sp
    return {'method_version': VERSION, 'assumption_only': True, 'population': population,
            'prevalence_pct': prevalence, 'sensitivity_pct': sensitivity, 'specificity_pct': specificity,
            'expected_true_positive': tp, 'expected_false_negative': fn, 'expected_false_positive': fp, 'expected_true_negative': tn,
            'ppv_pct': tp / (tp + fp) * 100 if tp + fp else None, 'alerts_per_1000': (tp + fp) / population * 1000}


def methods(data):
    validate(data)
    return {'schema_version': '1.0', 'data_origin': 'synthetic_and_hypothetical',
            'input_sha256': run(data)[0]['input_sha256'], 'execution_platform': 'local-python',
            'method_version': VERSION, 'trajectory': trajectory(data['subjects']),
            'base_rate_scenarios': [base_rate(p, 80, 95) for p in (0.1, 1, 5)],
            'limitations': ['Not clinical performance', 'Archiving is not recovery', 'Assumed prevalence, sensitivity and specificity are not measured']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', type=Path, default=Path('methods-output'))
    args = parser.parse_args()
    report = methods(json.loads(args.input.read_text(encoding='utf-8')))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'methods.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'complete', 'paired': report['trajectory']['paired'], 'hypothetical_scenarios': 3, 'output': str(args.out)}))


if __name__ == '__main__':
    main()
