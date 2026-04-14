"""
Módulo: config_loader.py
Lê config.toml e fornece pontos, informações do bairro e matriz de distâncias.

A matriz é carregada do cache (cache/{slug}/matriz_distancias.csv) se existir,
ou gerada automaticamente via OSRM na primeira execução (requer internet).
"""

import os
import tomllib

import pandas as pd
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


def load_or_build_matrix(cfg: dict, base_dir: str, G_streets=None, points_snapped=None) -> dict:
    """
    Carrega a matriz de distâncias do cache ou gera via OSMnx.

    Usa a mesma malha viária da visualização — garante consistência entre
    as distâncias usadas no Kruskal/Prim e as rotas desenhadas no mapa.

    Cache em: cache/{slug}/matriz_distancias.csv
    """
    slug = get_slug(cfg)
    cache_dir = os.path.join(base_dir, "cache", slug)
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "matriz_distancias.csv")

    if os.path.exists(cache_path):
        print(f"  Matriz carregada do cache: cache/{slug}/matriz_distancias.csv")
        return load_distance_matrix(cache_path)

    print("  Nenhum cache encontrado. Gerando matriz via OSMnx...")
    from router import (
        download_or_load_street_network,
        snap_points_to_network,
        build_distance_matrix_from_network,
    )

    points = points_snapped if points_snapped is not None else get_points(cfg)

    if G_streets is None:
        cache_streets = os.path.join(cache_dir, "street_network.graphml")
        G_streets = download_or_load_street_network(points, cache_streets)
        points = snap_points_to_network(G_streets, points)

    df = build_distance_matrix_from_network(G_streets, points)
    df.to_csv(cache_path)
    print(f"  [OK] Matriz salva em: cache/{slug}/matriz_distancias.csv")
    return load_distance_matrix(cache_path)
