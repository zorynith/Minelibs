<template>
  <div class="video-page">
    <!-- 固定导航栏 -->
    <nav class="custom-navbar">
      <button class="back-btn" @click="goBack">← 返回</button>
      <div class="logo">
        <img src="https://minelibs.eu.org/Minelibs.png" alt="Logo" />
      </div>
      <div class="navbar-placeholder"></div>
    </nav>

    <!-- 粘性视频容器（包含视频和标题） -->
    <div class="player-container" ref="playerContainer">
      <!-- 视频包装器（16:9占位） -->
      <div class="video-wrapper">
        <!-- 加载动画（不阻挡点击） -->
        <div v-if="!videoLoaded || isBuffering" class="loading-placeholder" @click.stop>
          <div class="loading-spinner"></div>
        </div>
        <!-- 错误提示 -->
        <div v-if="videoError" class="video-error" @click.stop>
          视频加载失败，请检查文件路径
        </div>
        <video
          ref="video"
          class="video-player"
          :src="currentVideo.url"
          preload="metadata"
          @timeupdate="onTimeUpdate"
          @loadedmetadata="onLoadedMetadata"
          @loadeddata="onLoadedData"
          @waiting="onWaiting"
          @playing="onPlaying"
          @dblclick="togglePlay"
          @mousedown="onVideoMouseDown"
          @mouseup="onVideoMouseUp"
          @mouseleave="onVideoMouseLeave"
          @click="onVideoClick"
          @error="onVideoError"
        ></video>
      </div>

      <!-- 控制栏（单击视频显示） -->
      <Transition name="fade">
        <div v-if="controlsVisible" class="controls-overlay" @mousedown.stop>
          <!-- 进度条（含缓冲） -->
          <div class="progress-bar-container" @mousedown="onProgressMouseDown">
            <div class="progress-wrapper" ref="progressWrapper">
              <div class="progress-buffered" :style="{ width: bufferedPercent + '%' }"></div>
              <div class="progress-played" :style="{ width: playedPercent + '%' }"></div>
              <div
                class="progress-handle"
                :class="{ dragging: isDragging }"
                :style="{ left: playedPercent + '%' }"
                @mousedown.stop="onProgressMouseDown"
              ></div>
            </div>
          </div>

          <!-- 底部控件 -->
          <div class="controls">
            <!-- 播放/暂停 -->
            <div
              class="play-pause"
              @click="togglePlay"
              @mouseenter="playPauseHovered = true"
              @mouseleave="playPauseHovered = false"
            >
              <span v-if="videoPaused" class="play-icon" :class="{ hovered: playPauseHovered }"></span>
              <span v-else class="pause-icon" :class="{ hovered: playPauseHovered }"></span>
            </div>

            <div class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</div>
            <div class="spacer"></div>

            <!-- 倍速菜单 -->
            <div class="dropdown" ref="speedDropdown">
              <button
                class="dropdown-btn"
                :class="{ hovered: speedHovered && !speedClicked, clicked: speedClicked }"
                @click="toggleSpeedMenu"
                @mouseenter="speedHovered = true"
                @mouseleave="speedHovered = false"
                @mousedown="onSpeedMouseDown"
              >
                {{ speedButtonText }}
              </button>
              <Transition name="dropdown-fade">
                <div v-if="speedMenuOpen" class="dropdown-menu">
                  <div
                    v-for="rate in playbackRates"
                    :key="rate"
                    class="dropdown-item"
                    :class="{ active: selectedPlaybackRate === parseFloat(rate) }"
                    @click="selectPlaybackRate(parseFloat(rate))"
                  >
                    {{ rate }}x
                  </div>
                </div>
              </Transition>
            </div>

            <!-- 分辨率菜单 -->
            <div class="dropdown" ref="resolutionDropdown">
              <button
                class="dropdown-btn"
                :class="{ hovered: resolutionHovered && !resolutionClicked, clicked: resolutionClicked }"
                @click="toggleResolutionMenu"
                @mouseenter="resolutionHovered = true"
                @mouseleave="resolutionHovered = false"
                @mousedown="onResolutionMouseDown"
              >
                {{ resolutionButtonText }}
              </button>
              <Transition name="dropdown-fade">
                <div v-if="resolutionMenuOpen" class="dropdown-menu">
                  <div
                    v-for="res in resolutions"
                    :key="res.value"
                    class="dropdown-item"
                    :class="{ active: selectedResolution === res.value }"
                    @click="selectResolution(res.value)"
                  >
                    {{ res.label }}
                  </div>
                </div>
              </Transition>
            </div>

            <!-- 全屏按钮 -->
            <div
              class="fullscreen-btn-custom"
              :class="{ hovered: fullscreenHovered && !fullscreenClicked, clicked: fullscreenClicked }"
              @click="toggleFullscreen"
              @mouseenter="fullscreenHovered = true"
              @mouseleave="fullscreenHovered = false"
              @mousedown="onFullscreenMouseDown"
            >
              <div class="fullscreen-border"></div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- 视频标题（紧贴视频下方） -->
      <h1 class="video-title">{{ pageTitle }}</h1>
    </div>

    <!-- 占位元素，防止粘性容器覆盖后续内容 -->
    <div class="player-placeholder" :style="{ height: placeholderHeight + 'px' }"></div>

    <!-- 视频选集列表 -->
    <div class="video-list">
      <h2>视频选集</h2>
      <ul>
        <li
          v-for="video in videoList"
          :key="video.url"
          :class="{
            active: video.url === currentVideo.url,
            hovered: hoveredListItem === video.url && video.url !== currentVideo.url
          }"
          @click="video.url !== currentVideo.url && playVideo(video)"
          @mouseenter="hoveredListItem = video.url"
          @mouseleave="hoveredListItem = null"
          @mousedown="onListItemMouseDown"
          @mouseup="onListItemMouseUp"
        >
          {{ video.name }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useData } from 'vitepress'

const router = useRouter()
const { frontmatter, page } = useData()

// ========== 响应式数据 ==========
const video = ref(null)
const playerContainer = ref(null)
const progressWrapper = ref(null)
const currentTime = ref(0)
const duration = ref(0)
const videoPaused = ref(true)
const selectedPlaybackRate = ref(1.0)
const playbackRate = ref(1.0) // 实际播放速度
const controlsVisible = ref(false)
const videoLoaded = ref(false)
const isBuffering = ref(false)
const isDragging = ref(false)
const videoError = ref(false)
const isLongPressing = ref(false)

// 下拉菜单
const speedMenuOpen = ref(false)
const resolutionMenuOpen = ref(false)
const speedDropdown = ref(null)
const resolutionDropdown = ref(null)

// 按钮状态
const playPauseHovered = ref(false)
const speedHovered = ref(false)
const resolutionHovered = ref(false)
const fullscreenHovered = ref(false)
const speedClicked = ref(false)
const resolutionClicked = ref(false)
const fullscreenClicked = ref(false)

// 列表悬浮
const hoveredListItem = ref(null)

// 占位高度
const placeholderHeight = ref(0)

// 分辨率选项
const resolutions = [
  { value: '1080p', label: '1080P 高清' },
  { value: '720p', label: '720P 准高清' },
  { value: '480p', label: '480P 标清' },
  { value: '360p', label: '360P 流畅' }
]
const selectedResolution = ref('720p')

const playbackRates = ['2.0', '1.5', '1.25', '1.0', '0.75', '0.5']

const currentVideo = ref({ url: '', name: '' })

// ========== 定时器 ==========
let longPressTimer = null
let hideControlsTimer = null
let clickTimer = null
let resizeObserver = null

// ========== 计算属性 ==========
const pageTitle = computed(() => frontmatter.value.title || currentVideo.value.name)

const playedPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const bufferedPercent = computed(() => {
  if (!video.value || duration.value === 0) return 0
  const buffered = video.value.buffered
  for (let i = 0; i < buffered.length; i++) {
    if (currentTime.value >= buffered.start(i) && currentTime.value <= buffered.end(i)) {
      return (buffered.end(i) / duration.value) * 100
    }
  }
  return 0
})

const formatTime = (seconds) => {
  if (isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const speedButtonText = computed(() => {
  if (isLongPressing.value) return '3.0x'
  return selectedPlaybackRate.value === 1.0 ? '倍速' : selectedPlaybackRate.value + 'x'
})

const resolutionButtonText = computed(() => {
  const res = resolutions.find(r => r.value === selectedResolution.value)
  return res ? res.label : '720P 准高清'
})

// ========== 视频文件列表 ==========
const videoModules = import.meta.glob(
  ['/**/*.mp4', '/**/*.webm', '/**/*.ogg', '/**/*.mov', '/**/*.avi', '/**/*.mkv', '/**/*.flv'],
  { eager: true, as: 'url' }
)

const currentDir = computed(() => {
  const filePath = page.value.filePath
  if (!filePath) return ''
  const lastSlash = filePath.lastIndexOf('/')
  return lastSlash === -1 ? '' : filePath.substring(0, lastSlash + 1)
})

const videoList = computed(() => {
  const dir = currentDir.value
  if (!dir) return []
  const list = []
  for (const [filePath, url] of Object.entries(videoModules)) {
    const relativePath = filePath.startsWith('/') ? filePath.slice(1) : filePath
    if (relativePath.startsWith(dir)) {
      const fileName = filePath.split('/').pop().replace(/\.[^/.]+$/, '')
      list.push({ url, name: fileName })
    }
  }
  return list
})

// ========== 视频操作 ==========
const playVideo = (videoItem) => {
  currentVideo.value = videoItem
  videoLoaded.value = false
  videoError.value = false
  isBuffering.value = false
  nextTick(() => {
    video.value?.load()
    video.value?.play().catch(() => (videoError.value = true))
  })
  controlsVisible.value = true
  resetHideControlsTimer()
}

const initCurrentVideo = () => {
  const list = videoList.value
  if (!list.length) return
  let initial = list[0]
  if (frontmatter.value.video) {
    const matched = list.find(v => v.url.endsWith('/' + frontmatter.value.video) || v.name === frontmatter.value.video)
    if (matched) initial = matched
  }
  currentVideo.value = initial
}
watch(videoList, initCurrentVideo, { immediate: true })

// ========== 视频事件 ==========
const onTimeUpdate = () => { currentTime.value = video.value?.currentTime || 0 }
const onLoadedMetadata = () => { duration.value = video.value?.duration || 0 }
const onLoadedData = () => {
  videoLoaded.value = true
  isBuffering.value = false
  updatePlaceholderHeight()
}
const onWaiting = () => { isBuffering.value = true }
const onPlaying = () => { isBuffering.value = false }
const onVideoError = () => {
  videoError.value = true
  videoLoaded.value = false
}

// ========== 播放控制 ==========
const togglePlay = () => {
  if (!video.value || videoError.value) return
  if (video.value.paused) {
    video.value.play().catch(() => {})
  } else {
    video.value.pause()
  }
  videoPaused.value = video.value.paused
  resetHideControlsTimer()
}

// ========== 长按加速 ==========
const onVideoMouseDown = () => {
  if (!video.value || videoError.value) return
  longPressTimer = setTimeout(() => {
    isLongPressing.value = true
    playbackRate.value = 3.0
    video.value.playbackRate = 3.0
  }, 500)
  resetHideControlsTimer()
}
const onVideoMouseUp = () => {
  if (longPressTimer) clearTimeout(longPressTimer)
  if (isLongPressing.value) {
    isLongPressing.value = false
    playbackRate.value = selectedPlaybackRate.value
    video.value.playbackRate = selectedPlaybackRate.value
  }
  resetHideControlsTimer()
}
const onVideoMouseLeave = onVideoMouseUp

// ========== 单击/双击处理 ==========
const onVideoClick = () => {
  if (clickTimer) clearTimeout(clickTimer)
  clickTimer = setTimeout(() => {
    controlsVisible.value = !controlsVisible.value
    if (controlsVisible.value) {
      resetHideControlsTimer()
    } else if (hideControlsTimer) {
      clearTimeout(hideControlsTimer)
    }
    clickTimer = null
  }, 250)
}
const onDblClick = togglePlay

// ========== 进度条拖拽 ==========
const onProgressMouseDown = (e) => {
  e.preventDefault()
  e.stopPropagation()
  if (duration.value <= 0 || !video.value) return

  controlsVisible.value = true
  isDragging.value = true
  resetHideControlsTimer()

  const wrapper = progressWrapper.value
  if (!wrapper) {
    isDragging.value = false
    return
  }

  const update = (clientX) => {
    const rect = wrapper.getBoundingClientRect()
    let percent = (clientX - rect.left) / rect.width
    percent = Math.max(0, Math.min(1, percent))
    video.value.currentTime = percent * duration.value
  }

  update(e.clientX)

  const onMove = (e) => {
    e.preventDefault()
    update(e.clientX)
    resetHideControlsTimer()
  }
  const onUp = () => {
    isDragging.value = false
    resetHideControlsTimer()
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }

  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

// ========== 倍速选择 ==========
const selectPlaybackRate = (rate) => {
  selectedPlaybackRate.value = rate
  if (!isLongPressing.value) {
    playbackRate.value = rate
    if (video.value) video.value.playbackRate = rate
  }
  speedMenuOpen.value = false
  resetHideControlsTimer()
}

// ========== 分辨率选择 ==========
const selectResolution = (res) => {
  selectedResolution.value = res
  resolutionMenuOpen.value = false
  // 分辨率切换逻辑可根据需要扩展
  resetHideControlsTimer()
}

// ========== 控制栏自动隐藏 ==========
const resetHideControlsTimer = () => {
  if (hideControlsTimer) clearTimeout(hideControlsTimer)
  hideControlsTimer = setTimeout(() => {
    controlsVisible.value = false
  }, 5000)
}

// ========== 全屏 ==========
const toggleFullscreen = () => {
  if (!playerContainer.value) return
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    playerContainer.value.requestFullscreen()
  }
  resetHideControlsTimer()
}

// ========== 返回上一页 ==========
const goBack = () => window.history.back()

// ========== 下拉菜单切换 ==========
const toggleSpeedMenu = () => {
  speedMenuOpen.value = !speedMenuOpen.value
  resolutionMenuOpen.value = false
  resetHideControlsTimer()
}
const toggleResolutionMenu = () => {
  resolutionMenuOpen.value = !resolutionMenuOpen.value
  speedMenuOpen.value = false
  resetHideControlsTimer()
}

// ========== 点击外部关闭菜单 ==========
const handleClickOutside = (e) => {
  if (speedDropdown.value && !speedDropdown.value.contains(e.target)) {
    speedMenuOpen.value = false
  }
  if (resolutionDropdown.value && !resolutionDropdown.value.contains(e.target)) {
    resolutionMenuOpen.value = false
  }
}

// ========== 按钮点击效果 ==========
const onSpeedMouseDown = () => {
  speedClicked.value = true
  setTimeout(() => { if (!speedHovered.value) speedClicked.value = false }, 300)
}
const onResolutionMouseDown = () => {
  resolutionClicked.value = true
  setTimeout(() => { if (!resolutionHovered.value) resolutionClicked.value = false }, 300)
}
const onFullscreenMouseDown = () => {
  fullscreenClicked.value = true
  setTimeout(() => { if (!fullscreenHovered.value) fullscreenClicked.value = false }, 300)
}
const onListItemMouseDown = () => {} // CSS :active 处理

// ========== 占位高度更新 ==========
const updatePlaceholderHeight = () => {
  if (!playerContainer.value) return
  requestAnimationFrame(() => {
    placeholderHeight.value = playerContainer.value.getBoundingClientRect().height
  })
}

// ========== 生命周期 ==========
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  updatePlaceholderHeight()
  window.addEventListener('resize', updatePlaceholderHeight)
  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(updatePlaceholderHeight)
    resizeObserver.observe(playerContainer.value)
  }
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', updatePlaceholderHeight)
  resizeObserver?.disconnect()
  clearTimeout(hideControlsTimer)
  clearTimeout(longPressTimer)
  clearTimeout(clickTimer)
})

// 视频切换时更新高度
watch([videoLoaded, currentVideo], () => nextTick(updatePlaceholderHeight))
</script>

<style scoped>
/* ========== 全局滚动条隐藏 ========== */
:global(html), :global(body) {
  overflow: hidden;
  height: 100%;
  margin: 0;
  padding: 0;
}
.video-page {
  max-width: 100%;
  margin: 0;
  padding: 0;
  background-color: #fff;
  height: 100vh;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.video-page::-webkit-scrollbar {
  display: none;
}

/* ========== 导航栏 ========== */
.custom-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: white;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  padding: 0 20px;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.back-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: #333;
  cursor: pointer;
  width: 60px;
  text-align: left;
}
.logo {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.logo img {
  height: 60px;
  width: auto;
  pointer-events: none;
}
.navbar-placeholder {
  width: 60px;
}

/* ========== 视频容器 ========== */
.player-container {
  position: sticky;
  top: 60px;
  z-index: 90;
  background-color: #000;
  width: 100%;
  overflow: visible;
}
.video-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background-color: #000;
}
.video-player {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.loading-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0,0,0,0.5);
  z-index: 20;
  pointer-events: none;
}
.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #2563eb;
  animation: spin 1s ease-in-out infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.video-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  background: rgba(0,0,0,0.7);
  padding: 10px 20px;
  border-radius: 4px;
  z-index: 25;
  pointer-events: none;
}

/* ========== 控制栏 ========== */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.controls-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  z-index: 30;
}
.progress-bar-container {
  padding: 10px 12px 5px;
  cursor: pointer;
}
.progress-wrapper {
  position: relative;
  height: 6px;
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
  cursor: pointer;
}
.progress-buffered {
  position: absolute;
  height: 100%;
  background-color: rgba(255,255,255,0.3);
  border-radius: 3px;
  pointer-events: none;
}
.progress-played {
  position: absolute;
  height: 100%;
  background-color: #2563eb;
  border-radius: 3px;
  pointer-events: none;
}
.progress-handle {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background-color: #2563eb;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  transition: transform 0.2s ease;
}
.progress-handle.dragging {
  transform: translate(-50%, -50%) scale(1.5);
}
.controls {
  display: flex;
  align-items: center;
  padding: 5px 12px 10px;
  color: white;
  font-size: 14px;
}
.play-pause {
  cursor: pointer;
  margin-right: 15px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}
.play-pause:active { transform: scale(0.98); }
.play-icon {
  width: 0;
  height: 0;
  border-left: 16px solid white;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  border-radius: 2px;
  margin-left: 4px;
  transition: border-left-color 0.2s;
}
.play-icon.hovered { border-left-color: #2563eb; }
.pause-icon {
  width: 16px;
  height: 20px;
  display: flex;
  justify-content: space-between;
}
.pause-icon::before, .pause-icon::after {
  content: '';
  width: 5px;
  height: 20px;
  background-color: white;
  border-radius: 2px;
  transition: background-color 0.2s;
}
.pause-icon.hovered::before, .pause-icon.hovered::after {
  background-color: #2563eb;
}
.time-display { margin-right: 15px; }
.spacer { flex: 1; }

/* ========== 下拉菜单 ========== */
.dropdown {
  position: relative;
  margin-right: 15px;
}
.dropdown-btn {
  background: transparent;
  border: none;
  color: white;
  font-weight: bold;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: color 0.2s;
  outline: none;
}
.dropdown-btn.hovered { color: #2563eb; }
.dropdown-btn.clicked { transform: scale(0.98); }
.dropdown-fade-enter-active, .dropdown-fade-leave-active {
  transition: opacity 0.2s ease;
}
.dropdown-fade-enter-from, .dropdown-fade-leave-to {
  opacity: 0;
}
.dropdown-menu {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 5px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 120px;
  z-index: 200;
  overflow: hidden;
}
.dropdown-item {
  padding: 8px 16px;
  cursor: pointer;
  color: #333;
  font-size: 14px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}
.dropdown-item:last-child { border-bottom: none; }
.dropdown-item:hover { background-color: #e6f7ff; }
.dropdown-item.active {
  background-color: #2563eb;
  color: white;
}

/* ========== 全屏按钮 ========== */
.fullscreen-btn-custom {
  width: 32px;
  height: 32px;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s;
  margin-left: 10px;
}
.fullscreen-btn-custom.clicked { transform: scale(0.98); }
.fullscreen-btn-custom.hovered .fullscreen-border { border-color: #2563eb; }
.fullscreen-border {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid white;
  border-radius: 8px;
  box-sizing: border-box;
  pointer-events: none;
}
.fullscreen-btn-custom::before {
  content: '';
  position: absolute;
  top: 4px;
  left: 4px;
  right: 4px;
  bottom: 4px;
  background: rgba(0,0,0,0.5);
  border-radius: 4px;
  z-index: 1;
}
.fullscreen-btn-custom::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  border: 2px solid white;
  border-radius: 6px;
  pointer-events: none;
}

/* ========== 视频标题 ========== */
.video-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin: 0;
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fff;
}

/* ========== 占位元素 ========== */
.player-placeholder {
  width: 100%;
  transition: height 0.2s ease;
}

/* ========== 视频选集 ========== */
.video-list {
  margin: 0 20px 20px;
}
.video-list h2 {
  font-size: 18px;
  color: #666;
  margin-bottom: 10px;
}
.video-list ul {
  list-style: none;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.video-list li {
  padding: 12px 16px;
  background-color: #f5f5f5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #333;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.video-list li.active {
  background-color: #2563eb;
  color: white;
  cursor: default;
  pointer-events: none;
}
.video-list li:not(.active).hovered {
  background-color: #2563eb;
  color: white;
}
.video-list li:not(.active):active {
  transform: scale(0.98);
}
</style>
