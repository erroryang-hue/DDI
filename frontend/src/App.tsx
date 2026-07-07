import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Dashboard from './pages/Dashboard'
import InteractionAnalysis from './pages/InteractionAnalysis'
import Polypharmacy from './pages/Polypharmacy'
import DrugSearch from './pages/DrugSearch'
import GraphExplorer from './pages/GraphExplorer'
import Recommendations from './pages/Recommendations'
import Analytics from './pages/Analytics'
import NotFound from './pages/NotFound'

const routeTitle: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/analysis': 'Interaction Analysis',
  '/polypharmacy': 'Polypharmacy',
  '/search': 'Drug Search',
  '/graph': 'Graph Explorer',
  '/recommendations': 'Recommendations',
  '/analytics': 'Analytics',
}

function Content() {
  const location = useLocation()
  const title = routeTitle[location.pathname] || 'DDI Intelligence'

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="content-area">
        <Topbar title={title} />
        <main className="content-panel">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analysis" element={<InteractionAnalysis />} />
            <Route path="/polypharmacy" element={<Polypharmacy />} />
            <Route path="/search" element={<DrugSearch />} />
            <Route path="/graph" element={<GraphExplorer />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Content />
    </BrowserRouter>
  )
}
