import { useState, useEffect } from 'react'
import { listYoutubeVideos, listInstagramVideos, postCampaign } from '../api'

export default function Campaigns() {
  const [platform, setPlatform] = useState('youtube')
  const [videos, setVideos] = useState({ youtube: [], instagram: [] })
  const [contentId, setContentId] = useState('')
  const [actions, setActions] = useState(10)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadVideos() {
      try {
        const [yt, ig] = await Promise.all([
          listYoutubeVideos(),
          listInstagramVideos(),
        ])
        const vids = {
          youtube: yt.videos || [],
          instagram: ig.videos || [],
        }
        setVideos(vids)
        if (vids.youtube.length > 0) {
          setContentId(vids.youtube[0].video_id)
        }
      } catch (e) {
        setError(e.message)
      }
    }
    loadVideos()
  }, [])

  useEffect(() => {
    const list = videos[platform] || []
    if (list.length > 0) {
      setContentId(list[0].video_id)
    } else {
      setContentId('')
    }
  }, [platform, videos])

  useEffect(() => {
    if (!result) return
    const timer = setTimeout(() => setResult(null), 5000)
    return () => clearTimeout(timer)
  }, [result])

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await postCampaign(platform, actions, contentId)
      setResult(res.message)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const currentVideos = videos[platform] || []

  return (
    <div>
      <div className="page-header">
        <h1>Lançar Campanha</h1>
        <div className="page-subtitle">
          Orquestrar engajamento entre plataformas
        </div>
      </div>

      {result && (
        <div className="alert alert-success">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {result}
        </div>
      )}
      {error && (
        <div className="alert alert-error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          {error}
        </div>
      )}

      <div className="form-card">
        <div className={`form-card-accent ${platform}`} />
        <div className="form-card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Plataforma</label>
              <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
              </select>
            </div>

            <div className="form-group">
              <label>Vídeo</label>
              <select
                className="mono"
                value={contentId}
                onChange={(e) => setContentId(e.target.value)}
              >
                {currentVideos.map((v) => (
                  <option key={v.video_id} value={v.video_id}>
                    {v.video_id} — {v.likes} likes
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Número de ações</label>
              <input
                className="mono"
                type="number"
                min="1"
                max="1000"
                value={actions}
                onChange={(e) => setActions(Number(e.target.value))}
              />
            </div>

            <button
              type="submit"
              className={`btn btn-${platform}`}
              disabled={loading || !contentId}
            >
              {loading ? 'Enviando...' : 'Lançar Campanha'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
