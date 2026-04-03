import { useState, useEffect } from 'react'
import { getFlag, toggleFlag, getPauseTime, setPauseTime } from '../api'

const FLAG_GROUPS = [
  {
    label: 'Controle de Taxa',
    flags: [
      {
        key: 'threshold',
        label: 'Threshold Adaptativo',
        desc: 'Ajuste automático do rate limit com base no feedback dos workers',
        icon: (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 20v-6M6 20V10M18 20V4" />
          </svg>
        ),
      },
      {
        key: 'dynamic_distribution',
        label: 'Distribuição Dinâmica',
        desc: 'Distribuição ponderada de campanhas entre plataformas',
        icon: (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="16 3 21 3 21 8" />
            <line x1="4" y1="20" x2="21" y2="3" />
            <polyline points="21 16 21 21 16 21" />
            <line x1="15" y1="15" x2="21" y2="21" />
            <line x1="4" y1="4" x2="9" y2="9" />
          </svg>
        ),
      },
    ],
  },
  {
    label: 'Resiliência',
    flags: [
      {
        key: 'jitter',
        label: 'Jitter',
        desc: 'Variação aleatória no tempo entre requests para evitar padrões',
        icon: (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 12h2l3-9 4 18 3-9h2" />
            <path d="M18 12h4" />
          </svg>
        ),
      },
      {
        key: 'circuit_breaker',
        label: 'Circuit Breaker',
        desc: 'Pausa exponencial após rate limits consecutivos',
        icon: (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        ),
      },
    ],
  },
]

export default function Flags() {
  const [values, setValues] = useState({})
  const [toggling, setToggling] = useState(null)
  const [pauseTime, setPauseTimeVal] = useState('')
  const [pauseLoading, setPauseLoading] = useState(false)

  useEffect(() => {
    async function load() {
      const allFlags = FLAG_GROUPS.flatMap((g) => g.flags)
      const results = await Promise.all(
        allFlags.map(async (f) => {
          try {
            const val = await getFlag(f.key)
            return [f.key, val === 1]
          } catch {
            return [f.key, false]
          }
        })
      )
      setValues(Object.fromEntries(results))

      try {
        const pt = await getPauseTime()
        setPauseTimeVal(String(pt))
      } catch {}
    }
    load()
  }, [])

  async function handleToggle(key) {
    setToggling(key)
    try {
      await toggleFlag(key)
      setValues((prev) => ({ ...prev, [key]: !prev[key] }))
    } catch (e) {
      console.error('Failed to toggle flag', e)
    } finally {
      setToggling(null)
    }
  }

  async function handlePauseTime() {
    const val = parseInt(pauseTime, 10)
    if (isNaN(val) || val < 1) return
    setPauseLoading(true)
    try {
      await setPauseTime(val)
    } catch (e) {
      console.error('Failed to set pause time', e)
    } finally {
      setPauseLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Controles do Sistema</h1>
        <div className="page-subtitle">
          Feature flags para comportamento distribuído
        </div>
      </div>

      {FLAG_GROUPS.map((group) => (
        <div key={group.label} className="flag-group">
          <div className="flag-group-label">{group.label}</div>
          {group.flags.map((f) => {
            const isOn = values[f.key] || false
            return (
              <div key={f.key} className={`toggle-row ${isOn ? 'active' : ''}`}>
                <div className="toggle-info">
                  <div className="toggle-icon">{f.icon}</div>
                  <div>
                    <div className="toggle-label">{f.label}</div>
                    <div className="toggle-desc">{f.desc}</div>
                  </div>
                </div>
                <div className="toggle-right">
                  <span className={`status-chip ${isOn ? 'on' : 'off'}`}>
                    {isOn ? 'Ativo' : 'Inativo'}
                  </span>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={isOn}
                      onChange={() => handleToggle(f.key)}
                      disabled={toggling === f.key}
                    />
                    <span className="toggle-slider" />
                  </label>
                </div>
              </div>
            )
          })}
        </div>
      ))}

      <div className="config-section">
        <h2>Configuração do Circuit Breaker</h2>
        <div className="config-row">
          <input
            type="number"
            min="1"
            value={pauseTime}
            onChange={(e) => setPauseTimeVal(e.target.value)}
            placeholder="64"
          />
          <button
            className="btn btn-primary"
            onClick={handlePauseTime}
            disabled={pauseLoading}
          >
            {pauseLoading ? 'Salvando...' : 'Salvar'}
          </button>
          <span className="config-hint">Tempo máximo de pausa (segundos)</span>
        </div>
      </div>
    </div>
  )
}
