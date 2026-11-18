#!/usr/bin/env python3
"""Download drivable roads + speed limits from OpenStreetMap (Overpass API) for the
area in tools/area.json and write small map tiles to roads/ for Driving Coach.

Tile file roads/<ty>_<tx>.json, where ty = floor(lat / tile), tx = floor(lon / tile):
  {"v": 2, "w": [[id, highway, name, limit_or_null, oneway(0/1), [lat1e5, lon1e5, ...], source], ...]}
  source: "c" City of London by-law, "l" city road not in the by-law (50 by law), "o" Ontario Road Network,
          "m" OpenStreetMap tag, null = unknown. A road is cut into pieces where its limit changes.
roads/index.json lists the tiles that exist, so the app only asks for tiles it can get.
Run:  python3 tools/build_roads.py            (downloads)
      python3 tools/build_roads.py data.json  (uses a saved Overpass reply)
"""
import json, math, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import official

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

def build(data, offline_official=None):
    t = AREA["tile"]
    bbox = (AREA["south"], AREA["west"], AREA["north"], AREA["east"])
    if offline_official is not None:
        city, orn = offline_official
    else:
        try:
            city = official.load_city(bbox) if AREA.get("city_of_london", True) else []
        except Exception as ex:
            print("City of London data unavailable:", repr(ex)[:200], flush=True); city = []
        try:
            orn = official.load_orn(bbox)
        except Exception as ex:
            print("Ontario Road Network unavailable:", repr(ex)[:200], flush=True); orn = []
    ci, oi = official.build_indexes(city, orn)
    have_city = bool(city)
    tiles = {}
    n = pieces_n = 0
    by_src = {}
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
        pts = [(p["lat"], p["lon"]) for p in g]
        pieces = official.split_way(pts, limit, ci, oi, have_city)
        for k, (ppts, plim, psrc) in enumerate(pieces):
            pid = e["id"] if len(pieces) == 1 else e["id"] * 100 + k
            flat = []
            for la, lo in ppts:
                flat += [round(la * 1e5), round(lo * 1e5)]
            rec = [pid, hw, name, plim, oneway, flat, psrc]
            L = official.length(ppts)
            by_src[psrc] = by_src.get(psrc, 0) + L
            # put the piece in every tile any of its segments touches
            keys = set()
            for i in range(len(ppts) - 1):
                (la0, lo0), (la1, lo1) = ppts[i], ppts[i + 1]
                y0, x0 = tile_of(min(la0, la1), min(lo0, lo1), t)
                y1, x1 = tile_of(max(la0, la1), max(lo0, lo1), t)
                for y in range(y0, y1 + 1):
                    for x in range(x0, x1 + 1):
                        keys.add(f"{y}_{x}")
            for key in keys:
                tiles.setdefault(key, []).append(rec)
            pieces_n += 1
        n += 1
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".json"):
            os.remove(os.path.join(OUT, f))
    tagged = sum(1 for e in data["elements"] if parse_max((e.get("tags") or {}).get("maxspeed")))
    for k, recs in tiles.items():
        with open(os.path.join(OUT, k + ".json"), "w") as fh:
            json.dump({"v": 2, "w": recs}, fh, separators=(",", ":"), ensure_ascii=False)
    total = sum(by_src.values()) or 1
    share = {str(k): round(v / total * 100, 1) for k, v in sorted(by_src.items(), key=lambda kv: -kv[1])}
    with open(os.path.join(OUT, "index.json"), "w") as fh:
        json.dump({"v": 2, "tile": t, "area": AREA["name"], "built": time.strftime("%Y-%m-%d"),
                   "roads": n, "pieces": pieces_n, "osm_tagged": tagged, "km": round(total / 1000),
                   "share_by_source_pct": share, "tiles": sorted(tiles)}, fh, separators=(",", ":"))
    print(f"Wrote {len(tiles)} tiles, {n} roads in {pieces_n} pieces ({tagged} OSM roads had a limit tag).")
    print("Share of road length by limit source (%):", share,
          " [c=City by-law, l=City default 50, o=Ontario Road Network, m=OpenStreetMap, None=unknown]")

if __name__ == "__main__":
    if len(sys.argv) > 2:  # offline test: osm.json official.json
        off = json.load(open(sys.argv[2]))
        city = [([tuple(p) for p in c[0]], c[1]) for c in off["city"]]
        orn = [([tuple(p) for p in o[0]], o[1], o[2], o[3]) for o in off["orn"]]
        build(json.load(open(sys.argv[1])), (city, orn))
    else:
        build(json.load(open(sys.argv[1])) if len(sys.argv) > 1 else download())
