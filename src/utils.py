import json
import networkx as nx

def load_graph(json_file="data/graph.json"):
    """Load city graph and landmarks from JSON file into NetworkX graph."""
    with open(json_file, "r") as f:
        data = json.load(f)

    G = nx.Graph()

    # Add nodes
    for node in data["nodes"]:
        G.add_node(node)

    # Add edges with current weight
    for edge in data["edges"]:
        src, dst, weight_dict = edge
        G.add_edge(src, dst, weight=weight_dict["current_weight"])

    landmarks = data.get("landmarks", {})

    return G, landmarks



