import { writeFile } from 'fs/promises';

const USERNAME = process.env.GITHUB_USERNAME || 'Mouy-leng';
const BASE_URL = 'https://api.github.com';
const OUTPUT_FILE = 'UPDATE_LOG.md';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

interface Repo {
  name: string;
  html_url: string;
  description: string;
  updated_at: string;
}

interface Commit {
  sha: string;
  commit: {
    message: string;
    author: {
      date: string;
    };
  };
}

async function getHeaders() {
  const headers: HeadersInit = {
    'Accept': 'application/vnd.github.v3+json',
  };
  if (GITHUB_TOKEN) {
    headers['Authorization'] = `token ${GITHUB_TOKEN}`;
  }
  return headers;
}

async function getRepos(username: string): Promise<Repo[]> {
  const url = `${BASE_URL}/users/${username}/repos`;
  let repos: Repo[] = [];
  let page = 1;
  const headers = await getHeaders();
  while (true) {
    try {
      const response = await fetch(`${url}?page=${page}&per_page=100`, { headers });
      if (response.ok) {
        const data = await response.json();
        if (data.length === 0) {
          break;
        }
        repos = repos.concat(data);
        page++;
      } else {
        console.error(`Error fetching repos: ${response.status} - ${await response.text()}`);
        break;
      }
    } catch (e) {
      console.error(`Connection error: ${e}`);
      break;
    }
  }
  return repos;
}

async function getCommits(username: string, repoName: string): Promise<Commit[]> {
  const url = `${BASE_URL}/repos/${username}/${repoName}/commits`;
  const headers = await getHeaders();
  try {
    const response = await fetch(`${url}?per_page=10`, { headers });
    if (response.ok) {
      return await response.json();
    } else if (response.status === 409) { // Empty repository
      return [];
    } else {
      // console.error(`Error fetching commits for ${repoName}: ${response.status}`);
      return [];
    }
  } catch (e) {
    return [];
  }
}

async function main() {
  console.log(`Syncing logs for GitHub account: ${USERNAME}`);
  let repos = await getRepos(USERNAME);
  if (!repos || repos.length === 0) {
    console.log('No repositories found or error occurred.');
    return;
  }

  console.log(`Found ${repos.length} repositories.`);

  repos.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

  let content = `# Update Log for ${USERNAME}\\n\\n`;
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  content += `Generated on: ${now}\\n\\n`;

  for (const repo of repos) {
    const repoName = repo.name;
    console.log(`Fetching logs for ${repoName}...`);
    content += `## [${repoName}](${repo.html_url})\\n`;
    content += `${repo.description || 'No description provided.'}\\n\\n`;

    const commits = await getCommits(USERNAME, repoName);
    if (!commits || commits.length === 0) {
      content += `*No commits found (empty repository or error).*\\n\\n`;
    } else {
      for (const commit of commits) {
        const sha = commit.sha.substring(0, 7);
        const message = commit.commit.message.split('\\n')[0];
        const date = commit.commit.author.date;
        content += `- \`${sha}\`: ${message} (${date})\\n`;
      }
      content += `\\n`;
    }
  }
  await writeFile(OUTPUT_FILE, content);
  console.log(`Successfully generated ${OUTPUT_FILE}`);
}

main();
