import { useState, useEffect } from 'react'
import { getYoutubeLikes, getInstagramLikes } from '../api'
import VideoCard from '../components/VideoCard'

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

export default function Videos() {
  const [youtube, setYoutube] = useState(null)
  const [instagram, setInstagram] = useState(null)
  const [error, setError] = useState(null)

  async function fetchAll() {
    try {
      const [yt, ig] = await Promise.all([
        getYoutubeLikes(),
        getInstagramLikes(),
      ])
      setYoutube(yt)
      setInstagram(ig)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => clearInterval(id)
  }, [])

  if (error) return <div className="alert alert-error">{error}</div>
  if (!youtube || !instagram) return <div className="loading">Carregando vídeos...</div>

  return (
    <div>
      <div className="page-header">
        <h1>Monitor de Engajamento</h1>
        <div className="page-subtitle">
          Likes em tempo real por plataforma
          <span className="live-badge">
            <span className="live-dot" />
            Live
          </span>
        </div>
      </div>

      <div className="platform-section youtube">
        <div className="platform-title youtube">
          <span className="platform-icon"><YoutubeIcon /></span>
          YouTube
          <span className="platform-total">
            Total: <strong>{youtube.total_likes}</strong> likes
          </span>
        </div>
        <div className="video-grid">
          {Object.entries(youtube.videos || {}).map(([id, likes]) => (
            <VideoCard key={id} videoId={id} likes={likes} platform="youtube" />
          ))}
        </div>
      </div>

      <div className="platform-section instagram">
        <div className="platform-title instagram">
          <span className="platform-icon"><InstagramIcon /></span>
          Instagram
          <span className="platform-total">
            Total: <strong>{instagram.total_likes}</strong> likes
          </span>
        </div>
        <div className="video-grid">
          {Object.entries(instagram.videos || {}).map(([id, likes]) => (
            <VideoCard key={id} videoId={id} likes={likes} platform="instagram" />
          ))}
        </div>
      </div>
    </div>
  )
}
