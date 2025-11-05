import { Octokit } from "octokit";
import { delay, Listr, type ListrTask, type ListrTaskWrapper, PRESET_TIMER, Spinner } from "listr2";

const octokit = new Octokit({
  auth: process.env.GH_TOKEN
});

const repoPath = Bun.argv[2];
if (!repoPath) {
  console.log("Please provide a repository!");
  process.exit(1);
}

const repoParts = repoPath.split('/');
if (repoParts.length != 2) {
  console.log("Please provide a repository on the format {owner}/{repository}!");
  console.log(`You provided ${repoPath}`);
  process.exit(1);
}

type Repository = {
  owner: string,
  repo: string,
}

function time(name: string, promise: (task: ListrTaskWrapper<Ctx, any, any>) => Promise<any>): ListrTask {
  return {
    title: `Fetching ${name} from ${repoPath}`,
    task: async (_, task) => await promise(task)
  };
}

async function fetchData(task: ListrTaskWrapper<Ctx, any, any>, api: string, repo: Repository) {
  return task.newListr([
      {
        title: "Fetching data",
        task: async ctx => {
          ctx[api] = await octokit.paginate(`GET /repos/{owner}/{repo}/${api}`, {
            owner: repoParts[0],
            repo: repoParts[1],
            per_page: 100,
            state: "all",
            headers: {
              'X-GitHub-Api-Version': '2022-11-28'
            }
          });
        },
      },
      {
        title: "Saving data",
        task: async (ctx, subTask) => {
          const file = Bun.file(`downloads/${repoPath}/${api.replaceAll("/", "_")}.json`);
          await file.write(JSON.stringify(ctx[api]));
        }
      }
    ],
    {
      concurrent: false,
    }
  );
}

const repo = {
  owner: repoParts[0]!,
  repo: repoParts[1]!
}

type Ctx = {
  [id: string]: unknown[]
}

class NewSpinner extends Spinner {
  spinner = [
    "▱▱▱▱▱▱▱",
    "▰▱▱▱▱▱▱",
    "▰▰▱▱▱▱▱",
    "▰▰▰▱▱▱▱",
    "▰▰▰▰▱▱▱",
    "▰▰▰▰▰▱▱",
    "▰▰▰▰▰▰▱",
    "▰▰▰▰▰▰▰",
    "▱▰▰▰▰▰▰",
    "▱▱▰▰▰▰▰",
    "▱▱▱▰▰▰▰",
    "▱▱▱▱▰▰▰",
    "▱▱▱▱▱▰▰",
    "▱▱▱▱▱▱▰",
  ];
}

const tasks = new Listr<undefined>([], {
  rendererOptions: {
    timer: PRESET_TIMER,
    spinner: new NewSpinner(),
  },
  concurrent: true
})

tasks.add([
  time("issues", task => fetchData(task, "issues", repo)),
  time("issue comments", task => fetchData(task, "issues/comments", repo)),
  time("pull requests", task => fetchData(task, "pulls", repo)),
  time("PR review comments", task => fetchData(task, "pulls/comments", repo))
]);

await tasks.run();
