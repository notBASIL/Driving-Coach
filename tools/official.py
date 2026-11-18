"""Official speed-limit sources for Driving Coach, and matching them onto OpenStreetMap roads.

Sources, best first:
  city   City of London "Speed Limits" open data (by-law schedules: 40 zones, 60/70/80 roads)
  law    a City of London road the by-law doesn't list -> 50 km/h (Ontario Highway Traffic Act default)
  orn    Ontario Road Network speed-limit records (province-wide; many date from 2017)
  osm    the OpenStreetMap maxspeed tag
"""
import json, math, time, urllib.parse, urllib.request

UA = {"User-Agent": "DrivingCoach/1.0 (github.com/notBASIL/Driving-Coach)"}
CITY_URL = "https://maps.london.ca/server/rest/services/OpenData/OpenData_Transportation/MapServer/15"
LIO = "https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open09/MapServer"
ORN_ROADS, ORN_SPEED, ORN_JURIS = LIO + "/0", LIO + "/13", LIO + "/5"
CITY_JURIS = "City of London"
DEFAULT_CITY = 50


# ---------------------------------------------------------------- downloads
def _get(url, params, post=False, tries=4):
    data = urllib.parse.urlencode(params).encode()
    for i in range(tries):
        try:
            if post:
                req = urllib.request.Request(url, data=data, headers=UA)
            else:
                req = urllib.request.Request(url + "?" + data.decode(), headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                j = json.load(r)
            if isinstance(j, dict) and j.get("error"):
                raise RuntimeError(str(j["error"])[:200])
            return j
        except Exception as e:
            if i == tries - 1:
                raise
            print("   retry", url.rsplit("/", 2)[-2:], repr(e)[:120], flush=True)
            time.sleep(5 * (i + 1))


def _all_features(url, params, page):
    out, off = [], 0
    while True:
        j = _get(url + "/query", dict(params, resultOffset=off, resultRecordCount=page), post=True)
        feats = j.get("features", [])
        out += feats
        if len(feats) < page and not j.get("exceededTransferLimit") and not (j.get("properties") or {}).get("exceededTransferLimit"):
            break
        if not feats:
            break
        off += len(feats)
    return out


def _lines(geom):
    if not geom:
        return []
    if geom["type"] == "LineString":
        return [geom["coordinates"]]
    if geom["type"] == "MultiLineString":
        return geom["coordinates"]
    return []


def load_city(bbox):
    s, w, n, e = bbox
    feats = _all_features(CITY_URL, {"where": "1=1", "outFields": "MaxSpeed,Highway,Source", "f": "geojson", "outSR": "4326",
                                      "geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope", "inSR": "4326",
                                      "spatialRel": "esriSpatialRelIntersects"}, 1000)
    out = []
    for f in feats:
        sp = (f.get("properties") or {}).get("MaxSpeed")
        if not sp:
            continue
        for line in _lines(f.get("geometry")):
            out.append(([(c[1], c[0]) for c in line], int(sp)))
    print(f"City of London: {len(feats)} speed-limit sections", flush=True)
    return out


def _events(url, ids, fields):
    res = {}
    for i in range(0, len(ids), 150):
        chunk = ids[i:i + 150]
        j = _get(url + "/query", {"where": "ORN_ROAD_NET_ELEMENT_ID in (" + ",".join(str(x) for x in chunk) + ")",
                                  "outFields": "ORN_ROAD_NET_ELEMENT_ID,FROM_MEASURE,TO_MEASURE," + fields,
                                  "returnGeometry": "false", "f": "json"}, post=True)
        for ft in j.get("features", []):
            a = ft["attributes"]
            res.setdefault(int(a["ORN_ROAD_NET_ELEMENT_ID"]), []).append(a)
    return res


def load_orn(bbox):
    s, w, n, e = bbox
    feats = _all_features(ORN_ROADS, {"where": "1=1", "outFields": "OGF_ID", "f": "geojson", "outSR": "4326",
                                      "geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope", "inSR": "4326",
                                      "spatialRel": "esriSpatialRelIntersects"}, 2000)
    geoms = {}
    for f in feats:
        oid = int((f.get("properties") or {}).get("OGF_ID") or 0)
        lines = _lines(f.get("geometry"))
        if oid and lines:
            geoms[oid] = [(c[1], c[0]) for c in lines[0]]
    ids = list(geoms)
    print(f"Ontario Road Network: {len(ids)} road pieces", flush=True)
    speeds = _events(ORN_SPEED, ids, "SPEED_LIMIT,EFFECTIVE_DATETIME")
    juris = _events(ORN_JURIS, ids, "JURISDICTION")
    out = []
    for oid, pts in geoms.items():
        ev = sorted(speeds.get(oid, []), key=lambda a: a["FROM_MEASURE"] or 0)
        jur = [a.get("JURISDICTION") or "" for a in juris.get(oid, [])]
        is_city = any(CITY_JURIS.lower() in j.lower() for j in jur)
        year = max((time.gmtime((a.get("EFFECTIVE_DATETIME") or 0) / 1000).tm_year for a in ev), default=0)
        out.append((pts, ev, is_city, year))
    print(f"   with speed records: {sum(1 for o in out if o[1])}, city roads: {sum(1 for o in out if o[2])}", flush=True)
    return out


# ---------------------------------------------------------------- geometry
LAT0 = 43.0
KX, KY = 111320 * math.cos(math.radians(LAT0)), 110540


def xy(lat, lon):
    return lon * KX, lat * KY


def bearing(a, b):
    (x1, y1), (x2, y2) = xy(*a), xy(*b)
    return math.degrees(math.atan2(x2 - x1, y2 - y1)) % 180  # undirected


def seg_dist(p, a, b):
    px, py = xy(*p); ax, ay = xy(*a); bx, by = xy(*b)
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def length(pts):
    return sum(math.hypot(*(u - v for u, v in zip(xy(*pts[i + 1]), xy(*pts[i])))) for i in range(len(pts) - 1))


class SegIndex:
    CELL = 0.0005  # ~50 m

    def __init__(self):
        self.cells = {}

    def add(self, a, b, val):
        brg = bearing(a, b)
        y0, y1 = sorted((int(a[0] // self.CELL), int(b[0] // self.CELL)))
        x0, x1 = sorted((int(a[1] // self.CELL), int(b[1] // self.CELL)))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.cells.setdefault((y, x), []).append((a, b, brg, val))

    def nearest(self, p, brg, max_d, max_angle=25):
        cy, cx = int(p[0] // self.CELL), int(p[1] // self.CELL)
        best, bd = None, max_d
        for y in (cy - 1, cy, cy + 1):
            for x in (cx - 1, cx, cx + 1):
                for a, b, sb, val in self.cells.get((y, x), ()):
                    d = abs(sb - brg)
                    if min(d, 180 - d) > max_angle:
                        continue
                    dist = seg_dist(p, a, b)
                    if dist < bd:
                        bd, best = dist, val
        return best


def build_indexes(city, orn):
    ci, oi = SegIndex(), SegIndex()
    for pts, sp in city:
        for i in range(len(pts) - 1):
            ci.add(pts[i], pts[i + 1], sp)
    for pts, ev, is_city, year in orn:
        if not ev and not is_city:
            continue
        total = max([a["TO_MEASURE"] or 0 for a in ev] + [1e-9])
        geo_total = length(pts) or 1
        run = 0.0
        for i in range(len(pts) - 1):
            seg = length(pts[i:i + 2])
            mid = (run + seg / 2) / geo_total * total  # position along the piece, in the records' measure
            run += seg
            sp = None
            for a in ev:
                if (a["FROM_MEASURE"] or 0) - 0.5 <= mid <= (a["TO_MEASURE"] or 0) + 0.5:
                    sp = a["SPEED_LIMIT"]
                    break
            if sp is None and ev:
                sp = ev[0]["SPEED_LIMIT"]
            oi.add(pts[i], pts[i + 1], (sp, is_city, year))
    return ci, oi


# ---------------------------------------------------------------- matching
def segment_value(a, b, osm_limit, ci, oi, have_city):
    """Best (limit, source) for one OSM segment, from samples along it."""
    L = length([a, b])
    brg = bearing(a, b)
    if L < 14:
        fr = [0.5]
    else:
        n = max(1, int((L - 12) // 10) + 1)
        fr = [(6 + (L - 12) * (k + 0.5) / n) / L for k in range(n)]
    votes = {}
    for f in fr:
        p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        v = None
        c = ci.nearest(p, brg, 15) if have_city else None
        if c:
            v = (c, "c")
        else:
            o = oi.nearest(p, brg, 18)
            if o:
                sp, is_city, year = o
                if is_city and have_city:
                    v = (DEFAULT_CITY, "l")          # city road the by-law doesn't list
                elif sp and osm_limit and year < 2020 and osm_limit != sp:
                    v = (osm_limit, "m")             # old provincial record vs. a mapper's tag: trust the tag
                elif sp:
                    v = (sp, "o")
        votes[v] = votes.get(v, 0) + 1
    best = max(votes.items(), key=lambda kv: (kv[1], kv[0] is not None))[0]
    if best is None and osm_limit:
        best = (osm_limit, "m")
    return best


def split_way(pts, osm_limit, ci, oi, have_city):
    """Cut an OSM road wherever its limit changes; returns [(points, limit, source), ...]."""
    vals = [segment_value(pts[i], pts[i + 1], osm_limit, ci, oi, have_city) for i in range(len(pts) - 1)]
    lens = [length(pts[i:i + 2]) for i in range(len(pts) - 1)]
    # smooth: a short run (< 30 m) between two equal neighbours takes their value (intersection noise)
    runs, i = [], 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        runs.append([i, j, vals[i], sum(lens[i:j + 1])])
        i = j + 1
    for k in range(1, len(runs) - 1):
        if runs[k][3] < 30 and runs[k - 1][2] == runs[k + 1][2]:
            runs[k][2] = runs[k - 1][2]
    merged = []
    for r in runs:
        if merged and merged[-1][2] == r[2]:
            merged[-1][1] = r[1]
        else:
            merged.append(r[:3])
    out = []
    for i0, i1, v in merged:
        piece = pts[i0:i1 + 2]
        out.append((piece, v[0] if v else None, v[1] if v else None))
    return out
