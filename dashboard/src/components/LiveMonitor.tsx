/**
 * Live monitor component showing latest simulation runs
 */

'use client'

import { useEffect, useState } from 'react'
import { supabase, SimulationBatchRun } from '@/lib/supabase'
import { Activity } from 'lucide-react'

export default function LiveMonitor() {
  const [runs, setRuns] = useState<SimulationBatchRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch initial data
    fetchRuns()

    // Set up real-time subscription
    const channel = supabase
      .channel('simulation_runs')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'simulation_batch_runs',
        },
        (payload) => {
          setRuns((prev) => [payload.new as SimulationBatchRun, ...prev].slice(0, 10))
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  const fetchRuns = async () => {
    try {
      const { data, error } = await supabase
        .from('simulation_batch_runs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10)

      if (error) throw error
      setRuns(data || [])
    } catch (error) {
      console.error('Error fetching runs:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-bold">Live Monitor</h2>
        </div>
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-blue-600" />
        <h2 className="text-xl font-bold">Live Monitor</h2>
      </div>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {runs.length === 0 ? (
          <p className="text-gray-500">No simulation runs yet</p>
        ) : (
          runs.map((run) => (
            <div
              key={run.id}
              className="p-3 bg-gray-50 rounded border-l-4 border-blue-500"
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold text-sm">
                    {run.machine_id} | {run.agent_strategy}
                  </p>
                  <p className="text-xs text-gray-600">
                    Density: {(run.resource_density * 100).toFixed(0)}% | 
                    Survived: {run.total_ticks_survived} ticks
                  </p>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(run.created_at).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

