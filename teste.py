pontos = []
pontos.append("Ponto A")
pontos.append("Ponto B")
pontos.append("Ponto C")

print(f"Total de pontos: {len(pontos)}")
print(f"Primeiro ponto: {pontos[0]}")
print(f"Ultimo ponto: {pontos[-1]}")


ponto_A ={
    "nome": "Praça da Liberdade",
    "longitude": -43.9378,
    "latitude": -19.9320,
    "tipo": "praça",
    "capacidade": 500
}


print(f"Nome: {ponto_A['nome']}")
print(f"Coordenada: ({ponto_A['latitude']},{ponto_A['longitude']})")
print(f"Tipo: {ponto_A['tipo']}")


todos_pontos =[
    {"nome":"Ponto A","lat": -19.9220, "lon":-43.9950, "tipo": "praça","amor_da_minha_vida":"voce"}
]

print("===================")

for ponto in todos_pontos:
    print(f"Quem é o amor da minha vida: ({ponto['amor_da_minha_vida']})")
    
    
for ponto in todos_pontos:
    if ponto['nome'] == "Ponto B":
        print(f"\n Encontrado: {ponto['nome']} em {ponto['tipo']}")  
 