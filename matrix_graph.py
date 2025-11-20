from graph_lib import AbstractGraph

class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, numVertices: int):
        self.num_vertices = numVertices
        self.matrix = [[0.0 for _ in range(numVertices)] for _ in range(numVertices)]
        self.vertex_weights = [1.0] * numVertices
        self.num_edges = 0

    def _validate_index(self, v: int):
        if v < 0 or v >= self.num_vertices:
            raise ValueError(f"Vértice {v} inválido. Deve estar entre 0 e {self.num_vertices - 1}.")

    def getVertexCount(self) -> int:
        return self.num_vertices

    def getEdgeCount(self) -> int:
        return self.num_edges

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_index(u)
        self._validate_index(v)
        return self.matrix[u][v] != 0.0

    def addEdge(self, u: int, v: int) -> None:
        self._validate_index(u)
        self._validate_index(v)
        
        if u == v:
            raise ValueError("Laços (self-loops) não são permitidos.")

        if not self.hasEdge(u, v):
            self.matrix[u][v] = 1.0
            self.num_edges += 1

    def removeEdge(self, u: int, v: int) -> None:
        self._validate_index(u)
        self._validate_index(v)
        if self.hasEdge(u, v):
            self.matrix[u][v] = 0.0
            self.num_edges -= 1

    def isSucessor(self, u: int, v: int) -> bool:
        return self.hasEdge(u, v)

    def isPredessor(self, u: int, v: int) -> bool:
        return self.hasEdge(v, u)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        if not (self.hasEdge(u1, v1) and self.hasEdge(u2, v2)):
            return False
        return u1 == u2 and v1 != v2

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        if not (self.hasEdge(u1, v1) and self.hasEdge(u2, v2)):
            return False
        return v1 == v2 and u1 != u2

    def isIncident(self, u: int, v: int, x: int) -> bool:
        if not self.hasEdge(u, v):
            return False
        return x == u or x == v

    def getVertexInDegree(self, u: int) -> int:
        self._validate_index(u)
        degree = 0
        for i in range(self.num_vertices):
            if self.matrix[i][u] != 0.0:
                degree += 1
        return degree

    def getVertexOutDegree(self, u: int) -> int:
        self._validate_index(u)
        degree = 0
        for j in range(self.num_vertices):
            if self.matrix[u][j] != 0.0:
                degree += 1
        return degree

    def setVertexWeight(self, v: int, w: float) -> None:
        self._validate_index(v)
        self.vertex_weights[v] = w

    def getVertexWeight(self, v: int) -> float:
        self._validate_index(v)
        return self.vertex_weights[v]

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._validate_index(u)
        self._validate_index(v)
        if self.hasEdge(u, v):
            self.matrix[u][v] = w

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._validate_index(u)
        self._validate_index(v)
        return self.matrix[u][v]

    def isConnected(self) -> bool:
        if self.num_vertices == 0: return False
        
        visited = set()
        queue = [0]
        visited.add(0)
        
        count = 0
        while queue:
            u = queue.pop(0)
            count += 1
            
            # Percorre todos os possíveis vizinhos (O(N))
            for v in range(self.num_vertices):
                # Verifica conexões de ida e volta (grafo fracamente conexo)
                if (self.matrix[u][v] != 0.0 or self.matrix[v][u] != 0.0):
                    if v not in visited:
                        visited.add(v)
                        queue.append(v)
        
        return count == self.num_vertices

    def isEmptyGraph(self) -> bool:
        return self.num_edges == 0

    def isCompleteGraph(self) -> bool:
        max_edges = self.num_vertices * (self.num_vertices - 1)
        return self.num_edges == max_edges

    def exportToGEPHI(self, path: str) -> None:
        with open(path, 'w') as f:
            f.write("nodedef>name VARCHAR,label VARCHAR,weight DOUBLE\n")
            for i in range(self.num_vertices):
                f.write(f"v{i},Node {i},{self.vertex_weights[i]}\n")
            
            f.write("edgedef>node1 VARCHAR,node2 VARCHAR,weight DOUBLE,directed BOOLEAN\n")
            for u in range(self.num_vertices):
                for v in range(self.num_vertices):
                    if self.matrix[u][v] != 0.0:
                        f.write(f"v{u},v{v},{self.matrix[u][v]},true\n")
        print(f"Grafo (Matriz) exportado para {path}")