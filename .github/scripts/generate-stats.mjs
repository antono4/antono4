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

const compact = (n) => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 10_000 ? 0 : 1)}K`;
  return String(n);
};

// Jumlah PR/issue diambil dari Search API; kalau gagal pakai nilai GraphQL.
const searchCount = async (q, fallback) => {
  try {
    const data = await fetchJson(
      `https://api.github.com/search/issues?q=${encodeURIComponent(q)}&per_page=1`
    );
    if (typeof data.total_count === 'number') return data.total_count;
  } catch (err) {
    console.warn(`Search failed for "${q}": ${err.message}`);
  }
  return fallback;
};

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

// Semua kartu memakai kanvas identik supaya tersusun rapi saat ditampilkan
// berdampingan (2 kartu per baris) di README.
const CARD = { width: 495, height: 220 };
const FONT = 'monospace';
const THEME = {
  bg: '#1a1b27',
  border: '#414868',
  title: '#7aa2f7',
  label: '#a9b1d6',
  value: '#f8f8f2',
  bar: '#7aa2f7',
  barTrack: '#2a2e3f',
  accent: '#6272a4',
};

const cardShell = (title, body) => {
  const { width: w, height: h } = CARD;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
  <rect x="0.5" y="0.5" width="${w - 1}" height="${h - 1}" rx="12" fill="${THEME.bg}" stroke="${THEME.border}"/>
  <text x="${w / 2}" y="36" fill="${THEME.title}" font-size="16" font-weight="bold" font-family="${FONT}" text-anchor="middle">${escapeXml(title)}</text>
  <line x1="24" y1="52" x2="${w - 24}" y2="52" stroke="${THEME.border}" stroke-width="1" opacity="0.6"/>
${body}
</svg>
`;
};

// Label di kiri, nilai rata kanan.
const statRows = (rows, { startY = 82, lineHeight = 31 } = {}) =>
  rows
    .map(([label, value], i) => {
      const y = startY + i * lineHeight;
      return `  <text x="40" y="${y}" fill="${THEME.label}" font-size="14" font-family="${FONT}">${escapeXml(label)}</text>
  <text x="${CARD.width - 40}" y="${y}" fill="${THEME.value}" font-size="15" font-weight="bold" font-family="${FONT}" text-anchor="end">${escapeXml(value)}</text>`;
    })
    .join('\n');

const statsCard = (user, repos, totals) =>
  cardShell(
    'GitHub Stats',
    statRows([
      ['Repositories', String(repos.length)],
      ['Total Stars', String(totals.stars)],
      ['Total Forks', String(totals.forks)],
      ['Followers', String(user.followers || 0)],
      ['Following', String(user.following || 0)],
    ])
  );

const activityCard = (totals) =>
  cardShell(
    'Contribution Activity',
    statRows(
      [
        ['Repositories Created (1 year)', String(totals.thisYear)],
        ['Commits (1 year)', compact(totals.commits)],
        ['Merged Pull Requests', compact(totals.merged)],
        ['Issues Opened', compact(totals.issues)],
      ],
      { startY: 88, lineHeight: 34 }
    )
  );

const topLangsCard = (topLangs, totalLangRepos) => {
  const startY = 70;
  const lineHeight = 25;
  const x = 30;
  const trackW = CARD.width - x * 2;
  const rows = topLangs
    .map(([lang, n], i) => {
      const y = startY + i * lineHeight;
      const pct = totalLangRepos > 0 ? Math.round((n / totalLangRepos) * 100) : 0;
      const barW = Math.max((trackW * pct) / 100, 2).toFixed(2);
      return `  <text x="${x}" y="${y}" fill="${THEME.value}" font-size="13" font-family="${FONT}">${escapeXml(lang)}</text>
  <text x="${CARD.width - x}" y="${y}" fill="${THEME.accent}" font-size="13" font-family="${FONT}" text-anchor="end">${pct}%</text>
  <rect x="${x}" y="${y + 6}" width="${trackW}" height="6" rx="3" fill="${THEME.barTrack}"/>
  <rect x="${x}" y="${y + 6}" width="${barW}" height="6" rx="3" fill="${THEME.bar}"/>`;
    })
    .join('\n');
  return cardShell('Most Used Languages', rows);
};

const achievementsCard = (totals, followers) => {
  const badges = [
    { value: totals.stars, label: 'Stars', icon: '⭐' },
    { value: totals.repos, label: 'Repos', icon: '📦' },
    { value: followers, label: 'Followers', icon: '👥' },
    { value: totals.merged, label: 'Merged PRs', icon: '🔀' },
    { value: totals.issues, label: 'Issues', icon: '📋' },
    { value: totals.commits, label: 'Commits', icon: '🚀' },
  ];
  const cardW = 115;
  const gap = 45;
  const startX = 30;
  const rowH = 60;
  const rowY = [70, 142];
  const parts = badges.map((b, i) => {
    const x = startX + (i % 3) * (cardW + gap);
    const y = rowY[Math.floor(i / 3)];
    const cx = x + cardW / 2;
    return `  <rect x="${x}" y="${y}" width="${cardW}" height="${rowH}" rx="10" fill="#22243a"/>
  <text x="${cx}" y="${y + 24}" text-anchor="middle" fill="#f1fa8c" font-size="20" font-weight="bold" font-family="${FONT}">${escapeXml(compact(b.value))}</text>
  <text x="${cx}" y="${y + 44}" text-anchor="middle" fill="${THEME.label}" font-size="12" font-family="${FONT}">${escapeXml(b.icon)} ${escapeXml(b.label)}</text>`;
  });
  return cardShell('Achievements', parts.join('\n'));
};

async function main() {
  const user = await fetchJson(`https://api.github.com/users/${USERNAME}`);
  const repos = await fetchAllRepos();

  const profile = await gql(
    `query ($login: String!) {
      user(login: $login) {
        pullRequests(states: MERGED) { totalCount }
        issues { totalCount }
        contributionsCollection { totalCommitContributions }
      }
    }`,
    { login: USERNAME }
  );
  const p = profile.user;

  const stars = repos.reduce((sum, r) => sum + (r.stargazers_count || 0), 0);
  const forks = repos.reduce((sum, r) => sum + (r.forks_count || 0), 0);
  const yearMs = 365 * 24 * 60 * 60 * 1000;
  const now = Date.now();
  const thisYear = repos.filter((r) => new Date(r.created_at).getTime() > now - yearMs).length;

  const langMap = {};
  for (const r of repos) {
    if (r.language) langMap[r.language] = (langMap[r.language] || 0) + 1;
  }
  const topLangs = Object.entries(langMap).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const totalLangRepos = repos.filter((r) => r.language).length;

  const merged = await searchCount(
    `author:${USERNAME} type:pr is:merged`,
    p.pullRequests.totalCount
  );
  const issues = await searchCount(`author:${USERNAME} type:issue`, p.issues.totalCount);

  const totals = {
    stars,
    forks,
    repos: repos.length,
    thisYear,
    commits: p.contributionsCollection.totalCommitContributions,
    merged,
    issues,
  };

  fs.writeFileSync('assets/stats.svg', statsCard(user, repos, totals));
  fs.writeFileSync('assets/streak.svg', activityCard(totals));
  fs.writeFileSync('assets/top-langs.svg', topLangsCard(topLangs, totalLangRepos));
  fs.writeFileSync('assets/trophies.svg', achievementsCard(totals, user.followers || 0));

  console.log('Profile stats refreshed');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
