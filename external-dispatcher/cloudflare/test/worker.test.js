import { test } from 'node:test';
import assert from 'node:assert/strict';

import { config, dueRoutines, dispatch, authorized } from '../src/worker.js';

test('config uses defaults', () => {
  const cfg = config({});
  assert.equal(cfg.owner, 'antono4');
  assert.equal(cfg.repo, 'antono4');
  assert.equal(cfg.ref, 'main');
  assert.equal(cfg.routines.length, 5);
  assert.deepEqual([...cfg.offsets].sort((a, b) => a - b), [2, 4, 6, 8, 10]);
});

test('dueRoutines only fires on configured minutes', () => {
  const cfg = config({});
  const at = (m) => dueRoutines(cfg, new Date(Date.UTC(2026, 0, 1, 0, m)));
  assert.deepEqual(at(2), cfg.routines);
  assert.deepEqual(at(10), cfg.routines);
  assert.deepEqual(at(3), []);
  assert.deepEqual(at(0), []);
});

test('authorized accepts matching bearer and query token', () => {
  const env = { DISPATCH_TOKEN: 's3cret' };
  const withBearer = new Request('https://x/', {
    headers: { Authorization: 'Bearer s3cret' },
  });
  assert.equal(authorized(withBearer, env), true);
  assert.equal(authorized(new Request('https://x/?token=s3cret'), env), true);
  assert.equal(authorized(new Request('https://x/'), env), false);
  assert.equal(authorized(new Request('https://x/?token=nope'), env), false);
  // No token configured -> open.
  assert.equal(authorized(new Request('https://x/'), {}), true);
});

test('dispatch posts to each routine and reports status', async () => {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    calls.push({ url, method: init.method, body: JSON.parse(init.body), auth: init.headers.Authorization });
    return { ok: true, status: 204, text: async () => '' };
  };
  try {
    const cfg = config({ ROUTINES: 'a.yml,b.yml' });
    const results = await dispatch(cfg, { GITHUB_TOKEN: 'tok' }, cfg.routines);
    assert.equal(calls.length, 2);
    assert.equal(calls[0].method, 'POST');
    assert.deepEqual(calls[0].body, { ref: 'main' });
    assert.equal(calls[0].auth, 'Bearer tok');
    assert.ok(calls[0].url.endsWith('/repos/antono4/antono4/actions/workflows/a.yml/dispatches'));
    assert.deepEqual(results, [
      { routine: 'a.yml', status: 204, ok: true },
      { routine: 'b.yml', status: 204, ok: true },
    ]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('dispatch requires GITHUB_TOKEN', async () => {
  await assert.rejects(() => dispatch(config({}), {}, ['a.yml']), /GITHUB_TOKEN/);
});
