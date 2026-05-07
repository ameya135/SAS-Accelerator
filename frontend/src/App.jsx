import React, { useState, useCallback } from 'react'
import { Toaster } from 'react-hot-toast'
import Header from './components/Header'
import WelcomePanel from './components/WelcomePanel'
import FileUpload from './components/FileUpload'
import DependencyGraph from './components/DependencyGraph'
import ChunkViewer from './components/ChunkViewer'
import MigrationPipeline from './components/MigrationPipeline'
import ResultsPanel from './components/ResultsPanel'
import GraphStats from './components/GraphStats'
import { useGraphMigration } from './hooks/useGraphMigration'
import { ArrowLeft, ArrowRight, Play } from 'lucide-react'

function App() {
  const [activeStep, setActiveStep] = useState(1)
  const {
    loading,
    graph,
    chunks,
    results,
    migrationPhase,
    completedPhases,
    uploadedFiles,
    initializeSession,
    uploadFiles,
    analyzeFile,
    startMigration,
    downloadFile,
    reset
  } = useGraphMigration()

  const handleStart = useCallback(async () => {
    const success = await initializeSession()
    if (success) {
      setActiveStep(2)
    }
  }, [initializeSession])

  const handleFilesUploaded = useCallback(async (files) => {
    const success = await uploadFiles(files)
    if (success) {
      setActiveStep(3)
    }
  }, [uploadFiles])

  const handleAnalyze = useCallback(async () => {
    if (uploadedFiles.length > 0) {
      const success = await analyzeFile(uploadedFiles[0])
      if (success) {
        setActiveStep(4)
      }
    }
  }, [analyzeFile, uploadedFiles])

  const handleStartMigration = useCallback(async () => {
    setActiveStep(5)
    const success = await startMigration()
    if (success) {
      setActiveStep(6)
    } else {
      setActiveStep(4)
    }
  }, [startMigration])

  const handleReset = useCallback(() => {
    reset()
    setActiveStep(1)
  }, [reset])

  const steps = [
    { number: 1, title: 'Welcome', description: 'Get started' },
    { number: 2, title: 'Upload', description: 'Upload SAS files' },
    { number: 3, title: 'Analyze', description: 'Build dependency graph' },
    { number: 4, title: 'Review', description: 'Review chunks' },
    { number: 5, title: 'Migrate', description: 'Convert to PySpark' },
    { number: 6, title: 'Results', description: 'Download results' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950/30 to-slate-950">
      <Toaster 
        position="top-right" 
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e1b4b',
            color: '#e0e7ff',
            border: '1px solid #4338ca',
            borderRadius: '12px',
            boxShadow: '0 10px 40px -10px rgba(99, 102, 241, 0.3)',
          },
        }}
      />
      
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-2 md:space-x-4 mb-6 overflow-x-auto pb-2">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center flex-shrink-0">
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-full border-2 font-semibold text-sm
                  transition-all duration-300
                  ${activeStep >= step.number 
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 border-indigo-400 text-white shadow-lg shadow-indigo-500/30' 
                    : 'bg-slate-900/50 border-slate-700 text-slate-500'
                  }
                  ${activeStep === step.number ? 'ring-4 ring-indigo-500/30 scale-110' : ''}
                `}>
                  {activeStep > step.number ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div className={`
                    w-8 md:w-16 h-0.5 mx-1 md:mx-2 transition-all duration-500
                    ${activeStep > step.number 
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-500' 
                      : 'bg-slate-800'}
                  `} />
                )}
              </div>
            ))}
          </div>
          
          <div className="text-center">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">
              {steps[activeStep - 1]?.title}
            </h2>
            <p className="text-indigo-200/70">
              {steps[activeStep - 1]?.description}
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className={`mx-auto ${activeStep === 4 || activeStep === 5 ? 'max-w-7xl' : 'max-w-4xl'}`}>
          {/* Step 1: Welcome */}
          {activeStep === 1 && (
            <WelcomePanel 
              onStart={handleStart}
              isLoading={loading}
            />
          )}
          
          {/* Step 2: Upload */}
          {activeStep === 2 && (
            <FileUpload 
              onFilesUploaded={handleFilesUploaded}
              isLoading={loading}
            />
          )}
          
          {/* Step 3: Analyze */}
          {activeStep === 3 && (
            <div className="space-y-6">
              <div className="card">
                <h3 className="text-xl font-semibold mb-4 text-white">Uploaded Files</h3>
                <p className="text-slate-400 mb-6">
                  Select Analyze Dependencies to build the dependency graph.
                </p>
                <div className="space-y-3 mb-6">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
                          <span className="text-white text-sm font-bold">{index + 1}</span>
                        </div>
                        <div>
                          <p className="font-medium text-white">{file.name || file.filename}</p>
                          <p className="text-sm text-slate-400">
                            {((file.size || 0) / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      <span className="px-3 py-1 rounded-full text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        SAS
                      </span>
                    </div>
                  ))}
                </div>
                
                <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
                  <button
                    onClick={() => setActiveStep(2)}
                    className="btn-secondary flex items-center justify-center space-x-2"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Back</span>
                  </button>
                  <button
                    onClick={handleAnalyze}
                    disabled={loading}
                    className="btn-primary flex-1 flex items-center justify-center space-x-2"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Analyzing...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5" />
                        <span>Analyze Dependencies</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Step 4: Review Graph & Chunks */}
          {activeStep === 4 && (
            <div className="space-y-6">
              {/* Graph Stats */}
              {graph && <GraphStats stats={graph.stats} />}
              
              {/* Dependency Graph */}
              <DependencyGraph graphData={graph} />
              
              {/* Chunks */}
              {chunks && chunks.length > 0 && (
                <ChunkViewer chunks={chunks} />
              )}
              
              <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
                <button
                  onClick={() => setActiveStep(3)}
                  className="btn-secondary flex items-center justify-center space-x-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
                <button
                  onClick={handleStartMigration}
                  disabled={loading}
                  className="btn-success flex-1 flex items-center justify-center space-x-2"
                >
                  <Play className="w-5 h-5" />
                  <span>Start Migration</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
          
          {/* Step 5: Migration Progress */}
          {activeStep === 5 && (
            <div className="space-y-6">
              <MigrationPipeline 
                currentPhase={migrationPhase}
                completedPhases={completedPhases}
              />
              
              {graph && <DependencyGraph graphData={graph} />}
            </div>
          )}
          
          {/* Step 6: Results */}
          {activeStep === 6 && (
            <ResultsPanel 
              results={results}
              onDownload={downloadFile}
              onStartNew={handleReset}
            />
          )}
        </div>
      </main>
    </div>
  )
}

export default App
