import { Octokit } from "octokit";
import { throttling } from "@octokit/plugin-throttling";
import {
  Listr,
  ListrLogger,
  ListrLogLevels,
  type ListrTask,
  type ListrTaskWrapper,
  PRESET_TIMER,
  Spinner
} from "listr2";

const logger = new ListrLogger({ useIcons: true })

const MyOctokit = Octokit.plugin(throttling);
const octokit = new MyOctokit({
  auth: process.env.GH_TOKEN,
  log: {
    debug: message => logger.log(ListrLogLevels.FAILED, message),
    info: message => logger.log(ListrLogLevels.FAILED, message),
    warn: message => logger.log(ListrLogLevels.FAILED, message),
    error: message => logger.log(ListrLogLevels.FAILED, message),
  },
  throttle: {
    onRateLimit: (retryAfter, options, octokit, retryCount) => {
      octokit.log.warn(
        `Request quota exhausted for request ${options.method} ${options.url}`,
      );

      if (retryCount < 50) {
        // only retries once
        octokit.log.info(`Retrying after ${retryAfter} seconds!`);
        return true;
      } else {
        octokit.log.error(
          `Failed after too many attempts!`,
        );
      }
    },
    onSecondaryRateLimit: (retryAfter, options, octokit, retryCount) => {
      octokit.log.warn(
        `Secondary rate limit detected for request ${options.method} ${options.url}`,
      );

      if (retryCount < 10) {
        // only retries once
        octokit.log.info(`Retrying after ${retryAfter} seconds!`);
        return true;
      } else {
        octokit.log.error(
          `Failed after too many attempts!`,
        );
      }
    },
  },
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
  const file = Bun.file(`downloads/${repoPath}/${api.replaceAll("/", "_")}.json`);
  if (await file.exists()) {
    return task;
  }

  return task.newListr([
      {
        title: "Fetching data",
        task: async ctx => {
          ctx[api] = await octokit.paginate(`GET /repos/{owner}/{repo}/${api}`, {
            owner: repo.owner,
            repo: repo.repo,
            per_page: 100,
            state: "all",
            headers: {'X-GitHub-Api-Version': '2022-11-28'}
          });
        },
      },
      {
        title: "Saving data",
        task: async (ctx, subTask) => {
          await file.write(JSON.stringify(ctx[api]));
        }
      }
    ],
    {
      concurrent: false,
    }
  );
}

async function fetchReview(task: ListrTaskWrapper<Ctx, any, any>, repo: Repository) {
  const file = Bun.file(`downloads/${repoPath}/pulls_reviews.json`);
  const pullsFile = Bun.file(`downloads/${repoPath}/pulls.json`);
  if (await file.exists()) {
    return task;
  }

  const pulls: any[] = JSON.parse(await pullsFile.text());
  const reviews: Record<string, any[]> = {};

  const batchSize = 16;

  return task.newListr([
      {
        title: "Fetching reviews",
        task: async (ctx, subTask) => {
          for (let i = 0; i < pulls.length; i += batchSize) {
            const batch = pulls.slice(i, i + batchSize);

            subTask.output = "yipyipyip"
            subTask.title = `Fetching reviews (${i + 1}-${Math.min(i + batchSize, pulls.length)} of ${pulls.length})`;

            await Promise.all(
              batch.map(async pull => {
                reviews[`${pull.number}`] = await octokit.paginate("GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews", {
                    owner: repoParts[0],
                    repo: repoParts[1],
                    pull_number: pull.number,
                    per_page: 100,
                    headers: {'X-GitHub-Api-Version': '2022-11-28'},
                  }
                );
              })
            );
          }
          ctx["pulls/reviews"] = reviews;
        }
      },
      {
        title: "Saving data",
        task: async (ctx, subTask) => {
          await file.write(JSON.stringify(ctx["pulls/reviews"]));
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
  [id: string]: any
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
  time("PR review comments", task => fetchData(task, "pulls/comments", repo)),
  time("PR reviews", task => fetchReview(task, repo)),
]);

await tasks.run();
