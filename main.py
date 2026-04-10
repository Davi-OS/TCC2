"""
main.py — Ponto de entrada do projeto TCC
Coleta Seletiva com Algoritmos de AGM — Heliópolis, Belo Horizonte (MG)

Autor: Davi de Oliveira Santos
Orientador: Bernardo Jeunon de Alencar
Instituição: PUC Minas — Sistemas de Informação

Execução:
    python main.py

Outputs gerados em:
    outputs/grafos/   → imagens PNG
    outputs/mapas/    → mapa interativo HTML
"""

import os
import sys

# Garante que src/ está no path independente de onde main.py é chamado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from data_loader import load_points, load_distance_matrix, build_edge_list
from graph_builder import build_networkx_graph, get_adjacency_list
from kruskal import kruskal_mst
from prim import prim_mst
from metrics import (
    naive_route_distance,
    mst_route_distance,
    compute_metrics,
    compare_routes,
    print_metrics_table,
)
from visualizer_graph import (
    plot_complete_graph,
    plot_mst_highlighted,
    plot_kruskal_steps,
    plot_prim_steps,
    plot_metrics_comparison,
)
from visualizer_map import (
    create_base_map,
    add_points_layer,
    add_complete_graph_layer,
    add_mst_layer,
    add_naive_route_layer,
    add_legend,
    save_map,
)

import networkx as nx


# ─── Caminhos ────────────────────────────────────────────────────────────────
DATA_DIR    = os.path.join(BASE_DIR, "data")
OUTPUT_GRAFOS = os.path.join(BASE_DIR, "outputs", "grafos")
OUTPUT_MAPAS  = os.path.join(BASE_DIR, "outputs", "mapas")

os.makedirs(OUTPUT_GRAFOS, exist_ok=True)
os.makedirs(OUTPUT_MAPAS, exist_ok=True)


def main():
    print("=" * 60)
    print("TCC — Coleta Seletiva com Algoritmos de AGM")
    print("Heliópolis, Belo Horizonte (MG)")
    print("=" * 60)

    # ─── 1. Carregar dados ────────────────────────────────────────
    print("\n[1/6] Carregando dados...")
    points = load_points(os.path.join(DATA_DIR, "pontos_coleta.csv"))
    matrix = load_distance_matrix(os.path.join(DATA_DIR, "matriz_distancias.csv"))
    edges  = build_edge_list(matrix)
    nodes  = [p["id"] for p in points]

    print(f"  Pontos de coleta:  {len(points)}")
    print(f"  Arestas no grafo:  {len(edges)}")

    # ─── 2. Construir grafo ───────────────────────────────────────
    print("\n[2/6] Construindo estruturas de grafo...")
    G   = build_networkx_graph(points, matrix)
    adj = get_adjacency_list(matrix)

    print(f"  Vértices: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}")
    print(f"  Grafo conexo: {nx.is_connected(G)}")

    # ─── 3. Executar algoritmos ───────────────────────────────────
    print("\n[3/6] Executando algoritmos de AGM...")

    mst_k, peso_k, steps_k = kruskal_mst(edges, nodes)
    print(f"  Kruskal — peso AGM: {peso_k} m ({peso_k/1000:.3f} km)")

    mst_p, peso_p, steps_p = prim_mst(adj, start_node="P01")
    print(f"  Prim    — peso AGM: {peso_p} m ({peso_p/1000:.3f} km)")

    # Validação: Kruskal e Prim devem produzir AGMs com o mesmo peso
    assert peso_k == peso_p, (
        f"ERRO: pesos divergem! Kruskal={peso_k} m, Prim={peso_p} m\n"
        "Verifique a matriz de distâncias (deve ser simétrica)."
    )
    print(f"  [VALIDAÇÃO OK] Ambos os algoritmos produziram AGM com {peso_k} m")

    # ─── 4. Calcular métricas ─────────────────────────────────────
    print("\n[4/6] Calculando métricas operacionais...")
    dist_agm   = mst_route_distance(mst_k)
    dist_naive = naive_route_distance(points, matrix)

    mst_m   = compute_metrics(dist_agm,   "AGM (Kruskal/Prim)", len(points))
    naive_m = compute_metrics(dist_naive, "Sequencial",          len(points))
    savings = compare_routes(naive_m, mst_m)

    print_metrics_table(naive_m, mst_m, savings)

    # ─── 5. Gerar visualizações estáticas ─────────────────────────
    print("\n[5/6] Gerando gráficos...")

    plot_complete_graph(
        G,
        os.path.join(OUTPUT_GRAFOS, "grafo_completo.png"),
    )
    plot_mst_highlighted(
        G, mst_k, "Kruskal",
        os.path.join(OUTPUT_GRAFOS, "agm_kruskal.png"),
    )
    plot_mst_highlighted(
        G, mst_p, "Prim",
        os.path.join(OUTPUT_GRAFOS, "agm_prim.png"),
    )
    plot_kruskal_steps(
        steps_k, G, mst_k,
        os.path.join(OUTPUT_GRAFOS, "kruskal_passos.png"),
    )
    plot_prim_steps(
        steps_p, G,
        os.path.join(OUTPUT_GRAFOS, "prim_passos.png"),
    )
    plot_metrics_comparison(
        naive_m, mst_m, savings,
        os.path.join(OUTPUT_GRAFOS, "comparacao_metricas.png"),
    )

    # ─── 6. Gerar mapa interativo ─────────────────────────────────
    print("\n[6/6] Gerando mapa interativo...")
    m = create_base_map(points)
    add_points_layer(m, points)
    add_complete_graph_layer(m, matrix, points)
    add_mst_layer(m, mst_k, points, algo_name="Kruskal", color="#1B5E20")
    add_mst_layer(m, mst_p, points, algo_name="Prim",    color="#0D47A1")
    add_naive_route_layer(m, points, matrix)
    add_legend(m)
    save_map(m, os.path.join(OUTPUT_MAPAS, "mapa_heliopolis.html"))

    # ─── Resumo final ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CONCLUÍDO! Arquivos gerados:")
    print(f"  outputs/grafos/grafo_completo.png")
    print(f"  outputs/grafos/agm_kruskal.png")
    print(f"  outputs/grafos/agm_prim.png")
    print(f"  outputs/grafos/kruskal_passos.png")
    print(f"  outputs/grafos/prim_passos.png")
    print(f"  outputs/grafos/comparacao_metricas.png")
    print(f"  outputs/mapas/mapa_heliopolis.html")
    print("=" * 60)


if __name__ == "__main__":
    main()
