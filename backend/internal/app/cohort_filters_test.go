package app

import (
	"testing"
	"time"
)

func TestAdvancedCohortFiltersFreezeSelectionAndDenominators(t *testing.T) {
	base, err := syntheticData(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 7})
	if err != nil {
		t.Fatal(err)
	}
	var product string
	for _, s := range base.Subjects {
		for _, o := range s.Observations {
			if len(o.Products) > 0 {
				product = o.Products[0].ID
				break
			}
		}
		if product != "" {
			break
		}
	}
	filtered, err := syntheticData(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 3, ProductID: product})
	if err != nil {
		t.Fatal(err)
	}
	if filtered.Selection == nil || filtered.Selection.Eligible != len(base.Subjects) || len(filtered.Subjects) == 0 || len(filtered.Subjects) >= len(base.Subjects) {
		t.Fatal("Product selection or exclusion evidence missing")
	}
	for _, s := range filtered.Subjects {
		if cohortExclusion(s, researchDefinition{Topic: "all", Category: "all", ProductID: product}, time.Time{}) != "" {
			t.Fatal("An included episode lacks the product")
		}
	}
	none, err := syntheticData(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 7, StartFrom: "2099-01-01"})
	if err != nil || len(none.Subjects) != 0 {
		t.Fatal("Date filter did not exclude out-of-range episodes")
	}
	if validateDefinition(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 7, StartFrom: "2026-10-19", StartTo: "2026-01-01"}) == nil {
		t.Fatal("Reversed dates accepted")
	}
}
func TestResearchHistoryWindowKeepsNegationAndEvidence(t *testing.T) {
	s := researchSubject{ID: "E1", ExpectedDays: 7, Observations: []researchObservation{{Day: 0, SourceID: "source-a", Symptoms: []map[string]string{{"code": "thirst", "assertion": "present"}, {"code": "urination", "assertion": "present"}, {"code": "weight_loss", "assertion": "present"}}}}}
	in := researchInput{Subjects: []researchSubject{s}}
	if got := researchHistory(in); len(got) != 1 || len(got[0]["evidence"].([]map[string]any)) != 3 {
		t.Fatal("Explicit window facts were not linked")
	}
	in.Subjects[0].Observations = append(in.Subjects[0].Observations, researchObservation{Day: 1, SourceID: "source-b", Symptoms: []map[string]string{{"code": "thirst", "assertion": "absent"}}})
	if len(researchHistory(in)) != 0 {
		t.Fatal("A later denial must clear the descriptive match")
	}
}
