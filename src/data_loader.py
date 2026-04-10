"""
Módulo: data_loader.py
Responsável por carregar e validar os dados do projeto:
- Pontos de coleta (CSV)
- Matriz de distâncias (CSV)
- Construção da lista de arestas para Kruskal
"""

import pandas as pd


def load_points(csv_path: str) -> list[dict]:
    """
    Carrega os pontos de coleta a partir de um CSV.

    Retorna lista de dicts com as chaves:
      id, nome, latitude, longitude, tipo, descricao
    """
    df = pd.read_csv(csv_path)
    required = {"id", "nome", "latitude", "longitude", "tipo", "descricao"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV de pontos faltando colunas: {missing}")
    return df.to_dict(orient="records")


def load_distance_matrix(csv_path: str) -> dict[tuple, int]:
    """
    Carrega a matriz de distâncias a partir de um CSV quadrado.

    O CSV deve ter o ID dos pontos como índice e como cabeçalho.
    Retorna dict {(Pi, Pj): distancia_metros} para todos os pares.
    Garante simetria: d[i][j] = d[j][i] = (d[i][j] + d[j][i]) // 2.
    """
    df = pd.read_csv(csv_path, index_col=0)

    nodes = list(df.index)
    distances = {}

    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            # Garante simetria com média inteira
            d_ij = int(df.loc[i, j])
            d_ji = int(df.loc[j, i])
            dist = (d_ij + d_ji) // 2
            distances[(i, j)] = dist

    return distances


def build_edge_list(distance_matrix: dict[tuple, int]) -> list[tuple]:
    """
    Constrói a lista de arestas ordenada por peso (crescente) para Kruskal.

    Cada aresta é representada como (peso, nó_u, nó_v),
    incluindo cada par apenas uma vez (u < v lexicograficamente).

    Retorna lista de tuplas (peso, u, v) ordenada por peso.
    """
    seen = set()
    edges = []

    for (u, v), weight in distance_matrix.items():
        pair = tuple(sorted([u, v]))
        if pair not in seen:
            seen.add(pair)
            edges.append((weight, pair[0], pair[1]))

    edges.sort()
    return edges


if __name__ == "__main__":
    import os

    base = os.path.dirname(os.path.dirname(__file__))
    points = load_points(os.path.join(base, "data", "pontos_coleta.csv"))
    matrix = load_distance_matrix(os.path.join(base, "data", "matriz_distancias.csv"))
    edges = build_edge_list(matrix)

    print(f"Pontos carregados: {len(points)}")
    for p in points:
        print(f"  {p['id']} - {p['nome']} ({p['tipo']})")

    print(f"\nPares de distâncias: {len(matrix)}")
    print(f"Arestas únicas (lista para Kruskal): {len(edges)}")
    print(f"\nAs 5 menores distâncias:")
    for w, u, v in edges[:5]:
        print(f"  {u} <-> {v}: {w} m")
