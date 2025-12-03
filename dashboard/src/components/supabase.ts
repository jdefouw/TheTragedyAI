/**
 * Supabase client configuration
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase credentials not configured. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Type definitions for database tables
export interface SimulationBatchRun {
  id: string
  created_at: string
  machine_id: string
  agent_strategy: string
  resource_density: number
  total_ticks_survived: number
  avg_agent_energy: number
  simulation_version: string
}

export interface HumanMatch {
  id: string
  created_at: string
  player_name: string
  human_survival_time: number
  ai_average_survival_time: number
  winner: string
  difficulty_level: string
}
