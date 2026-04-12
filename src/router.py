"""
Módulo: router.py
Gerencia a malha viária real (OpenStreetMap via OSMnx) e o roteamento
pelas ruas entre os pontos de coleta.

Funções principais:
  download_or_load_street_network() — baixa ou carrega do cache
  snap_points_to_network()          — encaixa cada ponto no nó OSM mais próximo
  get_route_coords()                — caminho mais curto pelas ruas entre dois nós

Cache: o grafo OSM é salvo em cache/{slug}/street_network.graphml
       para evitar re-downloads a cada execução.
"""

import os
import networkx as nx
import osmnx as ox


def download_or_load_street_network(points: list[dict], cache_path: str):
    """
    Baixa a malha viária de dirigir que cobre todos os pontos de coleta.

    Usa raio de 1.500 m a partir do centróide dos pontos.
    Se já existir cache em cache_path, carrega de lá.

    Retorna um MultiDiGraph do OSMnx (grafo dirigido da rede viária).
    """
    if os.path.exists(cache_path):
        print(f"  Malha viária carregada do cache: {os.path.basename(cache_path)}")
        return ox.load_graphml(cache_path)

    lats = [p["latitude"] for p in points]
    lons = [p["longitude"] for p in points]
    center = (sum(lats) / len(lats), sum(lons) / len(lons))

    print(f"  Baixando malha viária do OpenStreetMap...")
    print(f"  Centro: ({center[0]:.4f}, {center[1]:.4f}) | raio: 1.500 m")

    G = ox.graph_from_point(center, dist=1500, network_type="drive", simplify=True)
    ox.save_graphml(G, cache_path)
    print(f"  Malha salva em cache: {os.path.basename(cache_path)}")
    return G


def snap_points_to_network(G, points: list[dict]) -> list[dict]:
    """
    Encaixa cada ponto de coleta no nó OSM mais próximo da malha viária.

    Adiciona 'osm_node', 'snapped_lat' e 'snapped_lon' em cada ponto.
    """
    lons = [p["longitude"] for p in points]
    lats = [p["latitude"] for p in points]

    nearest = ox.nearest_nodes(G, lons, lats)

    for p, node in zip(points, nearest):
        p["osm_node"]    = node
        p["snapped_lat"] = G.nodes[node]["y"]
        p["snapped_lon"] = G.nodes[node]["x"]

    return points


def get_route_coords(G, node_u: int, node_v: int) -> list[tuple]:
    """
    Retorna lista de (lat, lon) do caminho mais curto entre node_u e node_v.

    Tenta dirigido → não-dirigido → linha reta como fallback.
    """
    try:
        route = nx.shortest_path(G, node_u, node_v, weight="length")
        return [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pass

    try:
        G_und = ox.convert.to_undirected(G)
        route = nx.shortest_path(G_und, node_u, node_v, weight="length")
        return [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pass

    # Fallback: linha reta
    return [
        (G.nodes[node_u]["y"], G.nodes[node_u]["x"]),
        (G.nodes[node_v]["y"], G.nodes[node_v]["x"]),
    ]
