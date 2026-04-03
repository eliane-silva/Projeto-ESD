import { useState, useEffect, useRef } from 'react'
import { getMetrics } from '../api'
import MetricCard from '../components/MetricCard'

const REFRESH_INTERVAL = 5000

const YoutubeIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--youtube)">
    <path d="M23.5 6.19a3.02 3.02 0 0 0-2.12-2.14C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.38.55A3.02 3.02 0 0 0 .5 6.19 31.6 31.6 0 0 0 0 12a31.6 31.6 0 0 0 .5 5.81 3.02 3.02 0 0 0 2.12 2.14c1.88.55 9.38.55 9.38.55s7.5 0 9.38-.55a3.02 3.02 0 0 0 2.12-2.14A31.6 31.6 0 0 0 24 12a31.6 31.6 0 0 0-.5-5.81zM9.75 15.02V8.98L15.5 12l-5.75 3.02z"/>
  </svg>
)

const InstagramIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--instagram)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="20" rx="5" />
    <circle cx="12" cy="12" r="5" />
    <circle cx="17.5" cy="6.5" r="1.5" fill="var(--instagram)" stroke="none" />
  </svg>
)

export default function Dashboard() {
  const [youtube, setYoutube] = useState(null)
  const [instagram, setInstagram] = useState(null)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const intervalRef = useRef(null)

  async function fetchAll() {
    try {
      const [yt, ig] = await Promise.all([
        getMetrics('youtube'),
        getMetrics('instagram'),
      ])
      setYoutube(yt)
      setInstagram(ig)
      setError(null)
      setLastUpdate(new Date())
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    fetchAll()
    intervalRef.current = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => clearInterval(intervalRef.current)
  }, [])

  function timeAgo() {
    if (!lastUpdate) return ''
    const secs = Math.floor((Date.now() - lastUpdate.getTime()) / 1000)
    if (secs < 5) return 'agora'
    return `${secs}s atrás`
  }

  if (error) return <div className="alert alert-error">{error}</div>
  if (!youtube || !instagram) return <div className="loading">Carregando métricas...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <div className="page-subtitle">
          Métricas do sistema em tempo real
          <span className="live-badge">
            <span className="live-dot" />
            Live
          </span>
          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {timeAgo()}
          </span>
        </div>
      </div>

      <PlatformMetrics
        title="YouTube"
        icon={<YoutubeIcon />}
        data={youtube}
        platform="youtube"
      />
      <PlatformMetrics
        title="Instagram"
        icon={<InstagramIcon />}
        data={instagram}
        platform="instagram"
      />
    </div>
  )
}

function PlatformMetrics({ title, icon, data, platform }) {
  return (
    <div className={`platform-section ${platform}`}>
      <div className={`platform-title ${platform}`}>
        <span className="platform-icon">{icon}</span>
        {title}
      </div>

      <h2>Ações</h2>
      <div className="cards-grid">
        <MetricCard label="Total" value={data.total} />
        <MetricCard label="Sucesso" value={data.success} variant="success" />
        <MetricCard label="Erros" value={data.errors} variant="danger" />
        <MetricCard label="Bloqueados" value={data.blocked} variant="warning" />
      </div>

      <h2>Taxas</h2>
      <div className="cards-grid">
        <MetricCard label="Taxa de Sucesso" value={data.success_rate} variant="success" showBar />
        <MetricCard label="Taxa de Erro" value={data.error_rate} variant="danger" showBar />
        <MetricCard label="Taxa de Bloqueio" value={data.block_rate} variant="warning" showBar />
      </div>

      <h2>Eventos</h2>
      <div className="cards-grid">
        <MetricCard label="Bloqueios" value={data.events.block_events} variant="warning" />
        <MetricCard label="Rate Increase" value={data.events.rate_increase} variant="success" />
        <MetricCard label="Rate Decrease" value={data.events.rate_decrease} variant="danger" />
      </div>
    </div>
  )
}
