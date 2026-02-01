import { useState, useEffect, useRef, useCallback } from "react"

const API = "/api"

export default function useFlowState() {
  const [state, setState] = useState(null)
  const [drift, setDrift] = useState([])
  const [stats, setStats] = useState(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  const fetchState = useCallback(async () => {
    try {
      const res = await fetch(`${API}/state`)
      if (!res.ok) throw new Error(`${res.status}`)
      const data = await res.json()
      setState(data)
      setConnected(true)
      setError(null)
    } catch (e) {
      setConnected(false)
      setError(e.message)
    }
  }, [])

  const fetchDrift = useCallback(async () => {
    try {
      const res = await fetch(`${API}/drift?limit=100`)
      if (!res.ok) return
      const data = await res.json()
      setDrift(data.drift || [])
    } catch {}
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API}/stats`)
      if (!res.ok) return
      const data = await res.json()
      setStats(data)
    } catch {}
  }, [])

  const trainModel = useCallback(async (nTicks = 500) => {
    try {
      const res = await fetch(`${API}/train?n_ticks=${nTicks}`, { method: "POST" })
      if (!res.ok) throw new Error(`${res.status}`)
      return await res.json()
    } catch (e) {
      setError(e.message)
      return null
    }
  }, [])

  const resetSimulator = useCallback(async () => {
    try {
      const res = await fetch(`${API}/reset`, { method: "POST" })
      if (!res.ok) throw new Error(`${res.status}`)
      setDrift([])
      return await res.json()
    } catch (e) {
      setError(e.message)
      return null
    }
  }, [])

  useEffect(() => {
    fetchState()
    fetchDrift()
    fetchStats()
    intervalRef.current = setInterval(() => {
      fetchState()
      fetchDrift()
      fetchStats()
    }, 1000)
    return () => clearInterval(intervalRef.current)
  }, [fetchState, fetchDrift, fetchStats])

  return { state, drift, stats, connected, error, trainModel, resetSimulator }
}
