const { GraphQLClient, gql } = require('graphql-request');
const fs = require('fs');

const endpoint = 'https://api.github.com/graphql';
const client = new GraphQLClient(endpoint, {
  headers: { authorization: 'Bearer ' + process.env.GITHUB_TOKEN },
});

const USERNAME = process.env.GITHUB_USER || 'antono4';
const THEME = process.env.ACTIVITY_GRAPH_THEME || 'dracula';
const OUTPUT = process.env.OUTPUT_PATH || 'assets/activity-graph.svg';
const DAYS = Number(process.env.ACTIVITY_GRAPH_DAYS || 31);

const THEMES = {
  dracula: {
    areaColor: 'ff79c6',
    bgColor: '44475a',
    borderColor: 'ffffff',
    color: 'f8f8f2',
    titleColor: 'f8f8f2',
    lineColor: 'ff79c6',
    pointColor: 'bd93f9',
  },
  'github-dark': {
    areaColor: '1F6FEB',
    bgColor: '0D1117',
    borderColor: 'ffffff',
    color: '58A6FF',
    titleColor: '58A6FF',
    lineColor: '58A6FF',
    pointColor: '58A6FF',
  },
};

const query = gql`
  query($username: String!) {
    user(login: $username) {
      contributionsCollection {
        contributionCalendar {
          totalContributions
          weeks {
            contributionDays {
              contributionCount
              date
            }
          }
        }
      }
    }
  }
`;

async function generate() {
  const theme = THEMES[THEME] || THEMES.dracula;
  const data = await client.request(query, { username: USERNAME });
  const calendar = data.user.contributionsCollection.contributionCalendar;

  const days = calendar.weeks
    .flatMap((w) => w.contributionDays)
    .map((d) => ({ date: d.date, count: d.contributionCount }))
    .slice(-DAYS);

  const total = days.reduce((sum, d) => sum + d.count, 0);

  const svg = renderSvg(days, theme, {
    title: `${USERNAME}'s GitHub Activity Graph`,
    subtitle: `${total.toLocaleString()} contributions in the last ${DAYS} days`,
  });

  fs.writeFileSync(OUTPUT, svg);
  console.log(`Activity graph SVG written to ${OUTPUT} (theme: ${THEME})`);
}

function renderSvg(days, theme, { title, subtitle }) {
  const width = 1200;
  const height = 600;
  const padLeft = 65;
  const padRight = 65;
  const padTop = 110;
  const padBottom = 45;
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const maxCount = Math.max(...days.map((d) => d.count), 5);
  const stepX = plotW / (days.length - 1);

  const points = days.map((d, i) => {
    const x = padLeft + i * stepX;
    const y = padTop + plotH - (d.count / maxCount) * (plotH - 20);
    return [x, y];
  });

  const linePath = points
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`)
    .join(' ');
  const areaPath = `${linePath} L ${(padLeft + plotW).toFixed(2)} ${padTop + plotH} L ${padLeft} ${padTop + plotH} Z`;

  const circles = points
    .map(
      ([x, y]) => `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="5" fill="#${theme.pointColor}" stroke="#${theme.bgColor}" stroke-width="1"/>`
    )
    .join('\n');

  const xLabels = days
    .map((d, i) => {
      if (i % 5 !== 0) return '';
      const [, mo, dy] = d.date.split('-');
      const x = padLeft + i * stepX;
      return `<text x="${x.toFixed(2)}" y="${height - 20}" fill="#${theme.color}" text-anchor="middle" font-size="12">${mo}/${dy}</text>`;
    })
    .filter(Boolean)
    .join('\n');

  const tickCount = 4;
  const yTicks = [];
  for (let i = 0; i <= tickCount; i++) {
    const value = Math.round((maxCount / tickCount) * i);
    const y = padTop + plotH - (value / maxCount) * (plotH - 20);
    yTicks.push(
      `<line x1="${padLeft}" x2="${padLeft + plotW}" y1="${y}" y2="${y}" stroke="#${theme.color}" stroke-opacity="0.15"/>`,
      `<text x="${padLeft - 8}" y="${y + 4}" fill="#${theme.color}" text-anchor="end" font-size="12">${value}</text>`
    );
  }

  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" rx="4.5" fill="#${theme.bgColor}" stroke="#${theme.borderColor}" stroke-opacity="1" style="stroke-width:1"/>
<style>svg { font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; } .header { font: 600 20px 'Segoe UI', Ubuntu, Sans-Serif; } text { user-select: none; }</style>
<text x="${width / 2}" y="40" fill="#${theme.titleColor}" text-anchor="middle" class="header">${escapeXml(title)}</text>
<text x="${width / 2}" y="65" fill="#${theme.color}" text-anchor="middle" font-size="14">${escapeXml(subtitle)}</text>
${yTicks.join('\n')}
<path d="${areaPath}" fill="#${theme.areaColor}" fill-opacity="0.3"/>
<path d="${linePath}" stroke="#${theme.lineColor}" stroke-width="2" fill="none"/>
${circles}
${xLabels}
</svg>
`;
}

function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

generate().catch((err) => {
  console.error(err);
  process.exit(1);
});
