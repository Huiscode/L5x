import { useMemo, useState } from 'react'

type Severity = 'error' | 'warning' | 'info'
type RelationType =
  | 'read_usage'
  | 'write_usage'
  | 'same_rung_cooccurrence'
  | 'cross_program_reference'
  | 'alias_base_mapping'
  | 'aoi_io_binding'

type ValidationIssue = {
  code: string
  severity: Severity
  message: string
  path: string | null
  details: Record<string, unknown> | null
}

type ParseSummary = {
  software_revision: string | null
  major_revision: number | null
  project_name: string | null
  controller_name: string | null
  file_size_bytes: number
}

type TreeNode = {
  id: string
  name: string
  type: string
  path: string
  attributes: Record<string, unknown>
  children: TreeNode[]
}

type EditableField = {
  target_path: string
  field_type: string
  locale: string | null
  original_value: string
  updated_value: string
  validation_state: 'valid' | 'warning' | 'error'
}

type DiffItem = {
  target_path: string
  field_type: string
  old_value: string
  new_value: string
}

type DiffPreview = {
  session_id: string
  total_changes: number
  items: DiffItem[]
}

type ExportPrecheck = {
  session_id: string
  can_export: boolean
  issues: ValidationIssue[]
  total_changes: number
}

type RelationshipEdge = {
  source_tag: string
  target_tag: string
  relation_type: RelationType
  program: string | null
  routine: string | null
  rung_ref: string | null
  evidence_excerpt: string | null
}

type RelationshipResponse = {
  session_id: string
  edges: RelationshipEdge[]
}

type ParseResponse = {
  session_id: string
  summary: ParseSummary
  nodes: TreeNode[]
  issues: ValidationIssue[]
  editable_fields: EditableField[]
  can_export: boolean
}

const RELATION_LABELS: Record<RelationType, string> = {
  read_usage: 'Read usage',
  write_usage: 'Write usage',
  same_rung_cooccurrence: 'Same rung co-occurrence',
  cross_program_reference: 'Cross-program reference',
  alias_base_mapping: 'Alias ↔ base',
  aoi_io_binding: 'AOI I/O binding',
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ParseResponse | null>(null)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<TreeNode | null>(null)

  const [selectedFieldPath, setSelectedFieldPath] = useState<string>('')
  const [draftValue, setDraftValue] = useState('')
  const [diff, setDiff] = useState<DiffPreview | null>(null)
  const [precheck, setPrecheck] = useState<ExportPrecheck | null>(null)

  const [edges, setEdges] = useState<RelationshipEdge[]>([])
  const [relationFilter, setRelationFilter] = useState<RelationType | 'all'>('all')
  const [selectedEdge, setSelectedEdge] = useState<RelationshipEdge | null>(null)

  const filteredNodes = useMemo(() => {
    if (!result) return []
    const q = search.trim().toLowerCase()
    if (!q) return result.nodes

    const hasMatch = (node: TreeNode): boolean => {
      const selfMatch =
        node.name.toLowerCase().includes(q) ||
        node.type.toLowerCase().includes(q) ||
        node.path.toLowerCase().includes(q)
      if (selfMatch) return true
      return node.children.some(hasMatch)
    }

    return result.nodes.filter(hasMatch)
  }, [result, search])

  const selectedField = useMemo(() => {
    if (!result || !selectedFieldPath) return null
    return result.editable_fields.find((f) => f.target_path === selectedFieldPath) ?? null
  }, [result, selectedFieldPath])

  const filteredEdges = useMemo(() => {
    if (relationFilter === 'all') return edges
    return edges.filter((edge) => edge.relation_type === relationFilter)
  }, [edges, relationFilter])

  const relationCounts = useMemo(() => {
    const counts: Record<RelationType, number> = {
      read_usage: 0,
      write_usage: 0,
      same_rung_cooccurrence: 0,
      cross_program_reference: 0,
      alias_base_mapping: 0,
      aoi_io_binding: 0,
    }
    for (const edge of edges) counts[edge.relation_type] += 1
    return counts
  }, [edges])

  async function uploadAndParse() {
    if (!file) {
      setError('Choose an .L5X file first.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://127.0.0.1:8000/api/l5x/parse', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const detail = (await response.json()) as { detail?: string }
        throw new Error(detail.detail ?? `Parse failed (${response.status})`)
      }

      const data = (await response.json()) as ParseResponse
      setResult(data)
      setSelected(data.nodes[0] ?? null)
      setSelectedFieldPath(data.editable_fields[0]?.target_path ?? '')
      setDraftValue(data.editable_fields[0]?.updated_value ?? '')
      setDiff(null)
      setPrecheck(null)
      setSelectedEdge(null)

      const relRes = await fetch(`http://127.0.0.1:8000/api/l5x/${data.session_id}/relationships`)
      if (relRes.ok) {
        const relData = (await relRes.json()) as RelationshipResponse
        setEdges(relData.edges)
      } else {
        setEdges([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  async function saveField() {
    if (!result || !selectedFieldPath) return

    const response = await fetch(`http://127.0.0.1:8000/api/l5x/${result.session_id}/fields`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_path: selectedFieldPath, updated_value: draftValue }),
    })

    if (!response.ok) {
      const detail = (await response.json()) as { detail?: string }
      setError(detail.detail ?? 'Failed to save field')
      return
    }

    const updated = (await response.json()) as {
      session_id: string
      field: EditableField
      diff: DiffPreview
    }

    setResult((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        editable_fields: prev.editable_fields.map((field) =>
          field.target_path === updated.field.target_path ? updated.field : field,
        ),
      }
    })

    setDiff(updated.diff)

    const relRes = await fetch(`http://127.0.0.1:8000/api/l5x/${result.session_id}/relationships`)
    if (relRes.ok) {
      const relData = (await relRes.json()) as RelationshipResponse
      setEdges(relData.edges)
    }
  }

  async function loadDiff() {
    if (!result) return
    const response = await fetch(`http://127.0.0.1:8000/api/l5x/${result.session_id}/diff`)
    if (!response.ok) return
    const data = (await response.json()) as DiffPreview
    setDiff(data)
  }

  async function runPrecheck() {
    if (!result) return
    const response = await fetch(`http://127.0.0.1:8000/api/l5x/${result.session_id}/precheck`)
    if (!response.ok) return
    const data = (await response.json()) as ExportPrecheck
    setPrecheck(data)
  }

  async function exportFile() {
    if (!result) return
    const response = await fetch(`http://127.0.0.1:8000/api/l5x/${result.session_id}/export`)
    if (!response.ok) {
      const detail = (await response.json()) as { detail?: string }
      setError(detail.detail ?? 'Export blocked')
      return
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${result.summary.project_name ?? 'project'}-edited.L5X`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <main className="shell">
      <section className="card">
        <h1>app-L5x</h1>
        <p className="subtitle">M5 • Parse, edit, diff, export, and inspect relationships</p>

        <section className="toolbar">
          <input type="file" accept=".l5x" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button className="primary" onClick={uploadAndParse} disabled={loading} type="button">
            {loading ? 'Working…' : 'Upload & Parse'}
          </button>
          {file ? <span className="file-pill">{file.name}</span> : null}
        </section>

        {error ? <p className="error-banner">{error}</p> : null}

        {result ? (
          <>
            <section className="summary-grid">
              <article>
                <h3>Project</h3>
                <p>{result.summary.project_name ?? 'Unknown'}</p>
              </article>
              <article>
                <h3>Controller</h3>
                <p>{result.summary.controller_name ?? 'Unknown'}</p>
              </article>
              <article>
                <h3>Revision</h3>
                <p>{result.summary.software_revision ?? 'Unknown'}</p>
              </article>
              <article>
                <h3>File Size</h3>
                <p>{formatBytes(result.summary.file_size_bytes)}</p>
              </article>
              <article>
                <h3>Editable Fields</h3>
                <p>{result.editable_fields.length}</p>
              </article>
              <article>
                <h3>Relationship Edges</h3>
                <p>{edges.length}</p>
              </article>
            </section>

            <section className="workspace" style={{ gridTemplateColumns: '1fr 1fr' }}>
              <article className="panel">
                <div className="panel-header">
                  <h2>Tree Explorer</h2>
                  <input
                    className="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search name/type/path"
                  />
                </div>
                <div className="tree" role="tree">
                  {filteredNodes.map((node) => (
                    <TreeView key={node.id} node={node} depth={0} onSelect={setSelected} selectedId={selected?.id ?? null} />
                  ))}
                </div>
              </article>

              <article className="panel">
                <h2>Node Details</h2>
                {selected ? (
                  <>
                    <p className="panel-meta">{selected.path}</p>
                    <pre>{JSON.stringify(selected.attributes, null, 2)}</pre>
                  </>
                ) : (
                  <p className="hint">Select a node.</p>
                )}
              </article>
            </section>

            <section className="workspace" style={{ marginTop: 14, gridTemplateColumns: '1fr 1fr' }}>
              <article className="panel">
                <h2>Edit + Diff + Export</h2>
                <label>
                  Field
                  <select
                    value={selectedFieldPath}
                    onChange={(event) => {
                      const path = event.target.value
                      setSelectedFieldPath(path)
                      const field = result.editable_fields.find((f) => f.target_path === path)
                      setDraftValue(field?.updated_value ?? '')
                    }}
                    style={{ width: '100%', marginTop: 6, marginBottom: 10 }}
                  >
                    {result.editable_fields.map((field) => (
                      <option key={field.target_path} value={field.target_path}>
                        [{field.field_type}] {field.target_path}
                      </option>
                    ))}
                  </select>
                </label>

                <textarea
                  value={draftValue}
                  onChange={(event) => setDraftValue(event.target.value)}
                  style={{ width: '100%', minHeight: 120, marginBottom: 10 }}
                />

                <div className="toolbar">
                  <button className="primary" type="button" onClick={saveField}>
                    Save Field
                  </button>
                  <button className="primary" type="button" onClick={loadDiff}>
                    Refresh Diff
                  </button>
                  <button className="primary" type="button" onClick={runPrecheck}>
                    Run Export Pre-check
                  </button>
                  <button className="primary" type="button" onClick={exportFile}>
                    Export .L5X
                  </button>
                </div>

                {selectedField ? (
                  <p className="panel-meta">
                    Field status: <strong>{selectedField.validation_state}</strong>
                  </p>
                ) : null}

                <h3>Diff Preview</h3>
                <div className="issues">
                  {diff?.items.length ? (
                    diff.items.map((item) => (
                      <article className="issue info" key={item.target_path}>
                        <p>
                          <strong>{item.field_type}</strong>
                        </p>
                        <p className="issue-path">{item.target_path}</p>
                        <p>
                          <strong>Old:</strong> {item.old_value.slice(0, 120)}
                        </p>
                        <p>
                          <strong>New:</strong> {item.new_value.slice(0, 120)}
                        </p>
                      </article>
                    ))
                  ) : (
                    <p>No pending edits.</p>
                  )}
                </div>

                {precheck ? (
                  <>
                    <h3>Pre-check</h3>
                    <p className={precheck.can_export ? 'good' : 'bad'}>
                      {precheck.can_export ? 'Export Allowed' : 'Export Blocked'}
                    </p>
                    <p>Total changes: {precheck.total_changes}</p>
                  </>
                ) : null}
              </article>

              <article className="panel">
                <h2>Relationship Graph (Edge List)</h2>
                <div className="toolbar">
                  <label>
                    Filter
                    <select
                      value={relationFilter}
                      onChange={(event) => setRelationFilter(event.target.value as RelationType | 'all')}
                      style={{ marginLeft: 8 }}
                    >
                      <option value="all">All</option>
                      {(Object.keys(RELATION_LABELS) as RelationType[]).map((key) => (
                        <option key={key} value={key}>
                          {RELATION_LABELS[key]} ({relationCounts[key]})
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="tree" style={{ maxHeight: 260 }}>
                  {filteredEdges.map((edge, index) => (
                    <button
                      type="button"
                      className={`tree-row ${selectedEdge === edge ? 'selected' : ''}`}
                      key={`${edge.source_tag}-${edge.target_tag}-${index}`}
                      onClick={() => setSelectedEdge(edge)}
                    >
                      <span className="node-name">
                        {edge.source_tag} → {edge.target_tag}
                      </span>
                      <span className="node-type">{edge.relation_type}</span>
                    </button>
                  ))}
                </div>

                <h3 style={{ marginTop: 12 }}>Context Link</h3>
                {selectedEdge ? (
                  <dl className="details-grid">
                    <dt>Relation</dt>
                    <dd>{RELATION_LABELS[selectedEdge.relation_type]}</dd>
                    <dt>Program</dt>
                    <dd>{selectedEdge.program ?? 'N/A'}</dd>
                    <dt>Routine</dt>
                    <dd>{selectedEdge.routine ?? 'N/A'}</dd>
                    <dt>Rung</dt>
                    <dd>{selectedEdge.rung_ref ?? 'N/A'}</dd>
                    <dt>Evidence</dt>
                    <dd>{selectedEdge.evidence_excerpt ?? 'No rung excerpt'}</dd>
                  </dl>
                ) : (
                  <p>Select an edge to inspect program/routine/rung context.</p>
                )}
              </article>
            </section>
          </>
        ) : (
          <p className="hint">Upload a `.L5X` file to begin.</p>
        )}
      </section>
    </main>
  )
}

function TreeView({
  node,
  depth,
  selectedId,
  onSelect,
}: {
  node: TreeNode
  depth: number
  selectedId: string | null
  onSelect: (node: TreeNode) => void
}) {
  const [open, setOpen] = useState(depth < 1)
  const hasChildren = node.children.length > 0

  return (
    <>
      <button
        type="button"
        className={`tree-row ${selectedId === node.id ? 'selected' : ''}`}
        style={{ paddingLeft: `${10 + depth * 14}px` }}
        onClick={() => onSelect(node)}
      >
        <span
          className={`twisty ${hasChildren ? '' : 'empty'}`}
          onClick={(event) => {
            event.stopPropagation()
            if (hasChildren) setOpen((value) => !value)
          }}
        >
          {hasChildren ? (open ? '▾' : '▸') : '·'}
        </span>
        <span className="node-name">{node.name}</span>
        <span className="node-type">{node.type}</span>
      </button>

      {open && hasChildren
        ? node.children.map((child) => (
            <TreeView key={child.id} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} />
          ))
        : null}
    </>
  )
}
