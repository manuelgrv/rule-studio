import { env } from 'cloudflare:workers';
import { workspaceToken, newWorkspaceToken, workspaceOwner, workspaceCookie } from '@/lib/anonymous-workspace';
import { transition } from '@/lib/workflow';
import defaults from '@/public/demo/defaults.json';
export const dynamic = 'force-dynamic';
const reply = (body: unknown, status = 200) =>
  Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
export async function GET(request: Request) {
  try {
    const previousToken = workspaceToken(request);
    const token = previousToken ?? newWorkspaceToken();
    const owner = await workspaceOwner(token);
    const row = await env.DB.prepare(
      'SELECT revision,state FROM workspaces WHERE owner = ?',
    )
      .bind(owner)
      .first<{ revision: number; state: string }>();
    const response = reply(
      row
        ? { revision: row.revision, state: JSON.parse(row.state) }
        : { revision: 0, state: null },
    );
    if (!previousToken) response.headers.set('Set-Cookie', workspaceCookie(token, request));
    return response;
  } catch (e) {
    return reply({ error: 'No se pudo abrir el espacio. Inténtalo de nuevo.' }, 500);
  }
}
export async function POST(request: Request) {
  try {
    if (request.headers.get('origin') !== new URL(request.url).origin)
      return reply({ error: 'Origen no autorizado' }, 403);
    const token = workspaceToken(request);
    if (!token) return reply({ error: 'Recarga la página y permite las cookies de este sitio para conservar tu espacio.' }, 400);
    const owner = await workspaceOwner(token);
    const text = await request.text();
    if (text.length > 750000)
      return reply({ error: 'Documento demasiado grande' }, 413);
    const req = JSON.parse(text);
    const row = await env.DB.prepare(
      'SELECT revision,state FROM workspaces WHERE owner = ?',
    )
      .bind(owner)
      .first<{ revision: number; state: string }>();
    if (req.action === 'initialize') {
      if (row)
        return reply({ revision: row.revision, state: JSON.parse(row.state) });
      const state = { ...defaults, history: [], audit: [], currentProducts: {} };
      await env.DB.prepare(
        'INSERT OR IGNORE INTO workspaces (owner,revision,state) VALUES (?,1,?)',
      )
        .bind(owner, JSON.stringify(state))
        .run();
      const saved = await env.DB.prepare(
        'SELECT revision,state FROM workspaces WHERE owner = ?',
      )
        .bind(owner)
        .first<{ revision: number; state: string }>();
      return reply({
        revision: saved!.revision,
        state: JSON.parse(saved!.state),
      });
    }
    if (!row || req.revision !== row.revision)
      return reply(
        {
          error: 'Otro cambio actualizó el espacio. Recarga antes de guardar.',
        },
        409,
      );
    const state = transition(JSON.parse(row.state), req);
    const result = await env.DB.prepare(
      'UPDATE workspaces SET state = ?, revision = revision + 1 WHERE owner = ? AND revision = ?',
    )
      .bind(JSON.stringify(state), owner, row.revision)
      .run();
    if (result.meta.changes !== 1)
      return reply({ error: 'Conflicto de versión; recarga el espacio.' }, 409);
    return reply({ revision: row.revision + 1, state });
  } catch (e) {
    return reply(
      { error: e instanceof Error ? e.message : String(e) },
      400,
    );
  }
}
