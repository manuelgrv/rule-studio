import type { Doc } from './runtime';
export const personas = [
  { id: 'policy', name: 'Lucía · Inputs', permission: 'Crear inputs' },
  { id: 'variables', name: 'Mateo · Variables', permission: 'Crear variables' },
  {
    id: 'specialist',
    name: 'Ana · Reglas',
    permission: 'Crear reglas y productos',
  },
  {
    id: 'po',
    name: 'Diego · Aprobación',
    permission: 'Aprobar inputs y paquetes',
  },
];
export type Snapshot = {
  id: string;
  kind: 'inputs' | 'evaluations';
  author: string;
  contributors: string[];
  document: Doc;
  status: 'proposed' | 'published' | 'rejected';
  at: string;
  reason?: string;
};
export type Workspace = {
  inputs: Doc;
  evaluations: Doc;
  history: Snapshot[];
  audit: { at: string; actor: string; action: string }[];
  currentInput?: Doc;
  currentProducts: Record<string, Doc>;
};
export function transition(state: Workspace, req: Doc): Workspace {
  const s = structuredClone(state);
  const actor = req.persona;
  if (!personas.some((p) => p.id === actor))
    throw new Error('Perfil no válido');
  const at = new Date().toISOString();
  const { action, kind } = req;
  if (action === 'save') {
    if (kind === 'inputs' && actor !== 'policy')
      throw new Error('Se requiere permiso para crear inputs');
    if (kind === 'evaluations' && !['variables', 'specialist'].includes(actor))
      throw new Error('Se requiere permiso de autoría');
    if (
      !['inputs', 'evaluations'].includes(kind) ||
      !req.document ||
      Array.isArray(req.document)
    )
      throw new Error('Documento inválido');
    const expected = kind === 'inputs' ? 'consolidated_inputs' : 'evaluations';
    if (req.document.kind !== expected || req.document.dsl_version !== '0.1' || !Number.isInteger(req.document.definition_version) || req.document.definition_version < 1)
      throw new Error('Cabecera DSL inválida');
    if (s.history.some(h => h.kind === kind && h.status === 'published' && h.document.definition_id === req.document.definition_id && h.document.definition_version === req.document.definition_version && JSON.stringify(h.document) !== JSON.stringify(req.document)))
      throw new Error('Esta versión ya está publicada. Crea una nueva versión antes de guardar cambios.');
    if (kind === 'inputs') s.inputs = req.document;
    else {
      const next = req.document;
      if (actor === 'variables') {
        const before = { ...s.evaluations, variables: [] },
          after = { ...next, variables: [] };
        if (JSON.stringify(before) !== JSON.stringify(after))
          throw new Error('Este perfil solo puede modificar variables');
      }
      if (
        actor === 'specialist' &&
        JSON.stringify(next.variables) !==
          JSON.stringify(s.evaluations.variables)
      )
        throw new Error(
          'Para modificar variables utiliza el perfil de variables',
        );
      s.evaluations = next;
    }
  } else if (action === 'submit') {
    if (
      (kind === 'inputs' && actor !== 'policy') ||
      (kind === 'evaluations' && actor !== 'specialist')
    )
      throw new Error('No tienes permiso para proponer este documento');
    if (!['inputs', 'evaluations'].includes(kind))
      throw new Error('Tipo inválido');
    if (s.history.some((v) => v.kind === kind && v.status === 'proposed'))
      throw new Error('Ya existe una propuesta pendiente de este tipo');
    const document = structuredClone(
      kind === 'inputs' ? s.inputs : s.evaluations,
    );
    if (s.history.some(h => h.kind === kind && h.status === 'published' && h.document.definition_id === document.definition_id && h.document.definition_version >= document.definition_version))
      throw new Error('La versión debe ser posterior a la última publicación. Crea una nueva versión.');
    if (kind === 'evaluations') {
      if (!s.currentInput)
        throw new Error('Publica primero la definición de inputs');
      if (
        document.input_contract.definition_id !==
          s.currentInput.definition_id ||
        document.input_contract.definition_version !==
          s.currentInput.definition_version
      )
        throw new Error('El paquete requiere la versión vigente de inputs');
    }
    s.history.unshift({
      id: crypto.randomUUID(),
      kind,
      author: actor,
      contributors:
        kind === 'inputs' ? ['policy'] : ['variables', 'specialist'],
      document,
      status: 'proposed',
      at,
    });
  } else if (action === 'approve' || action === 'reject') {
    if (actor !== 'po')
      throw new Error('Se requiere el permiso específico de aprobación');
    const item = s.history.find((v) => v.id === req.id);
    if (!item || item.status !== 'proposed')
      throw new Error('La propuesta ya no está pendiente');
    if (item.contributors.includes(actor) || item.author === actor)
      throw new Error('No puedes aprobar tu propio trabajo');
    if (action === 'reject') {
      if (typeof req.reason !== 'string' || !req.reason.trim())
        throw new Error('Indica el motivo del rechazo');
      item.status = 'rejected';
      item.reason = req.reason.trim();
    } else {
      if (item.kind === 'inputs') {
        const incompatible = Object.values(s.currentProducts).some(
          (d) =>
            d.input_contract.definition_id !== item.document.definition_id ||
            d.input_contract.definition_version !==
              item.document.definition_version,
        );
        if (incompatible)
          throw new Error(
            'Hay productos vigentes ligados a otro contrato de inputs. Se requiere una migración coordinada.',
          );
        s.currentInput = structuredClone(item.document);
      } else {
        const c = item.document.input_contract;
        if (
          !s.currentInput ||
          c.definition_id !== s.currentInput.definition_id ||
          c.definition_version !== s.currentInput.definition_version
        )
          throw new Error(
            'El contrato de inputs cambió. Rechaza y vuelve a proponer.',
          );
        for (const p of item.document.products)
          s.currentProducts[p.id] = structuredClone(item.document);
      }
      item.status = 'published';
    }
  } else throw new Error('Acción no válida');
  s.audit.unshift({ at, actor, action: `${action} · ${kind || req.id}` });
  return s;
}
