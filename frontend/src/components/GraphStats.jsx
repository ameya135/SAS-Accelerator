import React from 'react'
import { motion } from 'framer-motion'
import { 
  BarChart3, 
  GitBranch, 
  Layers, 
  AlertTriangle,
  Database,
  Settings,
  Zap,
  FileCode,
  CheckCircle
} from 'lucide-react'

/**
 * Stat card component
 */
const StatCard = ({ icon: Icon, label, value, color, subtext }) => {
  const colorClasses = {
    cyan: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400',
    purple: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
    amber: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    emerald: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    pink: 'bg-pink-500/10 border-pink-500/30 text-pink-400',
    red: 'bg-red-500/10 border-red-500/30 text-red-400'
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`p-4 rounded-xl border ${colorClasses[color]}`}
    >
      <div className="flex items-center space-x-3">
        <Icon className="w-5 h-5" />
        <div>
          <div className="text-2xl font-bold text-white">{value}</div>
          <div className="text-sm text-slate-400">{label}</div>
          {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
        </div>
      </div>
    </motion.div>
  )
}

/**
 * Node type breakdown component
 */
const NodeTypeBreakdown = ({ nodeTypes }) => {
  if (!nodeTypes || Object.keys(nodeTypes).length === 0) {
    return null
  }

  const typeConfig = {
    dataset: { icon: Database, color: 'cyan', label: 'Datasets', textClass: 'text-cyan-400', barClass: 'bg-cyan-500' },
    data_step: { icon: FileCode, color: 'amber', label: 'DATA Steps', textClass: 'text-amber-400', barClass: 'bg-amber-500' },
    proc: { icon: Zap, color: 'purple', label: 'PROCs', textClass: 'text-purple-400', barClass: 'bg-purple-500' },
    macro: { icon: Settings, color: 'emerald', label: 'Macros', textClass: 'text-emerald-400', barClass: 'bg-emerald-500' },
    macro_variable: { icon: FileCode, color: 'pink', label: 'Macro Variables', textClass: 'text-pink-400', barClass: 'bg-pink-500' },
    library: { icon: Database, color: 'cyan', label: 'Libraries', textClass: 'text-cyan-400', barClass: 'bg-cyan-500' },
    file_ref: { icon: FileCode, color: 'amber', label: 'File Refs', textClass: 'text-amber-400', barClass: 'bg-amber-500' }
  }

  const total = Object.values(nodeTypes).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-slate-400">Node Types</h4>
      <div className="space-y-2">
        {Object.entries(nodeTypes).map(([type, count]) => {
          const config = typeConfig[type] || { icon: GitBranch, color: 'cyan', label: type, textClass: 'text-cyan-400', barClass: 'bg-cyan-500' }
          const percent = total > 0 ? Math.round((count / total) * 100) : 0
          const Icon = config.icon

          return (
            <div key={type} className="flex items-center space-x-3">
              <Icon className={`w-4 h-4 ${config.textClass}`} />
              <div className="flex-1">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-slate-300 capitalize">{config.label}</span>
                  <span className="text-slate-400">{count}</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percent}%` }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className={`h-full ${config.barClass} rounded-full`}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/**
 * Edge type breakdown component
 */
const EdgeTypeBreakdown = ({ edgeTypes }) => {
  if (!edgeTypes || Object.keys(edgeTypes).length === 0) {
    return null
  }

  const typeConfig = {
    reads_from: { color: '#64748b', label: 'Reads From' },
    writes_to: { color: '#3b82f6', label: 'Writes To' },
    calls: { color: '#8b5cf6', label: 'Calls' },
    uses_variable: { color: '#f59e0b', label: 'Uses Variable' },
    defines_variable: { color: '#10b981', label: 'Defines Variable' },
    proc_input: { color: '#06b6d4', label: 'PROC Input' },
    proc_output: { color: '#ec4899', label: 'PROC Output' }
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-slate-400">Edge Types</h4>
      <div className="flex flex-wrap gap-2">
        {Object.entries(edgeTypes).map(([type, count]) => {
          const config = typeConfig[type] || { color: '#64748b', label: type }

          return (
            <div
              key={type}
              className="flex items-center space-x-2 px-2 py-1 rounded-lg bg-slate-800/50 border border-slate-700/50"
            >
              <div
                className="w-3 h-0.5 rounded"
                style={{ backgroundColor: config.color }}
              />
              <span className="text-xs text-slate-300">{config.label}</span>
              <span className="text-xs text-slate-500">({count})</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/**
 * GraphStats Component
 */
const GraphStats = ({ stats }) => {
  if (!stats) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-white">Graph Statistics</h3>
          <p className="text-sm text-slate-400">Dependency analysis results</p>
        </div>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard
          icon={GitBranch}
          label="Total Nodes"
          value={stats.total_nodes || 0}
          color="cyan"
        />
        <StatCard
          icon={GitBranch}
          label="Total Edges"
          value={stats.total_edges || 0}
          color="purple"
        />
        <StatCard
          icon={Layers}
          label="Layers"
          value={stats.total_layers || 0}
          color="amber"
          subtext="Execution depth"
        />
        <StatCard
          icon={stats.has_cycles ? AlertTriangle : CheckCircle}
          label="Cycles"
          value={stats.has_cycles ? 'Yes' : 'No'}
          color={stats.has_cycles ? 'red' : 'emerald'}
          subtext={stats.has_cycles ? 'Warning' : 'Clean'}
        />
      </div>

      {/* Breakdowns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <NodeTypeBreakdown nodeTypes={stats.node_types} />
        <EdgeTypeBreakdown edgeTypes={stats.edge_types} />
      </div>

      {/* Cycle Warning */}
      {stats.has_cycles && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-6 p-4 bg-red-500/10 rounded-xl border border-red-500/30"
        >
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-300">Circular Dependencies Detected</h4>
              <p className="text-sm text-red-200/70 mt-1">
                The code contains circular dependencies which may affect execution order.
                Review the graph to identify and resolve cycles.
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default GraphStats

