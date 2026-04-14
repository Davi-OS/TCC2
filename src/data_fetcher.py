"""
Módulo: data_fetcher.py
Busca distâncias reais de ruas usando a API pública do OSRM
(Open Source Routing Machine — baseado no OpenStreetMap).

API utilizada: http://router.project-osrm.org (gratuita, sem chave)
Endpoint: /table/v1/driving/ — retorna matriz N×N em uma única requisição
Modo: "driving" (distância por vias, equivale ao trajeto de caminhão)

Execução:
    python3 src/data_fetcher.py

O script:
  1. Lê os pontos de config.toml (via config_loader)
  2. Faz UMA requisição ao endpoint /table para obter toda a matriz
  3. Salva em cache/{slug}/matriz_distancias.csv

Tempo estimado: ~2-3 segundos (1 requisição para N pontos).
Requer conexão com a internet.
"""

import os
import sys
import time
import requests
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))


OSRM_TABLE_URL = "http://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance"
MAX_TENTATIVAS = 3


def construir_matriz_osrm(points: list[dict]) -> pd.DataFrame:
    """
    Constrói a matriz de distâncias completa em UMA única requisição ao OSRM.

    Usa o endpoint /table/v1/ que retorna uma matriz N×N diretamente,
    em vez de fazer N*(N-1)/2 chamadas individuais ao /route.

    Retorna um DataFrame quadrado com IDs dos pontos como índice e colunas.
    """
    ids    = [p["id"] for p in points]
    n      = len(ids)
    coords = ";".join(f"{p['longitude']},{p['latitude']}" for p in points)
    url    = OSRM_TABLE_URL.format(coords=coords)

    dados = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(url, timeout=30)
            dados    = resposta.json()
            if dados.get("code") != "Ok":
                raise ValueError(f"OSRM retornou código inesperado: {dados.get('code')}")
            break
        except Exception as e:
            print(f"  [Tentativa {tentativa}/{MAX_TENTATIVAS}] Falha: {e}")
            if tentativa == MAX_TENTATIVAS:
                raise
            time.sleep(3)

    raw    = dados["distances"]  # lista N×N de floats (ou None se sem rota)
    matriz = {i: {j: 0 for j in ids} for i in ids}
    falhas = []

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            val = raw[i][j]
            if val is None:
                falhas.append((ids[i], ids[j]))
            else:
                # Usa a média dos dois sentidos para garantir simetria
                inv  = raw[j][i]
                dist = int(round((val + (inv if inv is not None else val)) / 2))
                matriz[ids[i]][ids[j]] = dist

    if falhas:
        print(f"  [!] {len(falhas)} par(es) sem rota encontrada: {falhas}")
        print("  Esses pares ficaram como 0 na matriz.")

    print(f"  [OK] Matriz {n}×{n} obtida em 1 requisição.")
    return pd.DataFrame(matriz, index=ids, columns=ids)


def salvar_matriz(df: pd.DataFrame, output_path: str) -> None:
    """Salva a matriz como CSV com o ID dos pontos como índice."""
    df.to_csv(output_path)
    print(f"  [OK] Matriz salva em: {output_path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base)

    from config_loader import load_config, get_points, get_slug

    config_path = os.path.join(base, "config.toml")
    cfg    = load_config(config_path)
    points = get_points(cfg)
    slug   = get_slug(cfg)

    cache_dir  = os.path.join(base, "cache", slug)
    os.makedirs(cache_dir, exist_ok=True)
    csv_saida  = os.path.join(cache_dir, "matriz_distancias.csv")

    n     = len(points)
    total = n * (n - 1) // 2

    print("=" * 55)
    print("Buscando distâncias reais via OSRM (OpenStreetMap)")
    print("=" * 55)
    print(f"\nPontos: {n} | Pares: {total} | Requisições: 1\n")

    df_matriz = construir_matriz_osrm(points)

    print("\nMatriz final (metros):")
    print(df_matriz.to_string())

    salvar_matriz(df_matriz, csv_saida)

    print("\nPróximo passo: execute 'python3 main.py' para rodar a análise.")
