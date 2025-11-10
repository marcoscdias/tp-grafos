import json
from pathlib import Path

repo = ""

def main():
    global repo

    print("Qual o repositorio?")
    repo = input()

    project_files = Path("downloader/downloads/{}".format(repo))
    if not project_files.exists():
        error("Dados não encontrados, na pasta \033[92mdownloader\033[91m, faça o download com \033[36mbun run index.ts {}".format(repo))
        error("Caso não tenha o Bun, visite https://bun.sh/ para instalar")
        return

    # O formato do JSON segue a resposta da API
    # issues - https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#list-repository-issues
    # issues_comments - https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments-for-a-repository
    # pulls - https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests
    # pulls_comments - https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#list-review-comments-in-a-repository
    issues = read("issues")


def read(file):
    with open("downloader/downloads/{}/{}.json".format(repo, file), 'r') as file_content:
        return json.load(file_content)

def info(msg):
    print(msg)

def warn(msg):
    print("\033[93m{}\033[0m".format(msg))

def error(msg):
    print("\033[91m{}\033[0m".format(msg))

if __name__ == '__main__':
    main()
