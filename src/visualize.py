import networkx as nx
import matplotlib.pyplot as plt


import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

def draw_graph(G, path=[], landmarks={}):
    # Custom node coordinates
    pos = {
        "A": (0, 0),
        "B": (2, 1),
        "C": (1, -1),
        "D": (4, 0),
        "E": (2, -2),
        "F": (5, -1)
    }

    # Draw nodes (all lightblue)
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=800)

    # Draw edges
    nx.draw_networkx_edges(G, pos, width=2)

    # Highlight path in red
    if path:
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, width=4, edge_color='red')

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    # Add landmark icons
    icon_files = {
    "hospital": "assets/hospital.png",
    "atm": "assets/atm.png",
    "police": "assets/police.png",
    "fuel": "assets/fuel.png"
    }


    ax = plt.gca()
    for node, lm_list in landmarks.items():
        if node in pos:
            for lm in lm_list:  # loop through all landmarks for this node
                if lm in icon_files:
                    img = mpimg.imread(icon_files[lm])
                    imagebox = OffsetImage(img, zoom=0.50)  # adjust zoom
                    ab = AnnotationBbox(imagebox, (pos[node][0], pos[node][1] - 0.25), frameon=False)
                    ax.add_artist(ab)



    plt.axis('off')
    return plt.gcf()
