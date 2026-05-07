import React from 'react'
import { motion } from 'framer-motion'
import { 
  GitBranch, 
  Layers, 
  FileSearch, 
  Cpu, 
  FileCode,
  CheckCircle,
  Loader2
} from 'lucide-react'

const phases = [
  {
    id: 1,
    name: 'Graph Building',
    description: 'Parsing SAS code and extracting dependencies',
    icon: GitBranch,
    color: 'cyan'
  },
  {
    id: 2,
    name: 'Chunk Optimization',
    description: 'Grouping nodes into optimal chunks',
    icon: Layers,
    color: 'purple'
  },
  {
    id: 3,
    name: 'Context Enrichment',
    description: 'Adding schemas and RAG examples',
    icon: FileSearch,
    color: 'amber'
  },
  {
    id: 4,
    name: 'LLM Conversion',
    description: 'Converting chunks to PySpark',
    icon: Cpu,
    color: 'pink'
  },
  {
    id: 5,
    name: 'Code Reconciliation',
    description: 'Integrating into final script',
    icon: FileCode,
    color: 'emerald'
  }
]

const colorClasses = {
  cyan: {
    bg: 'bg-cyan-500',
    bgLight: 'bg-cyan-500/20',
    border: 'border-cyan-500/30',
    text: 'text-cyan-400',
    shadow: 'shadow-cyan-500/30',
    ring: 'ring-cyan-500/30'
  },
  purple: {
    bg: 'bg-purple-500',
    bgLight: 'bg-purple-500/20',
    border: 'border-purple-500/30',
    text: 'text-purple-400',
    shadow: 'shadow-purple-500/30',
    ring: 'ring-purple-500/30'
  },
  amber: {
    bg: 'bg-amber-500',
    bgLight: 'bg-amber-500/20',
    border: 'border-amber-500/30',
    text: 'text-amber-400',
    shadow: 'shadow-amber-500/30',
    ring: 'ring-amber-500/30'
  },
  pink: {
    bg: 'bg-pink-500',
    bgLight: 'bg-pink-500/20',
    border: 'border-pink-500/30',
    text: 'text-pink-400',
    shadow: 'shadow-pink-500/30',
    ring: 'ring-pink-500/30'
  },
  emerald: {
    bg: 'bg-emerald-500',
    bgLight: 'bg-emerald-500/20',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    shadow: 'shadow-emerald-500/30',
    ring: 'ring-emerald-500/30'
  }
}

/**
 * Phase card component
 */
const PhaseCard = ({ phase, isActive, isCompleted, index }) => {
  const colors = colorClasses[phase.color]
  const Icon = phase.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`
        relative p-4 rounded-xl border transition-all duration-300
        ${isCompleted ? `${colors.bgLight} ${colors.border}` : ''}
        ${isActive ? `${colors.bgLight} ${colors.border} ring-2 ${colors.ring}` : ''}
        ${!isActive && !isCompleted ? 'bg-slate-800/30 border-slate-700/30' : ''}
      `}
    >
      {/* Connection line */}
      {index < phases.length - 1 && (
        <div className="hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-slate-700">
          {isCompleted && (
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              className={`h-full ${colors.bg} origin-left`}
            />
          )}
        </div>
      )}

      <div className="flex items-center space-x-3">
        {/* Icon */}
        <div className={`
          w-12 h-12 rounded-xl flex items-center justify-center
          ${isCompleted ? `${colors.bg} shadow-lg ${colors.shadow}` : ''}
          ${isActive ? `${colors.bg} shadow-lg ${colors.shadow} animate-pulse` : ''}
          ${!isActive && !isCompleted ? 'bg-slate-700/50' : ''}
        `}>
          {isCompleted ? (
            <CheckCircle className="w-6 h-6 text-white" />
          ) : isActive ? (
            <Loader2 className="w-6 h-6 text-white animate-spin" />
          ) : (
            <Icon className={`w-6 h-6 ${isActive || isCompleted ? 'text-white' : 'text-slate-500'}`} />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <span className={`
              font-semibold
              ${isCompleted || isActive ? 'text-white' : 'text-slate-400'}
            `}>
              {phase.name}
            </span>
            {isActive && (
              <span className={`px-2 py-0.5 rounded text-xs ${colors.bg} text-white`}>
                Running
              </span>
            )}
            {isCompleted && (
              <span className="px-2 py-0.5 rounded text-xs bg-emerald-500 text-white">
                Done
              </span>
            )}
          </div>
          <p className={`text-sm ${isCompleted || isActive ? 'text-slate-300' : 'text-slate-500'}`}>
            {phase.description}
          </p>
        </div>
      </div>
    </motion.div>
  )
}

/**
 * MigrationPipeline Component
 */
const MigrationPipeline = ({ currentPhase, completedPhases = [] }) => {
  const completedCount = completedPhases.length
  const progressPercent = (completedCount / phases.length) * 100

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Migration Pipeline</h3>
            <p className="text-sm text-slate-400">
              Phase {currentPhase || completedCount} of {phases.length}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-white">{Math.round(progressPercent)}%</div>
          <div className="text-xs text-slate-400">Complete</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="h-full bg-gradient-to-r from-cyan-500 via-purple-500 to-emerald-500"
          />
        </div>
      </div>

      {/* Phases Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {phases.map((phase, index) => (
          <PhaseCard
            key={phase.id}
            phase={phase}
            index={index}
            isActive={currentPhase === phase.id}
            isCompleted={completedPhases.includes(phase.id)}
          />
        ))}
      </div>

      {/* Current Phase Detail */}
      {currentPhase && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 bg-slate-800/50 rounded-xl border border-slate-700/50"
        >
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-4 h-4 bg-cyan-500 rounded-full animate-ping absolute inset-0" />
              <div className="w-4 h-4 bg-cyan-500 rounded-full relative" />
            </div>
            <span className="text-slate-300">
              Currently {phases[currentPhase - 1]?.description.toLowerCase()}...
            </span>
          </div>
        </motion.div>
      )}

      {/* Completion Message */}
      {completedCount === phases.length && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-6 p-4 bg-emerald-500/20 rounded-xl border border-emerald-500/30"
        >
          <div className="flex items-center justify-center space-x-2">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <span className="font-medium text-emerald-300">
              Migration completed successfully!
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

export default MigrationPipeline

