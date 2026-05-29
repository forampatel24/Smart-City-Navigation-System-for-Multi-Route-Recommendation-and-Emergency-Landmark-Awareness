
#   
# app.py
import streamlit as st
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium
from shapely.geometry import Point, LineString
import math
from folium.plugins import LocateControl

#from streamlit_js_eval import st_js_eval

st.set_page_config(page_title="Smart City Navigation", layout="wide")
st.title("🚗 Smart City Navigation — India")

# -------------------------
# Cached Geocoding (Name → Coordinates) — Fixed for Polygon results
# -------------------------
import osmnx as ox
import streamlit as st

@st.cache_data(show_spinner=False)
def geocode_suggestions_cached(query):
    """
    Returns a list of (name, lat, lon) suggestions for a place query.
    Handles both point and polygon geometry types.
    """
    try:
        if not query or len(query) < 3:
            return []
        locations = ox.geocode_to_gdf(query)
        if locations.empty:
            return []
        results = []
        for _, row in locations.iterrows():
            name = row.get("display_name") or query
            geom = row.geometry
            # Handle both Point and Polygon geometries
            if geom.geom_type == "Point":
                lat, lon = geom.y, geom.x
            else:
                centroid = geom.centroid
                lat, lon = centroid.y, centroid.x
            results.append({"name": name, "lat": lat, "lon": lon})
        return results
    except Exception as e:
        st.warning(f"Geocoding error: {e}")
        return []


# # -------------------------
# # Theme Toggle (Day/Night)
# # -------------------------
# st.sidebar.markdown("### 🌓 Map Theme")
# dark_mode = st.sidebar.toggle("Enable Night Mode 🌙", value=False)

# -------------------------
# Global Theme Toggle
# -------------------------
st.sidebar.markdown("### 🌓 Theme")
theme = st.sidebar.radio("Choose theme:", ["Light", "Dark"], index=0, horizontal=True)

# Save in session state for access everywhere
st.session_state["theme"] = theme

# Apply basic CSS for theme
if theme == "Dark":
    st.markdown(
        """
        <style>
        body, [class*="stApp"] {
            background-color: #0E1117 !important;
            color: white !important;
        }
        [data-testid="stSidebar"] {
            background-color: #1E1E1E !important;
        }
        .stButton>button {
            background-color: #262730 !important;
            color: white !important;
            border: 1px solid #444 !important;
        }
        .stTextInput>div>div>input {
            background-color: #262730 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Ensure global graph variable always exists
if "G" not in st.session_state:
    st.session_state["G"] = None
G = st.session_state["G"]

import math

def haversine_m(lon1, lat1, lon2, lat2):
    """Compute distance in meters between two lat/lon points."""
    R = 6371000.0  # radius of Earth in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))


# -------------------------
# Helpers / cached utilities
# -------------------------
@st.cache_data(show_spinner=False)
def load_graph_dynamic(start_coords, end_coords):
    """
    Dynamically download a road graph between two coordinates (works globally, OSMnx ≥ 2.0.6).
    Automatically computes bounding box.
    """
    import osmnx as ox
    import shapely.geometry as geom

    lat1, lon1 = start_coords
    lat2, lon2 = end_coords

    # Create bounding box polygon from both points
    north = max(lat1, lat2) + 0.5
    south = min(lat1, lat2) - 0.5
    east = max(lon1, lon2) + 0.5
    west = min(lon1, lon2) - 0.5

    bbox_polygon = geom.box(west, south, east, north)

    st.info("🌍 Downloading road network... Please wait (depends on distance)...")

    # ✅ OSMnx 2.x syntax: graph_from_polygon instead of graph_from_bbox
    G = ox.graph_from_polygon(bbox_polygon, network_type="drive", simplify=True)

    st.success("✅ Road network loaded successfully!")
    return G


# -------------------------
# Updated POI cache (hashable key only)
# -------------------------
@st.cache_data(show_spinner=False)
def pois_near_route_cached(path_tuple, buffer_m=200, amenity_list=None):
    """Fetch POIs (hospitals, police, fuel, etc.) near a route using Overpass API directly (safe version)."""
    import requests

    if amenity_list is None:
        amenity_list = ["hospital", "atm", "fuel", "police"]

    # Get the global graph safely
    G = st.session_state.get("G")
    if G is None:
        st.warning("No graph loaded to find POIs.")
        return []

    # Collect lat/lon safely
    lats, lons = [], []
    for n in path_tuple:
        node_data = G.nodes.get(n)
        if node_data and "y" in node_data and "x" in node_data:
            lats.append(node_data["y"])
            lons.append(node_data["x"])

    if not lats or not lons:
        st.warning("Could not find coordinates for route nodes.")
        return []

    north, south = max(lats), min(lats)
    east, west = max(lons), min(lons)

    # Slightly expand bbox to cover nearby areas
    lat_margin = (north - south) * 0.05
    lon_margin = (east - west) * 0.05
    north += lat_margin
    south -= lat_margin
    east += lon_margin
    west -= lon_margin

    # Build Overpass query
    amenities = "|".join(amenity_list)
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"{amenities}"]({south},{west},{north},{east});
      way["amenity"~"{amenities}"]({south},{west},{north},{east});
      relation["amenity"~"{amenities}"]({south},{west},{north},{east});
    );
    out center;
    """

    try:
        response = requests.get(overpass_url, params={"data": query})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.warning(f"Error loading POIs from Overpass API: {e}")
        return []

    # Route coordinates for distance check
    route_coords = [
        (node["x"], node["y"]) for node in G.nodes.values()
        if "x" in node and "y" in node
    ]

    results = []
    for element in data.get("elements", []):
        if "lat" not in element or "lon" not in element:
            continue
        lat, lon = element["lat"], element["lon"]
        # Approximate distance: find closest route node
        min_d = min(
            haversine_m(lon, lat, rc[0], rc[1]) for rc in route_coords
        ) if route_coords else 0
        if min_d <= buffer_m:
            amenity_type = element["tags"].get("amenity", "unknown")
            name = element["tags"].get("name", "") or amenity_type.capitalize()
            results.append({
                "osmid": element["id"],
                "name": name,
                "amenity": amenity_type,
                "lat": lat,
                "lon": lon,
                "dist_m": min_d
            })

    return results

    # Expand bbox a bit to ensure POIs along the route are captured
    lat_margin = (north - south) * 0.05
    lon_margin = (east - west) * 0.05
    north += lat_margin
    south -= lat_margin
    east += lon_margin
    west -= lon_margin

    # Overpass query
    amenities = "|".join(amenity_list)
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"~"{amenities}"]({south},{west},{north},{east});
      way["amenity"~"{amenities}"]({south},{west},{north},{east});
      relation["amenity"~"{amenities}"]({south},{west},{north},{east});
    );
    out center;
    """

    try:
        response = requests.get(overpass_url, params={"data": query})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.warning(f"Error loading POIs from Overpass API: {e}")
        return []

    route_coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in path]
    results = []

    for element in data.get("elements", []):
        if "lat" not in element or "lon" not in element:
            continue
        lat, lon = element["lat"], element["lon"]
        min_d = min(haversine_m(lon, lat, rc[0], rc[1]) for rc in route_coords)
        if min_d <= buffer_m:
            amenity_type = element["tags"].get("amenity", "unknown")
            name = element["tags"].get("name", "") or amenity_type.capitalize()
            results.append({
                "osmid": element["id"],
                "name": name,
                "amenity": amenity_type,
                "lat": lat,
                "lon": lon,
                "dist_m": min_d
            })
    return results
   
# -------------------------
# Helper to get readable street names
# -------------------------
def get_route_streets(G, path):
    streets = []
    for u, v in zip(path, path[1:]):
        data = G.get_edge_data(u, v)
        if not data:
            continue
        if isinstance(data, dict):
            edge_attr = min(data.values(), key=lambda x: x.get("length", float("inf")))
        else:
            edge_attr = data
        name = edge_attr.get("name") or edge_attr.get("highway") or "unnamed road"
        if isinstance(name, list):
            name = name[0]
        if not streets or streets[-1] != name:
            streets.append(name)
    return streets

# -------------------------
# Load graph (cached)
# -------------------------
# with st.spinner("Loading Pune graph (cached) ..."):
#     G = load_graph_cached()
# st.success(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")

# Session state initialization
for key in ["start_node", "end_node", "last_path", "last_pois_key", "pois_for_last_path"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "pois_for_last_path" else []

# -------------------------
# Layout - Left Column
# -------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🚗 Search & select start / destination")

    import osmnx as ox

    # --- Start place ---
    # Auto-fill if set from map
    if "start_coords" in st.session_state:
        start_value = f"{st.session_state['start_coords'][0]:.5f}, {st.session_state['start_coords'][1]:.5f}"
    else:
        start_value = ""

    start_query = st.text_input("Start place (e.g., 'Swargate, Pune')", value=start_value, key="start_query")

    if st.button("🔍 Search start suggestions"):
        try:
            suggestions = geocode_suggestions_cached(start_query)
            if suggestions:
                display = [
                    f"{s.get('display_name', s.get('name', 'Unknown'))} ({s['lat']:.5f}, {s['lon']:.5f})"
                    for s in suggestions
                ]
                selected_start = st.selectbox("Select starting location:", display, index=0, key="start_selectbox")
                chosen = suggestions[display.index(selected_start)]
                start_lat, start_lon = chosen["lat"], chosen["lon"]
                st.session_state["start_coords"] = (start_lat, start_lon)

                # Load graph if not already loaded
                if "G" not in st.session_state or st.session_state["G"] is None:
                    st.session_state["G"] = ox.graph_from_point((start_lat, start_lon), dist=5000, network_type="drive")

                G = st.session_state["G"]
                st.session_state["start_node"] = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
                st.success(f"✅ Start point set at ({start_lat:.5f}, {start_lon:.5f})")
            else:
                st.warning("No suggestions found.")
        except Exception as e:
            st.error(f"Geocoding error: {e}")


    # --- Destination place ---
    # Auto-fill if set from map
    if "end_coords" in st.session_state:
        end_value = f"{st.session_state['end_coords'][0]:.5f}, {st.session_state['end_coords'][1]:.5f}"
    else:
        end_value = ""

    end_query = st.text_input("Destination place (e.g., 'Kothrud, Pune')", value=end_value, key="end_query")

    if st.button("🔍 Search destination suggestions"):
        try:
            suggestions2 = geocode_suggestions_cached(end_query)
            if suggestions2:
                display2 = [
                    f"{s.get('display_name', s.get('name', 'Unknown'))} ({s['lat']:.5f}, {s['lon']:.5f})"
                    for s in suggestions2
                ]
                selected_end = st.selectbox("Select destination location:", display2, index=0, key="end_selectbox")
                chosen2 = suggestions2[display2.index(selected_end)]
                end_lat, end_lon = chosen2["lat"], chosen2["lon"]
                st.session_state["end_coords"] = (end_lat, end_lon)

                # Load graph if not already loaded
                if "G" not in st.session_state or st.session_state["G"] is None:
                    st.session_state["G"] = ox.graph_from_point((end_lat, end_lon), dist=5000, network_type="drive")

                G = st.session_state["G"]
                st.session_state["end_node"] = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)
                st.success(f"✅ End point set at ({end_lat:.5f}, {end_lon:.5f})")
            else:
                st.warning("No suggestions found.")
        except Exception as e:
            st.error(f"Geocoding error: {e}")

    # --- Summary ---
    st.markdown("**🧭 Current selection:**")
    st.write("Start node:", st.session_state.get("start_node"))
    st.write("End node:", st.session_state.get("end_node"))
   

# -------------------------
# Compute shortest 3 best routes (persistent + selectable)
# -------------------------
from itertools import islice

# Compute routes only when button clicked
if st.button("Compute best routes"):
    if not st.session_state.get("start_node") or not st.session_state.get("end_node"):
        st.error("Please set both start and end.")
    else:
        start_n = st.session_state["start_node"]
        end_n = st.session_state["end_node"]

        with st.spinner("Finding up to 3 alternate routes..."):
            try:
                # Convert MultiDiGraph → simple DiGraph
                if G.is_multigraph():
                    G_simple = nx.DiGraph()
                    for u, v, data in G.edges(data=True):
                        length = data.get("length", 1)
                        if G_simple.has_edge(u, v):
                            if length < G_simple[u][v]["weight"]:
                                G_simple[u][v]["weight"] = length
                        else:
                            G_simple.add_edge(u, v, weight=length)
                    G = G_simple

                # Get up to 3 shortest distinct paths
                all_paths = list(islice(nx.shortest_simple_paths(G, start_n, end_n, weight="weight"), 3))
                routes_info = []

                for i, path in enumerate(all_paths):
                    dist_m = nx.path_weight(G, path, weight="weight")
                    time_min = (dist_m / 1000) / 40 * 60  # assuming avg 40 km/h
                    routes_info.append({
                        "id": i + 1,
                        "path": path,
                        "distance_km": round(dist_m / 1000, 2),
                        "time_min": round(time_min, 1)
                    })

                # Save routes persistently in session state
                st.session_state["routes_list"] = routes_info
                st.session_state["chosen_route"] = routes_info[0]


                # Compute AI Recommendation based on distance, time, and POIs
                try:
                    for r in routes_info:
                        pois = pois_near_route_cached(tuple(r["path"]), buffer_m=200)
                        r["poi_count"] = len(pois or [])
                        # Weighted scoring (customizable)
                        r["score"] = (
                            (1 / r["distance_km"]) * 0.4 +
                            (1 / r["time_min"]) * 0.4 +
                            (r["poi_count"] * 0.2)
                        )
                    # Pick route with highest score
                    best_route = max(routes_info, key=lambda x: x["score"])
                    st.session_state["recommended_route"] = best_route

                except Exception as e:
                    st.warning(f"AI Recommendation skipped: {e}")


                # Load POIs for the first route initially
                with st.spinner("Finding landmarks (hospitals, police, fuel, etc.) along the route..."):
                    pois = pois_near_route_cached(tuple(routes_info[0]["path"]), buffer_m=200)
                    st.session_state["pois_for_last_path"] = pois or []

                st.success(f"✅ Found {len(routes_info)} route(s)! Choose one below:")

            except Exception as e:
                st.error(f"Error computing routes: {e}")
                st.session_state["routes_list"] = []
                st.session_state["chosen_route"] = None


# 🟢 Always show route chooser if routes exist (persistent)
if "routes_list" in st.session_state and st.session_state["routes_list"]:
    routes_info = st.session_state["routes_list"]
    chosen_label = (
        f"Route {st.session_state['chosen_route']['id']}: "
        f"{st.session_state['chosen_route']['distance_km']} km "
        f"(~{st.session_state['chosen_route']['time_min']} min)"
        if st.session_state.get("chosen_route") else None
    )

    chosen = st.radio(
        "Select route to display:",
        [f"Route {r['id']}: {r['distance_km']} km (~{r['time_min']} min)" for r in routes_info],
        index=next(
            (i for i, r in enumerate(routes_info) if f'Route {r["id"]}' in (chosen_label or "")),
            0
        ),
        key="route_selector"
    )


    # 💡 Display AI-recommended route
    if "recommended_route" in st.session_state:
        rec = st.session_state["recommended_route"]
        st.info(
            f"🤖 **AI Recommended Route:** Route {rec['id']} "
            f"({rec['distance_km']} km, ~{rec['time_min']} min, {rec['poi_count']} landmarks)"
        )



    # Update chosen route and POIs dynamically without rerun
    for r in routes_info:
        if f"Route {r['id']}" in chosen:
            if st.session_state.get("chosen_route") != r:
                st.session_state["chosen_route"] = r
                with st.spinner("Updating landmarks for selected route..."):
                    pois = pois_near_route_cached(tuple(r["path"]), buffer_m=200)
                    st.session_state["pois_for_last_path"] = pois or []
            break


# -------------------------
# Route Summary Table
# -------------------------
if "routes_list" in st.session_state and st.session_state["routes_list"]:
    st.markdown("### 🛣️ Route Summary")

    import pandas as pd
    summary_data = [
        {
            "Route": f"Route {r['id']}",
            "Distance (km)": r["distance_km"],
            "Estimated Time (min)": r["time_min"],
            "Landmarks": len(st.session_state.get("pois_for_last_path", [])) if r == st.session_state.get("chosen_route") else "-"
        }
        for r in st.session_state["routes_list"]
    ]
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, hide_index=True, use_container_width=True)
        


# -------------------------
# Map visualization (worldwide, click-to-set + autofill)
# -------------------------
with col2:
    st.subheader("🌍 Interactive map (click to set start or end)")

    from folium.plugins import LocateControl

    # Default map center (India)
    center_lat, center_lon = 20.5937, 78.9629

    # Use graph if available to recenter
    if "G" in st.session_state and st.session_state["G"] is not None:
        G = st.session_state["G"]
        if st.session_state.get("start_node") in G.nodes:
            center_lat, center_lon = G.nodes[st.session_state["start_node"]]["y"], G.nodes[st.session_state["start_node"]]["x"]
        elif st.session_state.get("end_node") in G.nodes:
            center_lat, center_lon = G.nodes[st.session_state["end_node"]]["y"], G.nodes[st.session_state["end_node"]]["x"]
        else:
            anynode = next(iter(G.nodes(data=True)))[1]
            center_lat, center_lon = anynode["y"], anynode["x"]

    # Initialize folium map (auto theme)
    tiles = "CartoDB dark_matter" if st.session_state.get("theme") == "Dark" else "CartoDB positron"
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles=tiles)
    LocateControl(auto_start=True).add_to(m)

    # Draw all routes if availaable
    if "routes_list" in st.session_state and st.session_state["routes_list"]:
        colors = ["red", "blue", "green"]
        chosen = st.session_state.get("chosen_route")
        for i, r in enumerate(st.session_state["routes_list"]):
            path = r["path"]
            if "G" in st.session_state and st.session_state["G"]:
                G = st.session_state["G"]
                route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
                folium.PolyLine(
                    route_coords,
                    color=colors[i % len(colors)],
                    weight=7 if r == chosen else 4,
                    opacity=0.9 if r == chosen else 0.5,
                    tooltip=f"Route {r['id']}: {r['distance_km']} km (~{r['time_min']} min)"
                ).add_to(m)

    # Draw POIs (landmarks) for the selected route
    for item in st.session_state.get("pois_for_last_path", []):
        amen = item.get("amenity", "").lower()
        lat, lon = item["lat"], item["lon"]
        name = item.get("name") or amen.capitalize()
        if "hospital" in amen:
            icon = folium.Icon(color="purple", icon="plus-sign")
        elif "police" in amen:
            icon = folium.Icon(color="darkblue", icon="star")
        elif "fuel" in amen or "gas" in amen:
            icon = folium.Icon(color="orange", icon="tint")
        elif "atm" in amen:
            icon = folium.Icon(color="green", icon="usd")
        else:
            icon = folium.Icon(color="gray")
        folium.Marker([lat, lon], tooltip=name, icon=icon).add_to(m)

        # Add start/end markers (safe version)
        if "G" in st.session_state and st.session_state["G"]:
            G = st.session_state["G"]

            # ---- START marker ----
            if st.session_state.get("start_node"):
                n = st.session_state["start_node"]
                if n in G.nodes:
                    folium.Marker(
                        [G.nodes[n]["y"], G.nodes[n]["x"]],
                        tooltip="Start",
                        icon=folium.Icon(color="green")
                    ).add_to(m)
                elif st.session_state.get("start_coords"):
                    # Fallback: use saved coordinates instead
                    lat, lon = st.session_state["start_coords"]
                    folium.Marker(
                        [lat, lon],
                        tooltip="Start (approx)",
                        icon=folium.Icon(color="lightgreen", icon="map-marker")
                    ).add_to(m)

            # ---- END marker ----
            if st.session_state.get("end_node"):
                n2 = st.session_state["end_node"]
                if n2 in G.nodes:
                    folium.Marker(
                        [G.nodes[n2]["y"], G.nodes[n2]["x"]],
                        tooltip="End",
                        icon=folium.Icon(color="red")
                    ).add_to(m)
                elif st.session_state.get("end_coords"):
                    # Fallback: use saved coordinates instead
                    lat2, lon2 = st.session_state["end_coords"]
                    folium.Marker(
                        [lat2, lon2],
                        tooltip="End (approx)",
                        icon=folium.Icon(color="lightred", icon="map-marker")
                    ).add_to(m)

    # Allow click-to-set
    set_start_by_click = st.checkbox("Set start by clicking map")
    set_end_by_click = st.checkbox("Set end by clicking map")
    m.add_child(folium.LatLngPopup())

    # Display the map
    map_result = st_folium(m, width=900, height=700)

    # Handle clicks to set start/end
    if map_result and map_result.get("last_clicked"):
        lat_clicked = map_result["last_clicked"]["lat"]
        lon_clicked = map_result["last_clicked"]["lng"]

        try:
            import osmnx as ox
            G_click = ox.graph_from_point((lat_clicked, lon_clicked), dist=5000, network_type="drive")
            st.session_state["G"] = G_click
            node_clicked = ox.distance.nearest_nodes(G_click, X=lon_clicked, Y=lat_clicked)

            if set_start_by_click:
                st.session_state["start_node"] = int(node_clicked)
                st.session_state["start_coords"] = (lat_clicked, lon_clicked)
                st.toast(f"✅ Start location set at {lat_clicked:.5f}, {lon_clicked:.5f}")
                st.rerun()

            elif set_end_by_click:
                st.session_state["end_node"] = int(node_clicked)
                st.session_state["end_coords"] = (lat_clicked, lon_clicked)
                st.toast(f"✅ End location set at {lat_clicked:.5f}, {lon_clicked:.5f}")
                st.rerun()

        except Exception as e:
            st.error(f"Error mapping click to graph node: {e}")


# -------------------------
# Landmarks summary
# -------------------------
st.markdown("---")
st.subheader("Landmarks found along the selected route")

pois_show = st.session_state.get("pois_for_last_path", [])
if not pois_show:
    st.write("No landmarks found (or compute a route first).")
else:
    grouped = {}
    for p in pois_show:
        a = p.get("amenity", "unknown")
        grouped.setdefault(a, []).append(p)

    for amen, items in grouped.items():
        st.markdown(f"**{amen.capitalize()} ({len(items)})**")
        for it in items:
            nm = it.get("name") or "(no name)"
            st.write(f"- {nm} — {it['lat']:.5f}, {it['lon']:.5f} (≈{int(it['dist_m'])} m from route)")