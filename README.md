# Smart City Navigation System for Multi-Route Recommendation and Emergency Landmark Awareness

## Overview

Smart City Navigation System is a Python-based route planning and visualization platform that uses real-world OpenStreetMap (OSM) road networks to compute optimal routes between locations.

The project combines classical graph algorithms with modern mapping technologies to provide:

* Shortest path computation
* Alternative route generation
* Interactive map-based navigation
* Landmark discovery along routes
* Traffic-aware routing simulation
* AI-assisted route recommendation

## Features

### Route Planning

* Find shortest paths between locations
* Generate multiple alternative routes
* Estimate travel distance and travel time

### Interactive Mapping

* Worldwide map support using OpenStreetMap
* Click-to-select start and destination points
* Dynamic route visualization with Folium

### Landmark Discovery

Searches for nearby:

* Hospitals
* ATMs
* Fuel Stations
* Police Stations

along the selected route.

### AI Route Recommendation

Routes are ranked using:

* Distance
* Estimated travel time
* Number of nearby landmarks

to recommend the most practical route.

### Traffic Simulation

Supports dynamic edge-weight modification to simulate traffic conditions and study routing behavior under changing network states.

---

## Technologies Used

### Backend

* Python
* NetworkX
* OSMnx

### Frontend

* Streamlit
* Folium

### Geospatial Tools

* OpenStreetMap
* Geopy
* Shapely

---

## Project Structure

```text
├── app.py
├── requirements.txt
├── src/
│   ├── algorithms.py
│   ├── osm_loader.py
│   ├── osm_utils.py
│   ├── traffic.py
│   ├── utils.py
│   └── visualize.py
├── data/
│   └── graph.json
├── assets/
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/forampatel24/Smart-City-Navigation-System-for-Multi-Route-Recommendation-and-Emergency-Landmark-Awareness.git smartnav
cd smartnav
```

### Create Virtual Environment

```bash
python -m venv venv
```

Activate:

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Application

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

## Algorithms Used

### Dijkstra's Algorithm

Computes the shortest path between source and destination nodes based on edge weights.

### K-Shortest Paths

Used to generate multiple route alternatives.

### Weighted Route Ranking

Combines:

* Distance
* Travel Time
* Nearby Landmarks

to recommend the best route.

---

## Research Publication

This project was developed as part of an academic research initiative in the domain of **Smart City Navigation**, **Route Optimization**, and **Intelligent Transportation Systems**.

### Publication Status

**Accepted at:**

**2026 International Conference on Emerging Smart Computing and Informatics (ESCI), IEEE**

### Paper Title

**Smart City Navigation System for Multi-Route Recommendation and Emergency Landmark Awareness**

### Abstract

SmartNav is a smart city navigation framework that combines graph-based route optimization with emergency landmark awareness. Using OpenStreetMap, OSMnx, NetworkX, and Folium, the system generates multiple alternative routes between source and destination locations and recommends the most balanced route using a rule-based scoring model that considers travel distance, estimated travel time, and nearby emergency points of interest such as hospitals, fuel stations, and police stations.

### Research Paper

[View Research Paper](./doc/Research_Paper%20doc.docx)

### Authors

- Foram Patel
- Om Ganjewar
- Manthan Gadiya
- Pragati Jadhav
- Sanskar Gogawale

**Guide:** Prof. Sheela Chinchmalatpure

**Department of Artificial Intelligence and Data Science**  
Vishwakarma Institute of Technology, Pune

## Future Improvements

* Real-time traffic integration
* Weather-aware routing
* Public transport support
* Accident detection and rerouting
* Machine Learning based travel-time prediction
* User authentication and route history

---

## Academic Relevance

This project demonstrates practical applications of:

* Graph Theory
* Shortest Path Algorithms
* Geographic Information Systems (GIS)
* Smart City Infrastructure
* Intelligent Transportation Systems

---

## Author

Developed as an academic project for studying graph algorithms, intelligent navigation systems, and smart city technologies.
