"""
main.py — Ponto de entrada do projeto TCC
Coleta Seletiva com Algoritmos de AGM

Autor: Davi de Oliveira Santos
Orientador: Bernardo Jeunon de Alencar
Instituição: PUC Minas — Sistemas de Informação

Execução:
    python3 main.py

O bairro e os pontos de coleta são configurados em config.toml.
A matriz de distâncias é gerada automaticamente via OSRM na 1ª execução
e cacheada em cache/{slug}/matriz_distancias.csv.

Outputs gerados em:
    outputs/{slug}/grafos/   → imagens PNG
    outputs/{slug}/mapas/    → mapa interativo HTML
"""

import os
import sys

# Garante que src/ está no path independente de onde main.py é chamado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from config_loader import load_config, get_points, get_bairro_label, get_slug, load_or_build_matrix
from data_loader import build_edge_list
from router import download_or_load_street_network, snap_points_to_network
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


def main():
    # ─── Carregar configuração ────────────────────────────────────
    CONFIG_PATH = os.path.join(BASE_DIR, "config.toml")
    cfg          = load_config(CONFIG_PATH)
    points       = get_points(cfg)
    bairro_label = get_bairro_label(cfg)
    slug         = get_slug(cfg)

    OUTPUT_GRAFOS = os.path.join(BASE_DIR, "outputs", slug, "grafos")
    OUTPUT_MAPAS  = os.path.join(BASE_DIR, "outputs", slug, "mapas")
    os.makedirs(OUTPUT_GRAFOS, exist_ok=True)
    os.makedirs(OUTPUT_MAPAS, exist_ok=True)

    print("=" * 60)
    print("TCC — Coleta Seletiva com Algoritmos de AGM")
    print(bairro_label)
    print("=" * 60)

    # ─── 1. Malha viária real (OSMnx) ────────────────────────────
    print("\n[1/7] Baixando malha viária (OpenStreetMap)...")
    CACHE_STREETS = os.path.join(BASE_DIR, "cache", slug, "street_network.graphml")
    G_streets = download_or_load_street_network(points, CACHE_STREETS)
    points    = snap_points_to_network(G_streets, points)
    print(f"  Nós na malha: {G_streets.number_of_nodes()} | Arestas: {G_streets.number_of_edges()}")

    # ─── 2. Carregar dados ────────────────────────────────────────
    print("\n[2/7] Carregando dados...")
    matrix = load_or_build_matrix(cfg, BASE_DIR, G_streets=G_streets, points_snapped=points)
    edges  = build_edge_list(matrix)
    nodes  = [p["id"] for p in points]

    print(f"  Pontos de coleta:  {len(points)}")
    print(f"  Arestas no grafo:  {len(edges)}")

    # ─── 3. Construir grafo ───────────────────────────────────────
    print("\n[3/7] Construindo estruturas de grafo...")
    G   = build_networkx_graph(points, matrix)
    adj = get_adjacency_list(matrix)

    print(f"  Vértices: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}")
    print(f"  Grafo conexo: {nx.is_connected(G)}")

    # ─── 4. Executar algoritmos ───────────────────────────────────
    print("\n[4/7] Executando algoritmos de AGM...")

    mst_k, peso_k, steps_k = kruskal_mst(edges, nodes)
    print(f"  Kruskal — peso AGM: {peso_k} m ({peso_k/1000:.3f} km)")

    start_node = points[0]["id"]
    mst_p, peso_p, steps_p = prim_mst(adj, start_node=start_node)
    print(f"  Prim    — peso AGM: {peso_p} m ({peso_p/1000:.3f} km)")

    assert peso_k == peso_p, (
        f"ERRO: pesos divergem! Kruskal={peso_k} m, Prim={peso_p} m\n"
        "Verifique a matriz de distâncias (deve ser simétrica)."
    )
    print(f"  [VALIDAÇÃO OK] Ambos os algoritmos produziram AGM com {peso_k} m")

    # ─── 5. Calcular métricas ─────────────────────────────────────
    print("\n[5/7] Calculando métricas operacionais...")
    dist_agm   = mst_route_distance(mst_k)
    dist_naive = naive_route_distance(points, matrix)

    mst_m   = compute_metrics(dist_agm,   "AGM (Kruskal/Prim)", len(points))
    naive_m = compute_metrics(dist_naive, "Sequencial",          len(points))
    savings = compare_routes(naive_m, mst_m)

    print_metrics_table(naive_m, mst_m, savings)

    # ─── 6. Gerar visualizações estáticas ─────────────────────────
    print("\n[6/7] Gerando gráficos...")

    plot_complete_graph(
        G,
        os.path.join(OUTPUT_GRAFOS, "grafo_completo.png"),
        bairro_label=bairro_label,
    )
    plot_mst_highlighted(
        G, mst_k, "Kruskal",
        os.path.join(OUTPUT_GRAFOS, "agm_kruskal.png"),
        bairro_label=bairro_label,
    )
    plot_mst_highlighted(
        G, mst_p, "Prim",
        os.path.join(OUTPUT_GRAFOS, "agm_prim.png"),
        bairro_label=bairro_label,
    )
    plot_kruskal_steps(
        steps_k, G, mst_k,
        os.path.join(OUTPUT_GRAFOS, "kruskal_passos.png"),
        bairro_label=bairro_label,
    )
    plot_prim_steps(
        steps_p, G,
        os.path.join(OUTPUT_GRAFOS, "prim_passos.png"),
        bairro_label=bairro_label,
    )
    plot_metrics_comparison(
        naive_m, mst_m, savings,
        os.path.join(OUTPUT_GRAFOS, "comparacao_metricas.png"),
        bairro_label=bairro_label,
    )

    # ─── 7. Gerar mapa interativo ─────────────────────────────────
    print("\n[7/7] Gerando mapa interativo...")
    m = create_base_map(points, bairro_label=bairro_label)
    add_points_layer(m, points)
    add_complete_graph_layer(m, matrix, points)
    add_mst_layer(m, mst_k, points, algo_name="Kruskal", color="#1B5E20", G_streets=G_streets)
    add_mst_layer(m, mst_p, points, algo_name="Prim",    color="#0D47A1", G_streets=G_streets)
    add_naive_route_layer(m, points, matrix, G_streets=G_streets)
    add_legend(m)
    save_map(m, os.path.join(OUTPUT_MAPAS, f"mapa_{slug}.html"))

    # ─── Resumo final ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CONCLUÍDO! Arquivos gerados:")
    print(f"  outputs/{slug}/grafos/grafo_completo.png")
    print(f"  outputs/{slug}/grafos/agm_kruskal.png")
    print(f"  outputs/{slug}/grafos/agm_prim.png")
    print(f"  outputs/{slug}/grafos/kruskal_passos.png")
    print(f"  outputs/{slug}/grafos/prim_passos.png")
    print(f"  outputs/{slug}/grafos/comparacao_metricas.png")
    print(f"  outputs/{slug}/mapas/mapa_{slug}.html")
    print(f"  (Matriz e rotas calculadas via OSMnx — fonte única de dados)")
    print("=" * 60)


if __name__ == "__main__":
    main()
