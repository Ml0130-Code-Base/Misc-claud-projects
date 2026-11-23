import copy
import tempfile
import unittest
from pathlib import Path

from metro_maps.analyze import analyze_file, render_report
from metro_maps.fetch import save_snapshot
from metro_maps.model import from_payload
from tests.fixture_data import make_payload


def section(text: str, title: str) -> str:
    start = text.index(f"## {title}\n")
    return text[start:].split("\n## ", 1)[0]


class PunchListTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = render_report(from_payload(make_payload()))

    # --- spacing --------------------------------------------------------------
    def test_tram_too_close(self):
        self.assertIn("- `Alpha` -> `Beta` on `Main Tram`: 171 m (TRAM min 250 m)", section(self.report, "MERGE"))

    def test_regional_gap(self):
        self.assertIn("- infill between `Union Station` and `Far Town` on `R Line`: gap 18.6 km (REGIONAL max 15.0 km)",
                      section(self.report, "CREATE"))

    def test_ferry_skipped(self):
        self.assertNotIn("on `Ferry`", self.report)
        self.assertNotIn("FERRY", section(self.report, "CREATE"))

    def test_waypoints_never_reported(self):
        self.assertNotIn("(blank name)", self.report)

    # --- drafts ---------------------------------------------------------------
    def test_concept_line_is_draft_only(self):
        self.assertIn("- line `Concept 1`: draft line (TRAM, 2 stations)", section(self.report, "HOUSEKEEPING"))
        for title in ("DELETE", "MERGE", "CREATE"):
            body = section(self.report, title)
            self.assertNotIn("Concept", body)
            self.assertNotIn("Airport", body)

    def test_five_concept_lines(self):
        p = make_payload()
        m = p["props"]["pageProps"]["fullSystem"]["map"]
        base = m["lines"]["l5"]
        for i in range(2, 6):
            m["lines"][f"c{i}"] = dict(copy.deepcopy(base), id=f"c{i}", name=f"Concept {i}")
        hk = section(render_report(from_payload(p)), "HOUSEKEEPING")
        self.assertEqual(hk.count("draft line"), 5)

    # --- orphans and duplicates ----------------------------------------------
    def test_orphan(self):
        body = section(self.report, "DELETE")
        self.assertIn("- `Lonely Stop`: on no line; nearest line `A Line` at 745 m", body)
        self.assertEqual(body.count("\n- "), 1)

    def test_near_duplicate(self):
        self.assertIn("- `Union Station` (`R Line`, `Stub Line`) x `Union Station` (`A Line`, "
                      "`D Line  - North Extension`): same name, 37 m apart", section(self.report, "MERGE"))

    def test_same_name_far_apart(self):
        self.assertIn("- `Far Town` (`Ferry`) x `Far Town` (`R Line`): same name, 15.8 km apart",
                      section(self.report, "MERGE"))

    def test_same_line_pairs_not_duplicates(self):
        merge = section(self.report, "MERGE")
        dupes = merge.split("### Stops closer")[0]
        self.assertNotIn("County Admin. Ctr.", dupes)  # same name, both on Mystery Line
        self.assertNotIn("`Alpha`", dupes)  # 171 m, both on Main Tram: spacing item only
        self.assertIn("`Alpha` -> `Beta` on `Main Tram`", merge)

    def test_placeholder_names_not_name_matched(self):
        p = make_payload()
        st = p["props"]["pageProps"]["fullSystem"]["map"]["stations"]
        st["s10"]["name"] = "Station Name"  # A Line
        st["s14"]["name"] = "Station Name"  # Ferry, ~7 km away
        r = render_report(from_payload(p))
        self.assertNotIn("`Station Name` (`A Line`) x `Station Name`", r)
        self.assertNotIn("`Station Name` (`Ferry`) x `Station Name`", r)
        self.assertEqual(section(r, "HOUSEKEEPING").count("- station `Station Name`: placeholder name"), 2)

    def test_placeholder_close_to_other_line_is_duplicate(self):
        p = make_payload()
        st = p["props"]["pageProps"]["fullSystem"]["map"]["stations"]
        st["s7"]["name"] = "Station Name"  # 37 m from Union Station on other lines
        self.assertIn("`Station Name` (`A Line`, `D Line  - North Extension`) x `Union Station` (`R Line`, "
                      "`Stub Line`): 37 m apart", section(render_report(from_payload(p)), "MERGE"))

    def test_close_pair_without_same_name(self):
        p = make_payload()
        p["props"]["pageProps"]["fullSystem"]["map"]["stations"]["s7"]["name"] = "Union Station East"
        self.assertIn("`Union Station` (`R Line`, `Stub Line`) x `Union Station East` (`A Line`, "
                      "`D Line  - North Extension`): 37 m apart", section(render_report(from_payload(p)), "MERGE"))

    # --- housekeeping ---------------------------------------------------------
    def test_housekeeping_items(self):
        hk = section(self.report, "HOUSEKEEPING")
        for expected in (
            "- station `Station 12`: placeholder name (on `A Line` between `Alpha` and (end))",
            "- line `Mystery Line`: no mode set",
            "- line `D Line  - North Extension`: leading, trailing or doubled space in name",
            "- line group `Proposed  Services`: leading, trailing or doubled space in label",
            "- line `Stub Line`: only 1 station(s)",
            "- line `Shuttle Tram`: visits `Santa Fe Depot` 2 times",
        ):
            self.assertIn(expected, hk)

    def test_loop_closure_not_flagged(self):
        self.assertNotIn("Loop Tram", self.report)

    # --- report format --------------------------------------------------------
    def test_section_order_and_header(self):
        r = self.report
        self.assertTrue(r.startswith("# Punch list: Fixture Fantasy Map\n"))
        self.assertIn("TRAM 250 m-1.5 km", r)
        idx = [r.index(f"## {s}\n") for s in ("DELETE", "MERGE", "CREATE", "HOUSEKEEPING")]
        self.assertEqual(idx, sorted(idx))

    def test_empty_section(self):
        p = make_payload()
        del p["props"]["pageProps"]["fullSystem"]["map"]["stations"]["s6"]
        self.assertIn("Nothing found.", section(render_report(from_payload(p)), "DELETE"))

    def test_en_dash_exact(self):
        p = make_payload()
        p["props"]["pageProps"]["fullSystem"]["map"]["stations"]["s6"]["name"] = "San Diego–Old Town"
        r = render_report(from_payload(p))
        self.assertIn("`San Diego–Old Town`", r)
        self.assertNotIn("San Diego-Old Town", r)

    def test_byte_identical_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snap_path, _ = save_snapshot(root, "fixture", make_payload(42), 42)
            out1, text1 = analyze_file(snap_path, root, "fixture")
            bytes1 = out1.read_bytes()
            out2, text2 = analyze_file(snap_path, root, "fixture")
            self.assertEqual(out1, out2)
            self.assertEqual(out1.name, "42.md")
            self.assertEqual(bytes1, out2.read_bytes())
            self.assertEqual(text1, text2)


if __name__ == "__main__":
    unittest.main()
