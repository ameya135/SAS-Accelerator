import React, { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, File, X, CheckCircle, AlertCircle, FileCode } from 'lucide-react'

const FileUpload = ({ onFilesUploaded, isLoading }) => {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [error, setError] = useState('')

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError('')
    
    if (rejectedFiles.length > 0) {
      const reasons = rejectedFiles.map(file => 
        file.errors.map(error => error.message).join(', ')
      ).join('; ')
      setError(`Some files were rejected: ${reasons}`)
    }

    if (acceptedFiles.length > 0) {
      const newFiles = acceptedFiles.map(file => ({
        file,
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        status: 'ready'
      }))
      
      setSelectedFiles(prev => [...prev, ...newFiles])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.sas']
    },
    maxSize: 10 * 1024 * 1024,
    multiple: true
  })

  const removeFile = (fileId) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file')
      return
    }

    const files = selectedFiles.map(f => f.file)
    const success = await onFilesUploaded(files)
    
    if (success) {
      setSelectedFiles([])
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
          <Upload className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-xl font-semibold text-white">
            Upload SAS Files
          </h3>
          <p className="text-sm text-slate-400">Drag and drop or click to browse</p>
        </div>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          relative cursor-pointer transition-all duration-300 rounded-xl border-2 border-dashed p-8
          ${isDragActive 
            ? 'border-cyan-500 bg-cyan-500/10' 
            : 'border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800/30'
          }
          ${selectedFiles.length > 0 ? 'mb-6' : ''}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-4">
          <motion.div 
            animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
            className={`
              w-16 h-16 rounded-2xl flex items-center justify-center transition-colors duration-300
              ${isDragActive 
                ? 'bg-gradient-to-br from-cyan-500 to-blue-500 shadow-lg shadow-cyan-500/30' 
                : 'bg-slate-800/50 border border-slate-700'
              }
            `}
          >
            <FileCode className={`
              w-8 h-8 transition-colors duration-300
              ${isDragActive ? 'text-white' : 'text-slate-400'}
            `} />
          </motion.div>
          
          <div className="text-center">
            <p className="text-lg font-medium text-white mb-2">
              {isDragActive ? 'Drop your files here' : 'Drag & drop SAS files'}
            </p>
            <p className="text-slate-400 mb-4">
              or <span className="text-cyan-400 font-medium hover:underline">click to browse</span>
            </p>
            <div className="text-sm text-slate-500 space-y-1">
              <p>Supports .sas files only</p>
              <p>Maximum file size: 10MB</p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center space-x-2 p-4 bg-red-500/10 border border-red-500/30 rounded-xl mb-4"
          >
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Selected Files */}
      <AnimatePresence>
        {selectedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-white">
                Selected Files ({selectedFiles.length})
              </h4>
              <button
                onClick={() => setSelectedFiles([])}
                className="text-sm text-slate-400 hover:text-red-400 transition-colors"
              >
                Clear all
              </button>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
              {selectedFiles.map((fileItem, index) => (
                <motion.div
                  key={fileItem.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50"
                >
                  <div className="flex items-center space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-xl flex items-center justify-center border border-orange-500/30">
                      <File className="w-5 h-5 text-orange-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-white truncate">
                        {fileItem.name}
                      </p>
                      <p className="text-sm text-slate-400">
                        {formatFileSize(fileItem.size)}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <CheckCircle className="w-5 h-5 text-emerald-400" />
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(fileItem.id)}
                    className="ml-3 p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                    aria-label="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </motion.div>
              ))}
            </div>

            <div className="pt-4 border-t border-slate-700/50">
              <button
                onClick={handleUpload}
                disabled={isLoading || selectedFiles.length === 0}
                className="w-full py-4 text-lg font-semibold rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:from-cyan-600 hover:to-blue-600 transition-all disabled:opacity-50"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Uploading...</span>
                  </div>
                ) : (
                  `Upload ${selectedFiles.length} File${selectedFiles.length === 1 ? '' : 's'}`
                )}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tips */}
      <div className="mt-6 p-4 bg-cyan-500/10 rounded-xl border border-cyan-500/30">
        <h4 className="font-medium text-cyan-300 mb-2">Graph Analysis Benefits</h4>
        <ul className="text-sm text-cyan-200/70 space-y-1">
          <li>Automatic dependency detection between DATA steps and PROCs</li>
          <li>Optimal chunk generation based on execution layers</li>
          <li>Schema tracking through transformations</li>
        </ul>
      </div>
    </motion.div>
  )
}

export default FileUpload

