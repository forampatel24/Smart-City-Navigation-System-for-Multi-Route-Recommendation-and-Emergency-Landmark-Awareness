from src.utils import load_graph
from src.algorithms import dijkstra
from src.visualize import draw_graph

# Load graph
G = load_graph()

# Find shortest path
distance, path = dijkstra(G, "A", "F")
print(f"Shortest distance from A to F: {distance}")
print(f"Path: {' -> '.join(path)}")

# Draw graph and highlight path
draw_graph(G, path)
