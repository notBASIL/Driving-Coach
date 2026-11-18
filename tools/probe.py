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


show("London layers", ldn_layers)
show("London speed layer 9", ldn)
show("LIO services", lio_list)
show("LIO road net element sample", lio_roads)
