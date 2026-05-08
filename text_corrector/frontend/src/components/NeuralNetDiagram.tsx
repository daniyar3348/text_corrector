import { useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Node,
  type Edge,
  Position,
  BackgroundVariant,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

// ── Custom node styles ─────────────────────────────────────────────────────

const nodeBase: React.CSSProperties = {
  padding: '10px 16px',
  borderRadius: 12,
  fontSize: 12,
  fontWeight: 600,
  textAlign: 'center',
  minWidth: 160,
  border: '2px solid',
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  lineHeight: 1.4,
}

function InputNode({ data }: { data: { label: string; sub?: string } }) {
  return (
    <div style={{ ...nodeBase, background: '#eff6ff', borderColor: '#3b82f6', color: '#1d4ed8' }}>
      <div>{data.label}</div>
      {data.sub && <div style={{ fontSize: 10, fontWeight: 400, color: '#60a5fa', marginTop: 2 }}>{data.sub}</div>}
    </div>
  )
}

function BertNode({ data }: { data: { label: string; sub?: string } }) {
  return (
    <div style={{ ...nodeBase, background: '#f5f3ff', borderColor: '#8b5cf6', color: '#5b21b6' }}>
      <div>{data.label}</div>
      {data.sub && <div style={{ fontSize: 10, fontWeight: 400, color: '#a78bfa', marginTop: 2 }}>{data.sub}</div>}
    </div>
  )
}

function LstmNode({ data }: { data: { label: string; sub?: string } }) {
  return (
    <div style={{ ...nodeBase, background: '#fff7ed', borderColor: '#f97316', color: '#c2410c' }}>
      <div>{data.label}</div>
      {data.sub && <div style={{ fontSize: 10, fontWeight: 400, color: '#fb923c', marginTop: 2 }}>{data.sub}</div>}
    </div>
  )
}

function FusionNode({ data }: { data: { label: string; sub?: string } }) {
  return (
    <div style={{ ...nodeBase, background: '#f0fdf4', borderColor: '#22c55e', color: '#15803d' }}>
      <div>{data.label}</div>
      {data.sub && <div style={{ fontSize: 10, fontWeight: 400, color: '#4ade80', marginTop: 2 }}>{data.sub}</div>}
    </div>
  )
}

function OutputNode({ data }: { data: { label: string; sub?: string } }) {
  return (
    <div style={{ ...nodeBase, background: '#ecfdf5', borderColor: '#10b981', color: '#065f46', minWidth: 180 }}>
      <div style={{ fontSize: 14 }}>✅ {data.label}</div>
      {data.sub && <div style={{ fontSize: 10, fontWeight: 400, color: '#34d399', marginTop: 2 }}>{data.sub}</div>}
    </div>
  )
}

function GroupNode({ data }: { data: { label: string } }) {
  return (
    <div style={{
      padding: '6px 14px',
      borderRadius: 10,
      background: 'rgba(139,92,246,0.07)',
      border: '1.5px dashed #8b5cf6',
      color: '#7c3aed',
      fontSize: 11,
      fontWeight: 700,
      textAlign: 'center',
    }}>
      {data.label}
    </div>
  )
}

const nodeTypes = {
  input: InputNode,
  bert: BertNode,
  lstm: LstmNode,
  fusion: FusionNode,
  output: OutputNode,
  group: GroupNode,
}

// ── Layout constants ────────────────────────────────────────────────────────

const CX = 420   // BERT column center x
const RX = 760   // LSTM column center x
const MX = 590   // Merge column center x

// ── Nodes ───────────────────────────────────────────────────────────────────

const initialNodes: Node[] = [
  // ── Input ──
  {
    id: 'input',
    type: 'input',
    position: { x: MX - 80, y: 0 },
    data: { label: '📥 Входной текст', sub: 'Русский / Казахский' },
    sourcePosition: Position.Bottom,
  },

  // ── Tokenizer ──
  {
    id: 'tokenizer',
    type: 'bert',
    position: { x: MX - 80, y: 100 },
    data: { label: '🔤 WordPiece Tokenizer', sub: 'BERT-совместимый' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },

  // ── BERT path ──────────────────────────────────────────────────────────
  {
    id: 'bert-embed',
    type: 'bert',
    position: { x: CX - 80, y: 230 },
    data: { label: '🧩 Эмбеддинги', sub: 'Token + Position + Segment' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },

  // BERT encoder group label
  {
    id: 'bert-group',
    type: 'group',
    position: { x: CX - 110, y: 340 },
    data: { label: 'BERT Encoder × 12 блоков' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
    style: { width: 220, height: 220 },
  },

  {
    id: 'bert-attn',
    type: 'bert',
    position: { x: CX - 75, y: 370 },
    data: { label: '🎯 Multi-Head Self-Attention', sub: '12 голов, dim=768' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
    parentId: 'bert-group',
    extent: 'parent',
  },
  {
    id: 'bert-norm1',
    type: 'bert',
    position: { x: CX - 75, y: 460 },
    data: { label: 'Add & LayerNorm' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
    parentId: 'bert-group',
    extent: 'parent',
  },
  {
    id: 'bert-ffn',
    type: 'bert',
    position: { x: CX - 75, y: 550 },
    data: { label: '⚡ Feed-Forward Network', sub: 'dim 768 → 3072 → 768' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
    parentId: 'bert-group',
    extent: 'parent',
  },
  {
    id: 'bert-norm2',
    type: 'bert',
    position: { x: CX - 75, y: 640 },
    data: { label: 'Add & LayerNorm' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
    parentId: 'bert-group',
    extent: 'parent',
  },

  {
    id: 'bert-cls',
    type: 'bert',
    position: { x: CX - 80, y: 590 },
    data: { label: '🏷 [CLS] Представление', sub: 'dim = 768' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },

  // ── LSTM path ──────────────────────────────────────────────────────────
  {
    id: 'bilstm',
    type: 'lstm',
    position: { x: RX - 80, y: 230 },
    data: { label: '🔁 BiLSTM Layer', sub: 'hidden=256, 2 слоя' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'lstm-fwd',
    type: 'lstm',
    position: { x: RX - 140, y: 360 },
    data: { label: '→ Forward LSTM', sub: 'h=256' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'lstm-bwd',
    type: 'lstm',
    position: { x: RX + 20, y: 360 },
    data: { label: '← Backward LSTM', sub: 'h=256' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'lstm-attn',
    type: 'lstm',
    position: { x: RX - 80, y: 490 },
    data: { label: '🔦 Attention Pooling', sub: 'Bahdanau-style' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },

  // ── Fusion ─────────────────────────────────────────────────────────────
  {
    id: 'concat',
    type: 'fusion',
    position: { x: MX - 80, y: 710 },
    data: { label: '🔗 Конкатенация', sub: 'BERT [CLS] + BiLSTM → dim 1280' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'dropout',
    type: 'fusion',
    position: { x: MX - 80, y: 830 },
    data: { label: '🎲 Dropout', sub: 'p = 0.3' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'dense',
    type: 'fusion',
    position: { x: MX - 80, y: 940 },
    data: { label: '🧠 Dense Linear Layer', sub: '1280 → vocab_size' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'softmax',
    type: 'fusion',
    position: { x: MX - 80, y: 1050 },
    data: { label: '📊 Softmax', sub: 'Вероятности по словарю' },
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  },
  {
    id: 'output',
    type: 'output',
    position: { x: MX - 90, y: 1160 },
    data: { label: 'Исправленный токен', sub: 'argmax → декодирование' },
    targetPosition: Position.Top,
  },
]

// ── Edges ───────────────────────────────────────────────────────────────────

const edgeStyle = { stroke: '#94a3b8', strokeWidth: 2 }
const bertEdge = { stroke: '#8b5cf6', strokeWidth: 2 }
const lstmEdge = { stroke: '#f97316', strokeWidth: 2 }
const fusionEdge = { stroke: '#22c55e', strokeWidth: 2 }

const initialEdges: Edge[] = [
  // Input → Tokenizer
  { id: 'e-in-tok', source: 'input', target: 'tokenizer', style: edgeStyle, animated: true },

  // Tokenizer → BERT path
  { id: 'e-tok-embed', source: 'tokenizer', target: 'bert-embed', style: bertEdge, animated: true, label: 'BERT path', labelStyle: { fontSize: 10, fill: '#8b5cf6', fontWeight: 600 } },

  // Tokenizer → LSTM path
  { id: 'e-tok-bilstm', source: 'tokenizer', target: 'bilstm', style: lstmEdge, animated: true, label: 'LSTM path', labelStyle: { fontSize: 10, fill: '#f97316', fontWeight: 600 } },

  // BERT internals
  { id: 'e-embed-attn', source: 'bert-embed', target: 'bert-attn', style: bertEdge },
  { id: 'e-attn-norm1', source: 'bert-attn', target: 'bert-norm1', style: bertEdge },
  { id: 'e-norm1-ffn', source: 'bert-norm1', target: 'bert-ffn', style: bertEdge },
  { id: 'e-ffn-norm2', source: 'bert-ffn', target: 'bert-norm2', style: bertEdge },
  { id: 'e-norm2-cls', source: 'bert-norm2', target: 'bert-cls', style: bertEdge },

  // BiLSTM internals
  { id: 'e-bilstm-fwd', source: 'bilstm', target: 'lstm-fwd', style: lstmEdge },
  { id: 'e-bilstm-bwd', source: 'bilstm', target: 'lstm-bwd', style: lstmEdge },
  { id: 'e-fwd-attn', source: 'lstm-fwd', target: 'lstm-attn', style: lstmEdge },
  { id: 'e-bwd-attn', source: 'lstm-bwd', target: 'lstm-attn', style: lstmEdge },

  // Fusion
  { id: 'e-cls-concat', source: 'bert-cls', target: 'concat', style: fusionEdge, animated: true },
  { id: 'e-attn-concat', source: 'lstm-attn', target: 'concat', style: fusionEdge, animated: true },

  // Output path
  { id: 'e-concat-drop', source: 'concat', target: 'dropout', style: fusionEdge },
  { id: 'e-drop-dense', source: 'dropout', target: 'dense', style: fusionEdge },
  { id: 'e-dense-soft', source: 'dense', target: 'softmax', style: fusionEdge },
  { id: 'e-soft-out', source: 'softmax', target: 'output', style: fusionEdge, animated: true },
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
    <div style={{ width: '100%', height: 680, borderRadius: 16, overflow: 'hidden', border: '1px solid #e2e8f0' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.3}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e2e8f0" />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(n) => {
            if (n.type === 'bert') return '#8b5cf6'
            if (n.type === 'lstm') return '#f97316'
            if (n.type === 'fusion') return '#22c55e'
            if (n.type === 'output') return '#10b981'
            return '#3b82f6'
          }}
          style={{ borderRadius: 8 }}
        />
      </ReactFlow>
    </div>
  )
}
