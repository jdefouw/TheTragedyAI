/**
 * Population Dynamics chart showing strategy convergence over time.
 * proves "Scarcity Window" hypothesis by visualizing population collapse or dominance.
 */

'use client'

import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { supabase } from '../lib/supabase'
import { Users } from 'lucide-react'

interface TimeSeriesPoint {
  tick: number
  coop_count: number
  aggressive_count: number
  gini_coefficient: number
}

export default function PopulationDynamics() {
  const [data, setData] = useState<TimeSeriesPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSimId, setSelectedSimId] = useState<string | null>(null)

  useEffect(() => {
    fetchLatestMixedSimulation()
  }, [])

  const fetchLatestMixedSimulation = async () => {
    try {
      // 1. Find the most recent Mixed Strategy run
      const { data: sims, error: simError } = await supabase
        .from('simulation_batch_runs')
        .select('id')
        .eq('agent_strategy', 'Mixed')
        .order('created_at', { ascending: false })
        .limit(1)

      if (simError) throw simError
      
      if (sims && sims.length > 0) {
        const simId = sims[0].id
        setSelectedSimId(simId)
        
        // 2. Fetch time-series data for this simulation
        const { data: timeSeries, error: tsError } = await supabase
          .from('simulation_time_series')
          .select('tick, coop_count, aggressive_count, gini_coefficient')
          .eq('simulation_id', simId)
          .order('tick', { ascending: true })

        if (tsError) throw tsError
        setData(timeSeries || [])
      }
    } catch (error) {
      console.error('Error fetching population dynamics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold">Population Dynamics</h2>
        </div>
        <p className="text-gray-500">Loading latest simulation data...</p>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-indigo-600" />
          <h2 className="text-xl font-bold">Population Dynamics</h2>
        </div>
        <p className="text-gray-500">No mixed-strategy simulation data found.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 col-span-2">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-indigo-600" />
          <div>
            <h2 className="text-xl font-bold">Population Dynamics (Convergence)</h2>
            <p className="text-xs text-gray-500">Latest Mixed Strategy Run | Sim ID: {selectedSimId?.slice(0, 8)}...</p>
          </div>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorCoop" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorAgg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <XAxis dataKey="tick" label={{ value: 'Time (Ticks)', position: 'insideBottom', offset: -5 }} />
          <YAxis label={{ value: 'Population Count', angle: -90, position: 'insideLeft' }} />
          <CartesianGrid strokeDasharray="3 3" />
          <Tooltip />
          <Legend verticalAlign="top" height={36}/>
          <Area 
            type="monotone" 
            dataKey="coop_count" 
            stroke="#10b981" 
            fillOpacity={1} 
            fill="url(#colorCoop)" 
            name="Cooperative Agents"
            stackId="1"
          />
          <Area 
            type="monotone" 
            dataKey="aggressive_count" 
            stroke="#ef4444" 
            fillOpacity={1} 
            fill="url(#colorAgg)" 
            name="Aggressive Agents"
            stackId="1"
          />
        </AreaChart>
      </ResponsiveContainer>
      
      <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-xs text-gray-500">Final Gini Coefficient</p>
          <p className="text-lg font-bold">{data[data.length - 1]?.gini_coefficient.toFixed(3)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Dominant Strategy</p>
          <p className={`text-lg font-bold ${
            data[data.length - 1]?.coop_count > data[data.length - 1]?.aggressive_count 
            ? 'text-green-600' 
            : 'text-red-600'
          }`}>
            {data[data.length - 1]?.coop_count > data[data.length - 1]?.aggressive_count 
              ? 'Cooperative' 
              : 'Aggressive'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Total Population</p>
          <p className="text-lg font-bold">
            {data[data.length - 1]?.coop_count + data[data.length - 1]?.aggressive_count}
          </p>
        </div>
      </div>
    </div>
  )
}

