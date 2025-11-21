from list_graph import AdjacencyListGraph

def teste_rapido():
    print("--- Iniciando Teste da Lista de Adjacência ---")
    
    g = AdjacencyListGraph(4)
    
    print("Adicionando arestas...")
    g.addEdge(0, 1)
    g.addEdge(0, 2)
    g.addEdge(1, 2)
    g.addEdge(2, 0)
    g.addEdge(2, 3)
    
    print(f"Tem aresta 0->1? {g.hasEdge(0, 1)}")
    print(f"Tem aresta 1->3? {g.hasEdge(1, 3)}")
    print(f"Grau de saída de 2: {g.getVertexOutDegree(2)}")
    print(f"Grau de entrada de 2: {g.getVertexInDegree(2)}")
    
    g.setEdgeWeight(0, 1, 5.5)
    print(f"Peso da aresta 0->1: {g.getEdgeWeight(0, 1)}")
    
    g.exportToGEPHI("teste.gdf")
    
    print("--- Teste Concluído ---")

if __name__ == "__main__":
    teste_rapido()