import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Layers, 
  ChevronDown, 
  ChevronUp, 
  Hash, 
  Code, 
  GitBranch,
  Database,
  Settings,
  Zap
} from 'lucide-react'
import CodePreview from './CodePreview'

/**
 * Single chunk card component
 */
const ChunkCard = ({ chunk, index, isExpanded, onToggle }) => {
  const getChunkIcon = () => {
    if (chunk.has_macros) return <Settings className="w-4 h-4 text-green-400" />
    if (chunk.has_procs) return <Zap className="w-4 h-4 text-purple-400" />
    if (chunk.has_data_steps) return <Database className="w-4 h-4 text-amber-400" />
    return <Code className="w-4 h-4 text-cyan-400" />
  }

  const getChunkType = () => {
    if (chunk.has_macros) return 'Macro'
    if (chunk.has_procs) return 'PROC'
    if (chunk.has_data_steps) return 'DATA Step'
    return 'Mixed'
  }

  const getChunkColor = () => {
    if (chunk.has_macros) return 'emerald'
    if (chunk.has_procs) return 'purple'
    if (chunk.has_data_steps) return 'amber'
    return 'cyan'
  }

  const chunkColors = {
    emerald: {
      icon: 'bg-emerald-500/20 border-emerald-500/30',
      badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
    },
    purple: {
      icon: 'bg-purple-500/20 border-purple-500/30',
      badge: 'bg-purple-500/20 text-purple-300 border-purple-500/30'
    },
    amber: {
      icon: 'bg-amber-500/20 border-amber-500/30',
      badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    },
    cyan: {
      icon: 'bg-cyan-500/20 border-cyan-500/30',
      badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
    }
  }

  const color = getChunkColor()

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden`}
    >
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <div className={`w-8 h-8 rounded-lg border flex items-center justify-center ${chunkColors[color].icon}`}>
            {getChunkIcon()}
          </div>
          <div className="text-left">
            <div className="flex items-center space-x-2">
              <span className="font-medium text-white">Chunk {index + 1}</span>
              <span className={`px-2 py-0.5 rounded text-xs border ${chunkColors[color].badge}`}>
                {getChunkType()}
              </span>
            </div>
            <div className="flex items-center space-x-3 text-xs text-slate-400">
              <span className="flex items-center space-x-1">
                <Hash className="w-3 h-3" />
                <span>{chunk.estimated_tokens} tokens</span>
              </span>
              <span className="flex items-center space-x-1">
                <GitBranch className="w-3 h-3" />
                <span>Layer {chunk.layer}</span>
              </span>
              <span className="flex items-center space-x-1">
                <Layers className="w-3 h-3" />
                <span>{chunk.node_count} nodes</span>
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {chunk.dependencies?.length > 0 && (
            <span className="px-2 py-1 rounded text-xs bg-slate-700/50 text-slate-400">
              {chunk.dependencies.length} deps
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-slate-700/50"
          >
            <div className="p-4 space-y-4">
              {/* Dependencies */}
              {chunk.dependencies?.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-slate-300 mb-2">Dependencies</h5>
                  <div className="flex flex-wrap gap-2">
                    {chunk.dependencies.map((dep, i) => (
                      <span 
                        key={i}
                        className="px-2 py-1 rounded text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                      >
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Source Preview */}
              {chunk.source_preview && (
                <div>
                  <h5 className="text-sm font-medium text-slate-300 mb-2">Source Preview</h5>
                  <CodePreview code={chunk.source_preview} language="sas" maxHeight="200px" />
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

/**
 * ChunkViewer Component
 */
const ChunkViewer = ({ chunks }) => {
  const [expandedChunks, setExpandedChunks] = useState(new Set())
  const [filter, setFilter] = useState('all')
  const chunkList = Array.isArray(chunks) ? chunks : []

  const toggleChunk = (index) => {
    const newExpanded = new Set(expandedChunks)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedChunks(newExpanded)
  }

  const expandAll = () => {
    setExpandedChunks(new Set(chunkList.map((_, i) => i)))
  }

  const collapseAll = () => {
    setExpandedChunks(new Set())
  }

  const filteredChunks = chunkList.filter(chunk => {
    if (filter === 'all') return true
    if (filter === 'macros') return chunk.has_macros
    if (filter === 'procs') return chunk.has_procs
    if (filter === 'data') return chunk.has_data_steps
    return true
  })

  const totalTokens = chunkList.reduce((sum, c) => sum + (c.estimated_tokens || 0), 0)
  const avgTokens = chunkList.length > 0 ? Math.round(totalTokens / chunkList.length) : 0

  if (chunkList.length === 0) {
    return null
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Optimized Chunks</h3>
            <p className="text-sm text-slate-400">
              {chunkList.length} chunks, {totalTokens.toLocaleString()} total tokens
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={expandAll}
            className="px-3 py-1 text-xs text-slate-400 hover:text-white transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1 text-xs text-slate-400 hover:text-white transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 text-center">
          <div className="text-xl font-bold text-white">{chunkList.length}</div>
          <div className="text-xs text-slate-400">Chunks</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 text-center">
          <div className="text-xl font-bold text-cyan-400">{totalTokens.toLocaleString()}</div>
          <div className="text-xs text-slate-400">Total Tokens</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 text-center">
          <div className="text-xl font-bold text-purple-400">{avgTokens}</div>
          <div className="text-xs text-slate-400">Avg Tokens</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 text-center">
          <div className="text-xl font-bold text-emerald-400">
            {Math.max(...chunkList.map(c => c.layer || 0)) + 1}
          </div>
          <div className="text-xs text-slate-400">Layers</div>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center space-x-2 mb-4">
        <span className="text-sm text-slate-400">Filter:</span>
        {['all', 'macros', 'data', 'procs'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
              filter === f
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:border-slate-600'
            }`}
          >
            {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Chunks List */}
      <div className="space-y-2">
        {filteredChunks.map((chunk, index) => (
          <ChunkCard
            key={chunk.chunk_id || index}
            chunk={chunk}
            index={index}
            isExpanded={expandedChunks.has(index)}
            onToggle={() => toggleChunk(index)}
          />
        ))}
      </div>
    </motion.div>
  )
}

export default ChunkViewer
