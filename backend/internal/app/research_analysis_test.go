package app

import (
	"bytes"
	"encoding/json"
	"image"
	"image/color"
	"image/jpeg"
	"testing"
)

func TestReferenceAnalysisAndWindows(t *testing.T) {
	for _, tc := range []struct {
		topic                         string
		window, n, expected, observed int
		complete                      float64
	}{
		{"all", 7, 48, 324, 267, 82.4}, {"all", 3, 48, 144, 129, 89.6}, {"皮肤不适", 7, 8, 54, 43, 79.6}, {"皮肤不适", 3, 8, 24, 21, 87.5},
	} {
		t.Run(tc.topic+string(rune(tc.window+'0')), func(t *testing.T) {
			in, err := syntheticData(researchDefinition{Source: "synthetic", Topic: tc.topic, Category: "all", Window: tc.window})
			if err != nil {
				t.Fatal(err)
			}
			r := analyze(in)
			m := r["metrics"].(map[string]any)
			if m["participants"] != tc.n || m["expected_patient_days"] != tc.expected || m["observed_patient_days"] != tc.observed || m["completeness_pct"] != tc.complete {
				t.Fatalf("unexpected metrics: %#v", m)
			}
			if m["missing_patient_days"] != tc.expected-tc.observed {
				t.Fatal("Missing is distinct from documented non-use")
			}
		})
	}
}
func TestInputHashMatchesPythonContract(t *testing.T) {
	in, err := syntheticData(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 7})
	if err != nil {
		t.Fatal(err)
	}
	if got := digest(in); got != "c4fae3592e5dd5703019372cfa775651a1529d49e565216e8facf34cf4fb30eb" {
		t.Fatalf("canonical hash differs from independent Python reference: %s", got)
	}
}
func TestNoDataDoesNotBecomeZeroPercent(t *testing.T) {
	in, _ := syntheticData(researchDefinition{Source: "synthetic", Topic: "nonexistent", Category: "all", Window: 7})
	m := analyze(in)["metrics"].(map[string]any)
	if m["completeness_pct"] != nil {
		t.Fatal("empty data must not imply complete or disease-free")
	}
}
func TestCandidateCounts(t *testing.T) {
	in, _ := syntheticData(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 7})
	r := analyze(in)
	for rule, count := range r["rules"].(map[string]int) {
		if count != 8 {
			t.Fatalf("rule %s got %d, want 8", rule, count)
		}
	}
	if len(r["candidates"].([]researchCandidate)) != 32 {
		t.Fatal("unexpected candidate count")
	}
}
func TestImageValidationAndReencoding(t *testing.T) {
	im := image.NewRGBA(image.Rect(0, 0, 40, 20))
	im.Set(0, 0, color.RGBA{R: 255, A: 255})
	var b bytes.Buffer
	_ = jpeg.Encode(&b, im, nil)
	data, kind, w, h, err := normalizeImage(b.Bytes())
	if err != nil || kind != "image/jpeg" || w != 40 || h != 20 || len(data) == 0 {
		t.Fatal("valid image failed", err)
	}
	if _, _, _, _, err = normalizeImage([]byte("<script>not an image</script>")); err == nil {
		t.Fatal("active content must not be accepted as an image")
	}
}
func TestCSVFormulaProtection(t *testing.T) {
	for _, v := range []string{"=1+1", "@SUM(A1)", "-1", "+abc"} {
		if csvSafe(v)[0] != '\'' {
			t.Fatal("formula injection is not escaped")
		}
	}
	if csvSafe("皮肤不适") != "皮肤不适" {
		t.Fatal("ordinary text changed")
	}
}
func TestJSONContractFields(t *testing.T) {
	in, _ := syntheticData(researchDefinition{Source: "synthetic", Topic: "all", Category: "all", Window: 7})
	b := canonical(in)
	var d map[string]any
	if err := json.Unmarshal(b, &d); err != nil {
		t.Fatal(err)
	}
	if d["data_origin"] != "synthetic" || d["schema_version"] != "1.0" {
		t.Fatal("source/version metadata lost")
	}
}
