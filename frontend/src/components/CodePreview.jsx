import React, { useEffect, useRef, useState } from 'react'
import { Copy, Check, FileCode } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

const LANGUAGE_MAP = {
  python: { language: 'python', label: 'Python' },
  sas: { language: 'plaintext', label: 'SAS' },
  text: { language: 'plaintext', label: 'Text' },
}

const CodePreview = ({ 
  code, 
  language = 'python', 
  title,
  maxHeight = '400px',
  showLineNumbers = true,
  showCopy = true
}) => {
  const [copied, setCopied] = useState(false)
  const copyTimeoutRef = useRef(null)

  useEffect(() => {
    return () => {
      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current)
      }
    }
  }, [])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)

      if (copyTimeoutRef.current) {
        clearTimeout(copyTimeoutRef.current)
      }

      copyTimeoutRef.current = setTimeout(() => {
        setCopied(false)
        copyTimeoutRef.current = null
      }, 2000)
    } catch {
      setCopied(false)
    }
  }

  if (!code) {
    return (
      <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 text-center">
        <FileCode className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        <p className="text-sm text-slate-500">No code to display</p>
      </div>
    )
  }

  const langConfig = LANGUAGE_MAP[language] || LANGUAGE_MAP.text

  return (
    <div className="relative bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
      {(title || showCopy) && (
        <div className="flex items-center justify-between px-4 py-2 bg-slate-900/50 border-b border-slate-800">
          {title && (
            <div className="flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-slate-500" />
              <span className="text-sm text-slate-400">{title}</span>
            </div>
          )}
          {showCopy && (
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1 px-2 py-1 rounded text-xs text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>
      )}

      <div className="overflow-auto custom-scrollbar" style={{ maxHeight }}>
        <SyntaxHighlighter
          language={langConfig.language}
          style={vscDarkPlus}
          showLineNumbers={showLineNumbers}
          wrapLines={true}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'transparent',
            fontSize: '0.875rem',
            lineHeight: '1.25rem',
          }}
          lineNumberStyle={{
            minWidth: '2.5em',
            paddingRight: '1em',
            color: '#475569',
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>

      <div className="absolute bottom-2 right-2">
        <span className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-500 uppercase">
          {langConfig.label}
        </span>
      </div>
    </div>
  )
}

export default CodePreview
