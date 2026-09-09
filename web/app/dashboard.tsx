'use client';
import { useEffect, useState, type ReactNode } from 'react';
import {
  Database,
  Braces,
  GitBranch,
  ShieldCheck,
  LayoutDashboard,
  ArrowRight,
  Layers,
  CheckCircle2,
  FlaskConical,
  FileJson,
  Save,
  Download,
  Plus,
  Trash2,
  ChevronRight,
  RefreshCw,
  CircleAlert,
} from 'lucide-react';
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarInset,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  compile,
  experiment,
  previewTable,
  tables,
  type Doc,
} from '@/lib/runtime';
import { personas, type Workspace } from '@/lib/workflow';
import { registerNavigation } from '@/lib/webmcp';

const modules = [
  'Resumen operativo',
  'Selección de inputs',
  'Variables virtuales',
  'Estudio de reglas',
  'Aprobaciones',
  'Laboratorio',
];
const icons = [
  LayoutDashboard,
  Database,
  Braces,
  GitBranch,
  ShieldCheck,
  FlaskConical,
];
const descriptions = [
  'Versiones, productos y trabajo pendiente.',
  'Define la información disponible por cliente.',
  'Cálculos reutilizables sobre el consolidado.',
  'Reglas booleanas y criterios por producto.',
  'Revisa y publica versiones completas.',
  'Experimentos con datos sintéticos en este navegador.',
];
const copy = <T,>(v: T): T => structuredClone(v);
const pretty = (x: unknown) => JSON.stringify(x, null, 2);
const ref = (scope: string, ...path: string[]) => ({ ref: { scope, path } });
const lit = (value = 0) => ({
  literal: { value, data_type: { type: 'integer', nullable: false } },
});
function Pick({
  value,
  onChange,
  options,
  label,
  disabled = false,
}: {
  value: string;
  onChange: (v: string) => void;
  options: (string | { value: string; label: string })[];
  label: string;
  disabled?: boolean;
}) {
  return (
    <Select
      value={value}
      onValueChange={(v) => v !== null && onChange(v)}
      disabled={disabled}
    >
      <SelectTrigger aria-label={label} className="min-h-10 w-full bg-white">
        <SelectValue>
          {(
            options.find((o) => typeof o === 'object' && o.value === value) as
              | { label: string }
              | undefined
          )?.label || value}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => {
          const v = typeof o === 'string' ? o : o.value;
          return (
            <SelectItem value={v} key={v}>
              {typeof o === 'string' ? o : o.label}
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
function Panel({
  title,
  aside,
  children,
}: {
  title: string;
  aside?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}
function Code({ value }: { value: unknown }) {
  return (
    <pre className="code-view">
      {typeof value === 'string' ? value : pretty(value)}
    </pre>
  );
}
function Fields({
  schema,
  prefix = '',
  onSelect,
}: {
  schema: Doc;
  prefix?: string;
  onSelect?: (path: string) => void;
}) {
  return (
    <div className="field-tree">
      {Object.entries(schema.fields || {}).map(([key, raw]) => {
        const t = raw as Doc,
          p = prefix ? `${prefix}.${key}` : key;
        return (
          <div key={key}>
            <div className="field-row">
              <Braces size={14} />
              {onSelect ? (
                <Button variant="ghost" size="sm" onClick={() => onSelect(p)}>
                  {key}
                </Button>
              ) : (
                <span>{key}</span>
              )}
              <code>
                {t.type}
                {t.nullable ? ' · null' : ''}
              </code>
            </div>
            {t.type === 'struct' && (
              <Fields schema={t} prefix={p} onSelect={onSelect} />
            )}
            {t.type === 'array' && (
              <Fields schema={t.items} prefix={`${p}[]`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
function paths(schema: Doc, prefix = ''): string[] {
  return Object.entries(schema.fields || {}).flatMap(([k, raw]) => {
    const t = raw as Doc,
      p = prefix ? `${prefix}.${k}` : k;
    return t.type === 'struct' ? paths(t, p) : [p];
  });
}
function expressionText(e: Doc): string {
  if (e.ref) return `${e.ref.scope}.${e.ref.path.join('.')}`;
  if (e.literal) return String(e.literal.value);
  return `${e.op}(${(e.args || []).map(expressionText).join(', ')}${e.path ? `; ${e.path.join('.')}` : ''})`;
}
const operators = [
  'add',
  'sub',
  'mul',
  'div',
  'gt',
  'gte',
  'lt',
  'lte',
  'eq',
  'ne',
  'and',
  'or',
  'not',
  'coalesce',
  'if',
  'is_null',
  'sum',
  'count',
  'min',
  'max',
  'mean',
  'exists',
  'all',
];
function ExpressionEditor({
  value,
  onChange,
  references,
  depth = 0,
  product = false,
}: {
  value: Doc;
  onChange: (v: Doc) => void;
  references: string[];
  depth?: number;
  product?: boolean;
}) {
  const kind = value.ref ? 'ref' : value.literal ? 'literal' : 'op';
  const ops = product ? ['and', 'or', 'not'] : operators;
  return (
    <div className="expression-node">
      <div className="flex flex-wrap gap-2">
        <div className="w-36">
          <Pick
            label="Tipo de expresión"
            value={kind}
            options={[
              { value: 'ref', label: 'Referencia' },
              ...(!product ? [{ value: 'literal', label: 'Constante' }] : []),
              { value: 'op', label: 'Operación' },
            ]}
            onChange={(k) =>
              onChange(
                k === 'ref'
                  ? ref(product ? 'rule' : 'input', product ? 'adult' : 'age')
                  : k === 'literal'
                    ? lit(18)
                    : {
                        op: product ? 'and' : 'gte',
                        args: [
                          ref(
                            product ? 'rule' : 'input',
                            product ? 'adult' : 'age',
                          ),
                          product ? ref('rule', 'affordability') : lit(18),
                        ],
                      },
              )
            }
          />
        </div>
        {kind === 'ref' && (
          <div className="min-w-48 flex-1">
            <Pick
              label="Campo o variable"
              value={`${value.ref.scope}.${value.ref.path.join('.')}`}
              options={references}
              onChange={(s) => {
                const [scope, ...path] = s.split('.');
                onChange(ref(scope, ...path));
              }}
            />
          </div>
        )}
        {kind === 'literal' && (
          <>
            <div className="w-36">
              <Pick
                label="Tipo de constante"
                value={value.literal.data_type.type}
                options={['integer', 'decimal', 'string', 'boolean']}
                onChange={(type) =>
                  onChange({
                    literal: {
                      value:
                        type === 'boolean'
                          ? true
                          : type === 'string'
                            ? ''
                            : type === 'decimal'
                              ? '0.00'
                              : 0,
                      data_type: {
                        type,
                        nullable: false,
                        ...(type === 'decimal'
                          ? { precision: 28, scale: 6 }
                          : {}),
                      },
                    },
                  })
                }
              />
            </div>
            {value.literal.data_type.type === 'boolean' ? (
              <Pick
                label="Valor booleano"
                value={String(value.literal.value)}
                options={['true', 'false']}
                onChange={(v) =>
                  onChange({
                    ...value,
                    literal: { ...value.literal, value: v === 'true' },
                  })
                }
              />
            ) : (
              <Input
                aria-label="Valor constante"
                className="max-w-48"
                value={String(value.literal.value)}
                onChange={(e) =>
                  onChange({
                    ...value,
                    literal: {
                      ...value.literal,
                      value:
                        value.literal.data_type.type === 'integer'
                          ? Number(e.target.value)
                          : e.target.value,
                    },
                  })
                }
              />
            )}
          </>
        )}
        {kind === 'op' && (
          <div className="w-40">
            <Pick
              label="Operador"
              value={value.op}
              options={ops}
              onChange={(op) =>
                onChange({
                  ...value,
                  op,
                  args: [
                    'not',
                    'is_null',
                    'sum',
                    'count',
                    'min',
                    'max',
                    'mean',
                  ].includes(op)
                    ? value.args.slice(0, 1)
                    : value.args,
                })
              }
            />
          </div>
        )}
      </div>
      {kind === 'op' && (
        <div className="expression-args">
          {(value.args || []).map((a: Doc, i: number) => (
            <div className="flex items-start gap-2" key={i}>
              <div className="min-w-0 flex-1">
                {depth < 8 ? (
                  <ExpressionEditor
                    value={a}
                    references={references}
                    product={product}
                    depth={depth + 1}
                    onChange={(v) =>
                      onChange({
                        ...value,
                        args: value.args.map((x: Doc, j: number) =>
                          i === j ? v : x,
                        ),
                      })
                    }
                  />
                ) : (
                  <Code value={a} />
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Eliminar operando"
                onClick={() =>
                  onChange({
                    ...value,
                    args: value.args.filter((_: Doc, j: number) => j !== i),
                  })
                }
              >
                <Trash2 size={14} />
              </Button>
            </div>
          ))}
          <Button
            size="sm"
            variant="ghost"
            onClick={() =>
              onChange({
                ...value,
                args: [...value.args, product ? ref('rule', 'adult') : lit()],
              })
            }
          >
            <Plus /> Operando
          </Button>
          {['sum', 'min', 'max', 'mean'].includes(value.op) && (
            <Input
              aria-label="Campo del objeto a agregar"
              placeholder="Campo del objeto, por ejemplo balance"
              value={(value.path || []).join('.')}
              onChange={(e) =>
                onChange({
                  ...value,
                  path: e.target.value.split('.').filter(Boolean),
                })
              }
            />
          )}
        </div>
      )}
    </div>
  );
}
function download(name: string, value: unknown) {
  const u = URL.createObjectURL(
    new Blob([pretty(value)], { type: 'application/json' }),
  );
  const a = document.createElement('a');
  a.href = u;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(u), 1000);
}

export default function Dashboard() {
  const [active, setActive] = useState(0),
    [persona, setPersona] = useState('policy');
  useEffect(() => registerNavigation(setActive), []);
  const [defaults, setDefaults] = useState<Doc | null>(null),
    [workspace, setWorkspace] = useState<Workspace | null>(null),
    [revision, setRevision] = useState(0);
  const [inputs, setInputs] = useState<Doc | null>(null),
    [evaluations, setEvaluations] = useState<Doc | null>(null);
  const [busy, setBusy] = useState(''),
    [message, setMessage] = useState(''),
    [error, setError] = useState('');
  const [source, setSource] = useState('clients'),
    [sample, setSample] = useState<Doc[]>([]),
    [sql, setSql] = useState('');
  const [raw, setRaw] = useState(''),
    [packageRaw, setPackageRaw] = useState('');
  const [variableId, setVariableId] = useState('nueva_variable'),
    [variableExpr, setVariableExpr] = useState<Doc>({
      op: 'add',
      args: [ref('variable', 'income'), lit(100)],
    });
  const [ruleId, setRuleId] = useState('nueva_regla'),
    [language, setLanguage] = useState('visual'),
    [ruleExpr, setRuleExpr] = useState<Doc>({
      op: 'gte',
      args: [ref('input', 'age'), lit(18)],
    });
  const [python, setPython] = useState(
      'def regla(inputs, variables, constants) -> bool:\n    return inputs["age"] >= constants["minimum_age"]',
    ),
    [sqlRule, setSqlRule] = useState('inputs.age >= constants.minimum_age');
  const [productId, setProductId] = useState('nuevo_producto'),
    [productExpr, setProductExpr] = useState<Doc>({
      op: 'and',
      args: [ref('rule', 'adult'), ref('rule', 'affordability')],
    }),
    [reason, setReason] = useState('');
  const [result, setResult] = useState<Doc | null>(null),
    [limit, setLimit] = useState('100'),
    [resultTab, setResultTab] = useState('products'),
    [filter, setFilter] = useState('');
  const [compiled, setCompiled] = useState<Doc | null>(null);
  const accept = (data: Doc) => {
    setRevision(data.revision);
    setWorkspace(data.state);
    setInputs(copy(data.state.inputs));
    setEvaluations(copy(data.state.evaluations));
    setRaw(pretty(data.state.inputs));
    setPackageRaw(pretty(data.state.evaluations));
  };
  async function request(body: Doc) {
    const r = await fetch('/api/workspace', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revision, persona, ...body }),
    });
    const d = (await r.json()) as Doc;
    if (!r.ok) throw new Error(d.error || 'No se pudo guardar');
    return d;
  }
  async function task(label: string, fn: () => Promise<void>) {
    if (busy) return;
    setBusy(label);
    setError('');
    setMessage('');
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy('');
    }
  }
  async function load() {
    setError('');
    try {
      const d = (await fetch('/demo/defaults.json').then((r) => r.json())) as Doc;
      setDefaults(d);
      const r = await fetch('/api/workspace');
      const s = (await r.json()) as Doc;
      if (!r.ok)
        throw new Error(
          r.status === 401
            ? 'Inicia sesión con ChatGPT para abrir tu espacio.'
            : s.error,
        );
      accept(s.state ? s : await request({ action: 'initialize' }));
    } catch (e) {
      setError(String(e));
    }
  }
  useEffect(() => {
    void load();
  }, []);
  const payload = (action: string, extra: Doc = {}) => ({
    action,
    inputs,
    evaluations,
    catalog: defaults!.inputs.sources,
    ...extra,
  });
  const references =
    inputs && evaluations
      ? [
          ...paths(inputs.output_schema).map((p) => `input.${p}`),
          ...evaluations.variables.map((v: Doc) => `variable.${v.id}`),
          ...Object.keys(evaluations.constants).map((k) => `constant.${k}`),
          ...paths(inputs.output_schema)
            .filter((p) => !p.includes('.'))
            .map((p) => `item.${p}`),
        ]
      : [];
  const ruleReferences =
    evaluations?.rules.map((r: Doc) => `rule.${r.id}`) || [];
  const canInput = persona === 'policy',
    canVariable = persona === 'variables',
    canRule = persona === 'specialist';
  function changeInput(doc: Doc) {
    setInputs(doc);
    setRaw(pretty(doc));
    setCompiled(null);
  }
  function changePackage(doc: Doc) {
    setEvaluations(doc);
    setPackageRaw(pretty(doc));
    setCompiled(null);
  }
  async function validate(kind = 'evaluations') {
    const v = await compile(payload(kind === 'inputs' ? 'inputs' : 'validate'));
    setSql(v.sql);
    setCompiled(v);
    setMessage('Compilación correcta. Tipos y referencias válidos.');
    return v;
  }
  async function save(kind: string) {
    await validate(kind);
    accept(
      await request({
        action: 'save',
        kind,
        document: kind === 'inputs' ? inputs : evaluations,
      }),
    );
    setMessage('Borrador guardado en tu espacio.');
  }
  async function submit(kind: string) {
    await validate(kind);
    const saved = await request({
      action: 'save',
      kind,
      document: kind === 'inputs' ? inputs : evaluations,
    });
    const r = await fetch('/api/workspace', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'submit',
        kind,
        persona,
        revision: saved.revision,
      }),
    });
    const d = (await r.json()) as Doc;
    if (!r.ok) {
      accept(saved);
      throw new Error(d.error);
    }
    accept(d);
    setMessage(
      'Propuesta enviada. Cambia al perfil de aprobación para revisarla.',
    );
  }
  function newVersion(kind: 'inputs' | 'evaluations') {
    const d = copy(kind === 'inputs' ? inputs! : evaluations!);
    d.definition_version =
      Math.max(
        d.definition_version,
        ...(workspace?.history
          .filter((h) => h.kind === kind)
          .map((h) => h.document.definition_version) || []),
      ) + 1;
    d.created_by = persona;
    d.created_at = new Date().toISOString();
    kind === 'inputs' ? changeInput(d) : changePackage(d);
  }
  const editorActions = (kind: 'inputs' | 'evaluations') => (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="outline"
        disabled={!!busy}
        onClick={() =>
          task('Compilando…', async () => {
            await validate(kind);
          })
        }
      >
        <CheckCircle2 /> Validar
      </Button>
      <Button
        variant="outline"
        disabled={
          !!busy || !(kind === 'inputs' ? canInput : canVariable || canRule)
        }
        onClick={() => task('Guardando…', () => save(kind))}
      >
        <Save /> Guardar
      </Button>
      <Button
        disabled={!!busy || !(kind === 'inputs' ? canInput : canRule)}
        onClick={() => task('Preparando propuesta…', () => submit(kind))}
      >
        Proponer publicación <ArrowRight />
      </Button>
    </div>
  );
  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader className="px-6 py-8">
          <div className="mb-3 flex items-center gap-3">
            <Layers size={27} />
            <span className="text-xs tracking-[.2em] opacity-70">
              ESPACIO DE REGLAS
            </span>
          </div>
          <strong className="text-xl">Rule Studio</strong>
          <span className="text-sm opacity-65">Diseño y evaluación</span>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>DISEÑO Y GOBIERNO</SidebarGroupLabel>
            <SidebarMenu>
              {modules.map((name, i) => {
                const Icon = icons[i];
                return (
                  <SidebarMenuItem key={name}>
                    <SidebarMenuButton
                      size="lg"
                      isActive={active === i}
                      onClick={() => setActive(i)}
                    >
                      <Icon />
                      <span>{name}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter className="p-6">
          <div className="rounded-lg border border-white/15 p-3 text-sm">
            <span className="block font-medium">Demo sintética</span>
            <span className="mt-1 block opacity-65">
              Datos y cálculos en tu navegador. Ediciones guardadas en Sites.
            </span>
          </div>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <header className="topbar">
          <div className="flex items-center gap-3">
            <SidebarTrigger />
            <span className="text-sm text-muted-foreground">
              Mi espacio <ChevronRight className="inline" size={14} /> Rule Studio
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="secondary">Experimental</Badge>
            <div className="w-64">
              <Pick
                label="Perfil sintético de demostración"
                value={persona}
                onChange={setPersona}
                options={personas.map((p) => ({ value: p.id, label: p.name }))}
              />
            </div>
          </div>
        </header>
        <div className="workspace">
          <div className="page-heading">
            <div>
              <p className="eyebrow">
                {active < 4 ? 'DISEÑO DE POLÍTICAS' : 'CONTROL Y TRAZABILIDAD'}
              </p>
              <h1>{modules[active]}</h1>
              <p className="mt-2 text-muted-foreground">
                {descriptions[active]}
              </p>
            </div>
            {active === 1 && editorActions('inputs')}
            {(active === 2 || active === 3) && editorActions('evaluations')}
          </div>
          <div className="mb-5 text-sm text-muted-foreground">
            Perfil de demostración:{' '}
            {personas.find((p) => p.id === persona)?.permission}. Puedes
            cambiarlo para recorrer el flujo.
          </div>
          {(busy || message || error) && (
            <div
              role={error ? 'alert' : 'status'}
              className={`notice ${error ? 'notice-error' : ''}`}
            >
              {error ? (
                <CircleAlert size={18} />
              ) : busy ? (
                <RefreshCw size={18} className="animate-spin" />
              ) : (
                <CheckCircle2 size={18} />
              )}
              <span>{error || busy || message}</span>
            </div>
          )}
          {!workspace || !inputs || !evaluations ? (
            <Panel title="Tu espacio de trabajo">
              <Skeleton className="h-28 w-full" />
              {error && (
                <div className="mt-4 flex gap-3">
                  <Button onClick={load}>Reintentar</Button>
                  <a
                    className="text-primary underline"
                    href="/signin-with-chatgpt?return_to=%2F"
                    target="_top"
                  >
                    Iniciar sesión
                  </a>
                </div>
              )}
            </Panel>
          ) : (
            <>
              {active === 0 && (
                <>
                  <div className="stats-grid">
                    {[
                      [
                        'Inputs disponibles',
                        paths(inputs.output_schema).length,
                        'Campos tipados',
                      ],
                      [
                        'Variables virtuales',
                        evaluations.variables.length,
                        'Cálculos reutilizables',
                      ],
                      [
                        'Reglas de evaluación',
                        evaluations.rules.length,
                        'Salida booleana',
                      ],
                      [
                        'Productos vigentes',
                        Object.keys(workspace.currentProducts).length,
                        'Una evaluación por producto',
                      ],
                    ].map(([label, note, sub]) => (
                      <div className="stat" key={label}>
                        <span>{label}</span>
                        <strong>{note}</strong>
                        <small>{sub}</small>
                      </div>
                    ))}
                  </div>
                  <div className="module-grid">
                    {modules.slice(1, 4).map((name, i) => (
                      <Panel
                        key={name}
                        title={name}
                        aside={<span className="step-number">0{i + 1}</span>}
                      >
                        <p className="mb-6 text-muted-foreground">
                          {descriptions[i + 1]}
                        </p>
                        <Button
                          variant="outline"
                          onClick={() => setActive(i + 1)}
                        >
                          Abrir módulo <ArrowRight />
                        </Button>
                      </Panel>
                    ))}
                  </div>
                  <div className="two-columns">
                    <Panel title="Publicaciones vigentes">
                      <div className="catalog-row">
                        <Database size={18} />
                        <div>
                          <strong>Consolidado compartido</strong>
                          <p className="text-sm text-muted-foreground">
                            {workspace.currentInput
                              ? `Versión ${workspace.currentInput.definition_version}`
                              : 'Aún no publicado'}
                          </p>
                        </div>
                      </div>
                      {Object.entries(workspace.currentProducts).map(
                        ([id, d]) => (
                          <div className="catalog-row" key={id}>
                            <GitBranch size={18} />
                            <strong>{id}</strong>
                            <Badge variant="secondary">
                              v{d.definition_version}
                            </Badge>
                          </div>
                        ),
                      )}
                      <Button
                        className="mt-4"
                        variant="ghost"
                        onClick={() => setActive(4)}
                      >
                        Ver aprobaciones <ArrowRight />
                      </Button>
                    </Panel>
                    <Panel title="Actividad reciente">
                      {workspace.audit.length ? (
                        workspace.audit.slice(0, 5).map((a, i) => (
                          <div className="catalog-row" key={i}>
                            <div>
                              <p>{a.action}</p>
                              <small>
                                {a.actor} ·{' '}
                                {new Date(a.at).toLocaleString('es-PE')}
                              </small>
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-muted-foreground">
                          Empieza por revisar y proponer el consolidado de
                          inputs.
                        </p>
                      )}
                    </Panel>
                  </div>
                </>
              )}
              {active === 1 && (
                <>
                  <div className="version-strip">
                    <FileJson size={17} />
                    <strong>{inputs.definition_id}</strong>
                    <Badge variant="outline">
                      v{inputs.definition_version}
                    </Badge>
                    <span>Cliente · Fecha de proceso · Ejecución</span>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={!canInput}
                      onClick={() => newVersion('inputs')}
                    >
                      Nueva versión
                    </Button>
                  </div>
                  <Tabs defaultValue="designer">
                    <TabsList variant="line">
                      <TabsTrigger value="designer">Diseñador</TabsTrigger>
                      <TabsTrigger value="sources">
                        Fuentes y muestra
                      </TabsTrigger>
                      <TabsTrigger value="dsl">DSL y relaciones</TabsTrigger>
                    </TabsList>
                    <TabsContent value="designer">
                      <div className="two-columns">
                        <Panel
                          title="Campos del consolidado"
                          aside={
                            <Badge variant="secondary">Tipado estricto</Badge>
                          }
                        >
                          <p className="mb-4 text-sm text-muted-foreground">
                            Selecciona las secciones que estarán disponibles
                            para reglas y variables. Edita la estructura y los
                            joins en la pestaña DSL.
                          </p>
                          {Object.entries(
                            defaults!.inputs.output_schema.fields,
                          ).map(([key, rawType]) => (
                            <label
                              className="catalog-row cursor-pointer"
                              key={key}
                            >
                              <Checkbox
                                disabled={!canInput}
                                checked={key in inputs.output_schema.fields}
                                onCheckedChange={(checked) => {
                                  const d = copy(inputs);
                                  if (checked) {
                                    d.output_schema.fields[key] = copy(rawType);
                                    d.mappings[key] = copy(
                                      defaults!.inputs.mappings[key],
                                    );
                                  } else {
                                    delete d.output_schema.fields[key];
                                    delete d.mappings[key];
                                  }
                                  changeInput(d);
                                }}
                              />
                              <div>
                                <strong>{key}</strong>
                                <p className="text-sm text-muted-foreground">
                                  {(rawType as Doc).type === 'array'
                                    ? 'Relación 1:N · lista de objetos'
                                    : (rawType as Doc).type === 'struct'
                                      ? 'Relación 1:1 · objeto'
                                      : 'Campo del cliente'}
                                </p>
                              </div>
                            </label>
                          ))}
                        </Panel>
                        <Panel title="Estructura disponible">
                          <Fields schema={inputs.output_schema} />
                        </Panel>
                      </div>
                      <Panel title="Relaciones de recuperación">
                        {inputs.joins.map((j: Doc) => (
                          <div className="join-row" key={j.id}>
                            <code>
                              {j.parent}.{j.left_key}
                            </code>
                            <ArrowRight size={16} />
                            <code>
                              {j.source}.{j.right_key}
                            </code>
                            <Badge variant="outline">
                              {j.cardinality === 'many' ? '1:N' : '1:1'}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              {j.id}
                            </span>
                          </div>
                        ))}
                      </Panel>
                    </TabsContent>
                    <TabsContent value="sources">
                      <Panel title="Catálogo de fuentes sintéticas">
                        <div className="flex flex-wrap gap-2 mb-5">
                          {tables.map((t) => (
                            <Button
                              key={t}
                              variant={t === source ? 'default' : 'outline'}
                              disabled={!!busy}
                              onClick={() =>
                                task('Cargando tabla sintética…', async () => {
                                  setSource(t);
                                  setSample(await previewTable(t));
                                })
                              }
                            >
                              <Database />
                              {t}
                            </Button>
                          ))}
                        </div>
                        <div className="mb-5 flex flex-wrap gap-2">
                          {Object.entries(
                            defaults!.inputs.sources.find(
                              (s: Doc) => s.table_ref === source,
                            ).fields,
                          ).map(([k, t]) => (
                            <Badge key={k} variant="outline">
                              {k}: {(t as Doc).type}
                            </Badge>
                          ))}
                        </div>
                        {sample.length ? (
                          <DataTable rows={sample} />
                        ) : (
                          <Button
                            variant="outline"
                            disabled={!!busy}
                            onClick={() =>
                              task('Cargando datos…', async () =>
                                setSample(await previewTable(source)),
                              )
                            }
                          >
                            Consultar primeras 8 filas
                          </Button>
                        )}
                      </Panel>
                    </TabsContent>
                    <TabsContent value="dsl">
                      <Panel
                        title="Definición de inputs · JSON"
                        aside={
                          <Button
                            variant="ghost"
                            onClick={() => download('inputs.json', inputs)}
                          >
                            <Download />
                            Descargar
                          </Button>
                        }
                      >
                        <Textarea
                          aria-label="DSL de inputs"
                          className="json-editor"
                          value={raw}
                          onChange={(e) => setRaw(e.target.value)}
                          disabled={!canInput}
                        />
                        <Button
                          className="mt-3"
                          disabled={!canInput || !!busy}
                          onClick={() =>
                            task('Validando estructura…', async () => {
                              const d = JSON.parse(raw);
                              const r = await compile(
                                payload('inputs', { inputs: d }),
                              );
                              changeInput(d);
                              setSql(r.sql);
                              setMessage('Estructura aplicada al borrador.');
                            })
                          }
                        >
                          Validar y aplicar JSON
                        </Button>
                      </Panel>
                      {sql && (
                        <Panel title="Plan de consolidación generado">
                          <Code value={sql} />
                        </Panel>
                      )}
                    </TabsContent>
                  </Tabs>
                </>
              )}
              {active === 2 && (
                <>
                  <div className="two-columns">
                    <Panel title="Catálogo de variables">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Variable / expresión</TableHead>
                            <TableHead>Tipo</TableHead>
                            <TableHead>Editar</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {evaluations.variables.map((v: Doc) => (
                            <TableRow key={v.id}>
                              <TableCell>
                                <strong>{v.id}</strong>
                                <code className="expression-label">
                                  {expressionText(v.expression)}
                                </code>
                              </TableCell>
                              <TableCell>
                                {v.data_type.type}
                                {v.data_type.nullable ? '?' : ''}
                              </TableCell>
                              <TableCell>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => {
                                    setVariableId(v.id);
                                    setVariableExpr(copy(v.expression));
                                  }}
                                >
                                  Abrir
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Panel>
                    <Panel title="Inputs disponibles">
                      <Fields schema={inputs.output_schema} />
                    </Panel>
                  </div>
                  <Panel
                    title="Definir variable virtual"
                    aside={
                      <Badge variant="outline">
                        {canVariable ? 'Edición' : 'Solo lectura'}
                      </Badge>
                    }
                  >
                    <label className="form-label">
                      Identificador
                      <Input
                        value={variableId}
                        onChange={(e) => setVariableId(e.target.value)}
                        disabled={!canVariable}
                      />
                    </label>
                    <fieldset disabled={!canVariable || !!busy}>
                      <ExpressionEditor
                        value={variableExpr}
                        onChange={setVariableExpr}
                        references={references}
                      />
                    </fieldset>
                    <Button
                      className="mt-4"
                      disabled={!canVariable || !!busy}
                      onClick={() =>
                        task('Compilando variable…', async () => {
                          if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(variableId))
                            throw new Error(
                              'Usa un identificador sin espacios',
                            );
                          const entry = await compile(
                            payload('variable', {
                              id: variableId,
                              expression: variableExpr,
                            }),
                          );
                          const d = copy(evaluations);
                          const old = d.variables.find(
                            (v: Doc) => v.id === variableId,
                          );
                          entry.version = old ? old.version + 1 : 1;
                          d.variables = [
                            ...d.variables.filter(
                              (v: Doc) => v.id !== variableId,
                            ),
                            entry,
                          ];
                          await compile(
                            payload('validate', { evaluations: d }),
                          );
                          changePackage(d);
                          setMessage(
                            'Variable compilada. Guarda el paquete para conservarla.',
                          );
                        })
                      }
                    >
                      Compilar y añadir variable
                    </Button>
                  </Panel>
                  <Panel title="Traza de dependencias">
                    {evaluations.variables.map((v: Doc) => (
                      <div className="catalog-row" key={v.id}>
                        <GitBranch size={18} />
                        <strong>{v.id}</strong>
                        <ArrowRight size={16} />
                        <code className="text-sm break-all">
                          {expressionText(v.expression)}
                        </code>
                      </div>
                    ))}
                  </Panel>
                </>
              )}
              {active === 3 && (
                <>
                  <div className="version-strip">
                    <FileJson size={17} />
                    <strong>{evaluations.definition_id}</strong>
                    <Badge variant="outline">
                      v{evaluations.definition_version}
                    </Badge>
                    <span>
                      Contrato de inputs v
                      {evaluations.input_contract.definition_version}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={!canRule}
                      onClick={() => newVersion('evaluations')}
                    >
                      Nueva versión
                    </Button>
                  </div>
                  <Tabs defaultValue="rules">
                    <TabsList variant="line">
                      <TabsTrigger value="rules">Reglas</TabsTrigger>
                      <TabsTrigger value="products">Productos</TabsTrigger>
                      <TabsTrigger value="dsl">Paquete DSL</TabsTrigger>
                    </TabsList>
                    <TabsContent value="rules">
                      <Panel title="Catálogo de reglas">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Regla</TableHead>
                              <TableHead>Lógica</TableHead>
                              <TableHead>Salida</TableHead>
                              <TableHead>Acciones</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {evaluations.rules.map((r: Doc) => (
                              <TableRow key={r.id}>
                                <TableCell className="font-medium">
                                  {r.id}
                                </TableCell>
                                <TableCell>
                                  <code>{expressionText(r.expression)}</code>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="secondary">Booleano</Badge>
                                </TableCell>
                                <TableCell>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setRuleId(r.id);
                                      setRuleExpr(copy(r.expression));
                                      setLanguage('visual');
                                    }}
                                  >
                                    Editar
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </Panel>
                      <Panel title="Construir regla">
                        <label className="form-label">
                          Identificador
                          <Input
                            disabled={!canRule}
                            value={ruleId}
                            onChange={(e) => setRuleId(e.target.value)}
                          />
                        </label>
                        <Tabs
                          value={language}
                          onValueChange={(v) => setLanguage(String(v))}
                        >
                          <TabsList>
                            <TabsTrigger value="visual">Visual</TabsTrigger>
                            <TabsTrigger value="python">Python</TabsTrigger>
                            <TabsTrigger value="sql">SQL</TabsTrigger>
                          </TabsList>
                          <TabsContent value="visual">
                            <fieldset disabled={!canRule || !!busy}>
                              <ExpressionEditor
                                value={ruleExpr}
                                onChange={setRuleExpr}
                                references={references}
                              />
                            </fieldset>
                          </TabsContent>
                          <TabsContent value="python">
                            <p className="my-3 text-sm text-muted-foreground">
                              Declara una función que retorne bool. Sin imports
                              ni ejecución de código arbitrario.
                            </p>
                            <Textarea
                              aria-label="Código Python de la regla"
                              className="json-editor min-h-48"
                              value={python}
                              disabled={!canRule}
                              onChange={(e) => setPython(e.target.value)}
                            />
                          </TabsContent>
                          <TabsContent value="sql">
                            <p className="my-3 text-sm text-muted-foreground">
                              Expresión booleana sobre inputs, variables y
                              constants. Sin FROM.
                            </p>
                            <Textarea
                              aria-label="Expresión SQL de la regla"
                              className="json-editor min-h-32"
                              value={sqlRule}
                              disabled={!canRule}
                              onChange={(e) => setSqlRule(e.target.value)}
                            />
                          </TabsContent>
                        </Tabs>
                        <Button
                          className="mt-4"
                          disabled={!canRule || !!busy}
                          onClick={() =>
                            task('Compilando regla…', async () => {
                              if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(ruleId))
                                throw new Error(
                                  'Usa un identificador sin espacios',
                                );
                              const r = await compile(
                                payload('rule', {
                                  language,
                                  source:
                                    language === 'visual'
                                      ? ruleExpr
                                      : language === 'python'
                                        ? python
                                        : sqlRule,
                                }),
                              );
                              const d = copy(evaluations);
                              const old = d.rules.find(
                                (v: Doc) => v.id === ruleId,
                              );
                              d.rules = [
                                ...d.rules.filter((v: Doc) => v.id !== ruleId),
                                {
                                  id: ruleId,
                                  version: old ? old.version + 1 : 1,
                                  data_type: {
                                    type: 'boolean',
                                    nullable: false,
                                  },
                                  expression: r.expression,
                                },
                              ];
                              await compile(
                                payload('validate', { evaluations: d }),
                              );
                              changePackage(d);
                              setCompiled(r);
                              setMessage(
                                'Regla compilada a DSL. Guarda el paquete para conservarla.',
                              );
                            })
                          }
                        >
                          Compilar y añadir regla
                        </Button>
                        {compiled?.expression && (
                          <div className="mt-4">
                            <Code value={compiled} />
                          </div>
                        )}
                      </Panel>
                    </TabsContent>
                    <TabsContent value="products">
                      <Panel title="Criterios por producto">
                        {evaluations.products.map((p: Doc) => (
                          <div className="catalog-row" key={p.id}>
                            <GitBranch size={18} />
                            <div className="flex-1">
                              <strong>{p.id}</strong>
                              <code className="expression-label">
                                {expressionText(p.expression)}
                              </code>
                            </div>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setProductId(p.id);
                                setProductExpr(copy(p.expression));
                              }}
                            >
                              Editar
                            </Button>
                          </div>
                        ))}
                      </Panel>
                      <Panel title="Componer producto">
                        <label className="form-label">
                          Identificador
                          <Input
                            value={productId}
                            onChange={(e) => setProductId(e.target.value)}
                            disabled={!canRule}
                          />
                        </label>
                        <p className="mb-3 text-sm text-muted-foreground">
                          Combina resultados de reglas con AND, OR y NOT.
                        </p>
                        <fieldset disabled={!canRule || !!busy}>
                          <ExpressionEditor
                            product
                            value={productExpr}
                            onChange={setProductExpr}
                            references={ruleReferences}
                          />
                        </fieldset>
                        <Button
                          className="mt-4"
                          disabled={!canRule || !!busy}
                          onClick={() =>
                            task('Validando producto…', async () => {
                              if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(productId))
                                throw new Error('Identificador inválido');
                              const d = copy(evaluations),
                                old = d.products.find(
                                  (p: Doc) => p.id === productId,
                                );
                              d.products = [
                                ...d.products.filter(
                                  (p: Doc) => p.id !== productId,
                                ),
                                {
                                  id: productId,
                                  version: old ? old.version + 1 : 1,
                                  expression: productExpr,
                                },
                              ];
                              await compile(
                                payload('validate', { evaluations: d }),
                              );
                              changePackage(d);
                              setMessage('Producto añadido al borrador.');
                            })
                          }
                        >
                          Añadir al paquete
                        </Button>
                      </Panel>
                    </TabsContent>
                    <TabsContent value="dsl">
                      <Panel
                        title="Variables y evaluaciones · JSON"
                        aside={
                          <Button
                            variant="ghost"
                            onClick={() =>
                              download('evaluations.json', evaluations)
                            }
                          >
                            <Download />
                            Descargar
                          </Button>
                        }
                      >
                        <p className="mb-3 text-sm text-muted-foreground">
                          Incluye constantes, variables, reglas y productos. El
                          consolidado se referencia mediante su contrato.
                        </p>
                        <Textarea
                          aria-label="DSL del paquete de evaluación"
                          className="json-editor"
                          value={packageRaw}
                          onChange={(e) => setPackageRaw(e.target.value)}
                          disabled={!canRule && !canVariable}
                        />
                        <div className="mt-3 flex gap-3">
                          <Button
                            disabled={!!busy || (!canRule && !canVariable)}
                            onClick={() =>
                              task('Validando paquete…', async () => {
                                const d = JSON.parse(packageRaw);
                                await compile(
                                  payload('validate', { evaluations: d }),
                                );
                                changePackage(d);
                                setMessage('Paquete aplicado al borrador.');
                              })
                            }
                          >
                            Validar y aplicar
                          </Button>
                          <Button
                            variant="outline"
                            disabled={!canRule || !!busy}
                            onClick={() =>
                              task('Vinculando contrato…', async () => {
                                const r = await compile(payload('rebind'));
                                changePackage(r.evaluations);
                                setMessage(
                                  'Contrato actualizado y paquete validado.',
                                );
                              })
                            }
                          >
                            Vincular inputs del editor
                          </Button>
                        </div>
                      </Panel>
                    </TabsContent>
                  </Tabs>
                </>
              )}
              {active === 4 && (
                <>
                  <Panel
                    title="Propuestas y versiones"
                    aside={
                      <Badge variant="secondary">
                        {
                          workspace.history.filter(
                            (h) => h.status === 'proposed',
                          ).length
                        }{' '}
                        pendientes
                      </Badge>
                    }
                  >
                    {workspace.history.length === 0 ? (
                      <p className="text-muted-foreground">
                        No hay propuestas. Valida y propone primero la
                        definición de inputs.
                      </p>
                    ) : (
                      workspace.history.map((h) => (
                        <details key={h.id} className="proposal">
                          <summary>
                            <div>
                              <strong>
                                {h.kind === 'inputs'
                                  ? 'Consolidado de inputs'
                                  : 'Paquete de evaluación'}
                              </strong>
                              <p className="text-sm text-muted-foreground">
                                {h.document.definition_id} · v
                                {h.document.definition_version} · {h.author}
                              </p>
                            </div>
                            <Badge
                              variant={
                                h.status === 'published'
                                  ? 'secondary'
                                  : 'outline'
                              }
                            >
                              {
                                {
                                  proposed: 'Propuesto',
                                  published: 'Publicado',
                                  rejected: 'Rechazado',
                                }[h.status]
                              }
                            </Badge>
                          </summary>
                          <div className="mt-4">
                            <Code value={h.document} />
                            {h.reason && (
                              <p className="my-4">Motivo: {h.reason}</p>
                            )}
                            {h.status === 'proposed' && (
                              <div className="mt-4">
                                <label className="form-label">
                                  Motivo de rechazo
                                  <Textarea
                                    disabled={persona !== 'po'}
                                    value={reason}
                                    onChange={(e) => setReason(e.target.value)}
                                    placeholder="Indica qué debe corregirse"
                                  />
                                </label>
                                <div className="flex gap-3">
                                  <Button
                                    disabled={persona !== 'po' || !!busy}
                                    onClick={() =>
                                      task(
                                        'Publicando versión aprobada…',
                                        async () => {
                                          await compile(
                                            payload(
                                              h.kind === 'inputs'
                                                ? 'inputs'
                                                : 'validate',
                                              {
                                                [h.kind]: h.document,
                                                inputs:
                                                  h.kind === 'inputs'
                                                    ? h.document
                                                    : workspace.currentInput,
                                              },
                                            ),
                                          );
                                          accept(
                                            await request({
                                              action: 'approve',
                                              id: h.id,
                                            }),
                                          );
                                          setMessage(
                                            'Aprobación registrada y DSL publicado.',
                                          );
                                        },
                                      )
                                    }
                                  >
                                    <ShieldCheck />
                                    Aprobar y publicar
                                  </Button>
                                  <Button
                                    variant="outline"
                                    disabled={
                                      persona !== 'po' ||
                                      !reason.trim() ||
                                      !!busy
                                    }
                                    onClick={() =>
                                      task('Registrando rechazo…', async () => {
                                        accept(
                                          await request({
                                            action: 'reject',
                                            id: h.id,
                                            reason,
                                          }),
                                        );
                                        setReason('');
                                        setMessage(
                                          'Rechazo registrado. El borrador puede corregirse y volver a proponerse.',
                                        );
                                      })
                                    }
                                  >
                                    Rechazar
                                  </Button>
                                </div>
                              </div>
                            )}
                            <Button
                              className="mt-4"
                              variant="ghost"
                              onClick={() =>
                                download(
                                  `${h.kind}-v${h.document.definition_version}.json`,
                                  h.document,
                                )
                              }
                            >
                              <Download />
                              Descargar versión
                            </Button>
                          </div>
                        </details>
                      ))
                    )}
                  </Panel>
                  <Panel title="Auditoría">
                    <DataTable
                      rows={workspace.audit.map((a) => ({
                        fecha: a.at,
                        perfil: a.actor,
                        acción: a.action,
                      }))}
                    />
                  </Panel>
                </>
              )}
              {active === 5 && (
                <>
                  <Panel
                    title="Experimento en navegador"
                    aside={
                      <Badge variant="outline">
                        30.000 clientes sintéticos
                      </Badge>
                    }
                  >
                    <p className="mb-5 text-muted-foreground">
                      Consolida las fuentes y evalúa el borrador actual. Los
                      resultados son temporales y no publican ni ejecutan
                      procesos productivos.
                    </p>
                    <div className="flex flex-wrap items-end gap-3">
                      <label className="form-label m-0 w-60">
                        Clientes a evaluar
                        <Pick
                          label="Tamaño de muestra"
                          value={limit}
                          onChange={setLimit}
                          options={[
                            { value: '100', label: '100 · muestra rápida' },
                            {
                              value: '1000',
                              label: '1.000 · muestra ampliada',
                            },
                            { value: '30000', label: '30.000 · demo completa' },
                          ]}
                        />
                      </label>
                      <Button
                        disabled={!!busy}
                        onClick={() =>
                          task(
                            'Consolidando y evaluando datos sintéticos…',
                            async () => {
                              setResult(
                                await experiment(
                                  inputs,
                                  evaluations,
                                  defaults!.inputs.sources,
                                  Number(limit),
                                ),
                              );
                              setMessage(
                                'Experimento completado. Resultados y trazas disponibles.',
                              );
                            },
                          )
                        }
                      >
                        <FlaskConical />
                        Ejecutar experimento
                      </Button>
                    </div>
                  </Panel>
                  {result && (
                    <>
                      <div className="stats-grid">
                        {result.summary.map((p: Doc) => (
                          <div className="stat" key={p.product}>
                            <span>{p.product}</span>
                            <strong>
                              {((100 * p.accepted) / result.clients).toFixed(1)}
                              <small>%</small>
                            </strong>
                            <small>
                              {p.accepted} aceptados · {p.denied} denegados ·{' '}
                              {p.errors} errores
                            </small>
                          </div>
                        ))}
                      </div>
                      <Panel
                        title="Resultados y trazabilidad"
                        aside={
                          <Button
                            variant="ghost"
                            onClick={() =>
                              download(`experimento-${result.id}.json`, result)
                            }
                          >
                            <Download />
                            Exportar
                          </Button>
                        }
                      >
                        <p className="mb-4 text-sm text-muted-foreground">
                          Ejecución {result.id} · {result.clients} clientes. Los
                          errores se registran como resultado nulo.
                        </p>
                        <Input
                          className="mb-4 max-w-sm"
                          aria-label="Filtrar resultados por cliente"
                          placeholder="Buscar cliente…"
                          value={filter}
                          onChange={(e) => setFilter(e.target.value)}
                        />
                        <Tabs
                          value={resultTab}
                          onValueChange={(v) => setResultTab(String(v))}
                        >
                          <TabsList>
                            <TabsTrigger value="products">
                              Evaluaciones
                            </TabsTrigger>
                            <TabsTrigger value="variables">
                              Variables materializadas
                            </TabsTrigger>
                            <TabsTrigger value="rules">
                              Reglas y detalles
                            </TabsTrigger>
                          </TabsList>
                          {['products', 'variables', 'rules'].map((k) => (
                            <TabsContent value={k} key={k}>
                              <DataTable
                                rows={result[k]
                                  .filter(
                                    (r: Doc) =>
                                      !filter || r.client.includes(filter),
                                  )
                                  .slice(0, 100)}
                              />
                            </TabsContent>
                          ))}
                        </Tabs>
                        <p className="mt-3 text-sm text-muted-foreground">
                          Se muestran hasta 100 filas. La exportación incluye el
                          experimento completo.
                        </p>
                      </Panel>
                    </>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
function DataTable({ rows }: { rows: Doc[] }) {
  if (!rows.length)
    return <p className="text-sm text-muted-foreground">Sin registros.</p>;
  const columns = Object.keys(rows[0]);
  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map((k) => (
            <TableHead key={k}>{k}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r, i) => (
          <TableRow key={i}>
            {columns.map((k) => (
              <TableCell key={k}>
                {k === 'details' ? (
                  <details>
                    <summary className="cursor-pointer text-primary">
                      Ver detalle
                    </summary>
                    <Code
                      value={typeof r[k] === 'string' ? JSON.parse(r[k]) : r[k]}
                    />
                  </details>
                ) : r[k] === null ? (
                  <Badge variant="outline">Nulo / error</Badge>
                ) : typeof r[k] === 'boolean' ? (
                  <Badge variant="secondary">
                    {r[k] ? 'Aceptado' : 'Denegado'}
                  </Badge>
                ) : (
                  String(r[k])
                )}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
