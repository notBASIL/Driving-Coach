import json, urllib.request, urllib.parse

UA = {"User-Agent": "DrivingCoach/1.0 (github.com/notBASIL/Driving-Coach)"}


def get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        return json.load(r)


def show(title, fn):
    print("\n=====", title, flush=True)
    try:
        fn()
    except Exception as e:
        print("ERROR", repr(e))


LDN = "https://maps.london.ca/server/rest/services/References/Transportation/MapServer"
LIO = "https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA"


def ldn_layers():
    m = get(LDN, {"f": "pjson"})
    print([(l["id"], l["name"]) for l in m.get("layers", [])])


def ldn():
    m = get(LDN + "/9", {"f": "pjson"})
    print("name", m.get("name"), "maxRecordCount", m.get("maxRecordCount"), "geom", m.get("geometryType"))
    print("fields", [(f["name"], f["type"], f.get("alias")) for f in m.get("fields", [])])
    print("count", get(LDN + "/9/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"}))
    s = get(LDN + "/9/query", {"where": "1=1", "outFields": "*", "f": "geojson", "outSR": "4326",
                               "resultRecordCount": "4", "returnGeometry": "true"})
    for ft in s.get("features", []):
        print("props", ft["properties"], "geom", ft["geometry"]["type"], str(ft["geometry"]["coordinates"])[:150])


def lio_list():
    for svc in ["LIO_Open09", "LIO_Open08", "LIO_Open10", "LIO_Open07", "LIO_Open06"]:
        try:
            m = get(f"{LIO}/{svc}/MapServer", {"f": "pjson"})
            print(svc, "layers", [(l["id"], l["name"]) for l in m.get("layers", [])],
                  "tables", [(t["id"], t["name"]) for t in m.get("tables", [])])
        except Exception as e:
            print(svc, "ERR", repr(e))


def lio_roads():
    m = get(f"{LIO}/LIO_Open09/MapServer/0", {"f": "pjson"})
    print("L0", m.get("name"), "max", m.get("maxRecordCount"), "fields", [f["name"] for f in m.get("fields", [])])
    s = get(f"{LIO}/LIO_Open09/MapServer/0/query", {
        "geometry": "-81.26,42.97,-81.24,42.99", "geometryType": "esriGeometryEnvelope", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "f": "geojson", "outSR": "4326",
        "resultRecordCount": "3"})
    for ft in s.get("features", []):
        print("props", ft["properties"])



def ldn_root():
    for u in ["https://maps.london.ca/server/rest/services", "https://maps.london.ca/server/rest/services/References"]:
        try:
            m = get(u, {"f": "pjson"})
            print(u, "folders", m.get("folders"), "services", [(x["name"], x["type"]) for x in m.get("services", [])])
        except Exception as e:
            print(u, "ERR", repr(e))
    for svc in ["References/Transportation/MapServer", "References/Transportation/FeatureServer", "Transportation/MapServer"]:
        try:
            m = get("https://maps.london.ca/server/rest/services/" + svc, {"f": "pjson"})
            print(svc, "->", m.get("error") or [(l["id"], l["name"]) for l in m.get("layers", [])])
        except Exception as e:
            print(svc, "ERR", repr(e))


def orn_speed():
    m = get(f"{LIO}/LIO_Open09/MapServer/13", {"f": "pjson"})
    print("T13", m.get("name"), "fields", [(f["name"], f["type"]) for f in m.get("fields", [])])
    print("count", get(f"{LIO}/LIO_Open09/MapServer/13/query", {"where": "1=1", "returnCountOnly": "true", "f": "json"}))
    ids = "1500658852,1500681326,1500552542"
    for t in (13, 8, 5):
        mm = get(f"{LIO}/LIO_Open09/MapServer/{t}", {"f": "pjson"})
        key = [f["name"] for f in mm.get("fields", []) if "NET_ELEMENT" in f["name"] or f["name"] == "ORN_ROAD_NET_ELEMENT_ID"]
        print("table", t, mm.get("name"), "key", key)
        if key:
            s = get(f"{LIO}/LIO_Open09/MapServer/{t}/query", {"where": f"{key[0]} in ({ids})", "outFields": "*", "f": "json"})
            for ft in s.get("features", [])[:6]:
                print("   ", ft.get("attributes"))
    st = get(f"{LIO}/LIO_Open09/MapServer/13/query", {"where": "1=1", "outFields": "SPEED_LIMIT", "returnDistinctValues": "true", "returnGeometry": "false", "f": "json"})
    print("distinct speed values", sorted({tuple(f["attributes"].values()) for f in st.get("features", [])})[:40])


def orn_area_count():
    s = get(f"{LIO}/LIO_Open09/MapServer/0/query", {"geometry": "-81.50,42.82,-80.98,43.12", "geometryType": "esriGeometryEnvelope",
        "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "returnCountOnly": "true", "f": "json"})
    print("ORN elements in London area", s)



def ldn_open():
    base = "https://maps.london.ca/server/rest/services"
    for u in [base + "/OpenData", base + "/SLRN/MapServer", base + "/References/SLRN/MapServer", base + "/RoadWork/MapServer", base + "/StreetFeatures/MapServer"]:
        try:
            m = get(u, {"f": "pjson"})
            if "services" in m: print(u, [(x["name"], x["type"]) for x in m["services"]])
            else: print(u, m.get("error") or [(l["id"], l["name"]) for l in m.get("layers", [])])
        except Exception as e:
            print(u, "ERR", repr(e))
    for u in [base + "/SLRN/MapServer/0", base + "/References/SLRN/MapServer/0"]:
        try:
            m = get(u, {"f": "pjson"}); print(u, m.get("name"), [f["name"] for f in m.get("fields", [])])
        except Exception as e: print(u, "ERR", repr(e))


def hub():
    for q in ["speed limit", "speed limits london"]:
        try:
            m = get("https://hub.arcgis.com/api/v3/datasets", {"q": q, "filter[source]": "City of London", "page[size]": "10"})
            for d in m.get("data", []):
                a = d.get("attributes", {})
                print(q, "|", a.get("name"), "|", a.get("source"), "|", a.get("url"), "|", a.get("modified"))
        except Exception as e:
            print("hub ERR", repr(e))
    try:
        m = get("https://opendata.london.ca/api/search/v1/collections/dataset/items", {"q": "speed", "limit": "10"})
        for f in m.get("features", []):
            pr = f.get("properties", {}); print("opendata |", pr.get("title"), "|", pr.get("url"), "|", pr.get("modified"))
    except Exception as e:
        print("opendata ERR", repr(e))


def orn_fresh():
    from collections import Counter
    s = get(f"{LIO}/LIO_Open09/MapServer/0/query", {"geometry": "-81.40,42.90,-81.10,43.05", "geometryType": "esriGeometryEnvelope",
        "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "outFields": "OGF_ID", "returnGeometry": "false", "f": "json", "resultRecordCount": "1500"})
    ids = [str(int(f["attributes"]["OGF_ID"])) for f in s.get("features", [])]
    print("sample elements", len(ids))
    speeds, years, agencies, covered = Counter(), Counter(), Counter(), set()
    for i in range(0, len(ids), 200):
        r = get(f"{LIO}/LIO_Open09/MapServer/13/query", {"where": "ORN_ROAD_NET_ELEMENT_ID in (" + ",".join(ids[i:i+200]) + ")",
            "outFields": "ORN_ROAD_NET_ELEMENT_ID,SPEED_LIMIT,AGENCY_NAME,EFFECTIVE_DATETIME", "f": "json"})
        for ft in r.get("features", []):
            a = ft["attributes"]; covered.add(a["ORN_ROAD_NET_ELEMENT_ID"]); speeds[a["SPEED_LIMIT"]] += 1; agencies[a["AGENCY_NAME"]] += 1
            import time; years[time.gmtime(a["EFFECTIVE_DATETIME"] / 1000).tm_year] += 1
    print("elements with a speed record", len(covered), "of", len(ids))
    print("speeds", sorted(speeds.items())); print("years", sorted(years.items())); print("agencies", agencies.most_common(5))


show("London open data services", ldn_open)
show("Hub search", hub)
show("ORN freshness in London", orn_fresh)
