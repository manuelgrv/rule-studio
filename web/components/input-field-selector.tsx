'use client';
import { useMemo, useState } from 'react';
import { ChevronDown, Database, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '@/components/ui/collapsible';
import { catalogFields, hasInputField, selectInputField } from '@/lib/input-selection';
import type { Doc } from '@/lib/runtime';

export function InputFieldSelector({ inputs, template, disabled, onChange, onError }: {
  inputs: Doc; template: Doc; disabled: boolean; onChange: (doc: Doc) => void; onError: (message: string) => void;
}) {
  const [query, setQuery] = useState('');
  const [onlySelected, setOnlySelected] = useState(false);
  const [openTables, setOpenTables] = useState<Record<string, boolean>>({});
  const [filteredOpenTables, setFilteredOpenTables] = useState<Record<string, boolean>>({});
  const filtering = query.trim().length > 0 || onlySelected;
  const fields = useMemo(() => catalogFields(template), [template]);
  const normalize = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const terms = normalize(query).trim().split(/\s+/);
  const filtered = fields.filter(f => (!onlySelected || hasInputField(inputs, f.path)) && terms.every(term =>
    normalize(`${f.table} ${f.field} ${f.path.join('.')} ${f.dataType.type}`).includes(term)));
  const tables = [...new Set(filtered.map(f => f.table))];
  const selected = fields.filter(f => hasInputField(inputs, f.path)).length;
  function select(items: typeof fields, checked: boolean) {
    try {
      let next = inputs;
      for (const f of items) next = selectInputField(next, template, f.path, checked);
      onChange(next);
    } catch (error) { onError(error instanceof Error ? error.message : String(error)); }
  }
  return <div>
    <p className="mb-4 text-sm text-muted-foreground">Agrega o quita campos por tabla. La ruta indica su ubicación dentro del consolidado del cliente.</p>
    <div className="relative mb-3">
      <Search className="absolute left-3 top-3 text-muted-foreground" size={17} aria-hidden />
      <Input className="pl-9 min-h-10" aria-label="Buscar campos por nombre, tabla o ruta" placeholder="Buscar campo, tabla o ruta…" value={query} onChange={e => { setQuery(e.target.value); setFilteredOpenTables({}); }} />
    </div>
    <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
      <span className="text-sm text-muted-foreground" role="status">{selected} de {fields.length} campos seleccionados</span>
      <label className="flex items-center gap-2 text-sm"><Checkbox checked={onlySelected} onCheckedChange={value => { setOnlySelected(value === true); setFilteredOpenTables({}); }} />Solo seleccionados</label>
    </div>
    <div className="field-catalog">
      {!filtered.length && <div className="py-8 text-sm text-muted-foreground">No hay campos que coincidan. <Button variant="link" onClick={() => { setQuery(''); setOnlySelected(false); setFilteredOpenTables({}); }}>Limpiar filtros</Button></div>}
      {tables.map(table => {
        const visible = filtered.filter(f => f.table === table);
        const count = visible.filter(f => hasInputField(inputs, f.path)).length;
        const open = filtering ? (filteredOpenTables[table] ?? true) : (openTables[table] ?? false);
        return <Collapsible key={table} className="field-table" open={open}
          onOpenChange={value => (filtering ? setFilteredOpenTables : setOpenTables)(previous => ({ ...previous, [table]: value }))}>
          <CollapsibleTrigger className="field-table-heading w-full cursor-pointer text-left hover:bg-slate-100 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring"
            aria-label={`${open ? 'Ocultar' : 'Mostrar'} campos de ${table}`}>
            <span className="flex items-center gap-2"><Database size={17} aria-hidden /><strong>{table}</strong><Badge variant="secondary">{count}/{visible.length}</Badge></span>
            <ChevronDown size={18} aria-hidden className={`shrink-0 transition-transform motion-reduce:transition-none ${open ? 'rotate-180' : ''}`} />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="flex flex-wrap gap-1 border-t border-border px-3 py-2">
              <Button size="sm" variant="ghost" disabled={disabled || count === visible.length} onClick={() => select(visible, true)}>Agregar visibles</Button>
              <Button size="sm" variant="ghost" disabled={disabled || count === 0} onClick={() => select(visible, false)}>Quitar visibles</Button>
            </div>
          {visible.map(f => <label className="field-option" key={f.path.join('.')}>
            <Checkbox disabled={disabled} checked={hasInputField(inputs, f.path)} onCheckedChange={checked => select([f], checked === true)} />
            <div className="min-w-0 flex-1"><strong className="font-medium">{f.field}</strong><span className="block text-sm text-muted-foreground break-all">{f.path.join('.')}</span></div>
            <div className="flex flex-col items-end gap-1"><Badge variant="outline">{f.dataType.type}</Badge>{f.repeated && <span className="text-xs text-muted-foreground">Lista · 1:N</span>}</div>
          </label>)}
          </CollapsibleContent>
        </Collapsible>;
      })}
    </div>
  </div>;
}
