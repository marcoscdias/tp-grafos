import json, sys
from pathlib import Path

repo = ""

def main():
    global repo

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

    project_files = Path("downloader/downloads/{}".format(repo))
    if not project_files.exists():
        error("Dados não encontrados, na pasta \033[92mdownloader\033[91m, faça o download com \033[36mbun run index.ts {}".format(repo))
        error("Caso não tenha o Bun, visite https://bun.sh/ para instalar")
        return

    # O formato do JSON segue a resposta da API
    # issues          - https://docs.github.com/en/rest/issues/issues?apiVersion=2022-11-28#list-repository-issues
    # issues_comments - https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments-for-a-repository
    # pulls           - https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#list-pull-requests
    # pulls_comments  - https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28#list-review-comments-in-a-repository
    # pulls_reviews   - Root is a JSON Object with each element being on the format where the key is the PR number,
    #                   and the value is the API result https://docs.github.com/en/rest/pulls/reviews?apiVersion=2022-11-28#list-reviews-for-a-pull-request
    issues = read("issues")


def read(file):
    info("Lendo {}/{}.json".format(repo, file))
    with open("downloader/downloads/{}/{}.json".format(repo, file), 'r') as file_content:
        return json.load(file_content)

def info(msg):
    print(msg)

def warn(msg):
    print("\033[93m{}\033[0m".format(msg))

def error(msg):
    print("\033[91m{}\033[0m".format(msg))

def TODO():
    raise "TODO: Implement method"

if __name__ == '__main__':
    main()
