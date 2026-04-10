"""
Módulo: graph_builder.py
Constrói as estruturas de grafo utilizadas pelos algoritmos:
- Grafo NetworkX (para visualização e validação)
- Lista de adjacência (para o algoritmo de Prim)
"""

import networkx as nx


def build_networkx_graph(
    points: list[dict],
    distance_matrix: dict[tuple, int],
) -> nx.Graph:
    """
    Constrói um grafo completo ponderado com NetworkX.

    Nós possuem atributos: nome, lat, lon, tipo, descricao.
    Arestas possuem atributo: weight (distância em metros).
    """
    G = nx.Graph()

    for p in points:
        G.add_node(
            p["id"],
            nome=p["nome"],
            lat=p["latitude"],
            lon=p["longitude"],
            tipo=p["tipo"],
            descricao=p["descricao"],
            # pos usado pelo NetworkX para desenho georreferenciado
            pos=(p["longitude"], p["latitude"]),
        )

    seen = set()
    for (u, v), weight in distance_matrix.items():
        pair = tuple(sorted([u, v]))
        if pair not in seen:
            seen.add(pair)
            G.add_edge(pair[0], pair[1], weight=weight)

    return G


def get_adjacency_list(
    distance_matrix: dict[tuple, int],
) -> dict[str, list[tuple]]:
    """
    Constrói a lista de adjacência para o algoritmo de Prim.

    Retorna dict {nó: [(vizinho, peso), ...]} para todos os nós.
    """
    adj: dict[str, list[tuple]] = {}

    for (u, v), weight in distance_matrix.items():
        if u not in adj:
            adj[u] = []
        adj[u].append((v, weight))

    # Garante que cada nó tem sua lista ordenada por peso (facilita debug)
    for node in adj:
        adj[node].sort(key=lambda x: x[1])

    return adj


if __name__ == "__main__":
    import os
    from data_loader import load_points, load_distance_matrix

    base = os.path.dirname(os.path.dirname(__file__))
    points = load_points(os.path.join(base, "data", "pontos_coleta.csv"))
    matrix = load_distance_matrix(os.path.join(base, "data", "matriz_distancias.csv"))

    G = build_networkx_graph(points, matrix)
    adj = get_adjacency_list(matrix)

    print(f"Grafo NetworkX:")
    print(f"  Vértices: {G.number_of_nodes()}")
    print(f"  Arestas:  {G.number_of_edges()}")
    print(f"  Conexo:   {nx.is_connected(G)}")

    print(f"\nLista de adjacência (exemplo P01):")
    for vizinho, peso in adj.get("P01", []):
        print(f"  P01 -> {vizinho}: {peso} m")
