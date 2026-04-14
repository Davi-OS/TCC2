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

    G = ox.graph_from_point(center, dist=2500, network_type="drive", simplify=True)
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


def build_distance_matrix_from_network(G, points: list[dict]):
    """
    Calcula a matriz de distâncias usando o grafo OSMnx já baixado.

    Garante que MST e visualização usem a mesma fonte de dados —
    elimina inconsistências entre OSRM e OSMnx.

    Usa nx.shortest_path com weight="length" (metros).
    Fallback para grafo não-dirigido se não houver caminho no dirigido.
    """
    import pandas as pd

    ids   = [p["id"] for p in points]
    n     = len(ids)
    matriz = {i: {j: 0 for j in ids} for i in ids}
    G_und  = None  # criado sob demanda

    total = n * (n - 1) // 2
    par   = 0

    for i in range(n):
        for j in range(i + 1, n):
            par += 1
            u_node = points[i]["osm_node"]
            v_node = points[j]["osm_node"]
            dist   = None

            try:
                path = nx.shortest_path(G, u_node, v_node, weight="length")
                dist = int(round(sum(
                    G[path[k]][path[k + 1]][0].get("length", 0)
                    for k in range(len(path) - 1)
                )))
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass

            if dist is None:
                if G_und is None:
                    G_und = ox.convert.to_undirected(G)
                try:
                    path = nx.shortest_path(G_und, u_node, v_node, weight="length")
                    dist = int(round(sum(
                        G_und[path[k]][path[k + 1]].get("length", 0)
                        for k in range(len(path) - 1)
                    )))
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    dist = 0
                    print(f"  [!] Sem rota: {ids[i]} ↔ {ids[j]}")

            matriz[ids[i]][ids[j]] = dist
            matriz[ids[j]][ids[i]] = dist
            print(f"  [{par:>2}/{total}] {ids[i]} ↔ {ids[j]}: {dist} m")

    print(f"  [OK] Matriz {n}×{n} calculada via OSMnx.")
    return pd.DataFrame(matriz, index=ids, columns=ids)


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
