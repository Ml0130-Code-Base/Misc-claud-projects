"""Hand-built snapshot payload covering every check (coordinates near Denver).

At latitude 39.75: 0.01 deg longitude ~ 856 m, 0.01 deg latitude ~ 1112 m.

Expected findings:
  DELETE       Lonely Stop (orphan)
  MERGE        Union Station x Union Station (37 m, same name, different lines)
               Far Town (R Line) x Far Town (Ferry) (same name, ~15.8 km)
               Alpha -> Beta on Main Tram (171 m, TRAM min 250 m)
  CREATE       Union Station -> Far Town on R Line (~18.6 km, REGIONAL max 15 km)
  HOUSEKEEPING Station 12 placeholder; Concept 1 draft; Mystery Line no mode;
               D Line  - North Extension doubled space; Proposed  Services label;
               Stub Line < 2 stations; Shuttle Tram repeats Santa Fe Depot
  Not flagged  Ferry 9 km gap; Concept 1 stops 50 m apart; Loop Tram loop closure;
               County Admin. Ctr. x2 (same name but both on Mystery Line)
"""

import copy


def _st(sid, name, lat, lng, waypoint=False):
    s = {"id": sid, "name": name, "lat": lat, "lng": lng, "densityInfo": {}}
    if waypoint:
        s["isWaypoint"] = True
    return s


STATIONS = [
    _st("s1", "Union Station", 39.7530, -105.0000),
    _st("s2", "Alpha", 39.7530, -104.9900),
    _st("s3", "Beta", 39.7530, -104.9880),
    _st("s4", "San Diego–Santa Fe Depot", 39.7700, -105.0000),
    _st("s5", "Far Town", 39.9200, -105.0000),
    _st("s6", "Lonely Stop", 39.7600, -105.0000),
    _st("s7", "Union Station", 39.7533, -105.0002),
    _st("s8", "County Admin. Ctr.", 39.7000, -105.0000),
    _st("s9", "County Admin. Ctr.", 39.7180, -105.0000),
    _st("s10", "Station 12", 39.7530, -104.9800),
    _st("s11", "Airport A", 39.8500, -104.6700),
    _st("s12", "Airport B", 39.8504, -104.6700),
    _st("s13", "Far Town", 39.8000, -105.1000),
    _st("s14", "Ferry South", 39.7190, -105.1000),
    _st("s15", "Santa Fe Depot", 39.7400, -104.9800),
    _st("s16", "Civic Center", 39.7440, -104.9800),
    _st("s17", "Convention Center", 39.7360, -104.9800),
    _st("w1", "", 39.8300, -105.0000, waypoint=True),
    _st("w2", "", 39.7500, -105.0100, waypoint=True),
]


def _ln(lid, name, mode, ids, group="g2", color="#0000ff"):
    return {"id": lid, "name": name, "mode": mode, "stationIds": ids, "lineGroupId": group,
            "color": color, "waypointOverrides": [], "ridershipInfo": {}}


LINES = [
    _ln("l1", "A Line", "LIGHT", ["s7", "s2", "s10"]),
    _ln("l2", "R Line", "REGIONAL", ["s1", "w1", "s5"], group="g1"),
    _ln("l3", "Main Tram", "TRAM", ["s2", "s3"]),
    _ln("l4", "D Line  - North Extension", "LIGHT", ["s7", "s4"], group="g1"),
    _ln("l5", "Concept 1", "TRAM", ["s11", "s12"]),
    _ln("l6", "Ferry", "FERRY", ["s13", "s14"]),
    _ln("l7", "Mystery Line", "", ["s8", "s9"]),
    _ln("l8", "Stub Line", "LIGHT", ["s1", "w2"]),
    _ln("l9", "Shuttle Tram", "TRAM", ["s16", "s15", "s17", "s15"]),
    _ln("l10", "Loop Tram", "TRAM", ["s16", "s15", "s17", "s16"]),
]

LINE_GROUPS = {
    "g1": {"id": "g1", "label": "Proposed  Services"},
    "g2": {"id": "g2", "label": "Current"},
}

LAST_UPDATED = 1780278731273


def make_payload(last_updated: int = LAST_UPDATED) -> dict:
    """A __NEXT_DATA__-shaped dict, as the fetcher stores it."""
    m = {
        "stations": {s["id"]: copy.deepcopy(s) for s in STATIONS},
        "lines": {l["id"]: copy.deepcopy(l) for l in LINES},
        "interchanges": {},
        "lineGroups": copy.deepcopy(LINE_GROUPS),
        "title": "Fixture Fantasy Map",
        "caption": "",
    }
    return {
        "props": {
            "pageProps": {
                "fullSystem": {"map": m, "lastUpdated": last_updated, "meta": {}},
                "systemDocData": {"title": "Fixture Fantasy Map", "lastUpdated": last_updated,
                                  "numStations": 17, "isPrivate": False},
                "ownerDocData": {},
            }
        },
        "page": "/view/[systemId]",
    }
