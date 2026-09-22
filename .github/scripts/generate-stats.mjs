import fs from 'node:fs';

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const USERNAME = process.env.USERNAME || 'antono4';
const headers = {
  'Authorization': `Bearer ${GITHUB_TOKEN}`,
  'Accept': 'application/vnd.github+json',
  'User-Agent': 'profile-stats-refresh',
};

const fetchJson = async (url) => {
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${url}`);
  return res.json();
};

const gql = async (query, variables) => {
  const res = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, variables }),
  });
  if (!res.ok) throw new Error(`GraphQL ${res.status} ${res.statusText}`);
  const json = await res.json();
  if (json.errors) throw new Error(json.errors.map((e) => e.message).join('; '));
  return json.data;
};

const escapeXml = (s) => String(s)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#39;');

async function fetchAllRepos() {
  const repos = [];
  for (let page = 1; page <= 5; page++) {
    const batch = await fetchJson(
      `https://api.github.com/users/${USERNAME}/repos?type=owner&per_page=100&page=${page}&sort=updated`
    );
    if (!Array.isArray(batch) || batch.length === 0) break;
    repos.push(...batch);
    if (batch.length < 100) break;
  }
  return repos;
}

async function main() {
  const user = await fetchJson(`https://api.github.com/users/${USERNAME}`);
  const repos = await fetchAllRepos();

  const profile = await gql(
    `query ($login: String!) {
      user(login: $login) {
        followers { totalCount }
        repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
        pullRequests(states: MERGED) { totalCount }
        issues { totalCount }
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
        }
      }
    }`,
    { login: USERNAME }
  );
  const p = profile.user;
  const totalStars = repos.reduce((sum, r) => sum + (r.stargazers_count || 0), 0);
  const forks = repos.reduce((sum, r) => sum + (r.forks_count || 0), 0);
  const yearMs =365 * 24 * 60 * 60 * 1000;
  const now = Date.now();
  const thisYear = repos.filter((r) => new Date(r.created_at).getTime() > now - yearMs).length;
  const langMap = {};
  const totalLangRepos = repos.filter((r) => r.language).length;
  for (const r of repos) {
    if (r.language) langMap[r.language] = (langMap[r.language] || 0) + 1;
  }
  const topLangs = Object.entries(langMap).sort((a, b) => b[1] - a[1]).slice(0,  8);
  const totalLangs = topLangs.reduce((sum, entry) => sum + entry[1],  0);

  // --- stats.svg ---
  let width =  412;
  let height =  234;
  let card = `
  <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <rect x="0.5" y="0.5" width="${width-1}" height="${height-1}" rx="12" fill="#1a1b27" stroke="#414868"/>
    <text x="206" y="38" fill="#7aa2f7" font-size="16" font-weight="bold" font-family="monospace" text-anchor="middle">${escapeXml(USERNAME)}'s GitHub Stats</text>
    <text x="206" y="72" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Repositories: ${repos.length}</text>
    <text x="206" y="100" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Total Stars: ${totalStars}</text>
    <text x="206" y="128" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Total Forks: ${forks}</text>
    <text x="206" y="156" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Public Repos: ${user.public_repos || 0}</text>
    <text x="206" y="184" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Followers: ${user.followers || 0}</text>
    <text x="206" y="212" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Following: ${user.following || 0}</text>
  </svg>`;
  card = card.trim() + '\n';
  fs.writeFileSync('assets/stats.svg', card);

  // --- top-langs.svg ---
  width =  412;
  height =  80 + topLangs.length *  26;
  let top = `
  <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <rect x="0.5" y="0.5" width="${width-1}" height="${height-1}" rx="12" fill="#1a1b27" stroke="#414868"/>
    <text x="30" y="32" fill="#7aa2f7" font-size="15" font-weight="bold" font-family="monospace">Most Used Languages</text>`;
  let y =  58;
  for (const [lang, n] of topLangs) {
    const pct = totalLangRepos > 0 ? Math.round((n / totalLangRepos) * 100) : 0;
    top += `
    <text x="30" y="${y}" fill="#f8f8f2" font-size="13" font-family="monospace">${escapeXml(lang)}</text>
    <text x="${width-30}" y="${y}" fill="#6272a4" font-size="13" font-family="monospace" text-anchor="end">${pct}%</text>
    <rect x="30" y="${y+6}" width="${(width-60) * pct /  100}" height="6" rx="3" fill="#7aa2f7"/>`;
    y +=  26;
  }
  top += '\n</svg>\n';
  fs.writeFileSync('assets/top-langs.svg', top.trim() + '\n');

  // --- streak.svg ---
  width =  460;
  height =  152;
  let streak = `
  <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <rect x="0.5" y="0.5" width="${width-1}" height="${height-1}" rx="12" fill="#1a1b27" stroke="#414868"/>
    <text x="230" y="32" fill="#7aa2f7" font-size="15" font-weight="bold" font-family="monospace" text-anchor="middle">GitHub Contributions</text>
    
    <text x="230" y="62" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Repos Created (1 year): ${thisYear}</text>
    <text x="230" y="90" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Total Stars: ${totalStars}</text>
    <text x="230" y="118" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Total Forks: ${forks}</text>
    <text x="230" y="142" fill="#f8f8f2" font-size="13" font-family="monospace" text-anchor="middle">Followers: ${user.followers || 0}</text>
  </svg>`;
  fs.writeFileSync('assets/streak.svg', streak.trim() + '\n');

  // --- trophies.svg ---
  const starSum = repos.reduce((sum, r) => sum + (r.stargazers_count || 0), 0);
  const compact = (n) => (n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}K` : String(n));
  const badges = [
    { value: starSum, icon: '⭐', label: 'Stars', caption: 'Earned', color: '#bd93f9' },
    { value: p.pullRequests.totalCount, icon: '🔀', label: 'PRs Merged', caption: 'Pull Requests', color: '#50fa7b' },
    { value: p.issues.totalCount, icon: '📋', label: 'Issues', caption: 'Contributed', color: '#ff79c6' },
    { value: p.repositories.totalCount, icon: '📦', label: 'Repos', caption: 'Public', color: '#8be9fd' },
    { value: p.followers.totalCount, icon: '👥', label: 'Followers', caption: 'GitHub', color: '#ffb86c' },
    { value: p.contributionsCollection.totalCommitContributions, icon: '🚀', label: 'Commits', caption: 'Last Year', color: '#ff5555' },
  ];

  const cardW = 100;
  const gap = 20;
  const startX = 60;
  const rowH = 90;
  let troW = startX * 2 + badges.length * cardW + (badges.length - 1) * gap;
  let troH = 150;
  let trophy = `
  <svg xmlns="http://www.w3.org/2000/svg" width="${troW}" height="${troH}" viewBox="0 0 ${troW} ${troH}">
    <style>
      text { font-family: 'Segoe UI', Arial, sans-serif; }
      .title { fill: #8be9fd; font-size: 18px; font-weight: bold; }
      .badge-text { fill: #f8f8f2; font-size: 11px; font-weight: 600; }
      .badge-value { fill: #f1fa8c; font-size: 20px; font-weight: bold; }
    </style>

    <rect width="${troW}" height="${troH}" fill="#282a36" rx="12"/>
    <text x="${troW / 2}" y="28" text-anchor="middle" class="title">🏆 GitHub Achievements</text>
    <line x1="${startX - 10}" y1="40" x2="${troW - startX + 10}" y2="40" stroke="#44475a" stroke-width="1"/>

    <g transform="translate(${startX}, 15)">`;

  badges.forEach((b, i) => {
    const x = i * (cardW + gap);
    trophy += `
      <rect x="${x}" y="40" width="${cardW}" height="${rowH}" fill="#3d3d5c" rx="8"/>
      <text x="${x + cardW / 2}" y="70" text-anchor="middle" class="badge-value">${escapeXml(compact(b.value))}</text>
      <text x="${x + cardW / 2}" y="92" text-anchor="middle" fill="${b.color}" font-size="16">${b.icon}</text>
      <text x="${x + cardW / 2}" y="112" text-anchor="middle" class="badge-text">${escapeXml(b.label)}</text>
      <text x="${x + cardW / 2}" y="125" text-anchor="middle" fill="#6272a4" font-size="9">${escapeXml(b.caption)}</text>`;
  });

  trophy += `
    </g>
  </svg>`;
  fs.writeFileSync('assets/trophies.svg', trophy.trim() + '\n');

  console.log('Profile stats refreshed');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});