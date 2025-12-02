/**
 * Hardware efficiency chart showing simulations per hour by GPU type
 */

'use client'

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { supabase, SimulationBatchRun } from '@/lib/supabase'
import { Cpu } from 'lucide-react'

interface EfficiencyData {
  machine: string
  simulations: number
  avg_survival: number
}

export default function HardwareEfficiency() {
  const [data, setData] = useState<EfficiencyData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const { data: runs, error } = await supabase
        .from('simulation_batch_runs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(5000)

      if (error) throw error

      // Group by machine and calculate efficiency
      const machineStats: Record<string, { count: number, total_survival: number, timestamps: string[] }> = {}

      runs?.forEach((run: SimulationBatchRun) => {
        const machine = run.machine_id
        if (!machineStats[machine]) {
          machineStats[machine] = { count: 0, total_survival: 0, timestamps: [] }
        }
        machineStats[machine].count += 1
        machineStats[machine].total_survival += run.total_ticks_survived
        machineStats[machine].timestamps.push(run.created_at)
      })

      // Calculate simulations per hour
      const efficiencyData: EfficiencyData[] = Object.entries(machineStats).map(([machine, stats]) => {
        // Calculate time span
        const timestamps = stats.timestamps.map(t => new Date(t).getTime()).sort()
        const timeSpanHours = timestamps.length > 1
          ? (timestamps[timestamps.length - 1] - timestamps[0]) / (1000 * 60 * 60)
          : 1

        const simulationsPerHour = timeSpanHours > 0 ? stats.count / timeSpanHours : stats.count
        const avgSurvival = stats.total_survival / stats.count

        return {
          machine,
          simulations: Math.round(simulationsPerHour),
          avg_survival: Math.round(avgSurvival),
        }
      })

      setData(efficiencyData.sort((a, b) => b.simulations - a.simulations))
    } catch (error) {
      console.error('Error fetching efficiency data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-5 h-5 text-purple-600" />
          <h2 className="text-xl font-bold">Hardware Efficiency</h2>
        </div>
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <Cpu className="w-5 h-5 text-purple-600" />
        <h2 className="text-xl font-bold">Hardware Efficiency</h2>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="machine" />
          <YAxis
            label={{ value: 'Simulations per Hour', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip />
          <Legend />
          <Bar dataKey="simulations" fill="#8b5cf6" name="Simulations/Hour" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

