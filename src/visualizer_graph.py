"""
Módulo: visualizer_graph.py
Gera todas as visualizações estáticas (PNG) do projeto:
- Grafo completo com todos os pontos e arestas
- AGM destacada sobre o grafo completo
- Passo a passo do Kruskal
- Passo a passo do Prim
- Gráfico comparativo de métricas
"""

import os
import matplotlib
matplotlib.use("Agg")  # backend sem GUI — compatível com qualquer ambiente
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


# Paleta de cores por tipo de ponto
TIPO_CORES = {
    "praça":      "#4CAF50",
    "saude":      "#F44336",
    "escola":     "#2196F3",
    "comercio":   "#FF9800",
    "religioso":  "#9C27B0",
    "transporte": "#00BCD4",
    "comunitario":"#795548",
    "esporte":    "#8BC34A",
}
COR_PADRAO = "#9E9E9E"


def _get_pos(G: nx.Graph) -> dict:
    """Posições dos nós baseadas em coordenadas geográficas reais (lon, lat)."""
    return {node: (data["lon"], data["lat"]) for node, data in G.nodes(data=True)}


def _node_colors(G: nx.Graph) -> list:
    return [TIPO_CORES.get(G.nodes[n]["tipo"], COR_PADRAO) for n in G.nodes()]


def plot_complete_graph(G: nx.Graph, output_path: str, bairro_label: str = "") -> None:
    """
    Desenha o grafo completo com todos os 10 nós e 45 arestas.
    Os pesos das arestas são exibidos em metros.
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    pos = _get_pos(G)
    node_colors = _node_colors(G)

    nx.draw_networkx_edges(G, pos, alpha=0.3, edge_color="#BDBDBD", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color=node_colors, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold", ax=ax)

    edge_labels = {(u, v): f"{d['weight']}m" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6, alpha=0.7, ax=ax)

    # Legenda de tipos
    patches = [
        mpatches.Patch(color=cor, label=tipo.capitalize())
        for tipo, cor in TIPO_CORES.items()
        if any(G.nodes[n]["tipo"] == tipo for n in G.nodes())
    ]
    ax.legend(handles=patches, loc="lower left", fontsize=8, title="Tipo de ponto")

    ax.set_title(
        f"Grafo Completo — Sistema de Coleta Seletiva Proposto\n{bairro_label}",
        fontsize=13, fontweight="bold", pad=15,
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  [OK] {output_path}")


def plot_mst_highlighted(
    G: nx.Graph,
    mst_edges: list[tuple],
    algo_name: str,
    output_path: str,
    bairro_label: str = "",
) -> None:
    """
    Desenha a AGM em destaque sobre o grafo completo (fundo cinza).
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    pos = _get_pos(G)
    node_colors = _node_colors(G)

    mst_edge_set = {(u, v) for _, u, v in mst_edges} | {(v, u) for _, u, v in mst_edges}
    non_mst_edges = [(u, v) for u, v in G.edges() if (u, v) not in mst_edge_set]
    mst_only = [(u, v) for u, v in G.edges() if (u, v) in mst_edge_set]

    nx.draw_networkx_edges(G, pos, edgelist=non_mst_edges, alpha=0.15, edge_color="#BDBDBD", ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=mst_only, width=3.5, edge_color="#1B5E20", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=900, node_color=node_colors, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", ax=ax)

    mst_weight = sum(w for w, _, _ in mst_edges)
    mst_label = {(u, v): f"{w}m" for w, u, v in mst_edges}
    mst_label.update({(v, u): f"{w}m" for w, u, v in mst_edges})
    mst_edge_labels = {(u, v): mst_label[(u, v)] for u, v in mst_only if (u, v) in mst_label}
    nx.draw_networkx_edge_labels(G, pos, mst_edge_labels, font_size=8, font_color="#1B5E20", ax=ax)

    titulo = f"Árvore Geradora Mínima — Algoritmo de {algo_name}\n"
    titulo += f"Peso total da AGM: {mst_weight} m  |  Rota estimada: {mst_weight * 2} m"
    if bairro_label:
        titulo += f"\n{bairro_label}"
    ax.set_title(titulo, fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.2)

    legend_handles = [
        mpatches.Patch(color="#1B5E20", label=f"AGM — {algo_name}"),
        mpatches.Patch(color="#BDBDBD", label="Arestas não utilizadas"),
    ]
    ax.legend(handles=legend_handles, loc="lower left", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  [OK] {output_path}")


def plot_kruskal_steps(
    execution_steps: list[dict],
    G: nx.Graph,
    mst_edges: list[tuple],
    output_path: str,
    bairro_label: str = "",
) -> None:
    """
    Grid de painéis mostrando a evolução do Kruskal passo a passo.
    Cada painel corresponde a uma aresta ACEITA.
    Arestas aceitas acumulam em verde; rejeitadas aparecem em vermelho no passo correspondente.
    """
    accepted_steps = [s for s in execution_steps if s["decisao"] == "ACEITA"]
    rejected_steps = [s for s in execution_steps if s["decisao"] == "REJEITA"]
    n_steps = len(accepted_steps)  # V-1 = 9 para 10 nós

    cols = 3
    rows = (n_steps + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 4.5))
    axes = axes.flatten()

    pos = _get_pos(G)
    node_colors = _node_colors(G)
    accumulated_mst = []

    # Mapear arestas rejeitadas por passo (agrupa rejeitadas antes de cada aceita)
    rejected_map = {}
    step_aceita_idx = 0
    pending_rejected = []
    for s in execution_steps:
        if s["decisao"] == "REJEITA":
            pending_rejected.append(s["aresta"])
        else:
            rejected_map[step_aceita_idx] = pending_rejected
            pending_rejected = []
            step_aceita_idx += 1

    for idx, step in enumerate(accepted_steps):
        ax = axes[idx]
        u, v = step["aresta"].split(" — ")
        weight = step["peso_m"]
        accumulated_mst.append((weight, u, v))

        acc_edge_set = {(a, b) for _, a, b in accumulated_mst} | {(b, a) for _, a, b in accumulated_mst}
        current_edge = {(u, v), (v, u)}
        rejected_edges_str = rejected_map.get(idx, [])

        def parse_edge(s):
            a, b = s.split(" — ")
            return (a, b), (b, a)

        all_graph_edges = list(G.edges())
        nx.draw_networkx_edges(G, pos, edgelist=all_graph_edges, alpha=0.1, edge_color="#BDBDBD", ax=ax)

        for rej_str in rejected_edges_str:
            (ra, rb), (rb2, ra2) = parse_edge(rej_str)
            rej_list = [(ra, rb)] if (ra, rb) in G.edges() else [(rb, ra)] if (rb, ra) in G.edges() else []
            if rej_list:
                nx.draw_networkx_edges(G, pos, edgelist=rej_list, width=2, edge_color="#F44336", alpha=0.6, ax=ax)

        prev_mst_edges = [(a, b) for _, a, b in accumulated_mst[:-1]]
        prev_mst_edges = [(a, b) if (a, b) in G.edges() else (b, a) for a, b in prev_mst_edges]
        if prev_mst_edges:
            nx.draw_networkx_edges(G, pos, edgelist=prev_mst_edges, width=2.5, edge_color="#4CAF50", ax=ax)

        new_edge = [(u, v)] if (u, v) in G.edges() else [(v, u)]
        nx.draw_networkx_edges(G, pos, edgelist=new_edge, width=4, edge_color="#1B5E20", ax=ax)

        nx.draw_networkx_nodes(G, pos, node_size=400, node_color=node_colors, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=7, font_weight="bold", ax=ax)

        ax.set_title(
            f"Passo {idx+1}: ACEITA {step['aresta']} ({weight}m)\n"
            f"Comp. restantes: {step['componentes_restantes']}",
            fontsize=8, pad=5,
        )
        ax.set_axis_off()

    # Oculta eixos extras
    for idx in range(n_steps, len(axes)):
        axes[idx].set_visible(False)

    suptitle = "Algoritmo de Kruskal — Evolução Passo a Passo\n"
    suptitle += "(Verde escuro = nova aresta aceita | Verde claro = AGM acumulada | Vermelho = aresta rejeitada)"
    if bairro_label:
        suptitle += f"\n{bairro_label}"
    fig.suptitle(suptitle, fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {output_path}")


def plot_prim_steps(
    execution_steps: list[dict],
    G: nx.Graph,
    output_path: str,
    bairro_label: str = "",
) -> None:
    """
    Grid de painéis mostrando a evolução do Prim passo a passo.
    Cada painel corresponde a uma aresta ACEITA (adição de nó à AGM).
    O "blob" verde cresce a cada passo a partir do nó inicial.
    """
    accepted_steps = [s for s in execution_steps if s["decisao"] == "ACEITA"]
    n_steps = len(accepted_steps)

    cols = 3
    rows = (n_steps + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 4.5))
    axes = axes.flatten()

    pos = _get_pos(G)
    node_colors_base = _node_colors(G)
    node_list = list(G.nodes())

    for idx, step in enumerate(accepted_steps):
        ax = axes[idx]
        visited = set(step["visitados"])
        u, v = step["aresta"].split(" — ")
        weight = step["peso_m"]

        # Cores: nós visitados em verde, novo nó em verde escuro, restantes em cinza
        colors = []
        for n in node_list:
            if n == v:
                colors.append("#1B5E20")
            elif n in visited:
                colors.append("#81C784")
            else:
                colors.append("#E0E0E0")

        # Arestas: da AGM (visitados) em verde, restantes em cinza claro
        acc_edges = []
        other_edges = []
        for a, b in G.edges():
            if a in visited and b in visited:
                acc_edges.append((a, b))
            else:
                other_edges.append((a, b))

        new_edge = [(u, v)] if (u, v) in G.edges() else [(v, u)]

        nx.draw_networkx_edges(G, pos, edgelist=other_edges, alpha=0.1, edge_color="#BDBDBD", ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=acc_edges, width=2.5, edge_color="#4CAF50", ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=new_edge, width=4, edge_color="#1B5E20", ax=ax)
        nx.draw_networkx_nodes(G, pos, node_size=400, node_color=colors, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=7, font_weight="bold", ax=ax)

        ax.set_title(
            f"Passo {idx+1}: adiciona {v} via {step['aresta']} ({weight}m)\n"
            f"Visitados: {sorted(visited)}",
            fontsize=7, pad=5,
        )
        ax.set_axis_off()

    for idx in range(n_steps, len(axes)):
        axes[idx].set_visible(False)

    suptitle = "Algoritmo de Prim — Evolução Passo a Passo\n"
    suptitle += "(Verde escuro = novo nó adicionado | Verde claro = AGM acumulada | Cinza = não visitado)"
    if bairro_label:
        suptitle += f"\n{bairro_label}"
    fig.suptitle(suptitle, fontsize=12, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {output_path}")


def plot_metrics_comparison(
    naive_metrics: dict,
    mst_metrics: dict,
    savings: dict,
    output_path: str,
    bairro_label: str = "",
) -> None:
    """
    Gráfico de barras comparando as métricas da rota AGM vs rota sequencial.
    4 subgráficos: distância, custo, CO₂, tempo.
    """
    fig, axes = plt.subplots(1, 4, figsize=(16, 6))

    metricas = [
        ("Distância (km)",   "distancia_km",           "km"),
        ("Custo (R$)",        "custo_combustivel_brl",   "R$"),
        ("CO₂ (kg)",          "co2_kg",                  "kg"),
        ("Tempo (min)",       "tempo_total_min",          "min"),
    ]

    cores = {"AGM (Kruskal/Prim)": "#1B5E20", "Sequencial": "#B71C1C"}

    for ax, (titulo, chave, unidade) in zip(axes, metricas):
        categorias = ["AGM\n(Kruskal/Prim)", "Sequencial"]
        valores = [mst_metrics[chave], naive_metrics[chave]]
        bar_cores = [cores["AGM (Kruskal/Prim)"], cores["Sequencial"]]

        bars = ax.bar(categorias, valores, color=bar_cores, alpha=0.85, width=0.5)

        for bar, val in zip(bars, valores):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.02,
                f"{val:.2f} {unidade}",
                ha="center", va="bottom", fontsize=9, fontweight="bold",
            )

        pct = savings.get(f"reducao_{chave.split('_')[0]}_pct", None)
        if pct is None:
            # tenta chave alternativa
            for k in savings:
                if "pct" in k:
                    pct = savings[k]
                    break

        ax.set_title(f"{titulo}\n(redução: {savings['reducao_distancia_pct']}%)" if chave == "distancia_km" else titulo,
                     fontsize=10, fontweight="bold")
        ax.set_ylabel(unidade)
        ax.set_ylim(0, max(valores) * 1.25)
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle(
        f"Comparação de Métricas: Rota AGM vs Rota Sequencial\n"
        f"Sistema de Coleta Seletiva — {bairro_label}",
        fontsize=12, fontweight="bold", y=1.02,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {output_path}")
