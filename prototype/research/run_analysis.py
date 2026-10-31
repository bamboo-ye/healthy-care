#!/usr/bin/env python3
"""Reference analysis for the synthetic input exported by the research prototype.

No network, model, or external packages. Running this file on SciencePal is the
user's platform execution step; --platform records a declaration, not attestation.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlparse

VERSION = "research-2026.10.18.2"
DATA_VERSION = "synthetic-light-illness-v2"
RULE_VERSION = "medication-context-1"
KNOWLEDGE_VERSION = "symptom-pattern-demo-1"
COMMON = ("chief", "onset", "severity", "impact", "medicine")


def percentage(numerator, denominator):
    return math.floor(numerator * 1000 / denominator + 0.5) / 10 if denominator else None


def validate(data):
    if data.get("schema_version") != "1.0" or data.get("data_origin") != "synthetic":
        raise ValueError("This reference workflow accepts schema 1.0 synthetic data only.")
    if data.get("data_version") != DATA_VERSION:
        raise ValueError("Data version does not match the reference analysis.")
    if data.get("rule_version") != RULE_VERSION or data.get("knowledge_version") != KNOWLEDGE_VERSION:
        raise ValueError("Rule or knowledge version does not match.")
    subjects = data["subjects"]
    if not 5 <= len(subjects) <= 60:
        raise ValueError("This demonstration requires 5 to 60 authorized synthetic subjects.")
    ids = set()
    for subject in subjects:
        if subject["id"] in ids:
            raise ValueError("Duplicate participant.")
        ids.add(subject["id"])
        if not subject.get("research_consent"):
            raise ValueError("Unauthorized subject.")
        expected = subject["expected_days"]
        if not isinstance(expected, int) or not 1 <= expected <= data["config"]["window_days"]:
            raise ValueError("Invalid expected-day denominator.")
        days = set()
        for obs in subject["observations"]:
            day = obs["day"]
            if day in days or not 0 <= day < expected:
                raise ValueError("Duplicate or out-of-window patient-day.")
            days.add(day)
            if obs["use"] not in ("used", "not_used", "unknown"):
                raise ValueError("Unknown medication reporting status.")
            if not obs.get("source_id"):
                raise ValueError("Observation lacks source evidence.")


def medication_candidates(subjects):
    output = []
    for subject in subjects:
        found = {}

        def add(rule, obs, facts):
            if rule not in found:
                found[rule] = {
                    "participant_id": subject["id"], "rule": rule,
                    "topic": subject["topic"], "date": obs["date"],
                    "source_id": obs.get("medication_evidence", {}).get("source_id", obs["source_id"]), "facts": facts
                }

        for obs in subject["observations"]:
            if obs["use"] != "used":
                continue
            ingredient_products = {}
            for product in obs["products"]:
                for component in set(product["ingredients"]):
                    ingredient_products.setdefault(component, set()).add(product["id"])
                if not product["ingredients"]:
                    add("ingredient", obs, [product["name"], "未记录可归一的成分"])
                if product["kind"] == "antibiotic" and not product.get("basis"):
                    add("antibiotic", obs, [product["name"], "使用依据未记录"])
                if product["kind"] == "topical_steroid" and (
                    not product.get("strength") or not product.get("site")
                ):
                    add("steroid", obs, [product["name"],
                        "强度：" + (product.get("strength") or "未知"),
                        "部位：" + (product.get("site") or "未知")])
            for ingredient, product_ids in ingredient_products.items():
                if len(product_ids) > 1:
                    add("duplicate", obs, [ingredient, "同日不同产品数：" + str(len(product_ids))])
        output.extend(found.values())
    return output


def calculate(data):
    subjects = data["subjects"]
    expected = sum(s["expected_days"] for s in subjects)
    observations = [o for s in subjects for o in s["observations"]]
    use = {"used": 0, "not_used": 0, "unknown": 0, "missing": expected - len(observations)}
    for obs in observations:
        use[obs["use"]] += 1
    first = sum(sum(bool(s["first_fields"][f]) for f in COMMON) for s in subjects)
    full = sum(sum(any(o["known"][f] for o in s["observations"]) for f in COMMON) for s in subjects)
    slots = len(subjects) * len(COMMON)
    candidates = medication_candidates(subjects)
    metrics = {
        "participants": len(subjects),
        "expected_patient_days": expected,
        "observed_patient_days": len(observations),
        "completeness_pct": percentage(len(observations), expected),
        "first_field_coverage_pct": percentage(first, slots),
        "longitudinal_field_coverage_pct": percentage(full, slots),
        "coverage_difference_pp": percentage(full - first, slots),
        "medication_candidate_participants": len({c["participant_id"] for c in candidates}),
        "medication_candidate_count": len(candidates),
        "documented_use_days": use["used"],
        "documented_nonuse_days": use["not_used"],
        "unknown_use_days": use["unknown"],
        "missing_patient_days": use["missing"],
        "lower_use_pct": percentage(use["used"], expected),
        "upper_use_pct": percentage(use["used"] + use["unknown"] + use["missing"], expected),
    }
    return metrics, candidates


def run(data, platform="local-python", run_url=None):
    validate(data)
    if platform == "SciencePal":
        url = urlparse(run_url or "")
        if url.scheme != "https" or not (url.hostname == "sciencepal.ai" or (url.hostname or "").endswith(".sciencepal.ai")):
            raise ValueError("SciencePal declaration requires an actual HTTPS sciencepal.ai run URL.")
    # Key-sorted JSON, preserving arrays, for this integer/string/boolean fixture schema.
    normalized = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    metrics, candidates = calculate(data)
    report = {
        "schema_version": "1.0",
        "run_id": "analysis-20261018-" + digest[:10],
        "platform": platform,
        "run_url": run_url,
        "data_origin": "synthetic",
        "data_version": DATA_VERSION,
        "input_sha256": digest,
        "code_version": VERSION,
        "rule_version": RULE_VERSION,
        "knowledge_version": KNOWLEDGE_VERSION,
        "config": data["config"],
        "metrics": metrics,
        "limitations": [
            "合成边界样例，不代表真实人群频率",
            "字段覆盖改善不是诊断或疗效改善",
            "候选不是滥用、药物不良反应或耐药结论",
            "自评分不是经验证的临床结局量表",
        ],
        "artifacts": ["input.json", "report.json", "quality.csv", "medication_candidates.csv", "patient_days.csv"],
        "provenance": "self-declared-platform",
    }
    return report, candidates


def write_csv(path, headers, records):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--platform", choices=("local-python", "SciencePal"), default="local-python")
    parser.add_argument("--run-url")
    parser.add_argument("--out", type=Path, default=Path("analysis-output"))
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    report, candidates = run(data, args.platform, args.run_url)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(args.out / "medication_candidates.csv",
        ["data_origin", "participant_id", "rule", "topic", "date", "source_id", "facts"],
        [{"data_origin": "synthetic", **c, "facts": "；".join(c["facts"])} for c in candidates])
    quality = []
    for field in data["field_definitions"]:
        key = field["id"]
        quality.append({
            "data_origin": "synthetic", "field": key,
            "comparable": field.get("comparable", True),
            "first_available": sum(bool(s["first_fields"][key]) for s in data["subjects"]) if field.get("comparable", True) else "",
            "window_available": sum(any(o["known"][key] for o in s["observations"]) for s in data["subjects"]),
            "participants": len(data["subjects"]),
        })
    write_csv(args.out / "quality.csv", list(quality[0]), quality)
    patient_days = []
    for subject in data["subjects"]:
        by_day = {o["day"]: o for o in subject["observations"]}
        for day in range(subject["expected_days"]):
            obs = by_day.get(day)
            patient_days.append({
                "data_origin": "synthetic", "participant_id": subject["id"], "topic": subject["topic"],
                "patient_day": day + 1, "record_status": "recorded" if obs else "missing",
                "medication_status": obs["use"] if obs else "missing",
                "source_id": obs["source_id"] if obs else "",
            })
    write_csv(args.out / "patient_days.csv", list(patient_days[0]), patient_days)
    print(json.dumps({"status": "complete", "platform": args.platform,
        "participants": report["metrics"]["participants"], "input_sha256": report["input_sha256"],
        "output": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
