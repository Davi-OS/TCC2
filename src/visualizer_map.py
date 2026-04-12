"""
Módulo: visualizer_map.py
Gera o mapa interativo (HTML) com Folium:
- Pontos de coleta com marcadores coloridos por tipo
- Grafo completo (todas as arestas)
- AGM do Kruskal e do Prim (rotas pelas ruas reais via OSMnx)
- Rota sequencial (baseline, pelas ruas)
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


def _segment_coords(pu: dict, pv: dict, G_streets) -> list:
    """
    Retorna a lista de coordenadas [lat, lon] para o segmento entre pu e pv.
    Usa roteamento real pelas ruas se G_streets e osm_node disponíveis;
    caso contrário, linha reta.
    """
    if G_streets is not None and "osm_node" in pu and "osm_node" in pv:
        from router import get_route_coords
        return get_route_coords(G_streets, pu["osm_node"], pv["osm_node"])
    return [[pu["latitude"], pu["longitude"]], [pv["latitude"], pv["longitude"]]]


def create_base_map(points: list[dict], bairro_label: str = "") -> folium.Map:
    """Cria o mapa base centrado no bairro configurado."""
    lat, lon = _centroid(points)
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
    if bairro_label:
        title_html = (
            f'<div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);'
            f'z-index:1000;background:white;padding:6px 14px;border-radius:6px;'
            f'border:1px solid #CCC;font-size:14px;font-weight:bold;box-shadow:1px 1px 4px rgba(0,0,0,.2)">'
            f'{bairro_label}</div>'
        )
        m.get_root().html.add_child(folium.Element(title_html))
    return m


def add_points_layer(m: folium.Map, points: list[dict]) -> None:
    """
    Adiciona marcadores circulares para cada ponto de coleta.
    Usa posição snapped (sobre a rua) se disponível; caso contrário, coord original.
    """
    layer = folium.FeatureGroup(name="Pontos de Coleta", show=True)

    for p in points:
        cor = TIPO_CORES_FOLIUM.get(p["tipo"], COR_PADRAO_FOLIUM)
        lat = p.get("snapped_lat", p["latitude"])
        lon = p.get("snapped_lon", p["longitude"])
        popup_html = (
            f"<b>{p['nome']}</b><br>"
            f"ID: {p['id']}<br>"
            f"Tipo: {p['tipo'].capitalize()}<br>"
            f"<i>{p['descricao']}</i>"
        )
        CircleMarker(
            location=[lat, lon],
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
    """Adiciona todas as arestas do grafo completo (finas e cinza, linha reta)."""
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
    G_streets=None,
) -> None:
    """
    Adiciona as arestas da AGM ao mapa, seguindo as ruas reais se G_streets for passado.

    Parâmetros:
        algo_name: "Kruskal" ou "Prim"
        color:     cor da linha ("#1B5E20" para Kruskal, "#0D47A1" para Prim)
        G_streets: grafo OSMnx (opcional) para roteamento pelas ruas
    """
    total_weight = sum(w for w, _, _ in mst_edges)
    layer = folium.FeatureGroup(
        name=f"AGM — {algo_name} (peso total: {total_weight} m)",
        show=True,
    )

    for weight, u, v in mst_edges:
        pu = _point_by_id(points, u)
        pv = _point_by_id(points, v)
        coords = _segment_coords(pu, pv, G_streets)

        PolyLine(
            locations=coords,
            color=color,
            weight=5,
            opacity=0.85,
            tooltip=f"AGM {algo_name}: {u} ↔ {v} ({weight} m)",
        ).add_to(layer)

    layer.add_to(m)


def add_naive_route_layer(
    m: folium.Map,
    points: list[dict],
    distance_matrix: dict[tuple, int],
    G_streets=None,
) -> None:
    """
    Adiciona a rota sequencial ao mapa como linha tracejada laranja,
    seguindo as ruas reais se G_streets for passado.
    """
    ids = [p["id"] for p in points]
    layer = folium.FeatureGroup(name="Rota Sequencial (baseline)", show=False)

    n = len(ids)
    for i in range(n):
        u = ids[i]
        v = ids[(i + 1) % n]
        pu = _point_by_id(points, u)
        pv = _point_by_id(points, v)
        weight = distance_matrix.get((u, v), distance_matrix.get((v, u), 0))
        coords = _segment_coords(pu, pv, G_streets)

        PolyLine(
            locations=coords,
            color="#E65100",
            weight=4,
            opacity=0.75,
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
