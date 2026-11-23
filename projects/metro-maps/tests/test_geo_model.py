import unittest

from metro_maps.geo import fmt_dist, haversine_m
from metro_maps.model import SnapshotError, from_payload
from tests.fixture_data import make_payload


class GeoTest(unittest.TestCase):
    def test_london_paris(self):
        d = haversine_m(51.5074, -0.1278, 48.8566, 2.3522)
        self.assertAlmostEqual(d / 1000, 343.5, delta=1.0)

    def test_denver_union_station_to_dia(self):
        # Union Station to Denver Airport station, ~29.8 km straight line
        d = haversine_m(39.7527, -105.0002, 39.8471, -104.6738)
        self.assertAlmostEqual(d / 1000, 29.8, delta=1.0)

    def test_one_degree_latitude(self):
        self.assertAlmostEqual(haversine_m(0, 0, 1, 0), 111_195, delta=10)

    def test_zero(self):
        self.assertEqual(haversine_m(39.75, -105.0, 39.75, -105.0), 0.0)

    def test_format(self):
        self.assertEqual(fmt_dist(180.4), "180 m")
        self.assertEqual(fmt_dist(999.4), "999 m")
        self.assertEqual(fmt_dist(999.6), "1.0 km")
        self.assertEqual(fmt_dist(18_437), "18.4 km")


class ModelTest(unittest.TestCase):
    def setUp(self):
        self.snap = from_payload(make_payload())

    def test_counts(self):
        self.assertEqual(len(self.snap.real_stations), 17)
        self.assertEqual(self.snap.waypoint_count, 2)
        self.assertEqual(len(self.snap.lines), 10)
        self.assertEqual(self.snap.title, "Fixture Fantasy Map")

    def test_waypoints_dropped_from_sequence(self):
        r = next(l for l in self.snap.lines if l.name == "R Line")
        self.assertEqual(r.station_ids, ["s1", "w1", "s5"])
        self.assertEqual(r.seq, ["s1", "s5"])

    def test_exact_names_kept(self):
        self.assertEqual(self.snap.stations["s4"].name, "San Diego–Santa Fe Depot")
        self.assertIn("D Line  - North Extension", [l.name for l in self.snap.lines])

    def test_lines_sorted(self):
        names = [l.name for l in self.snap.lines]
        self.assertEqual(names, sorted(names))

    def test_top_level_stations_variant(self):
        p = make_payload()
        fs = p["props"]["pageProps"]["fullSystem"]
        fs.update(fs.pop("map"))
        self.assertEqual(len(from_payload(p).real_stations), 17)

    def test_structure_changed_error(self):
        p = make_payload()
        p["props"]["pageProps"]["fullSystem"] = {"lastUpdated": 1, "data": {}}
        with self.assertRaises(SnapshotError) as cm:
            from_payload(p)
        msg = str(cm.exception)
        self.assertIn("missing key", msg)
        self.assertIn("fullSystem: [data, lastUpdated]", msg)

    def test_missing_props(self):
        with self.assertRaises(SnapshotError) as cm:
            from_payload({"page": "/"})
        self.assertIn("found: page", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
