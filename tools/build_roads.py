#!/usr/bin/env python3
"""Download drivable roads + speed limits from OpenStreetMap (Overpass API) for the
area in tools/area.json and write small map tiles to roads/ for Driving Coach.

Tile file roads/<ty>_<tx>.json, where ty = floor(lat / tile), tx = floor(lon / tile):
  {"v": 1, "w": [[id, highway, name, limit_or_null, oneway(0/1), [lat1e5, lon1e5, ...]], ...]}
roads/index.json lists the tiles that exist, so the app only asks for tiles it can get.
Run:  python3 tools/build_roads.py            (downloads)
      python3 tools/build_roads.py data.json  (uses a saved Overpass reply)
"""
import json, math, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREA = json.load(open(os.path.join(ROOT, "tools", "area.json")))
OUT = os.path.join(ROOT, "roads")
ROADS = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|"
         "motorway_link|trunk_link|primary_link|secondary_link|tertiary_link")
SERVERS = ["https://overpass-api.de/api/interpreter",
           "https://overpass.private.coffee/api/interpreter",
           "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
NAMED = {"CA:ON:urban": 50, "CA:urban": 50, "CA:ON:rural": 80, "CA:rural": 80,
         "CA:ON:motorway": 100, "CA:motorway": 100}

def parse_max(v):
    if not v:
        return None
    v = str(v).split(";")[0].strip()
    if v in NAMED:
        return NAMED[v]
    m = re.match(r"^(\d+)\s*(mph)?", v)
    if not m:
        return None
    return round(int(m.group(1)) * 1.609) if m.group(2) else int(m.group(1))

def download():
    a = AREA
    q = (f'[out:json][timeout:300][maxsize:1073741824];'
         f'way({a["south"]},{a["west"]},{a["north"]},{a["east"]})[highway~"^({ROADS})$"];'
         f'out tags geom;')
    body = urllib.parse.urlencode({"data": q}).encode()
    last = None
    for attempt in range(3):
        for url in SERVERS:
            try:
                print(f"Downloading from {url} ...", flush=True)
                req = urllib.request.Request(url, data=body, headers={
                    "User-Agent": "DrivingCoach/1.0 (github.com/notBASIL/Driving-Coach)"})
                with urllib.request.urlopen(req, timeout=400) as r:
                    data = json.load(r)
                if data.get("elements"):
                    return data
                last = "empty reply: " + str(data.get("remark", ""))[:200]
            except Exception as e:  # try the next server
                last = repr(e)
            print("  failed:", last, flush=True)
        time.sleep(60)
    sys.exit(f"All Overpass servers failed: {last}")

def tile_of(lat, lon, t):
    return (math.floor(lat / t), math.floor(lon / t))

def build(data):
    t = AREA["tile"]
    tiles = {}
    n = 0
    for e in data["elements"]:
        g = e.get("geometry") or []
        if e.get("type") != "way" or len(g) < 2:
            continue
        tags = e.get("tags", {})
        hw = tags.get("highway", "")
        limit = (parse_max(tags.get("maxspeed")) or parse_max(tags.get("maxspeed:forward"))
                 or parse_max(tags.get("maxspeed:backward")))
        oneway = 1 if tags.get("oneway") == "yes" or hw.startswith("motorway") else 0
        name = tags.get("name") or tags.get("ref") or ""
        flat = []
        for p in g:
            flat += [round(p["lat"] * 1e5), round(p["lon"] * 1e5)]
        rec = [e["id"], hw, name, limit, oneway, flat]
        # put the road in every tile any of its segments touches
        keys = set()
        for i in range(len(g) - 1):
            a, b = g[i], g[i + 1]
            y0, x0 = tile_of(min(a["lat"], b["lat"]), min(a["lon"], b["lon"]), t)
            y1, x1 = tile_of(max(a["lat"], b["lat"]), max(a["lon"], b["lon"]), t)
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    keys.add(f"{y}_{x}")
        for k in keys:
            tiles.setdefault(k, []).append(rec)
        n += 1
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".json"):
            os.remove(os.path.join(OUT, f))
    tagged = sum(1 for e in data["elements"] if parse_max((e.get("tags") or {}).get("maxspeed")))
    for k, recs in tiles.items():
        with open(os.path.join(OUT, k + ".json"), "w") as fh:
            json.dump({"v": 1, "w": recs}, fh, separators=(",", ":"), ensure_ascii=False)
    with open(os.path.join(OUT, "index.json"), "w") as fh:
        json.dump({"v": 1, "tile": t, "area": AREA["name"], "built": time.strftime("%Y-%m-%d"),
                   "roads": n, "with_limit": tagged, "tiles": sorted(tiles)}, fh, separators=(",", ":"))
    print(f"Wrote {len(tiles)} tiles, {n} roads ({tagged} with a posted limit).")

if __name__ == "__main__":
    data = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else download()
    build(data)
