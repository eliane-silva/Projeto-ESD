const SCHEDULER = '/api/scheduler'
const YOUTUBE = '/api/youtube'
const INSTAGRAM = '/api/instagram'
const MONITORING = '/api/monitoring'

async function request(url, options = {}) {
  const res = await fetch(url, options)
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || res.statusText)
  }
  return res.json()
}

// --- Monitoring ---

export function getMetrics(platform) {
  return request(`${MONITORING}/metrics/${platform}`)
}

// --- Scheduler: Campaigns ---

export function postCampaign(platform, actions, contentId) {
  return request(
    `${SCHEDULER}/post_campaign?platform=${platform}&actions=${actions}&content_id=${contentId}`,
    { method: 'POST' }
  )
}

// --- Scheduler: Flags ---

export function getFlag(flag) {
  return request(`${SCHEDULER}/get_flag?flag=${flag}`)
}

export function toggleFlag(flag) {
  return request(`${SCHEDULER}/alt_flag?flag=${flag}`, { method: 'POST' })
}

// --- Scheduler: Pause Time ---

export function getPauseTime() {
  return request(`${SCHEDULER}/get_pause_time`)
}

export function setPauseTime(time) {
  return request(`${SCHEDULER}/set_pause_time?time=${time}`, { method: 'POST' })
}

// --- Mock YouTube ---

export function listYoutubeVideos() {
  return request(`${YOUTUBE}/list_videos`)
}

export function getYoutubeLikes() {
  return request(`${YOUTUBE}/get_likes`)
}

// --- Mock Instagram ---

export function listInstagramVideos() {
  return request(`${INSTAGRAM}/list_videos`)
}

export function getInstagramLikes() {
  return request(`${INSTAGRAM}/get_likes`)
}
