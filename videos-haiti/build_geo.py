import json, math, sys
GEO = sys.argv[1]; OUT = sys.argv[2]
K = 100; LON0 = -72.5; LAT0 = 19.0; C = math.cos(math.radians(LAT0))
def P(lon, lat): return ((lon - LON0) * C * K, -(lat - LAT0) * K)
def ring_d(ring, tol):
    pts = []; last = None
    for lon, lat in ring:
        x, y = P(lon, lat)
        if last and abs(x-last[0]) < tol and abs(y-last[1]) < tol: continue
        pts.append((x, y)); last = (x, y)
    if len(pts) < 3: return ""
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
def geom_d(g, tol):
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return "".join(ring_d(r, tol) for poly in polys for r in poly)
def centroid(g):
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    big = max((poly[0] for poly in polys), key=len)
    xs = [P(*p) for p in big]; return (sum(x for x, _ in xs)/len(xs), sum(y for _, y in xs)/len(xs))
a0 = json.load(open(f"{GEO}/adm0.geojson")); a1 = json.load(open(f"{GEO}/adm1.geojson"))
def inb(g):
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return any(-92 < lon < -55 and 5 < lat < 32 for poly in polys for lon, lat in poly[0])
countries = []
for f in a0["features"]:
    if inb(f["geometry"]):
        iso = f["properties"]["ADM0_A3"]
        countries.append({"iso": iso, "name": f["properties"]["NAME"], "d": geom_d(f["geometry"], 3)})
hti = []
for f in a1["features"]:
    if f["properties"]["adm0_a3"] == "HTI":
        cx, cy = centroid(f["geometry"])
        hti.append({"name": f["properties"]["name"], "d": geom_d(f["geometry"], 0.6), "cx": round(cx,1), "cy": round(cy,1)})
dom = [f for f in a1["features"] if f["properties"]["adm0_a3"] == "DOM"]
pap = P(-72.3074, 18.5944); sdq = P(-69.9312, 18.4861)
json_out = {"countries": countries, "hti": hti, "pap": pap, "sdq": sdq}
open(OUT, "w").write("window.GEO=" + json.dumps(json_out, ensure_ascii=False) + ";")
print(len(countries), "countries;", len(hti), "deps; size", len(json.dumps(json_out))//1024, "KB")
