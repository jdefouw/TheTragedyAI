import LiveMonitor from '@/components/LiveMonitor'
import SurvivalChart from '@/components/SurvivalChart'
import HardwareEfficiency from '@/components/HardwareEfficiency'
import HypothesisWidget from '@/components/HypothesisWidget'
import PopulationDynamics from '@/components/PopulationDynamics'
import EvolutionMonitor from '@/components/EvolutionMonitor'

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Tragedy of the Commons AI
          </h1>
          <p className="text-gray-600">
            Canadian National Science Fair (CWSF) - Grade 8
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Real-time simulation monitoring and analysis dashboard
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2">
             <HypothesisWidget />
          </div>
          <div>
             <EvolutionMonitor />
          </div>
        </div>

        {/* Scientific Validation Section - Full Width */}
        <PopulationDynamics />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <LiveMonitor />
          <HardwareEfficiency />
        </div>

        <SurvivalChart />
      </div>
    </main>
  )
}

