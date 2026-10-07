/**
 * External dispatcher for antono4/antono4 routine workflows.
 *
 * GitHub throttles `schedule:` triggers for high-frequency crons, so the routine
 * workflows end up running every few hours instead of every 10 minutes. This Worker
 * runs on a Cloudflare Cron Trigger (1-minute granularity, free tier) and calls the
 * GitHub `workflow_dispatch` API for each routine every 10 minutes.
 *
 * Two entry points:
 *   - scheduled(): the cron trigger, fires every minute and dispatches when the
 *     current minute matches one of the routine offsets.
 *   - fetch(): a manual/health endpoint. GET returns status; GET/POST with a
 *     `?token=` matching DISPATCH_TOKEN (or an Authorization: Bearer header) forces a
 *     dispatch, which is handy for testing and for pointing an external cron at it.
 *
 * Configuration (wrangler secret / vars):
 *   GITHUB_TOKEN   - PAT with `repo` + `workflow` scope (secret, required).
 *   DISPATCH_TOKEN - optional shared secret to protect the fetch endpoint.
 *   OWNER, REPO    - target repository (vars, default antono4/antono4).
 *   REF            - git ref to dispatch (var, default main).
 *   ROUTINES       - comma-separated workflow files to dispatch.
 *   MINUTE_OFFSETS - comma-separated minutes (0-59) at which a dispatch fires.
 */

const DEFAULT_OWNER = 'antono4';
const DEFAULT_REPO = 'antono4';
const DEFAULT_REF = 'main';
const DEFAULT_ROUTINES = [
  'activity-graph.yml',
  'generate-assets.yml',
  'profile-3d-contrib.yml',
  'profile-stats.yml',
  'autocommit.yml',
].join(',');

// Each routine fires once per hour at its own minute, matching the in-repo crons'
// offsets. Because every offset is unique, one cron tick dispatches exactly one
// routine, so the jobs never race each other on the same branch.
const DEFAULT_MINUTE_OFFSETS = '2,4,6,8,10';

const GITHUB_API = 'https://api.github.com';

function config(env) {
  return {
    owner: env.OWNER || DEFAULT_OWNER,
    repo: env.REPO || DEFAULT_REPO,
    ref: env.REF || DEFAULT_REF,
    routines: (env.ROUTINES || DEFAULT_ROUTINES).split(',').map((s) => s.trim()).filter(Boolean),
    offsets: new Set(
      (env.MINUTE_OFFSETS || DEFAULT_MINUTE_OFFSETS)
        .split(',')
        .map((s) => Number(s.trim()))
        .filter((n) => Number.isInteger(n) && n >= 0 && n < 60),
    ),
  };
}

function dueRoutines(cfg, date) {
  const minute = date.getUTCMinutes();
  return cfg.offsets.has(minute) ? cfg.routines : [];
}

async function dispatch(cfg, env, routines) {
  if (!env.GITHUB_TOKEN) {
    throw new Error('GITHUB_TOKEN is not set');
  }

  const results = [];
  for (const routine of routines) {
    const url = `${GITHUB_API}/repos/${cfg.owner}/${cfg.repo}/actions/workflows/${routine}/dispatches`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'antono4-external-dispatcher',
      },
      body: JSON.stringify({ ref: cfg.ref }),
    });
    results.push({ routine, status: res.status, ok: res.status === 204 });
    if (!res.ok) {
      const text = await res.text();
      results[results.length - 1].error = text.slice(0, 300);
    }
  }
  return results;
}

function authorized(request, env) {
  if (!env.DISPATCH_TOKEN) return true; // endpoint is open when no token is configured
  const header = request.headers.get('Authorization') || '';
  const bearer = header.startsWith('Bearer ') ? header.slice(7) : '';
  const url = new URL(request.url);
  return bearer === env.DISPATCH_TOKEN || url.searchParams.get('token') === env.DISPATCH_TOKEN;
}

async function handleFetch(request, env) {
  const cfg = config(env);
  const url = new URL(request.url);
  const now = new Date();

  if (!authorized(request, env)) {
    return Response.json({ error: 'unauthorized' }, { status: 401 });
  }

  const force = url.searchParams.get('force') === '1';
  const routines = force ? cfg.routines : dueRoutines(cfg, now);
  const body = {
    now: now.toISOString(),
    minute: now.getUTCMinutes(),
    due: routines,
    forced: force,
  };

  if (routines.length > 0) {
    body.results = await dispatch(cfg, env, routines);
  }

  return Response.json(body);
}

export default {
  async scheduled(event, env, ctx) {
    const cfg = config(env);
    const routines = dueRoutines(cfg, new Date(event.scheduledTime));
    if (routines.length === 0) return;
    ctx.waitUntil(dispatch(cfg, env, routines));
  },

  async fetch(request, env) {
    return handleFetch(request, env);
  },
};

export { config, dueRoutines, dispatch, authorized };
