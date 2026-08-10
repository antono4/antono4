const { GraphQLClient, gql } = require('graphql-request');
const fs = require('fs');

const endpoint = 'https://api.github.com/graphql';
const client = new GraphQLClient(endpoint, {
  headers: { authorization: 'Bearer ' + process.env.GITHUB_TOKEN }
});

const USERNAME = process.env.GITHUB_USER || 'antono4';

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
  const data = await client.request(query, { username: USERNAME });
  const calendar = data.user.contributionsCollection.contributionCalendar;
  const weeks = calendar.weeks;
  const totalContributions = calendar.totalContributions;
  const firstDay = weeks[0].contributionDays[0].date;
  const lastDay = weeks[weeks.length - 1].contributionDays[weeks[weeks.length - 1].contributionDays.length - 1].date;

  const svg = generateCity3D({ weeks, totalContributions, firstDay, lastDay });
  fs.writeFileSync('assets/contrib-3d.svg', svg);
  console.log('3D SVG generated! Total:', totalContributions);
}

function generateCity3D({ weeks, totalContributions, firstDay, lastDay }) {
  const colors = {
    building0: '#2d2d44',
    building1: '#9be9a8',
    building2: '#40c463',
    building3: '#216e39',
    building4: '#40a02b',
    window: '#ffffff22',
    text: '#ffffff',
    textMuted: '#888888'
  };

  const width = 1280, height = 850;
  const allContribs = [];
  weeks.forEach(w => w.contributionDays.forEach(d => allContribs.push(d.contributionCount)));
  const maxContrib = Math.max(...allContribs, 1);

  let blocks = '';
  const bw = 12, bd = 8, maxH = 80, gap = 2, sx = 50, sy = height - 150;

  weeks.forEach((week, wi) => {
    week.contributionDays.forEach((day, di) => {
      const x = sx + wi * (bw + gap);
      const y = sy + di * (bd + gap);
      let level = 0;
      if (day.contributionCount > 0) {
        const ratio = day.contributionCount / maxContrib;
        if (ratio > 0.8) level = 4;
        else if (ratio > 0.6) level = 3;
        else if (ratio > 0.3) level = 2;
        else level = 1;
      }
      const bh = level * (maxH / 4) + 5;
      const color = level === 0 ? colors.building0 :
        level === 1 ? colors.building1 :
        level === 2 ? colors.building2 :
        level === 3 ? colors.building3 : colors.building4;

      blocks += `<g transform="translate(${x},${y})">`;
      blocks += `<polygon points="0,${-bh} ${bw/2},${-bh-6} ${bw},${-bh} ${bw/2},${-bh+6}" fill="${color}" opacity="0.9"/>`;
      blocks += `<polygon points="0,${-bh} 0,0 ${bw/2},${bd/2} ${bw/2},${-bh+6}" fill="${adjustColor(color, -30)}"/>`;
      blocks += `<polygon points="${bw},${-bh} ${bw},0 ${bw/2},${bd/2} ${bw/2},${-bh+6}" fill="${adjustColor(color, -15)}"/>`;
      if (level >= 2) {
        for (let w = 0; w < 2; w++) {
          for (let h = 0; h < level; h++) {
            blocks += `<rect x="${2 + w * 5}" y="${-bh + 10 + h * 15}" width="3" height="5" fill="${colors.window}" rx="1"/>`;
          }
        }
      }
      blocks += '</g>';
    });
  });

  let stars = '';
  for (let i = 0; i < 50; i++) {
    stars += `<circle cx="${Math.floor(Math.random() * width)}" cy="${Math.floor(Math.random() * (height - 200))}" r="${Math.random() * 2 + 0.5}" fill="#ffffff" opacity="${Math.random() * 0.5 + 0.3}"/>`;
  }

  const total = totalContributions.toLocaleString();

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><defs><linearGradient id="skyGradient" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#0a0a1a"/><stop offset="100%" stop-color="#1a1a3a"/></linearGradient><linearGradient id="groundGradient" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#1a1a2e"/><stop offset="100%" stop-color="#0d0d1a"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="3" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter><filter id="shadow"><feDropShadow dx="2" dy="4" stdDeviation="3" flood-color="#000" flood-opacity="0.5"/></filter></defs><rect width="${width}" height="${height}" fill="url(#skyGradient)"/>${stars}<circle cx="1100" cy="100" r="40" fill="#f5f5dc" opacity="0.9"/><circle cx="1115" cy="90" r="8" fill="#e0e0c0" opacity="0.5"/><circle cx="1095" cy="105" r="5" fill="#e0e0c0" opacity="0.4"/><g filter="url(#shadow)">${blocks}</g><rect x="0" y="${height - 100}" width="${width}" height="100" fill="url(#groundGradient)"/><rect x="0" y="${height - 100}" width="${width}" height="2" fill="#333355"/><text x="50" y="50" fill="${colors.text}" font-family="Segoe UI, Arial" font-size="28" font-weight="bold">${USERNAME}'s Contribution City</text><text x="50" y="80" fill="${colors.textMuted}" font-family="Segoe UI, Arial" font-size="16">${firstDay} → ${lastDay}</text><g transform="translate(50, ${height - 60})"><rect x="0" y="0" width="200" height="50" rx="8" fill="#ffffff10"/><text x="100" y="25" fill="${colors.text}" font-family="Segoe UI, Arial" font-size="24" font-weight="bold" text-anchor="middle" filter="url(#glow)">${total}</text><text x="100" y="42" fill="${colors.textMuted}" font-family="Segoe UI, Arial" font-size="12" text-anchor="middle">contributions</text></g><g transform="translate(${width - 200}, ${height - 60})"><rect x="0" y="0" width="180" height="50" rx="8" fill="#ffffff10"/><rect x="10" y="15" width="15" height="15" fill="${colors.building0}"/><text x="30" y="27" fill="${colors.textMuted}" font-size="10">None</text><rect x="60" y="15" width="15" height="15" fill="${colors.building1}"/><text x="80" y="27" fill="${colors.textMuted}" font-size="10">Low</text><rect x="110" y="15" width="15" height="15" fill="${colors.building2}"/><text x="130" y="27" fill="${colors.textMuted}" font-size="10">Med</text><rect x="155" y="15" width="15" height="15" fill="${colors.building4}"/><text x="175" y="27" fill="${colors.textMuted}" font-size="10">High</text></g></svg>`;
}

function adjustColor(hex, amount) {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.max(0, Math.min(255, (num >> 16) + amount));
  const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + amount));
  const b = Math.max(0, Math.min(255, (num & 0x0000FF) + amount));
  return '#' + (0x1000000 + r * 0x10000 + g * 0x100 + b).toString(16).slice(1);
}

generate().catch(err => { console.error(err); process.exit(1); });
