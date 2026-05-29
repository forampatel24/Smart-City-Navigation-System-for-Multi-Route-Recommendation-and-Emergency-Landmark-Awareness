# src/osm_loader.py
import osmnx as ox
import networkx as nx

def load_city_graph(place_name="Pune, India"):
    # Download street network
    G = ox.graph_from_place(place_name, network_type="drive")

    # Convert to undirected (NetworkX native)
    G = G.to_undirected()

    # Ensure it's a MultiDiGraph (required by plot_graph_route)
    if not isinstance(G, nx.MultiDiGraph):
        G = nx.MultiDiGraph(G)

    return G

