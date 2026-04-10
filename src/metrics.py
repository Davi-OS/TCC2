"""
Módulo: metrics.py
Calcula as métricas operacionais do sistema de coleta seletiva:
- Distância percorrida (m / km)
- Consumo e custo de combustível (L / R$)
- Emissão de CO₂ (kg)
- Tempo estimado de operação (min)

Constantes baseadas em:
- Consumo: CETESB (2023) — caminhão de coleta leve a diesel
- Emissão CO₂: IPCC (2023) — 2,640 kg CO₂/litro de diesel
- Preço combustível: ANP (média BH, abril/2026)
- Velocidade: referência operacional de coleta urbana (ABRELPE, 2022)

Nota sobre a rota na AGM:
  A Árvore Geradora Mínima fornece as conexões de menor custo entre todos os
  pontos. A rota real do caminhão percorrendo essa árvore equivale a um
  percurso DFS (busca em profundidade), onde cada aresta é percorrida duas
  vezes (uma de ida, uma de volta), exceto a última aresta de retorno ao
  depósito. Portanto: distância_rota_AGM ≈ 2 × peso_total_AGM.
  Mesmo assim, a rota AGM é significativamente mais eficiente que a sequencial.
"""


# --- Constantes operacionais ---
CONSUMO_CAMINHAO_L_POR_KM = 0.35    # litros/km (caminhão leve de coleta, diesel)
PRECO_DIESEL_BRL_POR_L = 6.20       # R$/litro (ANP, média BH, abril 2026)
CO2_KG_POR_LITRO_DIESEL = 2.640     # kg CO₂/litro diesel (IPCC 2023)
VELOCIDADE_MEDIA_KMH = 20.0         # km/h (coleta urbana, paradas frequentes)
TEMPO_PARADA_MIN = 5                # minutos por ponto de coleta


def naive_route_distance(
    points: list[dict],
    distance_matrix: dict[tuple, int],
) -> int:
    """
    Calcula a distância total da rota ingênua (sequencial).

    A rota ingênua visita os pontos na ordem em que aparecem no CSV:
      P01 → P02 → P03 → ... → P10 → P01 (retorno ao ponto inicial)

    Esta é a abordagem sem otimização, usada como baseline de comparação.
    Retorna a distância total em metros.
    """
    ids = [p["id"] for p in points]
    total = 0
    n = len(ids)
    for i in range(n):
        origem = ids[i]
        destino = ids[(i + 1) % n]  # volta ao início no último ponto
        total += distance_matrix.get((origem, destino), distance_matrix.get((destino, origem), 0))
    return total


def mst_route_distance(mst_edges: list[tuple]) -> int:
    """
    Estima a distância percorrida pelo caminhão ao seguir a rota da AGM.

    O caminhão percorre a árvore via DFS: cada aresta é traversada duas vezes
    (ida + volta), exceto pela última aresta de retorno ao depósito.
    Aproximação conservadora: distância_rota = 2 × peso_total_AGM.

    Retorna a distância estimada em metros.
    """
    peso_agm = sum(w for w, _, _ in mst_edges)
    return peso_agm * 2


def compute_metrics(distance_m: int, label: str, num_pontos: int) -> dict:
    """
    Calcula todas as métricas operacionais para uma dada distância.

    Parâmetros:
        distance_m:  distância total do percurso em metros
        label:       nome da estratégia (ex: "AGM (Kruskal/Prim)", "Sequencial")
        num_pontos:  número de pontos de coleta visitados

    Retorna dict com todas as métricas.
    """
    dist_km = distance_m / 1000
    litros = dist_km * CONSUMO_CAMINHAO_L_POR_KM
    custo_brl = litros * PRECO_DIESEL_BRL_POR_L
    co2_kg = litros * CO2_KG_POR_LITRO_DIESEL
    tempo_viagem_min = (dist_km / VELOCIDADE_MEDIA_KMH) * 60
    tempo_paradas_min = num_pontos * TEMPO_PARADA_MIN
    tempo_total_min = tempo_viagem_min + tempo_paradas_min

    return {
        "label": label,
        "distancia_m": distance_m,
        "distancia_km": round(dist_km, 3),
        "combustivel_l": round(litros, 3),
        "custo_combustivel_brl": round(custo_brl, 2),
        "co2_kg": round(co2_kg, 3),
        "tempo_viagem_min": round(tempo_viagem_min, 1),
        "tempo_paradas_min": tempo_paradas_min,
        "tempo_total_min": round(tempo_total_min, 1),
    }


def compare_routes(naive_metrics: dict, mst_metrics: dict) -> dict:
    """
    Compara a rota AGM com a rota sequencial e calcula as economias.

    Retorna um dict com as reduções absolutas e percentuais.
    """
    def reducao_pct(naive_val, mst_val):
        if naive_val == 0:
            return 0.0
        return round((naive_val - mst_val) / naive_val * 100, 1)

    return {
        "reducao_distancia_pct": reducao_pct(naive_metrics["distancia_m"], mst_metrics["distancia_m"]),
        "reducao_distancia_m": naive_metrics["distancia_m"] - mst_metrics["distancia_m"],
        "economia_combustivel_brl": round(naive_metrics["custo_combustivel_brl"] - mst_metrics["custo_combustivel_brl"], 2),
        "reducao_co2_kg": round(naive_metrics["co2_kg"] - mst_metrics["co2_kg"], 3),
        "reducao_tempo_min": round(naive_metrics["tempo_total_min"] - mst_metrics["tempo_total_min"], 1),
        "economia_anual_brl": round((naive_metrics["custo_combustivel_brl"] - mst_metrics["custo_combustivel_brl"]) * 365, 2),
        "reducao_co2_anual_kg": round((naive_metrics["co2_kg"] - mst_metrics["co2_kg"]) * 365, 1),
    }


def print_metrics_table(naive_metrics: dict, mst_metrics: dict, savings: dict) -> None:
    """Exibe tabela comparativa formatada no terminal."""
    print("\n" + "=" * 65)
    print(f"{'MÉTRICA':<30} {'AGM (Kruskal/Prim)':<18} {'Sequencial':<15}")
    print("=" * 65)

    rows = [
        ("Distância (km)",       f"{mst_metrics['distancia_km']:.3f}",        f"{naive_metrics['distancia_km']:.3f}"),
        ("Combustível (L)",      f"{mst_metrics['combustivel_l']:.3f}",        f"{naive_metrics['combustivel_l']:.3f}"),
        ("Custo combustível (R$)", f"{mst_metrics['custo_combustivel_brl']:.2f}", f"{naive_metrics['custo_combustivel_brl']:.2f}"),
        ("Emissão CO₂ (kg)",    f"{mst_metrics['co2_kg']:.3f}",               f"{naive_metrics['co2_kg']:.3f}"),
        ("Tempo total (min)",    f"{mst_metrics['tempo_total_min']:.1f}",       f"{naive_metrics['tempo_total_min']:.1f}"),
    ]

    for label, mst_val, naive_val in rows:
        print(f"  {label:<28} {mst_val:<18} {naive_val:<15}")

    print("-" * 65)
    print(f"\n  Redução de distância:     {savings['reducao_distancia_pct']}%")
    print(f"  Economia de combustível:  R$ {savings['economia_combustivel_brl']:.2f} por dia")
    print(f"  Economia anual estimada:  R$ {savings['economia_anual_brl']:.2f}")
    print(f"  Redução de CO₂:           {savings['reducao_co2_kg']:.3f} kg por dia")
    print(f"  Redução anual de CO₂:     {savings['reducao_co2_anual_kg']:.1f} kg/ano")
    print("=" * 65)


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data_loader import load_points, load_distance_matrix, build_edge_list
    from kruskal import kruskal_mst

    base = os.path.dirname(os.path.dirname(__file__))
    points = load_points(os.path.join(base, "data", "pontos_coleta.csv"))
    matrix = load_distance_matrix(os.path.join(base, "data", "matriz_distancias.csv"))
    edges = build_edge_list(matrix)
    nodes = [p["id"] for p in points]

    mst_edges, _, _ = kruskal_mst(edges, nodes)

    dist_agm = mst_route_distance(mst_edges)
    dist_naive = naive_route_distance(points, matrix)

    mst_m = compute_metrics(dist_agm, "AGM (Kruskal/Prim)", len(points))
    naive_m = compute_metrics(dist_naive, "Sequencial", len(points))
    savings = compare_routes(naive_m, mst_m)

    print_metrics_table(naive_m, mst_m, savings)
