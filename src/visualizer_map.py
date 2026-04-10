"""
Módulo: visualizer_map.py
Gera o mapa interativo (HTML) com Folium:
- Pontos de coleta com marcadores coloridos por tipo
- Grafo completo (todas as arestas)
- AGM do Kruskal
- AGM do Prim
- Rota sequencial (baseline)
- LayerControl para o professor ativar/desativar cada camada
"""

import folium
from folium import LayerControl, PolyLine, CircleMarker, Popup, Tooltip


# Cores por tipo de ponto (consistente com visualizer_graph.py)
TIPO_CORES_FOLIUM = {
    "praça":      "#4CAF50",
    "saude":      "#F44336",
    "escola":     "#2196F3",
    "comercio":   "#FF9800",
    "religioso":  "#9C27B0",
    "transporte": "#00BCD4",
    "comunitario":"#795548",
    "esporte":    "#8BC34A",
}
COR_PADRAO_FOLIUM = "#9E9E9E"


def _centroid(points: list[dict]) -> tuple[float, float]:
    lat = sum(p["latitude"] for p in points) / len(points)
    lon = sum(p["longitude"] for p in points) / len(points)
    return lat, lon


def _point_by_id(points: list[dict], pid: str) -> dict:
    for p in points:
        if p["id"] == pid:
            return p
    raise KeyError(f"Ponto {pid} não encontrado")


def create_base_map(points: list[dict]) -> folium.Map:
    """Cria o mapa base centrado em Heliópolis."""
    lat, lon = _centroid(points)
    return folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")


def add_points_layer(m: folium.Map, points: list[dict]) -> None:
    """Adiciona marcadores circulares para cada ponto de coleta."""
    layer = folium.FeatureGroup(name="Pontos de Coleta", show=True)

    for p in points:
        cor = TIPO_CORES_FOLIUM.get(p["tipo"], COR_PADRAO_FOLIUM)
        popup_html = (
            f"<b>{p['nome']}</b><br>"
            f"ID: {p['id']}<br>"
            f"Tipo: {p['tipo'].capitalize()}<br>"
            f"Lat: {p['latitude']}<br>"
            f"Lon: {p['longitude']}<br>"
            f"<i>{p['descricao']}</i>"
        )
        CircleMarker(
            location=[p["latitude"], p["longitude"]],
            radius=10,
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=0.85,
            popup=Popup(popup_html, max_width=250),
            tooltip=Tooltip(f"{p['id']} — {p['nome']}"),
        ).add_to(layer)

    layer.add_to(m)


def add_complete_graph_layer(
    m: folium.Map,
    distance_matrix: dict[tuple, int],
    points: list[dict],
) -> None:
    """Adiciona todas as arestas do grafo completo (finas e cinza)."""
    layer = folium.FeatureGroup(name="Grafo Completo (todas as arestas)", show=False)

    seen = set()
    for (u, v), weight in distance_matrix.items():
        pair = tuple(sorted([u, v]))
        if pair in seen:
            continue
        seen.add(pair)

        pu = _point_by_id(points, u)
        pv = _point_by_id(points, v)

        PolyLine(
            locations=[[pu["latitude"], pu["longitude"]], [pv["latitude"], pv["longitude"]]],
            color="#9E9E9E",
            weight=1.5,
            opacity=0.4,
            tooltip=f"{u} ↔ {v}: {weight} m",
        ).add_to(layer)

    layer.add_to(m)


def add_mst_layer(
    m: folium.Map,
    mst_edges: list[tuple],
    points: list[dict],
    algo_name: str,
    color: str,
) -> None:
    """
    Adiciona as arestas da AGM ao mapa.

    Parâmetros:
        algo_name: nome do algoritmo para a legenda ("Kruskal" ou "Prim")
        color:     cor das linhas ("#1B5E20" para Kruskal, "#0D47A1" para Prim)
    """
    total_weight = sum(w for w, _, _ in mst_edges)
    layer = folium.FeatureGroup(
        name=f"AGM — {algo_name} (peso total: {total_weight} m)",
        show=True,
    )

    for weight, u, v in mst_edges:
        pu = _point_by_id(points, u)
        pv = _point_by_id(points, v)

        PolyLine(
            locations=[[pu["latitude"], pu["longitude"]], [pv["latitude"], pv["longitude"]]],
            color=color,
            weight=5,
            opacity=0.8,
            tooltip=f"AGM {algo_name}: {u} ↔ {v} ({weight} m)",
        ).add_to(layer)

    layer.add_to(m)


def add_naive_route_layer(
    m: folium.Map,
    points: list[dict],
    distance_matrix: dict[tuple, int],
) -> None:
    """
    Adiciona a rota sequencial (ingênua) ao mapa como linha tracejada laranja.
    Rota: P01 → P02 → ... → P10 → P01
    """
    ids = [p["id"] for p in points]
    total = 0
    layer = folium.FeatureGroup(name="Rota Sequencial (baseline)", show=False)

    n = len(ids)
    for i in range(n):
        u = ids[i]
        v = ids[(i + 1) % n]
        pu = _point_by_id(points, u)
        pv = _point_by_id(points, v)
        weight = distance_matrix.get((u, v), distance_matrix.get((v, u), 0))
        total += weight

        PolyLine(
            locations=[[pu["latitude"], pu["longitude"]], [pv["latitude"], pv["longitude"]]],
            color="#E65100",
            weight=4,
            opacity=0.7,
            dash_array="8 4",
            tooltip=f"Sequencial: {u} → {v} ({weight} m)",
        ).add_to(layer)

    layer.add_to(m)


def add_legend(m: folium.Map) -> None:
    """Adiciona legenda HTML flutuante ao mapa."""
    legend_html = """
    <div style="
        position: fixed; bottom: 30px; left: 30px; z-index: 1000;
        background: white; padding: 12px 16px; border-radius: 8px;
        border: 2px solid #CCC; font-size: 13px; line-height: 1.8;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    ">
        <b>Legenda</b><br>
        <span style="color:#1B5E20">&#9644;</span> AGM — Kruskal<br>
        <span style="color:#0D47A1">&#9644;</span> AGM — Prim<br>
        <span style="color:#E65100">- -</span> Rota Sequencial<br>
        <span style="color:#9E9E9E">&#9644;</span> Grafo Completo<br>
        <hr style="margin:4px 0">
        <span style="color:#4CAF50">&#9679;</span> Praça &nbsp;
        <span style="color:#F44336">&#9679;</span> Saúde<br>
        <span style="color:#2196F3">&#9679;</span> Escola &nbsp;
        <span style="color:#FF9800">&#9679;</span> Comércio<br>
        <span style="color:#00BCD4">&#9679;</span> Transporte &nbsp;
        <span style="color:#9C27B0">&#9679;</span> Religioso
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


def save_map(m: folium.Map, output_path: str) -> None:
    """Salva o mapa como HTML auto-contido."""
    LayerControl(collapsed=False).add_to(m)
    m.save(output_path)
    print(f"  [OK] {output_path}")
