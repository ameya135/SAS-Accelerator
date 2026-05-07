import { useState, useCallback, useEffect, useRef } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import SessionStorage from '../utils/sessionStorage'

const API_BASE = '/api'

let apiKey = null

export const setApiKey = (key) => {
  apiKey = key
}

axios.interceptors.request.use((config) => {
  if (apiKey && config.url?.startsWith(API_BASE)) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

/**
 * Custom hook for graph-based migration
 *
 * Provides methods and state for:
 * - Initializing migration sessions
 * - Uploading SAS files
 * - Analyzing dependency graphs
 * - Starting migrations
 * - Downloading results
 */
export const useGraphMigration = () => {
  const [sessionId, setSessionId] = useState(null)
  const [sessionToken, setSessionToken] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [graph, setGraph] = useState(null)
  const [chunks, setChunks] = useState([])
  const [results, setResults] = useState(null)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [originalFiles, setOriginalFiles] = useState([]) // Keep File objects for analysis
  const [migrationPhase, setMigrationPhase] = useState(0)
  const [completedPhases, setCompletedPhases] = useState([])
  const mountedRef = useRef(true)
  const operationGenerationRef = useRef(0)
  const abortControllersRef = useRef(new Set())

  const beginOperation = useCallback(() => {
    const controller = new AbortController()
    const generation = operationGenerationRef.current
    abortControllersRef.current.add(controller)

    return { controller, generation }
  }, [])

  const endOperation = useCallback((controller) => {
    abortControllersRef.current.delete(controller)
  }, [])

  const isOperationCurrent = useCallback((operation) => (
    mountedRef.current &&
    operation.generation === operationGenerationRef.current &&
    !operation.controller.signal.aborted
  ), [])

  const isCanceledError = useCallback((err) => (
    err?.code === 'ERR_CANCELED' ||
    err?.name === 'CanceledError' ||
    axios.isCancel?.(err)
  ), [])

  const abortPendingOperations = useCallback(() => {
    abortControllersRef.current.forEach(controller => controller.abort())
    abortControllersRef.current.clear()
  }, [])

  const getSessionHeaders = useCallback(() => (
    sessionToken ? { 'X-Session-Token': sessionToken } : {}
  ), [sessionToken])

  useEffect(() => {
    return () => {
      mountedRef.current = false
      operationGenerationRef.current += 1
      abortPendingOperations()
    }
  }, [abortPendingOperations])

  // Load session on mount
  useEffect(() => {
    const savedSession = SessionStorage.load()
    if (savedSession) {
      setSessionId(savedSession.sessionId)
      setSessionToken(savedSession.sessionToken || null)
      setGraph(savedSession.graph)
      setChunks(savedSession.chunks || [])
      setResults(savedSession.results)
      setUploadedFiles(savedSession.uploadedFiles || [])
      setCompletedPhases(savedSession.completedPhases || [])
    }
  }, [])

  // Save session whenever state changes
  const saveSession = useCallback((updates = {}) => {
    const sessionData = {
      sessionId,
      sessionToken,
      graph,
      chunks,
      results,
      uploadedFiles,
      completedPhases,
      ...updates
    }
    SessionStorage.save(sessionData)
  }, [sessionId, sessionToken, graph, chunks, results, uploadedFiles, completedPhases])

  /**
   * Initialize a new migration session
   */
  const initializeSession = useCallback(async (config = {}) => {
    const operation = beginOperation()
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/graph-migrate/initialize`, {
        model: config.model || 'gpt-4',
        use_rag: config.use_rag !== undefined ? config.use_rag : true
      }, {
        signal: operation.controller.signal
      })

      if (!isOperationCurrent(operation)) {
        return false
      }

      if (response.data.success) {
        const newSessionId = response.data.session_id
        const newSessionToken = response.data.session_token || null
        setSessionId(newSessionId)
        setSessionToken(newSessionToken)
        saveSession({ sessionId: newSessionId, sessionToken: newSessionToken })
        toast.success('Session initialized!')
        return true
      } else {
        throw new Error('Failed to initialize session')
      }
    } catch (err) {
      if (isCanceledError(err) || !isOperationCurrent(operation)) {
        return false
      }

      const errorMsg = err.response?.data?.error || err.message || 'Failed to initialize session'
      setError(errorMsg)
      toast.error(errorMsg)
      return false
    } finally {
      endOperation(operation.controller)
      if (isOperationCurrent(operation)) {
        setLoading(false)
      }
    }
  }, [beginOperation, endOperation, isCanceledError, isOperationCurrent, saveSession])

  /**
   * Upload SAS files
   */
  const uploadFiles = useCallback(async (files) => {
    if (!sessionId) {
      toast.error('No active session')
      return false
    }

    const operation = beginOperation()
    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('session_id', sessionId)

      files.forEach(file => {
        formData.append('files[]', file)
      })

      const response = await axios.post(`${API_BASE}/graph-migrate/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getSessionHeaders()
        },
        signal: operation.controller.signal
      })

      if (!isOperationCurrent(operation)) {
        return false
      }

      if (response.data.success) {
        const uploaded = response.data.uploaded_files || files.map(f => ({
          name: f.name,
          filename: f.name,
          size: f.size
        }))
        setUploadedFiles(uploaded)
        setOriginalFiles(files) // Store original File objects for later analysis
        saveSession({ uploadedFiles: uploaded })
        toast.success(`Uploaded ${uploaded.length} file(s)`)
        return true
      } else {
        throw new Error('Failed to upload files')
      }
    } catch (err) {
      if (isCanceledError(err) || !isOperationCurrent(operation)) {
        return false
      }

      const errorMsg = err.response?.data?.error || err.message || 'Failed to upload files'
      setError(errorMsg)
      toast.error(errorMsg)
      return false
    } finally {
      endOperation(operation.controller)
      if (isOperationCurrent(operation)) {
        setLoading(false)
      }
    }
  }, [beginOperation, endOperation, getSessionHeaders, isCanceledError, isOperationCurrent, sessionId, saveSession])

  /**
   * Analyze a SAS file and get dependency graph with chunks
   */
  const analyzeFile = useCallback(async (file) => {
    const operation = beginOperation()
    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      
      // Handle both File objects and file info objects
      if (file instanceof File) {
        formData.append('file', file)
      } else if (file.name || file.filename) {
        // If it's a file info object, try to find the original File object
        const filename = file.name || file.filename
        const originalFile = originalFiles.find(f => f.name === filename)
        
        if (originalFile) {
          formData.append('file', originalFile)
        } else {
          // Fall back to session-based approach
          formData.append('filename', filename)
          formData.append('session_id', sessionId)
        }
      }
      
      formData.append('format', 'react-flow')

      const response = await axios.post(`${API_BASE}/graph/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getSessionHeaders()
        },
        signal: operation.controller.signal
      })

      if (!isOperationCurrent(operation)) {
        return false
      }

      if (response.data.success) {
        const graphData = response.data.graph
        const chunksData = response.data.chunks || []
        
        // Ensure graph stats include node_types and edge_types from summary
        if (graphData.stats && response.data.summary) {
          graphData.stats.node_types = response.data.summary.node_counts_by_type || graphData.stats.node_types || {}
        }
        
        setGraph(graphData)
        setChunks(chunksData)
        saveSession({ graph: graphData, chunks: chunksData })
        
        const chunkSummary = response.data.chunk_summary
        if (chunkSummary) {
          toast.success(`Analysis complete! ${chunksData.length} chunks, ${chunkSummary.total_tokens || 0} tokens`)
        } else {
          toast.success('Analysis complete!')
        }
        return true
      } else {
        throw new Error('Failed to analyze file')
      }
    } catch (err) {
      if (isCanceledError(err) || !isOperationCurrent(operation)) {
        return false
      }

      const errorMsg = err.response?.data?.error || err.message || 'Failed to analyze file'
      setError(errorMsg)
      toast.error(errorMsg)
      return false
    } finally {
      endOperation(operation.controller)
      if (isOperationCurrent(operation)) {
        setLoading(false)
      }
    }
  }, [beginOperation, endOperation, getSessionHeaders, isCanceledError, isOperationCurrent, sessionId, originalFiles, saveSession])

  /**
   * Start the migration process
   */
  const startMigration = useCallback(async () => {
    if (!sessionId) {
      toast.error('No active session')
      return false
    }

    const operation = beginOperation()
    setLoading(true)
    setError(null)
    setCompletedPhases([])
    setMigrationPhase(1)

    let phaseUpdater = null

    try {
      phaseUpdater = setInterval(() => {
        if (!isOperationCurrent(operation)) {
          return
        }

        setMigrationPhase(prev => {
          if (prev < 5) {
            return prev + 1
          }
          return prev
        })
      }, 2000)

      const response = await axios.post(`${API_BASE}/graph-migrate/start`, {
        session_id: sessionId
      }, {
        headers: getSessionHeaders(),
        signal: operation.controller.signal
      })

      if (!isOperationCurrent(operation)) {
        return false
      }

      if (response.data.success) {
        setCompletedPhases([1, 2, 3, 4, 5])
        setMigrationPhase(0)
        setResults(response.data.results)
        saveSession({ 
          results: response.data.results,
          completedPhases: [1, 2, 3, 4, 5]
        })
        toast.success('Migration complete!')
        return true
      } else {
        throw new Error('Migration failed')
      }
    } catch (err) {
      if (isCanceledError(err) || !isOperationCurrent(operation)) {
        return false
      }

      const errorMsg = err.response?.data?.error || err.message || 'Migration failed'
      setError(errorMsg)
      toast.error(errorMsg)
      setMigrationPhase(0)
      return false
    } finally {
      if (phaseUpdater) {
        clearInterval(phaseUpdater)
      }
      endOperation(operation.controller)
      if (isOperationCurrent(operation)) {
        setLoading(false)
      }
    }
  }, [beginOperation, endOperation, getSessionHeaders, isCanceledError, isOperationCurrent, sessionId, saveSession])

  /**
   * Download a converted file
   */
  const downloadFile = useCallback(async (filename, options = {}) => {
    if (!sessionId) {
      toast.error('No active session')
      return
    }

    const operation = beginOperation()
    const isDownloadAll = options.downloadAll === true

    try {
      const endpoint = isDownloadAll
        ? `${API_BASE}/graph-migrate/download-all/${sessionId}`
        : `${API_BASE}/graph-migrate/download/${sessionId}/${encodeURIComponent(filename)}`

      const response = await axios.get(endpoint, {
        responseType: 'blob',
        headers: getSessionHeaders(),
        signal: operation.controller.signal
      })

      if (!isOperationCurrent(operation)) {
        return
      }

      let url
      try {
        url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', isDownloadAll ? 'migration_results.zip' : filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } finally {
        if (url) {
          window.URL.revokeObjectURL(url)
        }
      }

      toast.success(`Downloaded ${isDownloadAll ? 'all results' : filename}`)
    } catch (err) {
      if (isCanceledError(err) || !isOperationCurrent(operation)) {
        return
      }

      const errorMsg = err.response?.data?.error || err.message || 'Failed to download file'
      toast.error(errorMsg)
    } finally {
      endOperation(operation.controller)
    }
  }, [beginOperation, endOperation, getSessionHeaders, isCanceledError, isOperationCurrent, sessionId])

  /**
   * Reset the hook state
   */
  const reset = useCallback(() => {
    operationGenerationRef.current += 1
    abortPendingOperations()
    setSessionId(null)
    setSessionToken(null)
    setLoading(false)
    setError(null)
    setGraph(null)
    setChunks([])
    setResults(null)
    setUploadedFiles([])
    setOriginalFiles([])
    setMigrationPhase(0)
    setCompletedPhases([])
    SessionStorage.clear()
    toast.success('Session reset')
  }, [abortPendingOperations])

  return {
    // State
    sessionId,
    sessionToken,
    loading,
    error,
    graph,
    chunks,
    results,
    uploadedFiles,
    originalFiles,
    migrationPhase,
    completedPhases,

    // Methods
    initializeSession,
    uploadFiles,
    analyzeFile,
    startMigration,
    downloadFile,
    reset,
    setApiKey
  }
}

export default useGraphMigration
