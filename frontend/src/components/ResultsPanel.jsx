import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Download, 
  Package, 
  CheckCircle, 
  XCircle, 
  RotateCcw,
  BarChart3,
  AlertCircle,
  Sparkles,
  Trophy,
  FileCode,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import CodePreview from './CodePreview'

/**
 * Result card for individual file
 */
const ResultCard = ({ result, onDownload }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border-2 overflow-hidden ${
        result.success
          ? 'bg-emerald-500/10 border-emerald-500/30'
          : 'bg-red-500/10 border-red-500/30'
      }`}
    >
      {/* Header */}
      <div className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="min-w-0 flex-1 flex items-center space-x-3 text-left"
          aria-expanded={isExpanded}
        >
          <span className="flex-shrink-0">
            {result.success ? (
              <CheckCircle className="w-6 h-6 text-emerald-400" />
            ) : (
              <XCircle className="w-6 h-6 text-red-400" />
            )}
          </span>
          <span className="min-w-0">
            <span className="block font-medium text-white truncate">{result.file || result.filename}</span>
            {result.success ? (
              <span className="block text-sm text-emerald-300/70">
                {result.chunks_converted || 0}/{result.total_chunks || 0} chunks converted
              </span>
            ) : (
              <span className="block text-sm text-red-300/70">
                {result.error || (result.errors && result.errors.length > 0 ? `${result.errors.length} error(s)` : 'Migration failed')}
              </span>
            )}
          </span>
        </button>
        <div className="flex items-center space-x-3">
          {result.success && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDownload(result.file || result.filename)
              }}
              className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium flex items-center space-x-1 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </button>
          )}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-4 pt-0 space-y-4">
          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/30">
              <h5 className="text-sm font-medium text-amber-300 mb-2 flex items-center space-x-1">
                <AlertCircle className="w-4 h-4" />
                <span>Warnings ({result.warnings.length})</span>
              </h5>
              <ul className="text-xs text-amber-200/70 space-y-1 list-disc list-inside">
                {result.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Code Preview */}
          {result.success && result.pyspark_code && (
            <div>
              <h5 className="text-sm font-medium text-slate-300 mb-2">Generated PySpark Code</h5>
              <CodePreview 
                code={result.pyspark_code} 
                language="python" 
                maxHeight="300px" 
              />
            </div>
          )}

          {/* Errors */}
          {result.errors && result.errors.length > 0 && (
            <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/30">
              <h5 className="text-sm font-medium text-red-300 mb-2 flex items-center space-x-1">
                <XCircle className="w-4 h-4" />
                <span>Errors ({result.errors.length})</span>
              </h5>
              <ul className="text-xs text-red-200/70 space-y-1 list-disc list-inside">
                {result.errors.map((error, i) => (
                  <li key={i}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}

/**
 * ResultsPanel Component
 */
const ResultsPanel = ({ results, onDownload, onStartNew }) => {
  if (!results) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <p className="text-slate-400">No results available</p>
        </div>
      </div>
    )
  }

  // Handle different result structures
  const fileResults = Array.isArray(results) ? results : (results.results || [])
  const successful = fileResults.filter(r => r.success).length
  const failed = fileResults.length - successful
  const successRate = fileResults.length > 0 ? Math.round((successful / fileResults.length) * 100) : 0

  return (
    <div className="space-y-6">
      {/* Success Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-emerald-500/20 to-green-500/20 rounded-2xl border border-emerald-500/30 p-6"
      >
        <div className="flex items-center justify-center space-x-4">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-500 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <Trophy className="w-8 h-8 text-white" />
          </div>
          <div className="text-left">
            <h2 className="text-2xl font-bold text-white">Migration Complete!</h2>
            <p className="text-emerald-300/70">Your SAS code has been transformed to PySpark</p>
          </div>
        </div>
      </motion.div>

      {/* Summary Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
            <BarChart3 className="w-5 h-5 text-white" />
          </div>
          <h3 className="text-xl font-semibold text-white">Migration Summary</h3>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
            <div className="text-3xl font-bold text-white mb-1">{fileResults.length}</div>
            <div className="text-sm text-slate-400">Total Files</div>
          </div>
          <div className="text-center p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/30">
            <div className="text-3xl font-bold text-emerald-400 mb-1">{successful}</div>
            <div className="text-sm text-emerald-300/70">Successful</div>
          </div>
          <div className="text-center p-4 bg-red-500/10 rounded-xl border border-red-500/30">
            <div className="text-3xl font-bold text-red-400 mb-1">{failed}</div>
            <div className="text-sm text-red-300/70">Failed</div>
          </div>
          <div className="text-center p-4 bg-cyan-500/10 rounded-xl border border-cyan-500/30">
            <div className="text-3xl font-bold text-cyan-400 mb-1">{successRate}%</div>
            <div className="text-sm text-cyan-300/70">Success Rate</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-slate-400">Overall Success Rate</span>
            <span className="text-sm font-bold text-emerald-400">{successRate}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
            <motion.div
              className="h-3 rounded-full bg-gradient-to-r from-emerald-500 to-green-500"
              initial={{ width: 0 }}
              animate={{ width: `${successRate}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
          <button
            onClick={() => onDownload('all', { downloadAll: true })}
            className="flex-1 btn-primary flex items-center justify-center space-x-2"
          >
            <Package className="w-5 h-5" />
            <span>Download All Results (ZIP)</span>
          </button>
          <button
            onClick={onStartNew}
            className="btn-secondary flex items-center justify-center space-x-2"
          >
            <RotateCcw className="w-5 h-5" />
            <span>Start New</span>
          </button>
        </div>
      </motion.div>

      {/* File Results */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="space-y-4"
      >
        <div className="flex items-center space-x-3">
          <FileCode className="w-5 h-5 text-cyan-400" />
          <h3 className="text-xl font-semibold text-white">Conversion Results</h3>
        </div>

        {fileResults.length > 0 ? (
          <div className="space-y-3">
            {fileResults.map((result, index) => (
              <ResultCard 
                key={index} 
                result={result} 
                onDownload={onDownload}
              />
            ))}
          </div>
        ) : (
          <div className="card text-center py-8">
            <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400">No migration results found</p>
          </div>
        )}
      </motion.div>

      {/* Next Steps */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card"
      >
        <div className="flex items-center space-x-3 mb-4">
          <Sparkles className="w-5 h-5 text-purple-400" />
          <h4 className="font-semibold text-white">Next Steps</h4>
        </div>
        <div className="space-y-3 text-sm">
          {[
            'Review the generated PySpark code to ensure it meets your requirements',
            'Check execution order matches your expected data flow',
            'Test the PySpark code in your environment with sample data',
            'Validate schema mappings and data types'
          ].map((item, index) => (
            <div key={index} className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full mt-2 flex-shrink-0" />
              <p className="text-slate-300">{item}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default ResultsPanel
