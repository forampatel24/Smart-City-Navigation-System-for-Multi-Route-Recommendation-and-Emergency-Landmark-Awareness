import heapq

def dijkstra(G, start, end):
    """
    Compute shortest path from start to end using Dijkstra's algorithm.
    G: NetworkX graph
    start, end: node names
    Returns: (total_distance, path_list)
    """
    queue = [(0, start, [])]  # (distance, current_node, path)
    seen = set()

    while queue:
        (dist, current, path) = heapq.heappop(queue)
        if current in seen:
            continue
        path = path + [current]
        seen.add(current)

        if current == end:
            return dist, path

        for neighbor in G.neighbors(current):
            if neighbor not in seen:
                weight = G[current][neighbor]["weight"]
                heapq.heappush(queue, (dist + weight, neighbor, path))

    return float("inf"), []

# def multi_stop_path(G, stops):
#     """
#     Compute path through multiple stops in order.
#     G: NetworkX graph
#     stops: list of nodes in order
#     Returns: (total_distance, full_path)
#     """
#     if len(stops) < 2:
#         return 0, stops

#     total_distance = 0
#     full_path = []

#     for i in range(len(stops)-1):
#         dist, path = dijkstra(G, stops[i], stops[i+1])
#         total_distance += dist
#         if i == 0:
#             full_path.extend(path)
#         else:
#             # skip the first node to avoid duplicates
#             full_path.extend(path[1:])

#     return total_distance, full_path
