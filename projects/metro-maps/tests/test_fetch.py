import json
import tempfile
import unittest
from pathlib import Path

from metro_maps import list_snapshots
from metro_maps.fetch import (FetchError, extract_next_data, fetch_all, map_id, view_url)
from metro_maps.model import from_payload
from tests.fixture_data import make_payload

FIXTURES = Path(__file__).parent / "fixtures"
USER = "IhQFX1DgPtdvvwiqof368iqR1Lp2"
CONFIG = {"userId": USER, "maps": [{"index": 1, "slug": "denver"}, {"index": 14, "slug": "san-diego"}]}


def page(payload: dict) -> str:
    return ('<html><body><script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(payload, ensure_ascii=False) + "</script></body></html>")


class IdTest(unittest.TestCase):
    def test_map_id(self):
        self.assertEqual(map_id(USER, 1), "SWhRRlgxRGdQdGR2dndpcW9mMzY4aXFSMUxwMnwx")

    def test_padding_encoded(self):
        self.assertTrue(view_url(USER, 14).endswith("SWhRRlgxRGdQdGR2dndpcW9mMzY4aXFSMUxwMnwxNA%3D%3D"))
        self.assertNotIn("=", view_url(USER, 14))


class ExtractTest(unittest.TestCase):
    def test_real_trimmed_page(self):
        html = (FIXTURES / "view_denver_trimmed.html").read_text(encoding="utf-8")
        snap = from_payload(extract_next_data(html))
        self.assertEqual(snap.title, "Denver Metro Fantasy Rail Map")
        self.assertEqual(len(snap.real_stations), 5)
        self.assertEqual(snap.waypoint_count, 3)

    def test_no_script(self):
        with self.assertRaises(FetchError):
            extract_next_data("<html></html>")


class FetchAllTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.lines = []

    def tearDown(self):
        self.tmp.cleanup()

    def run_fetch(self, responses):
        def get(url):
            for idx, resp in responses.items():
                if url == view_url(USER, idx):
                    return resp
            raise AssertionError(url)
        return fetch_all(CONFIG, self.root, get=get, sleep=lambda s: None, out=self.lines.append)

    def test_new_then_unchanged(self):
        ok = {1: (200, page(make_payload(111))), 14: (200, page(make_payload(222)))}
        self.assertEqual(self.run_fetch(ok), 0)
        self.assertIn("new snapshot 111.json", self.lines[0])
        self.assertIn("17 stations", self.lines[0])
        self.assertEqual([p.name for p in list_snapshots(self.root, "san-diego")], ["222.json"])
        before = (self.root / "snapshots/denver/111.json").stat().st_mtime_ns
        self.lines.clear()
        self.assertEqual(self.run_fetch(ok), 0)
        self.assertTrue(all("unchanged" in l for l in self.lines), self.lines)
        self.assertEqual((self.root / "snapshots/denver/111.json").stat().st_mtime_ns, before)

    def test_new_edit_adds_file(self):
        self.run_fetch({1: (200, page(make_payload(111))), 14: (200, page(make_payload(222)))})
        self.run_fetch({1: (200, page(make_payload(333))), 14: (200, page(make_payload(222)))})
        self.assertEqual([p.name for p in list_snapshots(self.root, "denver")], ["111.json", "333.json"])

    def test_one_failure_isolated(self):
        code = self.run_fetch({1: (500, ""), 14: (200, page(make_payload(222)))})
        self.assertEqual(code, 1)
        self.assertIn("denver (#1): FAILED HTTP 500", self.lines[0])
        self.assertIn("new snapshot", self.lines[1])
        self.assertEqual(list_snapshots(self.root, "denver"), [])

    def test_structure_changed_not_saved(self):
        bad = make_payload(111)
        bad["props"]["pageProps"]["fullSystem"] = {"lastUpdated": 111, "other": {}}
        code = self.run_fetch({1: (200, page(bad)), 14: (200, page(make_payload(222)))})
        self.assertEqual(code, 1)
        self.assertIn("FAILED unexpected payload: missing key", self.lines[0])
        self.assertIn("fullSystem: [lastUpdated, other]", self.lines[0])
        self.assertEqual(list_snapshots(self.root, "denver"), [])

    def test_en_dash_preserved_on_disk(self):
        self.run_fetch({1: (200, page(make_payload(111))), 14: (200, page(make_payload(222)))})
        raw = (self.root / "snapshots/denver/111.json").read_text(encoding="utf-8")
        self.assertIn("San Diego–Santa Fe Depot", raw)


if __name__ == "__main__":
    unittest.main()
