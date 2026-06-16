"""
Módulo: generate_diagram.py
Gera diagramas do sistema em PNG para uso no TCC.
Executar: python3 src/generate_diagram.py
"""

import os
import shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAMA DE SEQUÊNCIA
# ─────────────────────────────────────────────────────────────────────────────

# Participantes e suas cores
PARTICIPANTES = [
    ("Usuário",         "#1565C0", "#E3F2FD"),
    ("main.py",         "#2E7D32", "#E8F5E9"),
    ("OSRM API",        "#6A1B9A", "#F3E5F5"),
    ("OSMnx/OSM",       "#00695C", "#E0F2F1"),
    ("Kruskal\n+ Prim", "#E65100", "#FFF3E0"),
    ("metrics.py",      "#B71C1C", "#FFEBEE"),
    ("Saídas\nPNG/HTML","#37474F", "#ECEFF1"),
]

# Mensagens: (origem_idx, destino_idx, texto, tipo)
# tipo: "call" = seta sólida →  |  "return" = seta tracejada ← (mais clara)
MENSAGENS = [
    (0, 1, "python3 main.py",                         "call"),
    (1, 1, "load config.toml\n(bairro + pontos)",     "self"),
    (1, 2, "GET /table/v1/driving/\n(N × N pares)",   "call"),
    (2, 1, "matriz de distâncias (metros)",            "return"),
    (1, 3, "download street network\n(raio 1.500 m)", "call"),
    (3, 1, "grafo OSM (nós + arestas de rua)",        "return"),
    (1, 1, "build K₁₀ graph\n(NetworkX, 45 arestas)", "self"),
    (1, 4, "kruskal_mst(edges)",                      "call"),
    (4, 1, "AGM: 9 arestas, peso total",              "return"),
    (1, 4, "prim_mst(adj, start)",                    "call"),
    (4, 1, "AGM: 9 arestas, peso total",              "return"),
    (1, 1, "assert peso_k == peso_p ✓",               "self"),
    (1, 5, "compute_metrics(AGM)\ncompute_metrics(sequencial)", "call"),
    (5, 1, "distância · custo · tempo",               "return"),
    (1, 6, "plot 6×PNG\n+ mapa HTML",                 "call"),
    (6, 0, "outputs/grafos/*.png\noutputs/mapas/*.html", "return"),
]


def generate_sequence(output_path: str) -> None:
    N = len(PARTICIPANTES)
    N_MSG = len(MENSAGENS)

    # Layout: colunas para participantes, linhas para mensagens
    FIG_W = 3.0 * N
    LINE_H = 0.72          # altura por mensagem
    HEADER_H = 1.4         # altura do cabeçalho
    FOOTER_H = 0.6
    FIG_H = HEADER_H + N_MSG * LINE_H + FOOTER_H

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.set_xlim(-0.3, N - 0.7)
    ax.set_ylim(-FOOTER_H, HEADER_H + N_MSG * LINE_H)
    ax.axis("off")
    ax.invert_yaxis()      # Y cresce para baixo

    # Posições X das lifelines
    xs = list(range(N))

    # ── Cabeçalhos dos participantes ──────────────────────────────────────────
    BOX_W, BOX_H = 1.5, 0.55
    for i, (nome, borda, fundo) in enumerate(PARTICIPANTES):
        patch = FancyBboxPatch(
            (xs[i] - BOX_W / 2, -HEADER_H + 0.1), BOX_W, BOX_H,
            boxstyle="round,pad=0.04",
            facecolor=fundo, edgecolor=borda, linewidth=2.0, zorder=4,
        )
        ax.add_patch(patch)
        ax.text(xs[i], -HEADER_H + 0.1 + BOX_H / 2, nome,
                ha="center", va="center", fontsize=8.5, fontweight="bold",
                color="#212121", zorder=5, multialignment="center")

    # ── Lifelines (linhas tracejadas verticais) ────────────────────────────────
    LIFE_TOP = -HEADER_H + 0.65
    LIFE_BOT = N_MSG * LINE_H + 0.2
    for i, (_, borda, _) in enumerate(PARTICIPANTES):
        ax.plot([xs[i], xs[i]], [LIFE_TOP, LIFE_BOT],
                color="#B0BEC5", lw=1.2, ls="--", zorder=1)

    # ── Mensagens ─────────────────────────────────────────────────────────────
    ARROW_CALL   = dict(arrowstyle="-|>", color="#212121",   lw=1.5, mutation_scale=14)
    ARROW_RETURN = dict(arrowstyle="-|>", color="#78909C",   lw=1.2, mutation_scale=12)
    ARROW_SELF   = dict(arrowstyle="-|>", color="#212121",   lw=1.5, mutation_scale=14)

    for idx, (src, dst, texto, tipo) in enumerate(MENSAGENS):
        y = idx * LINE_H + 0.35    # Y da linha de mensagem

        # caixas de ativação (retângulo sobre a lifeline)
        ACT_W, ACT_H = 0.12, LINE_H * 0.7
        for p in {src, dst}:
            ax.add_patch(plt.Rectangle(
                (xs[p] - ACT_W / 2, y - ACT_H / 2), ACT_W, ACT_H,
                facecolor=PARTICIPANTES[p][2], edgecolor=PARTICIPANTES[p][1],
                linewidth=1.2, zorder=2,
            ))

        if tipo == "self":
            # Chamada reflexiva: seta em L à direita
            lx = xs[src] + 0.55
            ax.annotate(
                "", xy=(xs[src] + ACT_W / 2, y + 0.18),
                xytext=(xs[src] + ACT_W / 2, y - 0.18),
                arrowprops=dict(
                    arrowstyle="-|>", color="#212121", lw=1.4, mutation_scale=12,
                    connectionstyle="arc3,rad=-0.5",
                ),
                zorder=3,
            )
            ax.text(xs[src] + 0.62, y, texto,
                    ha="left", va="center", fontsize=7.5, color="#212121",
                    style="italic", zorder=5, multialignment="left")

        elif tipo == "call":
            direction = 1 if dst > src else -1
            x0 = xs[src] + direction * ACT_W / 2
            x1 = xs[dst] - direction * ACT_W / 2
            ax.annotate("", xy=(x1, y), xytext=(x0, y),
                        arrowprops=ARROW_CALL, zorder=3)
            mx = (x0 + x1) / 2
            ax.text(mx, y - 0.14, texto,
                    ha="center", va="bottom", fontsize=7.8, color="#212121",
                    fontweight="bold", zorder=5, multialignment="center")

        elif tipo == "return":
            direction = 1 if dst > src else -1
            x0 = xs[src] + direction * ACT_W / 2
            x1 = xs[dst] - direction * ACT_W / 2
            ax.annotate("", xy=(x1, y), xytext=(x0, y),
                        arrowprops=ARROW_RETURN, zorder=3)
            # linha tracejada sobre a seta
            ax.plot([x0, x1], [y, y], color="#90A4AE", lw=1.0, ls="--", zorder=2)
            mx = (x0 + x1) / 2
            ax.text(mx, y + 0.13, texto,
                    ha="center", va="top", fontsize=7.5, color="#546E7A",
                    style="italic", zorder=5, multialignment="center")

    # ── Título ────────────────────────────────────────────────────────────────
    ax.text((N - 1) / 2, -HEADER_H + 0.92,
            "Diagrama de Sequência — Pipeline de Otimização de Rotas de Coleta Seletiva\n"
            "Trabalho de Conclusão de Curso · PUC Minas · Sistemas de Informação",
            ha="center", va="bottom", fontsize=10, fontweight="bold", color="#212121")

    # ── Legenda ───────────────────────────────────────────────────────────────
    legend_handles = [
        mpatches.Patch(facecolor="#E3F2FD", edgecolor="#212121",
                       label="→  Chamada (seta sólida)"),
        mpatches.Patch(facecolor="#ECEFF1", edgecolor="#78909C",
                       label="⇠  Retorno (seta tracejada)"),
        mpatches.Patch(facecolor="#FFFFFF", edgecolor="#212121",
                       label="↩  Auto-chamada (operação interna)"),
    ]
    ax.legend(handles=legend_handles, loc="lower right",
              fontsize=7.5, framealpha=0.95, title="Convenções", title_fontsize=8,
              bbox_to_anchor=(N - 0.7, N_MSG * LINE_H + 0.1))

    plt.tight_layout(pad=0.3)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    grafos_dir = os.path.join(base, "outputs", "barreiro", "grafos")
    overleaf_dir = os.path.join(base, "texto_tcc", "overleaf_upload", "grafos")

    print("Gerando diagrama de sequência...")
    seq_out = os.path.join(grafos_dir, "diagrama_sequencia.png")
    generate_sequence(seq_out)

    if os.path.isdir(overleaf_dir):
        dst = os.path.join(overleaf_dir, "diagrama_sequencia.png")
        shutil.copy2(seq_out, dst)
        print(f"  [OK] {dst}")

    print("Concluído.")
