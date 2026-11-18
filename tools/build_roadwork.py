#!/usr/bin/env python3
"""Download the City of London's ongoing road work (open data) and write roads/roadwork.json
for Driving Coach's construction warnings.

  {"v": 1, "built": "...", "items": [{"id", "street", "from", "to", "where", "end": ms|null,
                                      "p": [lat1e5, lon1e5, ...] }, ...]}
Multi-part lines become one item per part (same id).
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import official

URL = "https://maps.london.ca/server/rest/services/RoadWork/MapServer/0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def title(s):
    s = (s or "").strip()
    return " ".join(w if any(c.isdigit() for c in w) else w.capitalize() for w in s.split()) if s.isupper() else s


def main():
    feats, off = [], 0
    while True:  # plain GET, Esri JSON (this service rejects the paged/geojson queries)
        j = official._get(URL + "/query", {"where": "1=1", "outFields": "*", "returnGeometry": "true", "outSR": "4326",
                                           "f": "json", "resultOffset": off, "resultRecordCount": 1000})
        page = j.get("features", [])
        for ft in page:
            g = ft.get("geometry") or {}
            feats.append({"properties": ft.get("attributes") or {},
                          "geometry": {"type": "MultiLineString", "coordinates": g.get("paths") or []}})
        if not j.get("exceededTransferLimit") or not page:
            break
        off += len(page)
    now = time.time() * 1000
    items = []
    for f in feats:
        a = f.get("properties") or {}
        end = a.get("EndDate")
        if end and end < now - 86400000:
            continue  # finished
        for line in official._lines(f.get("geometry")):
            if len(line) < 2:
                continue
            flat = []
            for lon, lat in line:
                flat += [round(lat * 1e5), round(lon * 1e5)]
            items.append({"id": a.get("ObjectId") or a.get("ESRI_OID"), "street": title(a.get("Street")),
                          "from": title(a.get("LocationFrom")), "to": title(a.get("LocationTo")),
                          "where": title(a.get("LocationFreeform") or a.get("Intersection") or ""),
                          "end": end, "p": flat})
    out = os.path.join(ROOT, "roads", "roadwork.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump({"v": 1, "built": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()), "source": "City of London Open Data (RoadWork)",
                   "items": items}, fh, separators=(",", ":"), ensure_ascii=False)
    print(f"Road work: {len(feats)} records, {len(items)} active line parts written")


if __name__ == "__main__":
    main()
