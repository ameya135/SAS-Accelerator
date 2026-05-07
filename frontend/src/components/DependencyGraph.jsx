import React, { useCallback, useMemo, useEffect } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType
} from 'reactflow'
import 'reactflow/dist/style.css'
import { motion } from 'framer-motion'
import { GitBranch, ZoomIn, Maximize2 } from 'lucide-react'

// Node colors by type
const NODE_COLORS = {
  dataset: { bg: '#1e3a5f', border: '#60a5fa', text: '#93c5fd' },
  data_step: { bg: '#422006', border: '#fbbf24', text: '#fde68a' },
  proc: { bg: '#3b0764', border: '#a78bfa', text: '#c4b5fd' },
  macro: { bg: '#052e16', border: '#34d399', text: '#6ee7b7' },
  macro_variable: { bg: '#431407', border: '#f97316', text: '#fdba74' },
  library: { bg: '#500724', border: '#ec4899', text: '#f9a8d4' },
  file_ref: { bg: '#2e1065', border: '#8b5cf6', text: '#c4b5fd' }
}

// Edge colors by type
const EDGE_COLORS = {
  reads_from: '#64748b',
  writes_to: '#3b82f6',
  calls: '#8b5cf6',
  uses_variable: '#f59e0b',
  defines_variable: '#10b981',
  proc_input: '#06b6d4',
  proc_output: '#ec4899'
}

// Custom node icons
const NODE_ICONS = {
  dataset: '📊',
  data_step: '🔄',
  proc: '⚙️',
  macro: '🔧',
  macro_variable: '📝',
  library: '📁',
  file_ref: '📄'
}

/**
 * Custom node component
 */
const CustomNode = ({ data }) => {
  const nodeType = data.nodeType || 'dataset'
  const colors = NODE_COLORS[nodeType] || NODE_COLORS.dataset

  return (
    <div
      className="px-4 py-3 shadow-lg rounded-xl border-2 min-w-[160px]"
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
      }}
    >
      <div className="flex items-center space-x-2">
        <span className="text-lg">{NODE_ICONS[nodeType] || '📦'}</span>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate" style={{ color: colors.text }}>
            {data.label}
          </div>
          <div className="text-xs opacity-70" style={{ color: colors.text }}>
            {nodeType.replace('_', ' ')}
          </div>
        </div>
      </div>
      {data.metadata?.line_start && (
        <div className="mt-2 text-xs opacity-50" style={{ color: colors.text }}>
          Lines: {data.metadata.line_start}-{data.metadata.line_end || data.metadata.line_start}
        </div>
      )}
    </div>
  )
}

const nodeTypes = {
  custom: CustomNode
}

const EMPTY_ARRAY = []

/**
 * Legend component
 */
const GraphLegend = () => {
  return (
    <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-sm p-4 rounded-xl border border-slate-700/50 max-w-xs z-10">
      <h4 className="font-semibold text-sm mb-3 text-white">Node Types</h4>
      <div className="grid grid-cols-2 gap-2 text-xs">
        {Object.entries(NODE_COLORS).map(([type, colors]) => (
          <div key={type} className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded border-2"
              style={{ backgroundColor: colors.bg, borderColor: colors.border }}
            />
            <span className="text-slate-300 capitalize">{type.replace('_', ' ')}</span>
          </div>
        ))}
      </div>

      <h4 className="font-semibold text-sm mt-4 mb-2 text-white">Edge Types</h4>
      <div className="grid grid-cols-1 gap-1 text-xs">
        {Object.entries(EDGE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center space-x-2">
            <div className="w-6 h-0.5" style={{ backgroundColor: color }} />
            <span className="text-slate-300 capitalize">{type.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * DependencyGraph Component
 */
const DependencyGraph = ({ graphData, className = '' }) => {
  const graphNodes = Array.isArray(graphData?.nodes) ? graphData.nodes : EMPTY_ARRAY
  const graphEdges = Array.isArray(graphData?.edges) ? graphData.edges : EMPTY_ARRAY

  // Convert graph data to React Flow format
  const { initialNodes, initialEdges } = useMemo(() => {
    if (graphNodes.length === 0) {
      return { initialNodes: [], initialEdges: [] }
    }

    // Process nodes
    const nodes = graphNodes.map(node => ({
      ...node,
      type: 'custom',
      data: {
        label: node.data?.label || node.label || node.id,
        nodeType: node.data?.nodeType || node.type || 'dataset',
        metadata: node.data?.metadata || {}
      }
    }))

    // Process edges with styling
    const edges = graphEdges.map((edge, index) => {
      const edgeType = edge.data?.edgeType || edge.type || 'reads_from'
      const color = EDGE_COLORS[edgeType] || '#64748b'

      return {
        ...edge,
        id: edge.id || `e${index}`,
        type: 'smoothstep',
        animated: edgeType === 'calls' || edgeType === 'uses_variable',
        style: {
          stroke: color,
          strokeWidth: 2
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: color,
          width: 20,
          height: 20
        },
        labelStyle: { fill: '#94a3b8', fontSize: 10 },
        labelBgStyle: { fill: '#1e293b', fillOpacity: 0.8 }
      }
    })

    return { initialNodes: nodes, initialEdges: edges }
  }, [graphEdges, graphNodes])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Update nodes and edges when graphData changes
  useEffect(() => {
    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [initialNodes, initialEdges, setNodes, setEdges])

  // Mini map node color function
  const nodeColor = useCallback((node) => {
    const nodeType = node.data?.nodeType || 'dataset'
    return NODE_COLORS[nodeType]?.border || '#64748b'
  }, [])

  if (graphNodes.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={`card ${className}`}
      >
        <div className="flex items-center justify-center h-96">
          <div className="text-center text-slate-400">
            <GitBranch className="mx-auto h-12 w-12 text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No graph data</h3>
            <p className="text-sm text-slate-500">
              Upload a SAS file to visualize its dependency graph
            </p>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`card p-0 overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800/50 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center">
            <GitBranch className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Dependency Graph</h3>
            <p className="text-sm text-slate-400">
              {graphNodes.length} nodes, {graphEdges.length} edges
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-slate-400">
          <ZoomIn className="w-4 h-4" />
          <span className="text-xs">Scroll to zoom</span>
          <Maximize2 className="w-4 h-4 ml-2" />
          <span className="text-xs">Drag to pan</span>
        </div>
      </div>

      {/* Graph */}
      <div style={{ height: '500px' }} className="relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-right"
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#334155" gap={20} size={1} />
          <Controls 
            className="bg-slate-800 border-slate-700 rounded-lg"
            showInteractive={false}
          />
          <MiniMap
            nodeColor={nodeColor}
            nodeStrokeWidth={3}
            zoomable
            pannable
            className="bg-slate-900 rounded-lg border border-slate-700"
          />
        </ReactFlow>
        
        <GraphLegend />
      </div>
    </motion.div>
  )
}

export default DependencyGraph
