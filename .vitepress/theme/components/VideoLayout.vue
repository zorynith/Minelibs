<template>
  <div class="video-app">
    <!-- 毛玻璃导航栏 -->
    <header class="glass-navbar">
      <button class="nav-back" @click="goBack">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor"/>
        </svg>
      </button>
      <div class="nav-logo">
        <img src="https://minelibs.eu.org/Minelibs.png" alt="Logo">
      </div>
      <div class="nav-placeholder"></div>
    </header>

    <!-- 视频卡片区域（粘性） -->
    <section class="video-card" ref="videoCard">
      <div class="video-container">
        <!-- 16:9 视频包装器 -->
        <div class="video-wrapper" :class="{ 'ratio-fixed': !videoMeta.ready }">
          <!-- 加载动画 -->
          <div v-if="!videoMeta.ready || videoMeta.buffering" class="video-overlay loading-overlay">
            <div class="spinner"></div>
          </div>
          <!-- 错误提示 -->
          <div v-if="videoMeta.error" class="video-overlay error-overlay">
            <span>视频加载失败</span>
          </div>
          <video
            ref="videoPlayer"
            class="video-element"
            :src="currentSource.url"
            preload="metadata"
            @timeupdate="onProgress"
            @loadedmetadata="onMetaLoad"
            @loadeddata="onDataLoad"
            @waiting="onWait"
            @playing="onPlay"
            @error="onFail"
            @dblclick="togglePlayback"
            @mousedown="startLongPress"
            @mouseup="endLongPress"
            @mouseleave="cancelLongPress"
            @click="handleClick"
          ></video>
        </div>

        <!-- 控制栏（毛玻璃效果） -->
        <Transition name="fade">
          <div v-if="panelVisible" class="control-bar" @mousedown.stop>
            <!-- 进度条 -->
            <div class="progress-area" @mousedown="startSeek">
              <div class="progress-track">
                <div class="buffer-progress" :style="{ width: bufferPercent + '%' }"></div>
                <div class="play-progress" :style="{ width: playPercent + '%' }"></div>
                <div
                  class="progress-thumb"
                  :class="{ dragging: seekActive }"
                  :style="{ left: playPercent + '%' }"
                  @mousedown.stop="startSeek"
                ></div>
              </div>
            </div>

            <!-- 控制按钮组 -->
            <div class="control-group">
              <!-- 播放/暂停 -->
              <button
                class="control-btn play-btn"
                @click="togglePlayback"
                @mouseenter="playHover = true"
                @mouseleave="playHover = false"
              >
                <svg v-if="videoMeta.paused" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M8 5v14l11-7z" fill="currentColor" :class="{ 'hover-blue': playHover }"/>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <rect x="6" y="5" width="4" height="14" fill="currentColor" :class="{ 'hover-blue': playHover }"/>
                  <rect x="14" y="5" width="4" height="14" fill="currentColor" :class="{ 'hover-blue': playHover }"/>
                </svg>
              </button>

              <span class="time-display">{{ formatTime(currentPos) }} / {{ formatTime(totalDuration) }}</span>

              <div class="flex-spacer"></div>

              <!-- 倍速菜单 -->
              <div class="menu-wrapper" ref="speedMenu">
                <button
                  class="menu-trigger"
                  :class="{ active: speedHover && !speedClick, clicked: speedClick }"
                  @click="toggleSpeedMenu"
                  @mouseenter="speedHover = true"
                  @mouseleave="speedHover = false"
                  @mousedown="onSpeedPress"
                >
                  {{ speedLabel }}
                </button>
                <Transition name="menu-slide">
                  <div v-if="speedOpen" class="menu-dropdown">
                    <div
                      v-for="val in speedOptions"
                      :key="val"
                      class="menu-item"
                      :class="{ selected: selectedSpeed === val }"
                      @click="setSpeed(val)"
                    >
                      {{ val }}x
                    </div>
                  </div>
                </Transition>
              </div>

              <!-- 分辨率菜单 -->
              <div class="menu-wrapper" ref="resolutionMenu">
                <button
                  class="menu-trigger"
                  :class="{ active: resHover && !resClick, clicked: resClick }"
                  @click="toggleResMenu"
                  @mouseenter="resHover = true"
                  @mouseleave="resHover = false"
                  @mousedown="onResPress"
                >
                  {{ currentResLabel }}
                </button>
                <Transition name="menu-slide">
                  <div v-if="resOpen" class="menu-dropdown">
                    <div
                      v-for="item in resolutionList"
                      :key="item.value"
                      class="menu-item"
                      :class="{ selected: selectedRes === item.value }"
                      @click="setResolution(item.value)"
                    >
                      {{ item.label }}
                    </div>
                  </div>
                </Transition>
              </div>

              <!-- 全屏按钮 -->
              <button
                class="control-btn fullscreen-btn"
                :class="{ active: fullHover && !fullClick, clicked: fullClick }"
                @click="toggleFullscreen"
                @mouseenter="fullHover = true"
                @mouseleave="fullHover = false"
                @mousedown="onFullPress"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 视频标题（位于视频卡片下方） -->
      <h1 class="video-title">{{ pageHeading }}</h1>
    </section>

    <!-- 占位元素（防止粘性覆盖） -->
    <div class="card-placeholder" :style="{ height: cardHeight + 'px' }"></div>

    <!-- 视频选集（卡片网格） -->
    <div class="playlist-section">
      <h2 class="playlist-heading">视频选集</h2>
      <div class="playlist-grid">
        <div
          v-for="item in videoCatalog"
          :key="item.url"
          class="playlist-card"
          :class="{
            'active-card': item.url === currentSource.url,
            'hover-card': hoveredItem === item.url && item.url !== currentSource.url
          }"
          @click="item.url !== currentSource.url && loadVideo(item)"
          @mouseenter="hoveredItem = item.url"
          @mouseleave="hoveredItem = null"
          @mousedown="onItemPress"
        >
          <div class="card-thumbnail">
            <svg viewBox="0 0 16 9" width="100%" height="100%">
              <rect width="16" height="9" fill="#2563eb20" />
              <text x="8" y="5" text-anchor="middle" fill="#2563eb" font-size="2">▶</text>
            </svg>
          </div>
          <div class="card-title">{{ item.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useData, useRouter } from 'vitepress'

const { frontmatter, page } = useData()
const router = useRouter()

// DOM 元素
const videoPlayer = ref(null)
const videoCard = ref(null)
const speedMenu = ref(null)
const resolutionMenu = ref(null)

// 视频状态
const videoMeta = ref({
  ready: false,
  paused: true,
  buffering: false,
  error: false
})
const currentPos = ref(0)
const totalDuration = ref(0)
const bufferPercent = ref(0)

// 面板可见性
const panelVisible = ref(false)
let panelTimer = null
let clickTimer = null

// 长按加速
let pressTimer = null
const longPressActive = ref(false)
const selectedSpeed = ref(1.0)

// 菜单状态
const speedOpen = ref(false)
const resOpen = ref(false)
const speedHover = ref(false)
const resHover = ref(false)
const fullHover = ref(false)
const playHover = ref(false)
const speedClick = ref(false)
const resClick = ref(false)
const fullClick = ref(false)

// 列表悬浮
const hoveredItem = ref(null)

// 分辨率
const resolutionList = [
  { value: '1080p', label: '1080P 高清' },
  { value: '720p', label: '720P 准高清' },
  { value: '480p', label: '480P 标清' },
  { value: '360p', label: '360P 流畅' }
]
const selectedRes = ref('720p')
const currentResLabel = computed(() => {
  const found = resolutionList.find(r => r.value === selectedRes.value)
  return found ? found.label : '720P 准高清'
})

// 倍速选项
const speedOptions = ['2.0', '1.5', '1.25', '1.0', '0.75', '0.5']

// 当前视频
const currentSource = ref({ url: '', name: '' })

// 页面标题
const pageHeading = computed(() => frontmatter.value.title || currentSource.value.name)

// 进度百分比
const playPercent = computed(() => {
  if (totalDuration.value === 0) return 0
  return (currentPos.value / totalDuration.value) * 100
})

// 倍速按钮文字
const speedLabel = computed(() => {
  if (longPressActive.value) return '3.0x'
  return selectedSpeed.value === 1.0 ? '倍速' : selectedSpeed.value + 'x'
})

// 时间格式化
const formatTime = (sec) => {
  if (isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 获取视频列表
const videoFiles = import.meta.glob(
  ['/**/*.mp4', '/**/*.webm', '/**/*.ogg', '/**/*.mov', '/**/*.avi', '/**/*.mkv', '/**/*.flv'],
  { eager: true, as: 'url' }
)

const currentFolder = computed(() => {
  const path = page.value.filePath
  if (!path) return ''
  const idx = path.lastIndexOf('/')
  return idx === -1 ? '' : path.substring(0, idx + 1)
})

const videoCatalog = computed(() => {
  const folder = currentFolder.value
  if (!folder) return []
  const list = []
  for (const [fullPath, url] of Object.entries(videoFiles)) {
    const rel = fullPath.startsWith('/') ? fullPath.slice(1) : fullPath
    if (rel.startsWith(folder)) {
      const name = fullPath.split('/').pop().replace(/\.[^/.]+$/, '')
      list.push({ url, name })
    }
  }
  return list
})

// 初始化视频
const initVideo = () => {
  const catalog = videoCatalog.value
  if (!catalog.length) return
  let target = catalog[0]
  if (frontmatter.value.video) {
    const match = catalog.find(v => v.url.endsWith('/' + frontmatter.value.video) || v.name === frontmatter.value.video)
    if (match) target = match
  }
  currentSource.value = target
}
watch(videoCatalog, initVideo, { immediate: true })

// 加载视频
const loadVideo = (item) => {
  currentSource.value = item
  videoMeta.value = { ready: false, paused: true, buffering: false, error: false }
  currentPos.value = 0
  totalDuration.value = 0
  nextTick(() => {
    const v = videoPlayer.value
    if (!v) return
    v.load()
    v.play().catch(() => {})
  })
  showPanel()
}

// 视频事件
const onProgress = () => {
  const v = videoPlayer.value
  if (!v) return
  currentPos.value = v.currentTime
  if (v.buffered.length) {
    for (let i = 0; i < v.buffered.length; i++) {
      if (v.currentTime >= v.buffered.start(i) && v.currentTime <= v.buffered.end(i)) {
        bufferPercent.value = (v.buffered.end(i) / v.duration) * 100
        break
      }
    }
  }
}
const onMetaLoad = () => { totalDuration.value = videoPlayer.value?.duration || 0 }
const onDataLoad = () => {
  videoMeta.value.ready = true
  videoMeta.value.buffering = false
  updateCardHeight()
}
const onWait = () => { videoMeta.value.buffering = true }
const onPlay = () => { videoMeta.value.paused = false; videoMeta.value.buffering = false }
const onFail = () => { videoMeta.value.error = true; videoMeta.value.ready = false }

// 播放控制
const togglePlayback = () => {
  const v = videoPlayer.value
  if (!v || videoMeta.value.error) return
  if (v.paused) {
    v.play().catch(() => {})
  } else {
    v.pause()
  }
  videoMeta.value.paused = v.paused
  resetPanelTimer()
}

// 长按加速
const startLongPress = () => {
  if (!videoPlayer.value || videoMeta.value.error) return
  pressTimer = setTimeout(() => {
    longPressActive.value = true
    if (videoPlayer.value) videoPlayer.value.playbackRate = 3.0
  }, 500)
}
const endLongPress = () => {
  if (pressTimer) clearTimeout(pressTimer)
  if (longPressActive.value) {
    longPressActive.value = false
    if (videoPlayer.value) videoPlayer.value.playbackRate = selectedSpeed.value
  }
}
const cancelLongPress = endLongPress

// 单击处理
const handleClick = () => {
  if (clickTimer) clearTimeout(clickTimer)
  clickTimer = setTimeout(() => {
    panelVisible.value = !panelVisible.value
    if (panelVisible.value) {
      resetPanelTimer()
    } else {
      if (panelTimer) clearTimeout(panelTimer)
    }
    clickTimer = null
  }, 250)
}

// 进度条拖动
let seeking = false
const seekActive = ref(false)
const startSeek = (e) => {
  e.preventDefault()
  e.stopPropagation()
  if (totalDuration.value === 0 || !videoPlayer.value) return

  panelVisible.value = true
  seeking = true
  seekActive.value = true
  resetPanelTimer()

  const track = e.currentTarget.querySelector('.progress-track') || e.currentTarget
  const update = (clientX) => {
    const rect = track.getBoundingClientRect()
    let percent = (clientX - rect.left) / rect.width
    percent = Math.max(0, Math.min(1, percent))
    videoPlayer.value.currentTime = percent * totalDuration.value
  }

  update(e.clientX)

  const onMove = (ev) => {
    ev.preventDefault()
    update(ev.clientX)
    resetPanelTimer()
  }
  const onUp = () => {
    seeking = false
    seekActive.value = false
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

// 面板自动隐藏
const resetPanelTimer = () => {
  if (panelTimer) clearTimeout(panelTimer)
  panelTimer = setTimeout(() => {
    if (!seeking && !speedOpen.value && !resOpen.value) {
      panelVisible.value = false
    }
  }, 5000)
}
const showPanel = () => {
  panelVisible.value = true
  resetPanelTimer()
}

// 倍速选择
const setSpeed = (val) => {
  const num = parseFloat(val)
  selectedSpeed.value = num
  if (!longPressActive.value) {
    if (videoPlayer.value) videoPlayer.value.playbackRate = num
  }
  speedOpen.value = false
  resetPanelTimer()
}

// 分辨率选择
const setResolution = (val) => {
  selectedRes.value = val
  resOpen.value = false
  resetPanelTimer()
}

// 菜单切换
const toggleSpeedMenu = () => {
  speedOpen.value = !speedOpen.value
  resOpen.value = false
  resetPanelTimer()
}
const toggleResMenu = () => {
  resOpen.value = !resOpen.value
  speedOpen.value = false
  resetPanelTimer()
}

// 按钮点击效果
const onSpeedPress = () => {
  speedClick.value = true
  setTimeout(() => { if (!speedHover.value) speedClick.value = false }, 300)
}
const onResPress = () => {
  resClick.value = true
  setTimeout(() => { if (!resHover.value) resClick.value = false }, 300)
}
const onFullPress = () => {
  fullClick.value = true
  setTimeout(() => { if (!fullHover.value) fullClick.value = false }, 300)
}
const onItemPress = () => {}

// 全屏
const toggleFullscreen = () => {
  if (!videoCard.value) return
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    videoCard.value.requestFullscreen()
  }
  resetPanelTimer()
}

// 返回上一级
const goBack = () => window.history.back()

// 点击外部关闭菜单
const handleOutsideClick = (e) => {
  if (speedMenu.value && !speedMenu.value.contains(e.target)) speedOpen.value = false
  if (resolutionMenu.value && !resolutionMenu.value.contains(e.target)) resOpen.value = false
}

// 粘性卡片占位高度
const cardHeight = ref(0)
const updateCardHeight = () => {
  if (!videoCard.value) return
  requestAnimationFrame(() => {
    const height = videoCard.value.getBoundingClientRect().height
    cardHeight.value = height
  })
}
const ensureCardHeight = () => {
  updateCardHeight()
  setTimeout(updateCardHeight, 50)
  setTimeout(updateCardHeight, 200)
}

// 生命周期
onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  ensureCardHeight()
  window.addEventListener('resize', updateCardHeight)
  const obs = new ResizeObserver(() => { updateCardHeight() })
  if (videoCard.value) obs.observe(videoCard.value)
  onBeforeUnmount(() => {
    document.removeEventListener('click', handleOutsideClick)
    window.removeEventListener('resize', updateCardHeight)
    obs.disconnect()
    clearTimeout(panelTimer)
    clearTimeout(pressTimer)
    clearTimeout(clickTimer)
  })
})

// 监听可能影响高度的变化
watch([() => videoMeta.value.ready, currentSource, panelVisible], () => {
  nextTick(updateCardHeight)
})
</script>

<style scoped>
/* 全局滚动隐藏 */
:global(html), :global(body) {
  overflow: hidden;
  height: 100%;
  margin: 0;
  padding: 0;
  background: #f8f9fa;
}
.video-app {
  height: 100vh;
  overflow-y: auto;
  background: #f8f9fa;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.video-app::-webkit-scrollbar {
  display: none;
}

/* 毛玻璃导航 */
.glass-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0,0,0,0.05);
  display: flex;
  align-items: center;
  padding: 0 24px;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.nav-back {
  background: none;
  border: none;
  color: #2c3e50;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}
.nav-back:hover {
  background: rgba(37,99,235,0.1);
  color: #2563eb;
}
.nav-logo {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.nav-logo img {
  height: 48px;
  width: auto;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}
.nav-placeholder {
  width: 40px;
}

/* 视频卡片 */
.video-card {
  position: sticky;
  top: 64px;
  z-index: 90;
  background: white;
  width: 100%;
  overflow: visible;
  border-radius: 0 0 24px 24px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.05);
}
.video-container {
  position: relative;
  width: 100%;
  background: black;
  border-radius: 0;
}
.video-wrapper {
  position: relative;
  width: 100%;
  background: black;
}
.video-wrapper.ratio-fixed {
  aspect-ratio: 16 / 9;
}
.video-element {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.video-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.5);
  z-index: 20;
  pointer-events: none;
}
.loading-overlay .spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255,255,255,0.2);
  border-top: 4px solid #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.error-overlay span {
  color: white;
  font-size: 16px;
  background: rgba(0,0,0,0.7);
  padding: 8px 16px;
  border-radius: 40px;
}

/* 控制栏 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.control-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  padding: 16px 20px 12px;
  z-index: 30;
}
.progress-area {
  margin-bottom: 12px;
  cursor: pointer;
}
.progress-track {
  position: relative;
  height: 4px;
  background: rgba(255,255,255,0.2);
  border-radius: 4px;
  transition: height 0.2s;
}
.progress-area:hover .progress-track {
  height: 6px;
}
.buffer-progress {
  position: absolute;
  height: 100%;
  background: rgba(255,255,255,0.3);
  border-radius: 4px;
  pointer-events: none;
}
.play-progress {
  position: absolute;
  height: 100%;
  background: #2563eb;
  border-radius: 4px;
  pointer-events: none;
}
.progress-thumb {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  background: #2563eb;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
}
.progress-area:hover .progress-thumb {
  opacity: 1;
}
.progress-thumb.dragging {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1.5);
}
.control-group {
  display: flex;
  align-items: center;
  color: white;
  font-size: 14px;
}
.control-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background 0.2s, color 0.2s, transform 0.2s;
}
.control-btn:hover {
  background: rgba(255,255,255,0.1);
}
.control-btn.active {
  color: #2563eb;
}
.control-btn.clicked {
  transform: scale(0.9);
}
.play-btn {
  margin-right: 12px;
}
.hover-blue {
  fill: #2563eb;
}
.time-display {
  margin-right: 16px;
  font-variant-numeric: tabular-nums;
  color: rgba(255,255,255,0.9);
}
.flex-spacer {
  flex: 1;
}

/* 下拉菜单 */
.menu-wrapper {
  position: relative;
  margin: 0 8px;
}
.menu-trigger {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 30px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s, color 0.2s, transform 0.2s;
  backdrop-filter: blur(4px);
}
.menu-trigger.active {
  background: #2563eb;
  border-color: #2563eb;
  color: white;
}
.menu-trigger.clicked {
  transform: scale(0.95);
}
.menu-slide-enter-active, .menu-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.menu-slide-enter-from, .menu-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
.menu-dropdown {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.2);
  min-width: 130px;
  z-index: 200;
  overflow: hidden;
  padding: 6px 0;
}
.menu-item {
  padding: 10px 16px;
  cursor: pointer;
  color: #1e293b;
  font-size: 14px;
  text-align: center;
  transition: background 0.2s, color 0.2s;
  border-bottom: 1px solid #f1f5f9;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-item:hover {
  background: #f1f5f9;
}
.menu-item.selected {
  background: #2563eb;
  color: white;
}
.fullscreen-btn {
  margin-left: 8px;
}

/* 视频标题 */
.video-title {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  padding: 24px 24px 20px;
  background: white;
  border-top: 1px solid #eef2f6;
  letter-spacing: -0.01em;
}

/* 占位块 */
.card-placeholder {
  width: 100%;
  transition: height 0.2s;
}

/* 播放列表 */
.playlist-section {
  padding: 0 24px 40px;
}
.playlist-heading {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 20px 0;
}
.playlist-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.playlist-card {
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
  transition: transform 0.25s, box-shadow 0.25s, background 0.2s;
  cursor: pointer;
  border: 1px solid #f0f0f0;
}
.playlist-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 30px rgba(37,99,235,0.1);
}
.playlist-card.active-card {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}
.playlist-card.hover-card {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}
.playlist-card:active {
  transform: scale(0.98);
}
.card-thumbnail {
  aspect-ratio: 16 / 9;
  background: #eef2f6;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-title {
  padding: 14px 12px;
  font-weight: 500;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
}
.active-card .card-title,
.hover-card .card-title {
  color: white;
}
</style>
