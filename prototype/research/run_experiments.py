#!/usr/bin/env python3
"""Window/topic sensitivity on synthetic input; no AI or clinical effects estimated."""
import argparse
import copy
import csv
import json
from pathlib import Path
from run_analysis import run, validate


def derive(data, days, topic=None):
    result = copy.deepcopy(data)
    result['config']['window_days'] = days
    if topic:
        result['config']['topic'] = topic
        result['subjects'] = [s for s in result['subjects'] if s['topic'] == topic]
    for subject in result['subjects']:
        subject['expected_days'] = min(days, subject['expected_days'])
        subject['observations'] = [o for o in subject['observations'] if o['day'] < subject['expected_days']]
    return result


def experiment(data):
    validate(data)
    if data['config']['window_days'] != 7:
        raise ValueError('Use a seven-day frozen input; a three-day input cannot recover later days.')
    cases = [('all-7', '全部主题 · 7天', 7, None), ('all-3', '全部主题 · 3天', 3, None),
             ('skin-7', '皮肤主题 · 7天', 7, '皮肤不适')]
    rows = []
    for case_id, label, days, topic in cases:
        current = derive(data, days, topic)
        if len(current['subjects']) < 5:
            rows.append({'id': case_id, 'label': label, 'suppressed': True})
            continue
        report, _ = run(current)
        rows.append({'id': case_id, 'label': label, 'suppressed': False,
                     'input_sha256': report['input_sha256'], 'metrics': report['metrics']})
    return {'schema_version': '1.0', 'data_origin': 'synthetic', 'execution_platform': 'local-python',
            'experiment_version': 'window-sensitivity-1', 'source_input_sha256': run(data)[0]['input_sha256'],
            'conditions': rows, 'interpretation': 'Same frozen synthetic input, restricted by window/topic; not randomized and not an AI effect.',
            'sciencepal_execution': 'not_performed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--out', type=Path, default=Path('experiment-output'))
    args = parser.parse_args()
    result = experiment(json.loads(args.input.read_text(encoding='utf-8')))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'experiments.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    keys = ['id', 'label', 'participants', 'expected_patient_days', 'observed_patient_days', 'completeness_pct',
            'first_field_coverage_pct', 'longitudinal_field_coverage_pct', 'coverage_difference_pp', 'medication_candidate_participants']
    with (args.out / 'experiments.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        for row in result['conditions']:
            writer.writerow({'id': row['id'], 'label': row['label'], **row.get('metrics', {})})
    print(json.dumps({'status': 'complete', 'conditions': len(result['conditions']), 'output': str(args.out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
