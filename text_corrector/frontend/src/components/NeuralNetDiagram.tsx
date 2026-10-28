import { useCallback, type CSSProperties } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  BackgroundVariant,
  type Connection,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

// ── Detailed architecture diagram for KazRoBERTa ───────────────────────────
// KazRoBERTa (kz-transformers/kaz-roberta-conversational), fine-tuned as a
// token classifier: 6 encoder layers · hidden size 768 · 12 attention heads ·
// ~83M params · KEEP / ERROR label per word (models/kazakh_detector/config.json).

type NodeData = { label: string; sub?: string }

const handleStyle: CSSProperties = { opacity: 0, width: 7, height: 7, border: 'none' }

function Handles() {
  return (
    <>
      <Handle type="target" position={Position.Top} style={handleStyle} />
      <Handle type="source" position={Position.Bottom} style={handleStyle} />
      <Handle type="source" position={Position.Right} id="r" style={handleStyle} />
      <Handle type="target" position={Position.Left} id="l" style={handleStyle} />
    </>
  )
}

const nodeBase: CSSProperties = {
  padding: '9px 14px',
  borderRadius: 12,
  fontSize: 12,
  fontWeight: 600,
  textAlign: 'center',
  minWidth: 168,
  border: '2px solid',
  boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
  lineHeight: 1.35,
}

function makeNode(bg: string, border: string, color: string, subColor: string) {
  return function NodeComp({ data }: { data: NodeData }) {
    return (
      <div style={{ ...nodeBase, background: bg, borderColor: border, color }}>
        <Handles />
        <div>{data.label}</div>
        {data.sub && (
          <div style={{ fontSize: 10, fontWeight: 400, color: subColor, marginTop: 2 }}>
            {data.sub}
          </div>
        )}
      </div>
    )
  }
}

const InputNode = makeNode('#eff6ff', '#3b82f6', '#1d4ed8', '#60a5fa')
const EmbedNode = makeNode('#ecfeff', '#06b6d4', '#0e7490', '#22d3ee')
const EncoderNode = makeNode('#eef2ff', '#6366f1', '#4338ca', '#818cf8')
const AttnNode = makeNode('#f5f3ff', '#8b5cf6', '#5b21b6', '#a78bfa')
const HeadNode = makeNode('#f0fdf4', '#22c55e', '#15803d', '#4ade80')
const OutputNode = makeNode('#ecfdf5', '#10b981', '#065f46', '#34d399')

function GroupNode({ data }: { data: { label?: string; tone?: string; ghost?: boolean } }) {
  const tone = data.tone ?? '#6366f1'
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        borderRadius: 16,
        background: data.ghost ? `${tone}0d` : `${tone}0a`,
        border: `1.5px dashed ${data.ghost ? `${tone}66` : tone}`,
      }}
    >
      {data.label && (
        <span
          style={{
            position: 'relative',
            top: -10,
            left: 14,
            display: 'inline-block',
            background: '#fff',
            padding: '0 8px',
            fontSize: 11,
            fontWeight: 700,
            color: tone,
            whiteSpace: 'nowrap',
          }}
        >
          {data.label}
        </span>
      )}
    </div>
  )
}

const nodeTypes = {
  input: InputNode,
  embed: EmbedNode,
  encoder: EncoderNode,
  attn: AttnNode,
  head: HeadNode,
  output: OutputNode,
  group: GroupNode,
}

// ── Nodes ───────────────────────────────────────────────────────────────────

const groupDefaults = {
  draggable: false,
  selectable: false,
  connectable: false,
  zIndex: 0,
}

const initialNodes: Node[] = [
  // ── Group containers (declared first → painted behind content) ──
  {
    id: 'enc-ghost-2',
    type: 'group',
    position: { x: 318, y: 423 },
    data: { ghost: true, tone: '#6366f1' },
    style: { width: 290, height: 395 },
    ...groupDefaults,
  },
  {
    id: 'enc-ghost-1',
    type: 'group',
    position: { x: 304, y: 409 },
    data: { ghost: true, tone: '#6366f1' },
    style: { width: 290, height: 395 },
    ...groupDefaults,
  },
  {
    id: 'emb-group',
    type: 'group',
    position: { x: 205, y: 186 },
    data: { label: 'Эмбеддинги', tone: '#06b6d4' },
    style: { width: 446, height: 212 },
    ...groupDefaults,
  },
  {
    id: 'enc-group',
    type: 'group',
    position: { x: 290, y: 395 },
    data: { label: 'Encoder Layer  × 6', tone: '#6366f1' },
    style: { width: 290, height: 395 },
    ...groupDefaults,
  },
  {
    id: 'attn-group',
    type: 'group',
    position: { x: 612, y: 352 },
    data: { label: 'Раскрытие Self-Attention', tone: '#8b5cf6' },
    style: { width: 268, height: 320 },
    ...groupDefaults,
  },
  {
    id: 'head-group',
    type: 'group',
    position: { x: 286, y: 884 },
    data: { label: 'Token Classification Head', tone: '#22c55e' },
    style: { width: 304, height: 360 },
    ...groupDefaults,
  },

  // ── Input ──
  {
    id: 'input',
    type: 'input',
    position: { x: 346, y: 0 },
    data: { label: '📥 Входной текст', sub: 'одно казахское предложение за проход' },
    zIndex: 5,
  },
  {
    id: 'tokenizer',
    type: 'embed',
    position: { x: 316, y: 96 },
    data: { label: '🔤 Byte-level BPE токенизатор', sub: 'токены + <s> … </s> · словарь ≈ 52k' },
    zIndex: 5,
  },

  // ── Embeddings ──
  {
    id: 'token-emb',
    type: 'embed',
    position: { x: 232, y: 214 },
    data: { label: '🧩 Token Embeddings', sub: 'id → вектор · d = 768' },
    zIndex: 5,
  },
  {
    id: 'pos-emb',
    type: 'embed',
    position: { x: 442, y: 214 },
    data: { label: '📍 Position Embeddings', sub: 'обучаемые · позиции 0…514' },
    zIndex: 5,
  },
  {
    id: 'emb-sum',
    type: 'embed',
    position: { x: 300, y: 312 },
    data: { label: '⊕ Сумма + LayerNorm + Dropout', sub: 'без segment-эмбеддингов / NSP' },
    zIndex: 5,
  },

  // ── Encoder layer (internals unrolled, repeated × 6) ──
  {
    id: 'mha',
    type: 'encoder',
    position: { x: 322, y: 420 },
    data: { label: '🎯 Multi-Head Self-Attention', sub: '12 голов · d_k = 64' },
    zIndex: 5,
  },
  {
    id: 'addnorm1',
    type: 'encoder',
    position: { x: 332, y: 516 },
    data: { label: '➕ Add & LayerNorm', sub: 'остаточная связь' },
    zIndex: 5,
  },
  {
    id: 'ffn',
    type: 'encoder',
    position: { x: 322, y: 606 },
    data: { label: '⚡ Feed-Forward Network', sub: '768 → 3072 (GELU) → 768' },
    zIndex: 5,
  },
  {
    id: 'addnorm2',
    type: 'encoder',
    position: { x: 332, y: 700 },
    data: { label: '➕ Add & LayerNorm', sub: 'остаточная связь' },
    zIndex: 5,
  },

  // ── Self-attention internals (callout) ──
  {
    id: 'qkv',
    type: 'attn',
    position: { x: 636, y: 382 },
    data: { label: 'Q · K · V проекции', sub: 'Linear 768 → 768  (× 3)' },
    zIndex: 5,
  },
  {
    id: 'sdpa',
    type: 'attn',
    position: { x: 636, y: 476 },
    data: { label: 'Scaled Dot-Product', sub: 'softmax(QKᵀ / √d_k) · V' },
    zIndex: 5,
  },
  {
    id: 'concat-heads',
    type: 'attn',
    position: { x: 636, y: 570 },
    data: { label: 'Concat голов → Linear', sub: '12 × 64 → 768' },
    zIndex: 5,
  },

  // ── Encoder output ──
  {
    id: 'seq-out',
    type: 'encoder',
    position: { x: 318, y: 812 },
    data: { label: '📦 Контекстные эмбеддинги', sub: '[ seq_len × 768 ]' },
    zIndex: 5,
  },

  // ── Token classification head ──
  {
    id: 'cls-dropout',
    type: 'head',
    position: { x: 322, y: 906 },
    data: { label: 'Dropout', sub: 'p = 0.1' },
    zIndex: 5,
  },
  {
    id: 'cls-linear',
    type: 'head',
    position: { x: 322, y: 994 },
    data: { label: 'Linear 768 → 2', sub: 'для каждого токена' },
    zIndex: 5,
  },
  {
    id: 'cls-softmax',
    type: 'head',
    position: { x: 322, y: 1082 },
    data: { label: '📊 Softmax', sub: 'P(KEEP), P(ERROR)' },
    zIndex: 5,
  },
  {
    id: 'cls-word',
    type: 'head',
    position: { x: 322, y: 1170 },
    data: { label: 'Метка слова', sub: 'по первому подтокену · argmax' },
    zIndex: 5,
  },

  // ── Output ──
  {
    id: 'output',
    type: 'output',
    position: { x: 322, y: 1276 },
    data: { label: '🏷️ KEEP / ERROR', sub: 'ERROR → слово исправляет корректор' },
    zIndex: 5,
  },
]

// ── Edges ───────────────────────────────────────────────────────────────────

const E = {
  gray: { stroke: '#94a3b8', strokeWidth: 2 },
  sky: { stroke: '#06b6d4', strokeWidth: 2 },
  indigo: { stroke: '#6366f1', strokeWidth: 2 },
  violet: { stroke: '#8b5cf6', strokeWidth: 2 },
  violetDashed: { stroke: '#8b5cf6', strokeWidth: 2, strokeDasharray: '5 4' },
  green: { stroke: '#22c55e', strokeWidth: 2 },
}

const labelStyle = { fontSize: 10, fontWeight: 700, fill: '#475569' }
const labelBgStyle = { fill: '#ffffff', fillOpacity: 0.92 }

const initialEdges: Edge[] = [
  { id: 'e1', source: 'input', target: 'tokenizer', style: E.gray, animated: true },

  { id: 'e2', source: 'tokenizer', target: 'token-emb', style: E.sky },
  { id: 'e3', source: 'tokenizer', target: 'pos-emb', style: E.sky },
  { id: 'e4', source: 'token-emb', target: 'emb-sum', style: E.sky },
  { id: 'e5', source: 'pos-emb', target: 'emb-sum', style: E.sky },

  { id: 'e6', source: 'emb-sum', target: 'mha', style: E.indigo, animated: true },
  { id: 'e7', source: 'mha', target: 'addnorm1', style: E.indigo },
  { id: 'e8', source: 'addnorm1', target: 'ffn', style: E.indigo },
  { id: 'e9', source: 'ffn', target: 'addnorm2', style: E.indigo },
  {
    id: 'e10',
    source: 'addnorm2',
    target: 'seq-out',
    style: E.indigo,
    animated: true,
    label: '× 6 слоёв',
    labelStyle,
    labelBgStyle,
  },

  // Self-attention callout
  {
    id: 'e11',
    source: 'mha',
    sourceHandle: 'r',
    target: 'qkv',
    targetHandle: 'l',
    style: E.violetDashed,
    label: 'детализация',
    labelStyle,
    labelBgStyle,
  },
  { id: 'e12', source: 'qkv', target: 'sdpa', style: E.violet },
  { id: 'e13', source: 'sdpa', target: 'concat-heads', style: E.violet },

  // Token classification head
  { id: 'e14', source: 'seq-out', target: 'cls-dropout', style: E.green, animated: true },
  { id: 'e15', source: 'cls-dropout', target: 'cls-linear', style: E.green },
  { id: 'e16', source: 'cls-linear', target: 'cls-softmax', style: E.green },
  { id: 'e17', source: 'cls-softmax', target: 'cls-word', style: E.green },
  { id: 'e18', source: 'cls-word', target: 'output', style: E.green, animated: true },
]

// ── Component ────────────────────────────────────────────────────────────────

export default function NeuralNetDiagram() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  return (
    <div
      style={{
        width: '100%',
        height: 800,
        borderRadius: 16,
        overflow: 'hidden',
        border: '1px solid #e2e8f0',
        background: '#fafafa',
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        minZoom={0.2}
        maxZoom={1.6}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e2e8f0" />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => {
            switch (n.type) {
              case 'embed':
                return '#06b6d4'
              case 'encoder':
                return '#6366f1'
              case 'attn':
                return '#8b5cf6'
              case 'head':
                return '#22c55e'
              case 'output':
                return '#10b981'
              case 'group':
                return 'transparent'
              default:
                return '#3b82f6'
            }
          }}
          style={{ borderRadius: 8 }}
          pannable
          zoomable
        />
      </ReactFlow>
    </div>
  )
}
