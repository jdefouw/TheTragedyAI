/**
 * Evolution Monitor component.
 * Visualizes the progress of the Genetic Algorithm (fitness over generations).
 */

'use client'

import { useEffect, useState } from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { supabase } from '../lib/supabase'
import { Dna } from 'lucide-react'

interface GenerationStats {
  id: number
  avg_fitness: number
  best_fitness: number
}

export default function EvolutionMonitor() {
  const [generations, setGenerations] = useState<GenerationStats[]>([])
  const [loading, setLoading] = useState(true)
  const [currentGen, setCurrentGen] = useState<number>(0)

  useEffect(() => {
    fetchGenerations()
    
    // Real-time subscription
    const channel = supabase
      .channel('evolution_monitor')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'simulation_generations' },
        () => fetchGenerations()
      )
      .subscribe()
      
    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  const fetchGenerations = async () => {
    try {
      const { data, error } = await supabase
        .from('simulation_generations')
        .select('id, avg_fitness, best_fitness')
        .order('id', { ascending: true })

      if (error) throw error
      
      if (data) {
        setGenerations(data)
        if (data.length > 0) {
          setCurrentGen(data[data.length - 1].id)
        }
      }
    } catch (error) {
      console.error('Error fetching evolution stats:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Dna className="w-5 h-5 text-purple-600" />
          <h2 className="text-xl font-bold">Evolution Progress</h2>
        </div>
        <p className="text-gray-500">Loading genetic data...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Dna className="w-5 h-5 text-purple-600" />
          <div>
            <h2 className="text-xl font-bold">AI Evolution</h2>
            <p className="text-xs text-gray-500">Current Generation: {currentGen}</p>
          </div>
        </div>
      </div>

      {generations.length === 0 ? (
        <p className="text-gray-500 text-sm">No generations evolved yet.</p>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={generations}>
              <defs>
                <linearGradient id="colorBest" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="id" label={{ value: 'Generation', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Fitness Score', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="best_fitness" 
                stroke="#8b5cf6" 
                fillOpacity={1} 
                fill="url(#colorBest)" 
                name="Best Fitness"
              />
              <Area 
                type="monotone" 
                dataKey="avg_fitness" 
                stroke="#c4b5fd" 
                fillOpacity={0.3} 
                fill="#c4b5fd" 
                name="Avg Fitness"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
      
      <div className="mt-4 grid grid-cols-2 gap-4 text-center text-sm">
        <div className="bg-purple-50 p-2 rounded">
          <p className="text-gray-500">Best Fitness</p>
          <p className="font-bold text-purple-700">
            {generations.length > 0 ? generations[generations.length-1].best_fitness.toFixed(1) : '0.0'}
          </p>
        </div>
        <div className="bg-gray-50 p-2 rounded">
          <p className="text-gray-500">Avg Fitness</p>
          <p className="font-bold text-gray-700">
            {generations.length > 0 ? generations[generations.length-1].avg_fitness.toFixed(1) : '0.0'}
          </p>
        </div>
      </div>
    </div>
  )
}

