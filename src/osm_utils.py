# src/osm_utils.py
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static
import folium
from shapely.geometry import Point, LineString
import math

geolocator = Nominatim(user_agent="smartnav_app")

def geocode_suggestions(query, limit=5):
    """Return list of candidate locations for a text query."""
    try:
        res = geolocator.geocode(query, exactly_one=False, limit=limit, addressdetails=True)
        if not res:
            return []
        return [{
            "display_name": r.address,
            "lat": r.latitude,
            "lon": r.longitude
        } for r in res]
    except Exception:
        return []

def place_to_nearest_node(G, lat, lon):
    """Given lat/lon, return nearest graph node id (OSMnx uses lon,x order)."""
    # ox.distance.nearest_nodes expects X (lon), Y (lat)
    return ox.distance.nearest_nodes(G, X=lon, Y=lat)

def build_folium_map(G, center_lat=None, center_lon=None, zoom_start=13):
    """Return a folium.Map centered on the city/center point."""
    if center_lat is None or center_lon is None:
        # try to get centroid from graph nodes
        any_node = next(iter(G.nodes(data=True)))[1]
        center_lat = any_node.get("y")
        center_lon = any_node.get("x")
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles="OpenStreetMap")
    return m

def add_route_to_map(m, G, path, route_color="red"):
    """Draw polyline of route on folium map m."""
    # extract lat/lon pairs for path
    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
    folium.PolyLine(coords, color=route_color, weight=5, opacity=0.8).add_to(m)
    # add markers for start and end
    folium.Marker(coords[0], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(coords[-1], tooltip="End", icon=folium.Icon(color="red")).add_to(m)
    return m

def haversine_m(lon1, lat1, lon2, lat2):
    """Return distance in meters between two lon/lat points."""
    R = 6371000.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1); dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))

def landmarks_near_route(G, path, buffer_m=200, amenity_tags=None):
    """
    Query OSM for amenities near the route.
    - buffer_m: distance in meters around route to consider
    - amenity_tags: dict of OSM tags to search, e.g. {"amenity":["hospital","atm","police","fuel"]}
    Returns GeoDataFrame of found features (may be empty).
    """
    if amenity_tags is None:
        amenity_tags = {"amenity": ["hospital", "atm", "police", "fuel"]}

    # compute bbox around route path (tiny margin) to limit query
    lats = [G.nodes[n]["y"] for n in path]
    lons = [G.nodes[n]["x"] for n in path]
    north = max(lats) + 0.01
    south = min(lats) - 0.01
    east = max(lons) + 0.01
    west = min(lons) - 0.01

    # query OSM features in bbox with desired tags
    try:
        gdf = ox.geometries_from_bbox(north, south, east, west, amenity_tags)
    except Exception:
        return None

    # for each geometry, compute min distance to any route node (approx via haversine)
    route_coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in path]  # lon,lat
    results = []
    for idx, row in gdf.iterrows():
        # compute centroid lat/lon
        geom = row.geometry
        if geom.is_empty:
            continue
        pt = geom.representative_point()
        lon, lat = pt.x, pt.y
        # find min distance to route nodes
        min_d = min(haversine_m(lon, lat, rn[0], rn[1]) for rn in route_coords)
        if min_d <= buffer_m:
            results.append({
                "osmid": idx,
                "lat": lat,
                "lon": lon,
                "tags": row.to_dict()
            })
    return results
