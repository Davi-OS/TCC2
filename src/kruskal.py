"""
Módulo: kruskal.py
Implementação manual do algoritmo de Kruskal para Árvore Geradora Mínima (AGM).

Estrutura de dados principal: Union-Find (Disjoint Set Union)
  - find() com path compression
  - union() com union by rank

Complexidade: O(E log E) dominado pela ordenação das arestas.
Para grafos densos (E ≈ V²), equivale a O(V² log V).
"""


class UnionFind:
    """
    Estrutura Union-Find (Conjuntos Disjuntos).

    Usada pelo Kruskal para detectar ciclos: se dois vértices de uma
    aresta já estão no mesmo componente, adicioná-la criaria um ciclo.

    Otimizações implementadas:
    - Path compression no find(): achata a árvore para futuras buscas.
    - Union by rank: a árvore menor é sempre anexada sob a maior,
      mantendo a altura logarítmica.
    """

    def __init__(self, nodes: list[str]):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, x: str) -> str:
        """
        Encontra o representante (raiz) do componente de x.
        Aplica path compression: todos os nós no caminho apontam
        diretamente para a raiz após esta chamada.
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, a: str, b: str) -> bool:
        """
        Une os componentes de a e b.

        Retorna True se a união foi realizada (componentes distintos).
        Retorna False se a e b já estavam no mesmo componente (ciclo).
        """
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False  # mesmo componente → adicionaria um ciclo

        # Union by rank: menor árvore sob a maior
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True

    def num_components(self) -> int:
        """Retorna o número de componentes distintos."""
        return len({self.find(n) for n in self.parent})


def kruskal_mst(
    edge_list: list[tuple],
    nodes: list[str],
) -> tuple[list[tuple], int, list[dict]]:
    """
    Executa o algoritmo de Kruskal para encontrar a AGM.

    Parâmetros:
        edge_list: lista de (peso, u, v) ORDENADA por peso crescente
                   (gerada por data_loader.build_edge_list)
        nodes:     lista de todos os IDs dos nós do grafo

    Retorna:
        mst_edges:       lista de (peso, u, v) das arestas na AGM
        total_weight:    soma dos pesos da AGM (em metros)
        execution_steps: rastreamento passo a passo para análise acadêmica
    """
    uf = UnionFind(nodes)
    mst_edges = []
    total_weight = 0
    execution_steps = []
    step = 0

    for weight, u, v in edge_list:
        step += 1
        componentes_antes = uf.num_components()
        aceita = uf.union(u, v)

        decision = "ACEITA" if aceita else "REJEITA"
        reason = (
            f"une componentes distintos ({uf.find(u)} e {uf.find(v)} antes da união)"
            if aceita
            else f"criaria ciclo — {u} e {v} já estão no mesmo componente"
        )

        execution_steps.append({
            "passo": step,
            "aresta": f"{u} — {v}",
            "peso_m": weight,
            "decisao": decision,
            "motivo": reason,
            "componentes_restantes": uf.num_components(),
        })

        if aceita:
            mst_edges.append((weight, u, v))
            total_weight += weight

        # AGM completa quando temos V-1 arestas
        if len(mst_edges) == len(nodes) - 1:
            break

    return mst_edges, total_weight, execution_steps


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_points, load_distance_matrix, build_edge_list

    base = os.path.dirname(os.path.dirname(__file__))
    points = load_points(os.path.join(base, "data", "pontos_coleta.csv"))
    matrix = load_distance_matrix(os.path.join(base, "data", "matriz_distancias.csv"))
    edges = build_edge_list(matrix)
    nodes = [p["id"] for p in points]

    mst_edges, total, steps = kruskal_mst(edges, nodes)

    print("=== ALGORITMO DE KRUSKAL ===\n")
    print(f"{'Passo':<6} {'Aresta':<12} {'Peso (m)':<10} {'Decisão':<8} {'Componentes':<12} Motivo")
    print("-" * 90)
    for s in steps:
        print(
            f"{s['passo']:<6} {s['aresta']:<12} {s['peso_m']:<10} "
            f"{s['decisao']:<8} {s['componentes_restantes']:<12} {s['motivo']}"
        )

    print(f"\nAGM Kruskal:")
    for w, u, v in mst_edges:
        print(f"  {u} — {v}: {w} m")
    print(f"\nPeso total da AGM: {total} m ({total/1000:.3f} km)")
