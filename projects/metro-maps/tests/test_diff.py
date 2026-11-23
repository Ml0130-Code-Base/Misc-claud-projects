import unittest

from metro_maps.diff import diff_snapshots
from metro_maps.model import from_payload
from tests.fixture_data import make_payload


def section(text: str, title: str) -> str:
    """Body of one '## title' section."""
    start = text.index(f"## {title}")
    rest = text[start:].split("\n## ", 1)[0]
    return rest


class DiffTest(unittest.TestCase):
    def setUp(self):
        self.old_p = make_payload(100)
        self.new_p = make_payload(200)
        self.m = self.new_p["props"]["pageProps"]["fullSystem"]["map"]

    def diff(self):
        return diff_snapshots(from_payload(self.old_p), from_payload(self.new_p))

    def test_no_changes(self):
        out = self.diff()
        self.assertIn("None.", section(out, "Stations added"))
        self.assertIn("Waypoints moved: 0", out)

    def test_en_dash_rename(self):
        self.m["stations"]["s15"]["name"] = "San Diego–Santa Fe Depot"
        self.assertIn("- `Santa Fe Depot` -> `San Diego–Santa Fe Depot`", section(self.diff(), "Stations renamed"))

    def test_station_added_to_line(self):
        self.m["stations"]["s20"] = {"id": "s20", "name": "Gamma", "lat": 39.7530, "lng": -104.9850}
        self.m["lines"]["l3"]["stationIds"] = ["s2", "s3", "s20"]
        out = self.diff()
        self.assertIn("- `Gamma`", section(out, "Stations added"))
        self.assertIn("inserted `Gamma` between `Beta` and (end)", section(out, "Lines changed"))

    def test_station_removed(self):
        del self.m["stations"]["s6"]
        self.assertIn("- `Lonely Stop`", section(self.diff(), "Stations removed"))

    def test_moved(self):
        self.m["stations"]["s2"]["lat"] += 0.001  # ~111 m
        self.m["stations"]["s3"]["lat"] += 0.0001  # ~11 m, below threshold
        body = section(self.diff(), "Stations moved")
        self.assertIn("`Alpha` moved 111 m", body)
        self.assertNotIn("Beta", body)

    def test_waypoint_only_moves_counted(self):
        self.m["stations"]["w1"]["lat"] += 0.01
        self.m["stations"]["w2"]["lng"] += 0.01
        out = self.diff()
        self.assertIn("Waypoints moved: 2", out)
        self.assertIn("None.", section(out, "Stations moved"))

    def test_waypoint_toggle(self):
        self.m["stations"]["s3"]["isWaypoint"] = True
        self.assertIn("`Beta`: station -> waypoint", section(self.diff(), "Station / waypoint switched"))

    def test_line_changes(self):
        self.m["lines"]["l7"]["mode"] = "LIGHT"
        self.m["lines"]["l1"]["color"] = "#ff0000"
        self.m["lines"]["l2"]["name"] = "R Line Express"
        del self.m["lines"]["l6"]
        self.m["lines"]["l11"] = {"id": "l11", "name": "New Line", "mode": "TRAM", "stationIds": ["s2", "s3"]}
        out = self.diff()
        changed = section(out, "Lines changed")
        self.assertIn("mode (none) -> LIGHT", changed)
        self.assertIn("color #0000ff -> #ff0000", changed)
        self.assertIn("- `R Line Express`\n  - renamed from `R Line`", changed)
        self.assertIn("- `Ferry`", section(out, "Lines removed"))
        self.assertIn("- `New Line` (TRAM, 2 stations)", section(out, "Lines added"))

    def test_reorder(self):
        self.m["lines"]["l1"]["stationIds"] = ["s10", "s2", "s7"]
        self.assertIn("same stations, order changed", section(self.diff(), "Lines changed"))


if __name__ == "__main__":
    unittest.main()
