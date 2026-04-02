export default function VideoCard({ videoId, likes, platform }) {
  const shortId = videoId.replace(/^(youtube|instagram)_/, '')

  return (
    <div className={`video-card ${platform || ''}`}>
      <div className="video-card-id">{shortId}</div>
      <div className="video-card-likes">{likes}</div>
      <div className="video-card-label">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
        likes
      </div>
    </div>
  )
}
