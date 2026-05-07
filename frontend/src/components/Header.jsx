import React, { useEffect, useRef, useState } from 'react'
import { GitBranch, Database, Sparkles, Code, Key, Check, X } from 'lucide-react'
import { setApiKey } from '../hooks/useGraphMigration'

const Header = () => {
  const [showKeyInput, setShowKeyInput] = useState(false)
  const [keyValue, setKeyValue] = useState('')
  const [keySet, setKeySet] = useState(false)
  const keySetTimeoutRef = useRef(null)

  useEffect(() => {
    return () => {
      if (keySetTimeoutRef.current) {
        clearTimeout(keySetTimeoutRef.current)
      }
    }
  }, [])

  const handleSetKey = () => {
    if (keyValue.trim()) {
      setApiKey(keyValue.trim())
      setKeySet(true)
      setShowKeyInput(false)
      setKeyValue('')

      if (keySetTimeoutRef.current) {
        clearTimeout(keySetTimeoutRef.current)
      }

      keySetTimeoutRef.current = setTimeout(() => {
        setKeySet(false)
        keySetTimeoutRef.current = null
      }, 3000)
    }
  }

  return (
    <header className="bg-slate-900/80 backdrop-blur-xl border-b border-slate-800/50 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/20">
                  <Database className="w-5 h-5 text-white" />
                </div>
              </div>
              
              <div className="w-8 h-8 flex items-center justify-center">
                <GitBranch className="w-5 h-5 text-cyan-400" />
              </div>
              
              <div className="w-8 h-8 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-purple-400" />
              </div>
              
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Code className="w-5 h-5 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">
                Graph-Based Migration
              </h1>
              <p className="text-sm text-slate-400">
                SAS to PySpark with dependency analysis
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-2">
              <div className="px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30">
                <span className="text-sm font-medium text-cyan-300 flex items-center gap-2">
                  <GitBranch className="w-3.5 h-3.5" />
                  Graph-Powered
                </span>
              </div>
              <div className="px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30">
                <span className="text-sm font-medium text-purple-300">AI-Enhanced</span>
              </div>
            </div>
            
            {/* API Key Input */}
            <div className="flex items-center space-x-2">
              {showKeyInput ? (
                <div className="flex items-center space-x-1">
                  <input
                    type="password"
                    value={keyValue}
                    onChange={(e) => setKeyValue(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSetKey()}
                    placeholder="API Key"
                    className="px-2 py-1 text-xs bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500 w-32 focus:outline-none focus:border-cyan-500"
                    autoFocus
                  />
                  <button
                    onClick={handleSetKey}
                    className="p-1 rounded hover:bg-slate-800 text-emerald-400 hover:text-emerald-300 transition-colors"
                    aria-label="Confirm API key"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => { setShowKeyInput(false); setKeyValue('') }}
                    className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                    aria-label="Cancel API key input"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowKeyInput(true)}
                  className={`flex items-center space-x-1 px-2 py-1.5 rounded text-xs transition-colors ${
                    keySet 
                      ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/30' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                  aria-label="Set API key"
                >
                  <Key className="w-3.5 h-3.5" />
                  <span>{keySet ? 'Key Set' : 'Set Key'}</span>
                </button>
              )}
            </div>

            <div className="text-right hidden lg:block">
              <p className="text-sm text-slate-500">By RSystems International</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
