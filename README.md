# Otimização de Rotas de Coleta Seletiva com Algoritmos de AGM

**Trabalho de Conclusão de Curso — PUC Minas, Sistemas de Informação**

Autor: Davi de Oliveira Santos
Orientador: Bernardo Jeunon de Alencar

---

## Sobre o Projeto

Municípios brasileiros enfrentam baixos índices de coleta seletiva, em parte pela ineficiência das rotas utilizadas pelos veículos coletores. Este projeto aplica teoria dos grafos para otimizar essas rotas em bairros urbanos.

**Abordagem:**
- Os pontos de coleta (praças, escolas, unidades de saúde, comércios etc.) são modelados como vértices de um grafo completo ponderado
- As arestas recebem as distâncias reais entre os pontos, calculadas via [OSRM](http://project-osrm.org/) (roteamento real pelas ruas)
- Dois algoritmos clássicos de **Árvore Geradora Mínima (AGM)** — Kruskal e Prim — encontram a rota de menor custo total
- A rota otimizada é comparada a uma rota sequencial (baseline) em distância, custo de combustível, emissão de CO₂ e tempo

Os resultados são apresentados em visualizações estáticas (PNG) e em um mapa interativo (HTML) com as rotas desenhadas sobre as ruas reais.

---

## Como Funciona

A execução segue um pipeline de 7 etapas orquestradas por `main.py`:

```
[1] Carregar configuração     config.toml → pontos e metadados do bairro
[2] Matriz de distâncias      OSRM API → distâncias reais entre todos os pares
                              (gerada na 1ª execução, cacheada localmente)
[3] Construir grafo           NetworkX → grafo completo ponderado + lista de adjacência
[4] Executar algoritmos       Kruskal (Union-Find) + Prim (min-heap)
                              Validação: ambos devem produzir AGM com mesmo peso
[5] Calcular métricas         AGM vs rota sequencial: distância, custo, CO₂, tempo
[6] Gerar visualizações       6 imagens PNG com Matplotlib
[7] Malha viária + mapa       OSMnx baixa rede viária do OpenStreetMap
                              Folium gera mapa HTML com rotas pelas ruas reais
```

---

## Estrutura de Módulos

| Módulo | Responsabilidade |
|--------|-----------------|
| `main.py` | Ponto de entrada; orquestra o pipeline completo |
| `src/config_loader.py` | Lê `config.toml`; gerencia cache da matriz de distâncias |
| `src/data_fetcher.py` | Consulta a API OSRM para calcular distâncias reais entre pares de pontos |
| `src/data_loader.py` | Carrega a matriz CSV; constrói a lista de arestas ordenada para o Kruskal |
| `src/graph_builder.py` | Cria o grafo NetworkX com atributos geográficos; gera a lista de adjacência para o Prim |
| `src/kruskal.py` | Algoritmo de Kruskal com Union-Find (compressão de caminho + união por rank); registra passos |
| `src/prim.py` | Algoritmo de Prim com min-heap; registra passos e visitação dos nós |
| `src/metrics.py` | Calcula métricas operacionais usando dados de CETESB, IPCC e ANP (2023–2026) |
| `src/router.py` | Baixa/carrega a malha viária via OSMnx; encaixa pontos na rede; roteia pelas ruas |
| `src/visualizer_graph.py` | Gera as 6 visualizações estáticas em PNG com Matplotlib |
| `src/visualizer_map.py` | Gera o mapa interativo HTML com Folium (camadas toggleáveis) |

---

## Configuração

O bairro e os pontos de coleta são definidos em `config.toml`. Para testar com um novo bairro, basta editar esse arquivo e rodar `python3 main.py` — a matriz de distâncias e a malha viária são geradas automaticamente.

```toml
[bairro]
nome   = "Heliópolis"
cidade = "Belo Horizonte, MG"
slug   = "heliopolis"          # usado nos nomes de pasta e arquivo (sem acentos)

[[bairro.pontos]]
id        = "P01"
nome      = "Praça de Heliópolis"
latitude  = -20.0540
longitude = -44.0520
tipo      = "praça"            # praça | saude | escola | comercio | religioso | transporte | comunitario | esporte
descricao = "Centro do bairro - ponto de referência principal"

[[bairro.pontos]]
id        = "P02"
# ... demais pontos
```

Ao trocar o `slug`, o sistema cria um diretório isolado em `cache/{slug}/` e `outputs/{slug}/`, sem interferir nos dados de outros bairros.

---

## Estrutura de Pastas

```
TCC/
├── main.py                    # Ponto de entrada
├── config.toml                # Configuração do bairro e pontos de coleta
├── requirements.txt           # Dependências Python
├── .gitignore
│
├── src/
│   ├── config_loader.py
│   ├── data_fetcher.py
│   ├── data_loader.py
│   ├── graph_builder.py
│   ├── kruskal.py
│   ├── prim.py
│   ├── metrics.py
│   ├── router.py
│   ├── visualizer_graph.py
│   └── visualizer_map.py
│
├── cache/                     # Gerado automaticamente (ignorado pelo git)
│   └── {slug}/
│       ├── matriz_distancias.csv
│       └── street_network.graphml
│
└── outputs/                   # Gerado automaticamente (ignorado pelo git)
    └── {slug}/
        ├── grafos/            # Imagens PNG
        └── mapas/             # Mapa interativo HTML
```

---

## Pré-requisitos e Instalação

- **Python 3.11+** (tomllib é built-in a partir do 3.11)
- Conexão com internet na primeira execução (OSRM e OpenStreetMap)

```bash
# Instalar dependências
pip install -r requirements.txt
pip install osmnx
```

---

## Como Executar

```bash
python3 main.py
```

**Primeira execução** (sem cache):
1. Consulta a API OSRM para calcular as distâncias entre todos os pares de pontos
2. Baixa a malha viária do OpenStreetMap via OSMnx
3. Salva ambos em `cache/{slug}/` para execuções futuras
4. Requer conexão com internet; leva alguns minutos

**Execuções seguintes** (com cache):
- Carrega a matriz e a malha viária do cache local
- Executa em menos de 10 segundos

---

## Outputs Gerados

Todos os arquivos são salvos em `outputs/{slug}/`.

### Grafos (`grafos/`)

| Arquivo | Conteúdo |
|---------|----------|
| `grafo_completo.png` | Todos os 10 nós e 45 arestas com pesos em metros |
| `agm_kruskal.png` | AGM do Kruskal destacada em verde sobre o grafo completo |
| `agm_prim.png` | AGM do Prim destacada sobre o grafo completo |
| `kruskal_passos.png` | Grade de painéis mostrando cada aresta aceita/rejeitada passo a passo |
| `prim_passos.png` | Grade de painéis mostrando o crescimento da árvore a partir do nó inicial |
| `comparacao_metricas.png` | Gráfico de barras: AGM vs rota sequencial em distância, custo, CO₂ e tempo |

### Mapa (`mapas/`)

| Arquivo | Conteúdo |
|---------|----------|
| `mapa_{slug}.html` | Mapa interativo com 5 camadas toggleáveis: pontos de coleta, grafo completo, AGM Kruskal, AGM Prim e rota sequencial — todas desenhadas sobre as ruas reais |

---

## Dependências

| Biblioteca | Versão mínima | Uso no projeto |
|------------|:---:|----------------|
| networkx | 3.2 | Estrutura do grafo completo e validação de conectividade |
| matplotlib | 3.8 | Geração das visualizações estáticas (PNG) |
| numpy | 1.26 | Suporte numérico |
| pandas | 2.1 | Leitura e escrita da matriz de distâncias (CSV) |
| folium | 0.15 | Mapa interativo HTML com camadas |
| requests | 2.31 | Consultas à API OSRM |
| osmnx | — | Download da malha viária OSM e roteamento pelas ruas |
| tomllib | built-in | Leitura do `config.toml` (Python 3.11+) |
