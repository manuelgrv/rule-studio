import assert from 'node:assert/strict';
const origin = new URL(process.env.RULE_STUDIO_TEST_URL || 'http://localhost:3000').origin;
const base = `${origin}/api/workspace`;
const post = (cookie, body, extra = {}) => fetch(base, {
  method: 'POST', headers: { Cookie: cookie, Origin: origin, 'Content-Type': 'application/json', ...extra },
  body: JSON.stringify(body),
});
async function visitor(cookie = '') {
  const response = await fetch(base, { headers: { Cookie: cookie } });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  const setCookie = response.headers.getSetCookie().find((cookie) => cookie.startsWith('rule_studio_workspace='));
  assert.match(setCookie, /rule_studio_workspace=[a-f0-9]{64};/);
  assert.match(setCookie, /HttpOnly/);
  assert.match(setCookie, /SameSite=Lax/);
  if (origin.startsWith('https:')) assert.match(setCookie, /Secure/);
  assert.deepEqual(await response.json(), { revision: 0, state: null });
  return setCookie.split(';')[0];
}
const first = await visitor();
let response = await post(first, { action: 'initialize' });
assert.equal(response.status, 200);
const initial = await response.json();
assert.ok(initial.state.inputs.output_schema);
response = await post(first, { action: 'save', kind: 'inputs', persona: 'policy', revision: initial.revision, document: initial.state.inputs });
assert.equal(response.status, 200);
const saved = await response.json();
assert.equal(saved.revision, initial.revision + 1);
response = await fetch(base, { headers: { Cookie: first } });
assert.equal(response.headers.getSetCookie().some((cookie) => cookie.startsWith('rule_studio_workspace=')), false);
assert.deepEqual(await response.json(), saved);
const second = await visitor();
assert.notEqual(second, first);
response = await post(second, { action: 'initialize', owner: first }, { 'x-openai-user-id': first });
assert.equal(response.status, 200);
const separate = await response.json();
assert.equal(separate.revision, 1);
assert.deepEqual(separate.state.audit, []);
assert.notDeepEqual(separate, saved);
assert.equal((await post(first, { action: 'save', kind: 'inputs', persona: 'specialist', revision: saved.revision, document: saved.state.inputs })).status, 400);
assert.equal((await post(first, {}, { Origin: 'https://untrusted.invalid' })).status, 403);
assert.equal((await post(first, { action: 'save', kind: 'inputs', persona: 'policy', revision: -1, document: saved.state.inputs })).status, 409);
assert.equal((await post('', { action: 'initialize' })).status, 400);
await visitor('rule_studio_workspace=invalid');
assert.deepEqual(await (await fetch(base, { headers: { Cookie: first } })).json(), saved);
console.log('PASS: no-login initialization, saved edits, reload, visitor isolation, cookie protections, role checks, CSRF and revision conflicts.');
