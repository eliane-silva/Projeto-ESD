import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Campaigns from './pages/Campaigns'
import Flags from './pages/Flags'
import Videos from './pages/Videos'

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/flags" element={<Flags />} />
          <Route path="/videos" element={<Videos />} />
        </Routes>
      </main>
    </div>
  )
}
