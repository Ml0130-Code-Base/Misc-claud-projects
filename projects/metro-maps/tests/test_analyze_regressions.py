"""Cases found running against the live Denver and San Diego maps."""

import unittest

from metro_maps.analyze import render_report
from metro_maps.model import from_payload
from tests.fixture_data import make_payload


def section(text: str, title: str) -> str:
    start = text.index(f"## {title}\n")
    return text[start:].split("\n## ", 1)[0]


class RegressionTest(unittest.TestCase):
    def setUp(self):
        self.p = make_payload()
        self.m = self.p["props"]["pageProps"]["fullSystem"]["map"]

    def report(self):
        return render_report(from_payload(self.p))

    def test_station_name_placeholder(self):
        self.m["stations"]["s10"]["name"] = "Station Name"
        self.assertIn("- station `Station Name`: placeholder name", section(self.report(), "HOUSEKEEPING"))

    def test_shared_segment_each_mode_own_limit(self):
        # A REGIONAL line shares the 171 m Alpha-Beta segment with Main Tram (TRAM).
        self.m["lines"]["l11"] = {"id": "l11", "name": "Z Commuter", "mode": "REGIONAL", "stationIds": ["s2", "s3"]}
        merge = section(self.report(), "MERGE")
        self.assertIn("on `Main Tram`: 171 m (TRAM min 250 m)", merge)
        self.assertIn("on `Z Commuter`: 171 m (REGIONAL min 1.5 km)", merge)

    def test_shared_segment_same_mode_one_item(self):
        self.m["lines"]["l11"] = {"id": "l11", "name": "Second Tram", "mode": "TRAM", "stationIds": ["s3", "s2"]}
        merge = section(self.report(), "MERGE")
        self.assertIn("on `Main Tram`, `Second Tram`: 171 m (TRAM min 250 m)", merge)
        self.assertEqual(merge.count("171 m"), 1)

    def test_out_and_back_collapsed(self):
        self.m["lines"]["l9"]["stationIds"] = ["s16", "s15", "s17", "s15", "s16", "s17"]
        hk = section(self.report(), "HOUSEKEEPING")
        shuttle = [l for l in hk.splitlines() if "Shuttle Tram" in l]
        self.assertEqual(len(shuttle), 1)
        self.assertIn("visits 3 stations more than once", shuttle[0])


if __name__ == "__main__":
    unittest.main()
