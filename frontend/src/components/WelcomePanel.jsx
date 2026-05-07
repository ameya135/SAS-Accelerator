import React from 'react'
import { motion } from 'framer-motion'
import { 
  Upload, 
  Database, 
  Code, 
  ArrowRight, 
  Sparkles, 
  GitBranch, 
  Zap,
  Layers,
  Network,
  FileSearch
} from 'lucide-react'

const WelcomePanel = ({ onStart, isLoading }) => {
  const features = [
    {
      icon: GitBranch,
      title: 'Dependency Graph',
      description: 'Visualize code dependencies and execution order with interactive graphs',
      color: 'from-cyan-500 to-blue-500',
      bgColor: 'bg-cyan-500/10',
      borderColor: 'border-cyan-500/30'
    },
    {
      icon: Layers,
      title: 'Smart Chunking',
      description: 'Optimal code chunks based on dependency layers and token limits',
      color: 'from-purple-500 to-pink-500',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/30'
    },
    {
      icon: Network,
      title: 'Schema Tracking',
      description: 'Track data schemas through transformations for type safety',
      color: 'from-amber-500 to-orange-500',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/30'
    },
    {
      icon: FileSearch,
      title: 'RAG Integration',
      description: 'Learn from successful migration patterns with vector search',
      color: 'from-emerald-500 to-green-500',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/30'
    }
  ]

  const phases = [
    { step: '1', label: 'Build Graph', desc: 'Extract dependencies' },
    { step: '2', label: 'Optimize', desc: 'Generate chunks' },
    { step: '3', label: 'Enrich', desc: 'Add context' },
    { step: '4', label: 'Convert', desc: 'LLM migration' },
    { step: '5', label: 'Reconcile', desc: 'Final code' }
  ]

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      <div className="text-center">
        {/* Animated Header */}
        <div className="flex justify-center items-center space-x-4 mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring' }}
            className="relative"
          >
            <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center shadow-lg shadow-orange-500/30">
              <Database className="w-8 h-8 text-white" />
            </div>
          </motion.div>
          
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3 }}
          >
            <ArrowRight className="w-6 h-6 text-slate-600" />
          </motion.div>
          
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.4, type: 'spring' }}
            className="relative"
          >
            <div className="w-16 h-16 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg shadow-cyan-500/30">
              <GitBranch className="w-8 h-8 text-white" />
            </div>
          </motion.div>
          
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <ArrowRight className="w-6 h-6 text-slate-600" />
          </motion.div>
          
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.4 }}
          >
            <Sparkles className="w-8 h-8 text-purple-400 animate-pulse" />
          </motion.div>
          
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <ArrowRight className="w-6 h-6 text-slate-600" />
          </motion.div>
          
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.6, type: 'spring' }}
          >
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-500 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <Code className="w-8 h-8 text-white" />
            </div>
          </motion.div>
        </div>

        <motion.h2 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="text-3xl md:text-4xl font-bold text-white mb-4"
        >
          <span className="gradient-text-cyan">Graph-Based</span> SAS to PySpark Migration
        </motion.h2>
        
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto"
        >
          Analyze code dependencies, optimize chunks, and convert with AI-powered
          migration that understands your data flow.
        </motion.p>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 + index * 0.1 }}
              className={`p-5 rounded-xl ${feature.bgColor} border ${feature.borderColor}`}
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mx-auto mb-4 shadow-lg`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-slate-400">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* System Status */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.3 }}
          className="mb-8 p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/30"
        >
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
            <span className="text-emerald-300 font-medium">
              Graph migration engine ready
            </span>
          </div>
        </motion.div>

        {/* Action Button */}
        <motion.button
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.4 }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onStart}
          disabled={isLoading}
          className="px-8 py-4 text-lg font-semibold rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:from-cyan-600 hover:to-blue-600 transition-all disabled:opacity-50"
        >
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Initializing...</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Upload className="w-5 h-5" />
              <span>Start Migration</span>
              <Zap className="w-5 h-5" />
            </div>
          )}
        </motion.button>

        {/* Migration Pipeline Preview */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="mt-8 p-5 bg-slate-800/50 rounded-xl border border-slate-700/50"
        >
          <h4 className="font-medium text-white mb-4">Migration Pipeline</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
            {phases.map((item) => (
              <div key={item.step} className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-300 font-bold text-xs">
                  {item.step}
                </div>
                <div className="text-left">
                  <p className="text-slate-300 font-medium text-xs">{item.label}</p>
                  <p className="text-slate-500 text-xs">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

export default WelcomePanel
