"""
Módulo: prim.py
Implementação manual do algoritmo de Prim para Árvore Geradora Mínima (AGM).

Estrutura de dados principal: heap de mínimo (min-heap)
  - Usa o módulo heapq da biblioteca padrão do Python
  - O heap armazena (peso, nó_origem, nó_destino)

Complexidade: O(E log V) com heap binário.
Para grafos densos (E ≈ V²), equivale a O(V² log V),
mas na prática é mais eficiente que Kruskal em grafos esparsos.

Diferença conceitual em relação ao Kruskal:
  - Kruskal: olha para todas as arestas globalmente, ordena e constrói a AGM
    adicionando as menores sem criar ciclos (Union-Find).
  - Prim: cresce a AGM como um "blob" a partir de um nó inicial,
    sempre expandindo pela aresta mais barata que conecta a um nó ainda não visitado.
"""

import heapq


def prim_mst(
    adjacency_list: dict[str, list[tuple]],
    start_node: str,
) -> tuple[list[tuple], int, list[dict]]:
    """
    Executa o algoritmo de Prim para encontrar a AGM.

    Parâmetros:
        adjacency_list: dict {nó: [(vizinho, peso), ...]}
                        gerado por graph_builder.get_adjacency_list
        start_node:     nó inicial da expansão (qualquer nó do grafo)

    Retorna:
        mst_edges:       lista de (peso, u, v) das arestas na AGM
        total_weight:    soma dos pesos da AGM (em metros)
        execution_steps: rastreamento passo a passo para análise acadêmica
    """
    visited = {start_node}
    mst_edges = []
    total_weight = 0
    execution_steps = []
    step = 0

    # Inicializa o heap com todas as arestas do nó inicial
    heap = [(peso, start_node, vizinho) for vizinho, peso in adjacency_list[start_node]]
    heapq.heapify(heap)

    all_nodes = set(adjacency_list.keys())

    while heap and len(visited) < len(all_nodes):
        peso, u, v = heapq.heappop(heap)
        step += 1

        if v in visited:
            execution_steps.append({
                "passo": step,
                "aresta": f"{u} — {v}",
                "peso_m": peso,
                "decisao": "IGNORADA",
                "motivo": f"{v} já está na AGM",
                "visitados": sorted(visited),
                "tamanho_heap": len(heap),
            })
            continue

        # v ainda não está na AGM → aceita a aresta
        visited.add(v)
        mst_edges.append((peso, u, v))
        total_weight += peso

        execution_steps.append({
            "passo": step,
            "aresta": f"{u} — {v}",
            "peso_m": peso,
            "decisao": "ACEITA",
            "motivo": f"menor aresta que conecta {v} à AGM atual",
            "visitados": sorted(visited),
            "tamanho_heap": len(heap),
        })

        # Adiciona ao heap as arestas do novo nó para vizinhos não visitados
        for vizinho, w in adjacency_list[v]:
            if vizinho not in visited:
                heapq.heappush(heap, (w, v, vizinho))

    return mst_edges, total_weight, execution_steps


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_points, load_distance_matrix
    from graph_builder import get_adjacency_list

    base = os.path.dirname(os.path.dirname(__file__))
    points = load_points(os.path.join(base, "data", "pontos_coleta.csv"))
    matrix = load_distance_matrix(os.path.join(base, "data", "matriz_distancias.csv"))
    adj = get_adjacency_list(matrix)

    mst_edges, total, steps = prim_mst(adj, start_node="P01")

    print("=== ALGORITMO DE PRIM (início: P01) ===\n")
    print(f"{'Passo':<6} {'Aresta':<12} {'Peso (m)':<10} {'Decisão':<8} {'Heap':<6} Visitados")
    print("-" * 90)
    for s in steps:
        print(
            f"{s['passo']:<6} {s['aresta']:<12} {s['peso_m']:<10} "
            f"{s['decisao']:<8} {s['tamanho_heap']:<6} {s['visitados']}"
        )

    print(f"\nAGM Prim:")
    for w, u, v in mst_edges:
        print(f"  {u} — {v}: {w} m")
    print(f"\nPeso total da AGM: {total} m ({total/1000:.3f} km)")
