type Doc = Record<string, any>;
export type CatalogField = { path: string[]; table: string; source: string; field: string; dataType: Doc; repeated: boolean };

export function catalogFields(template: Doc): CatalogField[] {
  const fields: CatalogField[] = [];
  function visit(schema: Doc, mappings: Doc, path: string[], repeated: boolean) {
    for (const [key, mapping] of Object.entries(mappings) as [string, Doc][]) {
      const type = schema.fields[key];
      if (!type) continue;
      if (mapping.ref) {
        const source = template.sources.find((s: Doc) => s.id === mapping.ref.source);
        fields.push({ path: [...path, key], table: source?.table_ref || mapping.ref.source,
          source: mapping.ref.source, field: mapping.ref.field, dataType: type, repeated });
      } else if (mapping.object || mapping.array) {
        visit(type.type === 'array' ? type.items : type, mapping.object || mapping.array,
          [...path, key], repeated || type.type === 'array');
      }
    }
  }
  visit(template.output_schema, template.mappings, [], false);
  return fields;
}

export function hasInputField(inputs: Doc, path: string[]): boolean {
  let mapping = inputs.mappings;
  for (let i = 0; i < path.length; i++) {
    const node = mapping[path[i]];
    if (!node) return false;
    if (i === path.length - 1) return !!node.ref;
    mapping = node.object || node.array || {};
  }
  return false;
}

export function selectInputField(inputs: Doc, template: Doc, path: string[], selected: boolean): Doc {
  const next = structuredClone(inputs);
  if (selected) {
    // Enrich old drafts with the new catalog without replacing their definitions.
    for (const source of template.sources) {
      const existing = next.sources.find((s: Doc) => s.id === source.id);
      if (!existing) next.sources.push(structuredClone(source));
      else if (existing.table_ref !== source.table_ref) throw new Error(`El alias ${source.id} pertenece a otra tabla. Revisa la DSL.`);
      else existing.fields = { ...structuredClone(source.fields), ...existing.fields };
    }
    for (const join of template.joins) {
      const existing = next.joins.find((j: Doc) => j.id === join.id);
      if (!existing) next.joins.push(structuredClone(join));
      else if (['parent', 'source', 'left_key', 'right_key', 'cardinality'].some(k => existing[k] !== join[k]))
        throw new Error(`La relación ${join.id} tiene otra definición. Revisa la DSL.`);
    }
  }
  function update(schema: Doc, mappings: Doc, originalSchema: Doc, originals: Doc, depth: number) {
    const key = path[depth];
    const type = originalSchema.fields[key], mapping = originals[key];
    if (!type || !mapping) throw new Error('El campo no existe en el catálogo.');
    if (depth === path.length - 1) {
      if (selected) { schema.fields[key] = structuredClone(type); mappings[key] = structuredClone(mapping); }
      else { delete schema.fields[key]; delete mappings[key]; }
      return;
    }
    const shape = type.type === 'array' ? 'array' : 'object';
    if (!schema.fields[key] || !mappings[key]) {
      if (!selected) return;
      schema.fields[key] = structuredClone(type);
      (shape === 'array' ? schema.fields[key].items : schema.fields[key]).fields = {};
      mappings[key] = { ...structuredClone(mapping), [shape]: {} };
    }
    const child = shape === 'array' ? schema.fields[key].items : schema.fields[key];
    update(child, mappings[key][shape], shape === 'array' ? type.items : type, mapping[shape], depth + 1);
    if (!Object.keys(child.fields).length) { delete schema.fields[key]; delete mappings[key]; }
  }
  update(next.output_schema, next.mappings, template.output_schema, template.mappings, 0);
  return next;
}
