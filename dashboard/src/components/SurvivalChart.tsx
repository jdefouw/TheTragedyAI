/**
 * Survival chart comparing Cooperative vs Aggressive strategies
 */

'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { supabase, SimulationBatchRun } from './supabase'
import { TrendingUp } from 'lucide-react'

interface ChartData {
  density: number
  cooperative: number | null
  aggressive: number | null
}

export default function SurvivalChart() {
  const [data, setData] = useState<ChartData[]>([])
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
        .limit(1000)

      if (error) throw error

      // Group by resource density and strategy
      const grouped: Record<number, { cooperative: number[], aggressive: number[] }> = {}

      runs?.forEach((run: SimulationBatchRun) => {
        const density = run.resource_density
        if (!grouped[density]) {
          grouped[density] = { cooperative: [], aggressive: [] }
        }

        if (run.agent_strategy.includes('Cooperative')) {
          grouped[density].cooperative.push(run.total_ticks_survived)
        } else if (run.agent_strategy.includes('Aggressive')) {
          grouped[density].aggressive.push(run.total_ticks_survived)
        }
      })

      // Calculate averages
      const chartData: ChartData[] = Object.keys(grouped)
        .map(Number)
        .sort()
        .map((density) => {
          const group = grouped[density]
          const coopAvg = group.cooperative.length > 0
            ? group.cooperative.reduce((a, b) => a + b, 0) / group.cooperative.length
            : null
          const aggAvg = group.aggressive.length > 0
            ? group.aggressive.reduce((a, b) => a + b, 0) / group.aggressive.length
            : null

          return {
            density: density * 100, // Convert to percentage
            cooperative: coopAvg,
            aggressive: aggAvg,
          }
        })

      setData(chartData)
    } catch (error) {
      console.error('Error fetching chart data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-green-600" />
          <h2 className="text-xl font-bold">Survival Comparison</h2>
        </div>
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-green-600" />
        <h2 className="text-xl font-bold">Survival Comparison</h2>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="density"
            label={{ value: 'Resource Density (%)', position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            label={{ value: 'Average Survival Time (ticks)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="cooperative"
            stroke="#10b981"
            strokeWidth={2}
            name="Cooperative Strategy"
            dot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="aggressive"
            stroke="#ef4444"
            strokeWidth={2}
            name="Aggressive Strategy"
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

