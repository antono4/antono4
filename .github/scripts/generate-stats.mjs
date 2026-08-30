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

  console.log('Profile stats refreshed');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});