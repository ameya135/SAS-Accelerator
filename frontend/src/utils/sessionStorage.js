/**
 * Session Storage Utility
 * 
 * Handles persistent session storage for the graph migration tool.
 * Uses localStorage to maintain state across page refreshes.
 */

const STORAGE_KEY = 'graph_migration_session'

const SessionStorage = {
  /**
   * Save session data to localStorage
   */
  save: (data) => {
    try {
      const serialized = JSON.stringify({
        ...data,
        timestamp: Date.now()
      })
      localStorage.setItem(STORAGE_KEY, serialized)
      return true
    } catch (error) {
      console.error('Failed to save session:', error)
      return false
    }
  },

  /**
   * Load session data from localStorage
   */
  load: () => {
    try {
      const serialized = localStorage.getItem(STORAGE_KEY)
      if (!serialized) {
        return null
      }

      const data = JSON.parse(serialized)
      
      // Check if session is older than 24 hours
      const maxAge = 24 * 60 * 60 * 1000 // 24 hours in ms
      if (data.timestamp && Date.now() - data.timestamp > maxAge) {
        SessionStorage.clear()
        return null
      }

      return data
    } catch (error) {
      console.error('Failed to load session:', error)
      return null
    }
  },

  /**
   * Clear session data from localStorage
   */
  clear: () => {
    try {
      localStorage.removeItem(STORAGE_KEY)
      return true
    } catch (error) {
      console.error('Failed to clear session:', error)
      return false
    }
  },

  /**
   * Check if a session exists
   */
  exists: () => {
    try {
      return localStorage.getItem(STORAGE_KEY) !== null
    } catch (error) {
      return false
    }
  },

  /**
   * Update specific fields in the session
   */
  update: (updates) => {
    const current = SessionStorage.load() || {}
    return SessionStorage.save({
      ...current,
      ...updates
    })
  }
}

export default SessionStorage

