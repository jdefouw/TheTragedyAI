/**
 * Hypothesis status widget with P-value calculation
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import { supabase, SimulationBatchRun } from './supabase'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'

interface HypothesisStatus {
  confirmed: boolean | null
  pValue: number | null
  message: string
  threshold: number
}

export default function HypothesisWidget() {
  const [status, setStatus] = useState<HypothesisStatus>({
    confirmed: null,
    pValue: null,
    message: 'Calculating...',
    threshold: 0.05,
  })
  const [loading, setLoading] = useState(true)

  const calculateHypothesis = useCallback(async () => {
    try {
      const { data: runs, error } = await supabase
        .from('simulation_batch_runs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(1000)

      if (error) throw error

      // Filter for low resource density (< 20%)
      const lowDensityRuns = runs?.filter(
        (run: SimulationBatchRun) => run.resource_density < 0.20
      ) || []

      // Separate by strategy
      const cooperative = lowDensityRuns
        .filter((r: SimulationBatchRun) => r.agent_strategy.includes('Cooperative'))
        .map((r: SimulationBatchRun) => r.total_ticks_survived)

      const aggressive = lowDensityRuns
        .filter((r: SimulationBatchRun) => r.agent_strategy.includes('Aggressive'))
        .map((r: SimulationBatchRun) => r.total_ticks_survived)

      if (cooperative.length < 10 || aggressive.length < 10) {
        setStatus({
          confirmed: null,
          pValue: null,
          message: 'Insufficient data. Need at least 10 runs per strategy.',
          threshold: 0.05,
        })
        setLoading(false)
        return
      }

      // Simple t-test approximation (Welch's t-test)
      const coopMean = cooperative.reduce((a, b) => a + b, 0) / cooperative.length
      const aggMean = aggressive.reduce((a, b) => a + b, 0) / aggressive.length

      const coopVar =
        cooperative.reduce((sum, x) => sum + Math.pow(x - coopMean, 2), 0) /
        (cooperative.length - 1)
      const aggVar =
        aggressive.reduce((sum, x) => sum + Math.pow(x - aggMean, 2), 0) /
        (aggressive.length - 1)

      const se = Math.sqrt(coopVar / cooperative.length + aggVar / aggressive.length)
      const tStat = (coopMean - aggMean) / se

      // Approximate p-value (two-tailed, simplified)
      // For large samples, t ~ normal, so we use z-test approximation
      const pValue = 2 * (1 - normalCDF(Math.abs(tStat)))

      const confirmed = pValue < 0.05 && coopMean > aggMean
      const message = confirmed
        ? `Hypothesis CONFIRMED: Cooperative strategy shows significantly higher survival (p < 0.05)`
        : pValue < 0.05
        ? `Hypothesis REFUTED: No significant difference or opposite effect (p < 0.05)`
        : `Insufficient evidence: p = ${pValue.toFixed(3)} (need p < 0.05)`

      setStatus({
        confirmed,
        pValue,
        message,
        threshold: 0.05,
      })
    } catch (error) {
      console.error('Error calculating hypothesis:', error)
      setStatus({
        confirmed: null,
        pValue: null,
        message: 'Error calculating hypothesis status',
        threshold: 0.05,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    calculateHypothesis()
  }, [calculateHypothesis])

  // Normal CDF approximation
  const normalCDF = (x: number): number => {
    return 0.5 * (1 + erf(x / Math.sqrt(2)))
  }

  // Error function approximation
  const erf = (x: number): number => {
    const a1 = 0.254829592
    const a2 = -0.284496736
    const a3 = 1.421413741
    const a4 = -1.453152027
    const a5 = 1.061405429
    const p = 0.3275911

    const sign = x < 0 ? -1 : 1
    x = Math.abs(x)

    const t = 1.0 / (1.0 + p * x);
    const poly = (((a5 * t + a4) * t + a3) * t + a2) * t + a1;
    const y = 1.0 - poly * t * Math.exp(-x * x);

    return sign * y;
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Hypothesis Status</h2>
        <p className="text-gray-500">Calculating...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Hypothesis Status</h2>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          {status.confirmed === true && (
            <CheckCircle className="w-8 h-8 text-green-600" />
          )}
          {status.confirmed === false && (
            <XCircle className="w-8 h-8 text-red-600" />
          )}
          {status.confirmed === null && (
            <AlertCircle className="w-8 h-8 text-yellow-600" />
          )}
          <div>
            <p className="font-semibold text-lg">
              {status.confirmed === true
                ? 'HYPOTHESIS: CONFIRMED'
                : status.confirmed === false
                ? 'HYPOTHESIS: REFUTED'
                : 'HYPOTHESIS: INSUFFICIENT DATA'}
            </p>
            <p className="text-sm text-gray-600 mt-1">{status.message}</p>
          </div>
        </div>
        {status.pValue !== null && (
          <div className="bg-gray-50 p-3 rounded">
            <p className="text-sm">
              <span className="font-semibold">P-Value:</span> {status.pValue.toFixed(4)}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              Threshold: {status.threshold} (α = 0.05)
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

