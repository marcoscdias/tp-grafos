import json
import sys
from pathlib import Path
from typing import TypeVar, Type

from data_format import Issue, IssueComment, PullComment
from dacite import from_dict

from list_graph import AdjacencyListGraph

"""
Módulo de Análise de Redes de Colaboração do GitHub.

Este script é responsável por orquestrar o processo de ETL (Extract, Transform, Load) 
dos dados do GitHub. Ele carrega os arquivos JSON brutos, mapeia usuários para vértices 
de um grafo, pondera as interações (comentários, reviews, merges) e exporta o resultado 
para visualização no Gephi.
"""

repo = ""


class UserMapper:
    """
    Classe utilitária responsável pelo mapeamento bidirecional entre identificadores
    de usuários (strings/login do GitHub) e índices numéricos (inteiros).

    Necessária pois a implementação do Grafo (AdjacencyListGraph) opera sobre
    índices inteiros para otimização de memória, enquanto os dados brutos utilizam
    strings.
    """

    def __init__(self):
        self.user_to_id = {}
        self.id_to_user = {}
        self.counter = 0

    def get_id(self, username: str) -> int:
        """
        Recupera o ID numérico de um usuário. Se o usuário não existir,
        gera um novo ID incremental e o registra.
        """
        if username not in self.user_to_id:
            self.user_to_id[username] = self.counter
            self.id_to_user[self.counter] = username
            self.counter += 1
        return self.user_to_id[username]

    def get_name(self, user_id: int) -> str:
        """Retorna o login original do GitHub associado a um ID numérico."""
        return self.id_to_user.get(user_id, "Unknown")

    def count(self) -> int:
        """Retorna o número total de usuários únicos mapeados."""
        return self.counter


# noinspection DuplicatedCode
def main():
    """
    Função de entrada principal (Entry Point).

    Executa o pipeline de processamento:
    1. Validação de entrada e arquivos.
    2. Carregamento de dados JSON (Issues, PRs, Comentários).
    3. Mapeamento preliminar de autores para indexação de vértices.
    4. Construção do Grafo Ponderado baseado em regras de negócio.
    5. Exportação para formato GDF.
    """
    global repo

    # 1. Tratamento de Argumentos
    if len(sys.argv) > 1:
        repo = sys.argv[1]
    else:
        info("Qual o repositorio?")
        repo = input()
        while repo == "":
            error("Favor fornecer o repositorio!")
            info("Qual o repositorio?")
            repo = input()
        print()

    # 2. Verificação de integridade dos dados
    base_path = Path(f"downloader/downloads/{repo}")
    if not base_path.exists():
        error(f"Dados não encontrados na pasta downloader/downloads/{repo}")
        error(f"Faça o download com: bun run index.ts {repo}")
        return

    # 3. Carregamento dos artefatos (JSONs)
    try:
        issues: list[Issue] = process_list(Issue, read("issues"))
        issue_comments: list[IssueComment] = process_list(IssueComment, read("issues_comments"))
        # pulls: list = read("pulls")
        pulls_comments: list[PullComment] = process_list(PullComment, read("pulls_comments"))
        pulls_reviews: dict[str, list[PullComment]] = process_dict(PullComment, read("pulls_reviews"))
    except FileNotFoundError as e:
        error(f"Arquivo crítico faltando: {e}")
        return

    # 4. Pré-processamento e Indexação
    info("Indexando autores de Issues e PRs...")
    user_mapper = UserMapper()

    # Mapeia Autores de Issues (Necessário para identificar o alvo dos comentários)
    issue_authors = {}
    for issue in issues:
        user = issue.user
        if user is not None:
            u_id = user_mapper.get_id(user.login)
            issue_authors[issue.number] = u_id

    # Mapeia Autores de PRs
    # pr_authors = {}
    # for pr in pulls:
    #     user = pr.user
    #     if user:
    #         u_id = user_mapper.get_id(user['login'])
    #         pr_authors[pr['number']] = u_id

    # Varredura completa para registro de todos os nós (Vértices) antes da criação do grafo
    info("Mapeando espaço de usuários...")

    for c in issue_comments:
        if c.user is not None: user_mapper.get_id(c.user.login)

    for c in pulls_comments:
        if c.user is not None: user_mapper.get_id(c.user.login)

    for pr_num, reviews in pulls_reviews.items():
        for r in reviews:
            if r.user is not None: user_mapper.get_id(r.user.login)

    # for pr in pulls:
    #     if pr.get('merged_by'):
    #         user_mapper.get_id(pr['merged_by']['login'])

    num_users = user_mapper.count()
    info(f"Total de usuários únicos (Vértices): {num_users}")

    # 5. Construção do Grafo
    # Seleção de AdjacencyListGraph para otimização de memória em grafos esparsos
    graph = AdjacencyListGraph(num_users)

    info("Processando interações e calculando pesos das arestas...")

    # --- A: Processamento de Comentários em Issues ---
    # Regra de Negócio: Comentários denotam interação leve (Peso 2.0)
    count_comments = 0
    for comment in issue_comments:
        user_obj = comment.user
        if user_obj is None: continue

        commenter_id = user_mapper.get_id(user_obj.login)
        issue_url = comment.issue_url

        try:
            issue_number = int(issue_url.split('/')[-1])
        except ValueError:
            warn(f"Falha ao processar comentário de issue para [{issue_url.split('/')[-1]}] {issue_url}")
            continue

        if issue_number in issue_authors:
            author_id = issue_authors[issue_number]
            # Previne auto-loops (usuário comentando na própria issue)
            if commenter_id != author_id:
                add_interaction(graph, commenter_id, author_id, 2.0)
                count_comments += 1

    # --- B: Processamento de Comentários em Pull Requests ---
    # Regra de Negócio: Comentários de código também possuem Peso 2.0
    for comment in pulls_comments:
        user_obj = comment.user
        if user_obj is None: continue

        commenter_id = user_mapper.get_id(user_obj.login)
        pr_url = comment.pull_request_url

        try:
            pr_number = int(pr_url.split('/')[-1])
        except ValueError:
            warn(f"Falha ao processar comentário de review para [{pr_url.split('/')[-1]}] {pr_url}")
            continue

        if pr_number in issue_authors:
            author_id = issue_authors[pr_number]
            if commenter_id != author_id:
                add_interaction(graph, commenter_id, author_id, 2.0)
                count_comments += 1

    # --- C: Processamento de Code Reviews ---
    # Regra de Negócio: Reviews indicam colaboração técnica forte (Peso 4.0)
    count_reviews = 0
    for pr_num_str, reviews in pulls_reviews.items():
        pr_number = int(pr_num_str)

        if pr_number not in issue_authors: continue
        author_id = issue_authors[pr_number]

        for review in reviews:
            user_obj = review.user
            if user_obj is None: continue

            reviewer_id = user_mapper.get_id(user_obj.login)

            if reviewer_id != author_id:
                add_interaction(graph, reviewer_id, author_id, 4.0)
                count_reviews += 1

    # --- D: Processamento de Merges ---
    # Regra de Negócio: Merges representam a consolidação da colaboração (Peso 5.0)
    count_merges = 0
    for pr in issues:
        if pr.pull_request and pr.pull_request.merged_at and pr.closed_by:
            merger_id = user_mapper.get_id(pr.closed_by.login)
            author_id = issue_authors.get(pr.number)

            if author_id is not None and merger_id != author_id:
                add_interaction(graph, merger_id, author_id, 5.0)
                count_merges += 1

    # Relatório de Execução
    print("-" * 40)
    info(f"Grafo construído com sucesso!")
    info(f"Vértices: {graph.getVertexCount()}")
    info(f"Arestas: {graph.getEdgeCount()}")
    print(f"  - Interações de Comentários processadas: {count_comments}")
    print(f"  - Interações de Reviews processadas: {count_reviews}")
    print(f"  - Interações de Merges processadas: {count_merges}")
    print("-" * 40)

    # 6. Exportação dos Dados
    output_file = f"{repo.replace('/', '_')}.gdf"
    info(f"Exportando para formato GDF: {output_file}...")

    export_custom_gephi(graph, user_mapper, output_file)

    info("Pipeline finalizado com sucesso.")


def add_interaction(graph, u: int, v: int, weight: float):
    """
    Registra uma interação entre dois usuários no grafo.

    Implementa a lógica de Grafo Integrado: se a aresta já existe
    (interação prévia), o novo peso é somado ao atual.

    Args:
        graph: Instância de AbstractGraph.
        u: ID do usuário de origem.
        v: ID do usuário de destino.
        weight: Peso da interação a ser adicionada.
    """
    if graph.hasEdge(u, v):
        current_weight = graph.getEdgeWeight(u, v)
        graph.setEdgeWeight(u, v, current_weight + weight)
    else:
        graph.addEdge(u, v)
        graph.setEdgeWeight(u, v, weight)


def export_custom_gephi(graph, mapper, path):
    """
    Exporta a estrutura do grafo para o formato GDF (Guess Definition File).

    Realiza a tradução reversa de IDs numéricos para Logins do GitHub
    para permitir a análise visual legível no software Gephi.
    """
    with open(path, 'w', encoding='utf-8') as f:
        f.write("nodedef>name VARCHAR,label VARCHAR\n")
        num_v = graph.getVertexCount()

        for i in range(num_v):
            login = mapper.get_name(i)
            f.write(f"{login},{login}\n")

        f.write("edgedef>node1 VARCHAR,node2 VARCHAR,weight DOUBLE,directed BOOLEAN\n")
        for u in range(num_v):
            if hasattr(graph, 'adj'):
                for v, w in graph.adj[u].items():
                    u_name = mapper.get_name(u)
                    v_name = mapper.get_name(v)
                    f.write(f"{u_name},{v_name},{w},true\n")
            else:
                for v in range(num_v):
                    if graph.hasEdge(u, v):
                        w = graph.getEdgeWeight(u, v)
                        u_name = mapper.get_name(u)
                        v_name = mapper.get_name(v)
                        f.write(f"{u_name},{v_name},{w},true\n")


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


def or_default(value: T | None, default: T) -> T:
    if value is None: return default
    return value


def process_list(cls: Type[T], data: list) -> list[T]:
    return [from_dict(data_class=cls, data=item) for item in data]


def process_dict(cls: Type[T], data: dict[K, list[V]]) -> dict[K, list[V]]:
    new_dict: dict[K, list[V]] = {}
    for key in data:
        new_dict[key] = process_list(cls, data[key])

    return new_dict


def read(file):
    info(f"Lendo {repo}/{file}.json")
    with open(f"downloader/downloads/{repo}/{file}.json", 'r', encoding='utf-8') as file_content:
        return json.load(file_content)


def info(msg):
    print(f"[\033[94mINFO\033[0m] {msg}")


def warn(msg):
    print(f"[\033[93mWARN\033[0m] {msg}")


def error(msg):
    print(f"[\033[91mERROR\033[0m] {msg}")


if __name__ == '__main__':
    main()
