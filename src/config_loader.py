"""
Módulo: config_loader.py
Lê config.toml e fornece pontos, informações do bairro e matriz de distâncias.

A matriz é carregada do cache (cache/{slug}/matriz_distancias.csv) se existir,
ou gerada automaticamente via OSRM na primeira execução (requer internet).
"""

import os
import tomllib

from data_fetcher import construir_matriz_osrm, salvar_matriz
from data_loader import load_distance_matrix


def load_config(config_path: str) -> dict:
    """Lê e retorna o config.toml como dicionário."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {config_path}\n"
            "Crie um config.toml na raiz do projeto."
        )
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def get_points(cfg: dict) -> list[dict]:
    """Retorna a lista de pontos de coleta definida no config."""
    return cfg["bairro"]["pontos"]


def get_bairro_label(cfg: dict) -> str:
    """Retorna string de exibição: 'Nome, Cidade'."""
    return f"{cfg['bairro']['nome']}, {cfg['bairro']['cidade']}"


def get_slug(cfg: dict) -> str:
    """Retorna o slug do bairro (usado em nomes de pasta e arquivo)."""
    return cfg["bairro"]["slug"]


def load_or_build_matrix(cfg: dict, base_dir: str) -> dict:
    """
    Carrega a matriz de distâncias do cache ou gera via OSRM.

    Cache em: cache/{slug}/matriz_distancias.csv
    Na primeira execução (sem cache) requer conexão com a internet.
    """
    slug = get_slug(cfg)
    cache_dir = os.path.join(base_dir, "cache", slug)
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "matriz_distancias.csv")

    if os.path.exists(cache_path):
        print(f"  Matriz carregada do cache: cache/{slug}/matriz_distancias.csv")
        return load_distance_matrix(cache_path)

    print("  Nenhum cache encontrado. Gerando matriz via OSRM (requer internet)...")
    points = get_points(cfg)
    n = len(points)
    total = n * (n - 1) // 2
    print(f"  Pontos: {n} | Pares a consultar: {total}")

    df = construir_matriz_osrm(points)
    salvar_matriz(df, cache_path)
    return load_distance_matrix(cache_path)
