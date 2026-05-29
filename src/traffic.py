import random

def update_traffic(G, factor_range=(1, 3)):
    """
    Simulate traffic by randomly increasing edge weights.
    factor_range: (min_multiplier, max_multiplier)
    """
    for u, v, data in G.edges(data=True):
        base = data.get("base_weight", data["weight"])
        factor = random.uniform(*factor_range)
        data["weight"] = base * factor
