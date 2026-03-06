import { useMemo, useState } from 'react'

type Severity = 'error' | 'warning' | 'info'

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

type ParseResponse = {
  summary: ParseSummary
  nodes: TreeNode[]
  issues: ValidationIssue[]
  can_export: boolean
}

const MAX_RENDER_NODES = 1200

function flattenCount(nodes: TreeNode[]): number {
  let count = 0
  const stack = [...nodes]
  while (stack.length) {
    const current = stack.pop()
    if (!current) continue
    count += 1
    if (current.children.length) {
      for (const child of current.children) stack.push(child)
    }
  }
  return count
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function TreeItem({
  node,
  depth,
  expanded,
  onToggle,
  selectedId,
  onSelect,
  search,
}: {
  node: TreeNode
  depth: number
  expanded: Set<string>
  onToggle: (id: string) => void
  selectedId: string | null
  onSelect: (node: TreeNode) => void
  search: string
}) {
  const hasChildren = node.children.length > 0
  const isExpanded = expanded.has(node.id)
  const matches =
    search.length === 0 ||
    node.name.toLowerCase().includes(search) ||
    node.type.toLowerCase().includes(search) ||
    node.path.toLowerCase().includes(search)

  if (!matches && search.length > 0 && !node.children.some((child) => child.path.toLowerCase().includes(search))) {
    return null
  }

  return (
    <>
      <button
        className={`tree-row ${selectedId === node.id ? 'selected' : ''}`}
        style={{ paddingLeft: `${depth * 16 + 10}px` }}
        onClick={() => onSelect(node)}
        type="button"
      >
        <span
          className={`twisty ${hasChildren ? '' : 'empty'}`}
          onClick={(event) => {
            event.stopPropagation()
            if (hasChildren) onToggle(node.id)
          }}
        >
          {hasChildren ? (isExpanded ? '▾' : '▸') : '·'}
        </span>
        <span className="node-name">{node.name}</span>
        <span className="node-type">{node.type}</span>
      </button>

      {hasChildren && isExpanded
        ? node.children.map((child) => (
            <TreeItem
              key={child.id}
              node={child}
              depth={depth + 1}
              expanded={expanded}
              onToggle={onToggle}
              selectedId={selectedId}
              onSelect={onSelect}
              search={search}
            />
          ))
        : null}
    </>
  )
}

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ParseResponse | null>(null)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [selected, setSelected] = useState<TreeNode | null>(null)

  const normalizedSearch = search.trim().toLowerCase()

  const totalNodeCount = useMemo(() => (result ? flattenCount(result.nodes) : 0), [result])
  const renderLimited = totalNodeCount > MAX_RENDER_NODES

  const visibleRootNodes = useMemo(() => {
    if (!result) return []
    if (!normalizedSearch) return result.nodes

    const includesMatch = (node: TreeNode): boolean => {
      if (
        node.name.toLowerCase().includes(normalizedSearch) ||
        node.type.toLowerCase().includes(normalizedSearch) ||
        node.path.toLowerCase().includes(normalizedSearch)
      ) {
        return true
      }
      return node.children.some(includesMatch)
    }

    return result.nodes.filter(includesMatch)
  }, [result, normalizedSearch])

  const severityCounts = useMemo(() => {
    const counts: Record<Severity, number> = { error: 0, warning: 0, info: 0 }
    if (!result) return counts
    for (const issue of result.issues) {
      counts[issue.severity] += 1
    }
    return counts
  }, [result])

  const onToggle = (id: string) => {
    setExpanded((previous) => {
      const next = new Set(previous)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const uploadAndParse = async () => {
    if (!file) {
      setError('Choose an .L5X file first.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setSelected(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://127.0.0.1:8000/api/l5x/parse', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const detail = (await response.json()) as { detail?: string }
        throw new Error(detail.detail ?? `Parse failed with status ${response.status}`)
      }

      const data = (await response.json()) as ParseResponse
      setResult(data)

      const initialExpanded = new Set<string>()
      for (const node of data.nodes) {
        initialExpanded.add(node.id)
      }
      setExpanded(initialExpanded)
      setSelected(data.nodes[0] ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown parse error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="shell">
      <section className="card">
        <header className="header">
          <h1>app-L5x</h1>
          <p className="subtitle">M3 • Upload, validate, and explore L5X structure locally</p>
        </header>

        <section className="toolbar">
          <input
            type="file"
            accept=".l5x"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <button className="primary" onClick={uploadAndParse} disabled={loading} type="button">
            {loading ? 'Parsing…' : 'Upload & Parse'}
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
                <h3>Export Gate</h3>
                <p className={result.can_export ? 'good' : 'bad'}>{result.can_export ? 'Allowed' : 'Blocked'}</p>
              </article>
              <article>
                <h3>Issues</h3>
                <p>
                  {severityCounts.error} errors • {severityCounts.warning} warnings • {severityCounts.info} info
                </p>
              </article>
            </section>

            <section className="workspace">
              <article className="panel">
                <div className="panel-header">
                  <h2>Tree Explorer</h2>
                  <input
                    className="search"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search name, type, or path"
                  />
                </div>

                <p className="panel-meta">Nodes: {totalNodeCount.toLocaleString()}</p>
                {renderLimited ? (
                  <p className="warning-note">
                    Large tree detected. Showing search-filtered roots for performance. Narrow with search.
                  </p>
                ) : null}

                <div className="tree" role="tree">
                  {visibleRootNodes.map((node) => (
                    <TreeItem
                      key={node.id}
                      node={node}
                      depth={0}
                      expanded={expanded}
                      onToggle={onToggle}
                      selectedId={selected?.id ?? null}
                      onSelect={setSelected}
                      search={normalizedSearch}
                    />
                  ))}
                </div>
              </article>

              <article className="panel">
                <h2>Node Details</h2>
                {selected ? (
                  <>
                    <dl className="details-grid">
                      <dt>Name</dt>
                      <dd>{selected.name}</dd>
                      <dt>Type</dt>
                      <dd>{selected.type}</dd>
                      <dt>Path</dt>
                      <dd>{selected.path}</dd>
                      <dt>Children</dt>
                      <dd>{selected.children.length}</dd>
                    </dl>

                    <h3>Attributes</h3>
                    <pre>{JSON.stringify(selected.attributes, null, 2)}</pre>
                  </>
                ) : (
                  <p>Select a node in the explorer.</p>
                )}

                <h3>Validation Feedback</h3>
                <div className="issues">
                  {result.issues.length === 0 ? (
                    <p>No issues found.</p>
                  ) : (
                    result.issues.map((issue, index) => (
                      <article key={`${issue.code}-${index}`} className={`issue ${issue.severity}`}>
                        <p>
                          <strong>{issue.severity.toUpperCase()}</strong> • {issue.code}
                        </p>
                        <p>{issue.message}</p>
                        {issue.path ? <p className="issue-path">{issue.path}</p> : null}
                      </article>
                    ))
                  )}
                </div>
              </article>
            </section>
          </>
        ) : (
          <p className="hint">Upload a `.L5X` file to start parsing and browsing project structure.</p>
        )}
      </section>
    </main>
  )
}
