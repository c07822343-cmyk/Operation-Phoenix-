const CATEGORY_COLORS = {
  animal: '#00c853', space: '#2196f3', history: '#ff9800',
  science: '#9c27b0', body: '#f44336', food: '#ff5722',
  technology: '#00bcd4', psychology: '#e91e63',
  geography: '#8bc34a', culture: '#ffc107',
  facts: '#ff4444', crime: '#424242', custom: '#607d8b'
}

let pollInterval = null
let knownVideos = new Set()
let currentFilter = 'all'
let currentCount = 10

document.addEventListener('DOMContentLoaded', () => {
  loadKeys()
  checkExistingProgress()
})

function updateSlider(val) {
  currentCount = parseInt(val)
  document.getElementById('count-display').textContent = val
  document.getElementById('generate-btn').textContent =
    `GENERATE ${val} VIDEOS`
  const times = { 5: '~5 min', 10: '~10 min', 25: '~20 min' }
  let t = '~35 min'
  if (currentCount <= 5) t = '~5 min'
  else if (currentCount <= 10) t = '~10 min'
  else if (currentCount <= 25) t = '~20 min'
  document.getElementById('time-estimate').textContent = t
}

function toggleShow(btn) {
  const row = btn.parentElement
  const input = row.querySelector('input')
  if (input.type === 'password') {
    input.type = 'text'
    btn.textContent = 'Hide'
  } else {
    input.type = 'password'
    btn.textContent = 'Show'
  }
}

function saveKeys() {
  const groq = document.getElementById('groq-key').value.trim()
  const pexels = document.getElementById('pexels-key').value.trim()
  const pixabay = document.getElementById('pixabay-key').value.trim()

  fetch('/api/save-keys', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      groq_key: groq,
      pexels_key: pexels,
      pixabay_key: pixabay
    })
  }).then(() => {
    const confirm = document.getElementById('save-confirm')
    confirm.style.display = 'inline'
    setTimeout(() => { confirm.style.display = 'none' }, 2000)
    showToast('Keys saved', 'success')
    setTimeout(validateKeys, 600)
  })
}

function loadKeys() {
  fetch('/api/load-keys')
    .then(r => r.json())
    .then(data => {
      if (data.groq_key) document.getElementById('groq-key').value = data.groq_key
      if (data.pexels_key) document.getElementById('pexels-key').value = data.pexels_key
      if (data.pixabay_key) document.getElementById('pixabay-key').value = data.pixabay_key
      if (data.groq_key || data.pexels_key || data.pixabay_key) {
        setTimeout(validateKeys, 800)
      }
    })
    .catch(() => {})
}

function validateKeys() {
  fetch('/api/validate-keys')
    .then(r => r.json())
    .then(data => {
      const map = { groq: 'dot-groq', pexels: 'dot-pexels', pixabay: 'dot-pixabay' }
      for (const [key, dotId] of Object.entries(map)) {
        const dot = document.getElementById(dotId)
        if (!dot) continue
        dot.className = 'dot'
        if (data[key] === 'valid') dot.classList.add('valid')
        else if (data[key] === 'invalid') dot.classList.add('invalid')
      }
    })
    .catch(() => {})
}

function generateVideos() {
  const groq = document.getElementById('groq-key').value.trim()
  if (!groq) {
    const err = document.getElementById('generate-error')
    err.textContent = 'Groq API key is required. Get your free key at console.groq.com'
    err.style.display = 'block'
    document.getElementById('keys-card').scrollIntoView({ behavior: 'smooth' })
    return
  }

  document.getElementById('generate-error').style.display = 'none'

  const niche = document.getElementById('niche-input').value.trim() || 'random mind-blowing facts'
  const tone = document.getElementById('tone-select').value
  const audience = document.getElementById('audience-select').value
  const refsRaw = document.getElementById('references-input').value
  const reference_urls = refsRaw.split('\n').map(s => s.trim()).filter(Boolean)
  const styleCheckboxes = document.querySelectorAll('#style-types input[type="checkbox"]:checked')
  const style_types = Array.from(styleCheckboxes).map(c => c.value)
  const enable_evasion = document.getElementById('evasion-toggle').checked

  const btn = document.getElementById('generate-btn')
  btn.disabled = true
  btn.textContent = 'Factory Running...'

  fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      count: currentCount,
      groq_key: groq,
      pexels_key: document.getElementById('pexels-key').value.trim(),
      pixabay_key: document.getElementById('pixabay-key').value.trim(),
      niche, tone, audience, reference_urls,
      style_types, enable_evasion
    })
  })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        const err = document.getElementById('generate-error')
        err.textContent = data.error
        err.style.display = 'block'
        btn.disabled = false
        btn.textContent = `GENERATE ${currentCount} VIDEOS`
        showToast(data.error, 'error')
        return
      }
      document.getElementById('progress-card').style.display = 'block'
      document.getElementById('progress-card').scrollIntoView({ behavior: 'smooth' })
      startPolling()
    })
    .catch(e => {
      btn.disabled = false
      btn.textContent = `GENERATE ${currentCount} VIDEOS`
      showToast('Network error. Is Phoenix running?', 'error')
    })
}

function startPolling() {
  if (pollInterval) clearInterval(pollInterval)
  pollInterval = setInterval(fetchProgress, 2000)
}

function fetchProgress() {
  fetch('/api/progress')
    .then(r => r.json())
    .then(data => updateUI(data))
    .catch(() => {})
}

function updateUI(data) {
  for (let i = 1; i <= 7; i++) {
    const icon = document.getElementById(`icon-${i}`)
    const status = document.getElementById(`status-${i}`)
    const row = document.getElementById(`phase-${i}`)
    if (!icon) continue

    icon.className = 'phase-icon'
    if (i < data.phase) {
      icon.textContent = '✓'
      icon.classList.add('done')
      if (status) status.textContent = 'Done'
      if (row) row.classList.remove('active-row')
    } else if (i === data.phase) {
      icon.textContent = '●'
      icon.classList.add('active')
      if (status) status.textContent = 'Running'
      if (row) row.classList.add('active-row')
    } else {
      icon.textContent = '○'
      if (status) status.textContent = 'Waiting'
      if (row) row.classList.remove('active-row')
    }
  }

  const fill = document.getElementById('overall-fill')
  if (fill) fill.style.width = (data.percent || 0) + '%'

  const counter = document.getElementById('video-counter')
  if (counter) counter.textContent = `Video ${data.current_video} of ${data.total_videos}`

  const eta = document.getElementById('eta-display')
  if (eta) {
    if (data.eta_seconds > 120) eta.textContent = Math.ceil(data.eta_seconds / 60) + ' min remaining'
    else if (data.eta_seconds > 0) eta.textContent = data.eta_seconds + ' sec remaining'
    else eta.textContent = ''
  }

  const stats = document.getElementById('stats-display')
  if (stats) stats.textContent = `Done: ${data.successful} | Failed: ${data.failed}`

  for (const video of (data.videos || [])) {
    if (!knownVideos.has(video.number)) {
      knownVideos.add(video.number)
      addVideoCard(video)
    } else {
      updateVideoCard(video)
    }
  }

  if (data.done) {
    if (pollInterval) clearInterval(pollInterval)
    document.getElementById('results-card').style.display = 'block'
    document.getElementById('results-card').scrollIntoView({ behavior: 'smooth' })
    updateResultsStats(data)
    const btn = document.getElementById('generate-btn')
    btn.disabled = false
    btn.textContent = `GENERATE ${currentCount} VIDEOS`
    showToast('Your videos are ready!', 'success')
  }

  if (data.error && data.error.length > 0 && data.done) {
    if (pollInterval) clearInterval(pollInterval)
    showToast(data.error, 'error')
    const btn = document.getElementById('generate-btn')
    btn.disabled = false
    btn.textContent = `GENERATE ${currentCount} VIDEOS`
  }
}

function addVideoCard(video) {
  const grid = document.getElementById('videos-grid')
  if (!grid) return

  const color = CATEGORY_COLORS[video.category] || '#607d8b'
  const numStr = String(video.number).padStart(3, '0')
  const title = (video.title || '').substring(0, 60)

  let statusHtml = ''
  if (video.status === 'processing') {
    statusHtml = `<div class="vc-status processing">⟳ Processing...</div>`
  } else if (video.status === 'done') {
    statusHtml = `<div class="vc-status done">✓ Done</div>
    <div class="vc-actions">
      <button class="btn-dl" onclick="downloadVideo(${video.number})">⬇ Video</button>
      <button class="btn-dl" onclick="downloadThumbnail(${video.number})">⬇ Thumb</button>
    </div>`
  } else if (video.status === 'failed') {
    statusHtml = `<div class="vc-status failed">✗ Failed: ${video.error || ''}</div>`
  }

  const card = document.createElement('div')
  card.className = `video-card ${video.status}`
  card.dataset.status = video.status
  card.dataset.number = video.number
  card.dataset.category = video.category

  card.innerHTML = `
    <div class="vc-top">
      <span class="vc-num">#${numStr}</span>
      <span class="vc-badge" style="background:${color}20;color:${color}">${video.category}</span>
    </div>
    <p class="vc-topic">${video.topic || ''}</p>
    <p class="vc-title">${title}</p>
    ${statusHtml}
  `

  if (currentFilter !== 'all' && video.status !== currentFilter) {
    card.style.display = 'none'
  }

  grid.appendChild(card)
}

function updateVideoCard(video) {
  const card = document.querySelector(`[data-number="${video.number}"]`)
  if (!card) return

  card.dataset.status = video.status
  card.className = `video-card ${video.status}`

  let statusHtml = ''
  if (video.status === 'processing') {
    statusHtml = `<div class="vc-status processing">⟳ Processing...</div>`
  } else if (video.status === 'done') {
    statusHtml = `<div class="vc-status done">✓ Done</div>
    <div class="vc-actions">
      <button class="btn-dl" onclick="downloadVideo(${video.number})">⬇ Video</button>
      <button class="btn-dl" onclick="downloadThumbnail(${video.number})">⬇ Thumb</button>
    </div>`
  } else if (video.status === 'failed') {
    statusHtml = `<div class="vc-status failed">✗ Failed: ${video.error || ''}</div>`
  }

  const existing = card.querySelector('.vc-status, .vc-actions')
  if (existing) existing.remove()
  const actionsExisting = card.querySelector('.vc-actions')
  if (actionsExisting) actionsExisting.remove()

  card.insertAdjacentHTML('beforeend', statusHtml)

  if (currentFilter !== 'all' && video.status !== currentFilter) {
    card.style.display = 'none'
  } else {
    card.style.display = ''
  }
}

function updateResultsStats(data) {
  const el = document.getElementById('results-stats')
  if (!el) return
  el.innerHTML = `
    <div class="stat-box">
      <span class="stat-num" style="color:#2196f3">${data.total_videos}</span>
      <span class="stat-lbl">Total Videos</span>
    </div>
    <div class="stat-box">
      <span class="stat-num" style="color:#00c853">${data.successful}</span>
      <span class="stat-lbl">Successful</span>
    </div>
    <div class="stat-box">
      <span class="stat-num" style="color:#ff4444">${data.failed}</span>
      <span class="stat-lbl">Failed</span>
    </div>
    <div class="stat-box">
      <span class="stat-num" style="color:#ffd700">$0.00</span>
      <span class="stat-lbl">Total Cost</span>
    </div>
  `
}

function downloadVideo(number) {
  window.location.href = '/api/download/video/' + number
}

function downloadThumbnail(number) {
  window.location.href = '/api/download/thumbnail/' + number
}

function downloadAll() {
  window.location.href = '/api/download/all'
}

function downloadSchedule() {
  fetch('/api/schedule')
    .then(r => r.json())
    .then(data => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'upload_schedule.json'
      a.click()
      URL.revokeObjectURL(url)
    })
}

function filterVideos(status) {
  currentFilter = status
  document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'))
  const tab = document.getElementById('filter-' + status)
  if (tab) tab.classList.add('active')

  document.querySelectorAll('.video-card').forEach(card => {
    if (status === 'all' || card.dataset.status === status) {
      card.style.display = ''
    } else {
      card.style.display = 'none'
    }
  })
}

function showToast(msg, type = 'info') {
  const toast = document.getElementById('toast')
  if (!toast) return
  toast.textContent = msg
  toast.className = `toast ${type}`
  setTimeout(() => { toast.className = 'toast hidden' }, 3500)
}

function checkExistingProgress() {
  fetch('/api/progress')
    .then(r => r.json())
    .then(data => {
      if (data.running) {
        document.getElementById('progress-card').style.display = 'block'
        startPolling()
      } else if (data.done && data.videos && data.videos.length > 0) {
        for (const v of data.videos) {
          knownVideos.add(v.number)
          addVideoCard(v)
        }
        document.getElementById('results-card').style.display = 'block'
        updateResultsStats(data)
      }
    })
    .catch(() => {})
}
