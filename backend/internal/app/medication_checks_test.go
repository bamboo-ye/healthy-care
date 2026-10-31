package app

import (
	"encoding/json"
	"testing"
)

func TestMedicationChecksDistinguishActualTimeUnknownAndNonuse(t *testing.T) {
	var records []map[string]any
	if err := json.Unmarshal([]byte(`[
 {"id":"a","data":{"name":"A","state":"used","ingredients":["甲"],"used_at":"2026-10-19T08:00:00Z","amount":"2"}},
 {"id":"b","data":{"name":"B","state":"used","ingredients":["甲"],"used_at":"2026-10-19T09:00:00Z"}},
 {"id":"c","data":{"name":"C","state":"not_used","ingredients":["甲"]}},
 {"id":"d","data":{"name":"D","state":"used","ingredients":["甲"]}}
 ]`), &records); err != nil {
		t.Fatal(err)
	}
	checks := medicationChecks(records)
	overlaps, units := 0, 0
	for _, c := range checks {
		switch c["rule"] {
		case "same_day_ingredient":
			overlaps++
			if len(c["record_ids"].([]string)) != 2 {
				t.Fatal("Unknown dates and explicit nonuse must not become overlaps")
			}
		case "unit_unknown":
			units++
		}
	}
	if overlaps != 1 || units != 1 {
		t.Fatalf("checks=%v", checks)
	}
}

func TestMultipleEpisodesDoNotInflateParticipants(t *testing.T) {
	in, err := syntheticData(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 7})
	if err != nil {
		t.Fatal(err)
	}
	in.Subjects = in.Subjects[:2]
	in.Subjects[0].ParticipantID = "P1"
	in.Subjects[1].ParticipantID = "P1"
	in.Subjects[0].ExpectedDays = 1
	in.Subjects[1].ExpectedDays = 1
	in.Subjects[0].DayKeys = []string{"calendar-day-a"}
	in.Subjects[1].DayKeys = []string{"calendar-day-a"}
	in.Subjects[0].Observations = nil
	in.Subjects[1].Observations = nil
	m := analyze(in)["metrics"].(map[string]any)
	if m["events"] != 2 || m["participants"] != 1 || m["expected_patient_days"] != 1 {
		t.Fatalf("%v", m)
	}
}

func TestConfirmedInitialFieldsRemainAvailableWithoutFollowup(t *testing.T) {
	in := researchInput{DataOrigin: "consented", Subjects: []researchSubject{{ID: "E1", ExpectedDays: 1, FirstFields: map[string]bool{"chief": true, "onset": false}}}}
	metrics := analyze(in)["metrics"].(map[string]any)
	if metrics["longitudinal_field_coverage_pct"] != float64(20) || metrics["observed_patient_days"] != 0 {
		t.Fatalf("Initial facts must remain available without inventing a followup: %v", metrics)
	}
}
