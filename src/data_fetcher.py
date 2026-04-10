"""
Módulo: data_fetcher.py
Busca distâncias reais de ruas usando a API pública do OSRM
(Open Source Routing Machine — baseado no OpenStreetMap).

API utilizada: http://router.project-osrm.org (gratuita, sem chave)
Modo: "driving" (distância por vias, equivale ao trajeto de caminhão)

Execução:
    python3 src/data_fetcher.py

O script:
  1. Lê os pontos de data/pontos_coleta.csv
  2. Faz uma requisição para cada par único (45 requisições para 10 pontos)
  3. Salva a nova matriz em data/matriz_distancias.csv (sobrescreve a manual)

Tempo estimado: ~2 minutos (0.5s de pausa entre requisições).
Requer conexão com a internet.
"""

import os
import sys
import time
import requests
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from data_loader import load_points


OSRM_URL = "http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
PAUSA_ENTRE_CHAMADAS = 0.6  # segundos — evita sobrecarga da API pública


def buscar_distancia_osrm(lat1: float, lon1: float, lat2: float, lon2: float) -> int | None:
    """
    Consulta o OSRM e retorna a distância em metros (inteiro).

    Retorna None se a requisição falhar ou o OSRM não encontrar rota.
    """
    url = OSRM_URL.format(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)
    try:
        resposta = requests.get(url, timeout=10)
        dados = resposta.json()
        if dados.get("code") == "Ok":
            distancia_m = dados["routes"][0]["distance"]
            return int(round(distancia_m))
        else:
            print(f"    [OSRM] Código inesperado: {dados.get('code')}")
            return None
    except requests.exceptions.Timeout:
        print("    [ERRO] Timeout — o servidor OSRM demorou demais.")
        return None
    except Exception as e:
        print(f"    [ERRO] {e}")
        return None


def construir_matriz_osrm(points: list[dict]) -> pd.DataFrame:
    """
    Constrói a matriz de distâncias completa consultando o OSRM.

    Faz apenas o triângulo superior (45 pares para 10 pontos) e
    espelha para o triângulo inferior (matriz simétrica).

    Retorna um DataFrame quadrado com IDs dos pontos como índice e colunas.
    """
    ids = [p["id"] for p in points]
    n = len(ids)
    total_pares = n * (n - 1) // 2

    # Inicializa a matriz com zeros
    matriz = {i: {j: 0 for j in ids} for i in ids}

    par_atual = 0
    falhas = []

    for i in range(n):
        for j in range(i + 1, n):
            par_atual += 1
            u = points[i]
            v = points[j]

            distancia = buscar_distancia_osrm(
                u["latitude"], u["longitude"],
                v["latitude"], v["longitude"],
            )

            if distancia is not None:
                matriz[u["id"]][v["id"]] = distancia
                matriz[v["id"]][u["id"]] = distancia
                print(f"  [{par_atual:>2}/{total_pares}] {u['id']} ↔ {v['id']}: {distancia} m")
            else:
                falhas.append((u["id"], v["id"]))
                print(f"  [{par_atual:>2}/{total_pares}] {u['id']} ↔ {v['id']}: FALHOU")

            time.sleep(PAUSA_ENTRE_CHAMADAS)

    if falhas:
        print(f"\n  [!] {len(falhas)} par(es) falharam: {falhas}")
        print("  Esses pares ficaram como 0 na matriz. Preencha manualmente.")

    return pd.DataFrame(matriz, index=ids, columns=ids)


def salvar_matriz(df: pd.DataFrame, output_path: str) -> None:
    """Salva a matriz como CSV com o ID dos pontos como índice."""
    df.to_csv(output_path)
    print(f"\n  [OK] Matriz salva em: {output_path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_pontos = os.path.join(base, "data", "pontos_coleta.csv")
    csv_saida  = os.path.join(base, "data", "matriz_distancias.csv")

    print("=" * 55)
    print("Buscando distâncias reais via OSRM (OpenStreetMap)")
    print("=" * 55)

    points = load_points(csv_pontos)
    n = len(points)
    total = n * (n - 1) // 2

    print(f"\nPontos carregados: {n}")
    print(f"Pares a consultar: {total}")
    print(f"Tempo estimado:    ~{int(total * PAUSA_ENTRE_CHAMADAS / 60 + 1)} minuto(s)\n")

    df_matriz = construir_matriz_osrm(points)

    print("\nMatriz final (metros):")
    print(df_matriz.to_string())

    salvar_matriz(df_matriz, csv_saida)

    print("\nPróximo passo: execute 'python3 main.py' para rodar a análise com os dados reais.")
