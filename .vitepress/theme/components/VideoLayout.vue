<template>
  <div class="app-container">
    <!-- 顶部栏 -->
    <header class="app-header">
      <button class="nav-back" @click="goBack">← 返回</button>
      <div class="nav-logo">
        <img src="https://minelibs.eu.org/Minelibs.png" alt="Logo">
      </div>
      <div class="nav-spacer"></div>
    </header>

    <!-- 视频区域（粘性） -->
    <section class="video-section" ref="videoSection">
      <div class="video-box" :class="{ 'ratio-fixed': !videoMeta.ready }">
        <!-- 加载状态 -->
        <div v-if="!videoMeta.ready || videoMeta.buffering" class="video-overlay loading-state" @click.stop>
          <div class="spinner"></div>
        </div>
        <!-- 错误提示 -->
        <div v-if="videoMeta.error" class="video-overlay error-state" @click.stop>
          视频加载失败
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

      <!-- 控制面板 -->
      <Transition name="panel-fade">
        <div v-if="panelVisible" class="control-panel" @mousedown.stop>
          <!-- 进度条 -->
          <div class="seek-bar" @mousedown="startSeek">
            <div class="track">
              <div class="buffer-fill" :style="{ width: bufferPercent + '%' }"></div>
              <div class="progress-fill" :style="{ width: playPercent + '%' }"></div>
              <div
                class="thumb"
                :class="{ dragging: seekActive }"
                :style="{ left: playPercent + '%' }"
                @mousedown.stop="startSeek"
              ></div>
            </div>
          </div>

          <!-- 控件组 -->
          <div class="controls-row">
            <div
              class="play-toggle"
              @click="togglePlayback"
              @mouseenter="playHover = true"
              @mouseleave="playHover = false"
            >
              <span v-if="videoMeta.paused" class="icon-play" :class="{ hover: playHover }"></span>
              <span v-else class="icon-pause" :class="{ hover: playHover }"></span>
            </div>

            <span class="time-info">{{ formatTime(currentPos) }} / {{ formatTime(totalDuration) }}</span>

            <div class="flex-grow"></div>

            <!-- 倍速菜单 -->
            <div class="menu-container" ref="speedMenuRef">
              <button
                class="menu-button"
                :class="{ active: speedHover && !speedClick, clicked: speedClick }"
                @click="toggleSpeedMenu"
                @mouseenter="speedHover = true"
                @mouseleave="speedHover = false"
                @mousedown="onSpeedPress"
              >
                {{ speedLabel }}
              </button>
              <Transition name="menu-fade">
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
            <div class="menu-container" ref="resMenuRef">
              <button
                class="menu-button"
                :class="{ active: resHover && !resClick, clicked: resClick }"
                @click="toggleResMenu"
                @mouseenter="resHover = true"
                @mouseleave="resHover = false"
                @mousedown="onResPress"
              >
                {{ currentResLabel }}
              </button>
              <Transition name="menu-fade">
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
            <div
              class="fullscreen-button"
              :class="{ hover: fullHover && !fullClick, clicked: fullClick }"
              @click="toggleFullscreen"
              @mouseenter="fullHover = true"
              @mouseleave="fullHover = false"
              @mousedown="onFullPress"
            >
              <div class="full-icon"></div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- 视频标题（与视频一起粘性） -->
      <h1 class="video-headline">{{ pageHeading }}</h1>
    </section>

    <!-- 占位块，防止覆盖 -->
    <div class="section-placeholder" :style="{ height: sectionHeight + 'px' }"></div>

    <!-- 视频选集 -->
    <div class="playlist">
      <h2 class="playlist-title">视频选集</h2>
      <ul class="playlist-grid">
        <li
          v-for="item in videoCatalog"
          :key="item.url"
          :class="{
            current: item.url === currentSource.url,
            highlight: hoveredItem === item.url && item.url !== currentSource.url
          }"
          @click="item.url !== currentSource.url && loadVideo(item)"
          @mouseenter="hoveredItem = item.url"
          @mouseleave="hoveredItem = null"
          @mousedown="onItemPress"
        >
          {{ item.name }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useData, useRouter } from 'vitepress'

// ----- 数据源 -----
const { frontmatter, page } = useData()
const router = useRouter()

// ----- 视频元素 -----
const videoPlayer = ref(null)
const videoSection = ref(null)
const speedMenuRef = ref(null)
const resMenuRef = ref(null)

// ----- 视频状态 -----
const videoMeta = ref({
  ready: false,
  paused: true,
  buffering: false,
  error: false
})
const currentPos = ref(0)
const totalDuration = ref(0)
const bufferPercent = ref(0)

// ----- 控制面板可见性 -----
const panelVisible = ref(false)
let panelTimer = null
let clickTimer = null

// ----- 长按加速 -----
let pressTimer = null
const longPressActive = ref(false)
const selectedSpeed = ref(1.0)
const actualSpeed = ref(1.0)

// ----- 菜单状态 -----
const speedOpen = ref(false)
const resOpen = ref(false)
const speedHover = ref(false)
const resHover = ref(false)
const fullHover = ref(false)
const speedClick = ref(false)
const resClick = ref(false)
const fullClick = ref(false)
const playHover = ref(false)

// ----- 列表悬浮 -----
const hoveredItem = ref(null)

// ----- 分辨率 -----
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

// ----- 倍速选项 -----
const speedOptions = ['2.0', '1.5', '1.25', '1.0', '0.75', '0.5']

// ----- 当前视频源 -----
const currentSource = ref({ url: '', name: '' })

// ----- 页面标题 -----
const pageHeading = computed(() => frontmatter.value.title || currentSource.value.name)

// ----- 进度百分比 -----
const playPercent = computed(() => {
  if (totalDuration.value === 0) return 0
  return (currentPos.value / totalDuration.value) * 100
})

// ----- 倍速按钮文字 -----
const speedLabel = computed(() => {
  if (longPressActive.value) return '3.0x'
  return selectedSpeed.value === 1.0 ? '倍速' : selectedSpeed.value + 'x'
})

// ----- 时间格式化 -----
const formatTime = (sec) => {
  if (isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// ----- 获取同目录视频列表 -----
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

// ----- 初始化视频 -----
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

// ----- 加载视频 -----
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

// ----- 视频事件回调 -----
const onProgress = () => {
  const v = videoPlayer.value
  if (!v) return
  currentPos.value = v.currentTime
  // 计算缓冲
  if (v.buffered.length) {
    for (let i = 0; i < v.buffered.length; i++) {
      if (v.currentTime >= v.buffered.start(i) && v.currentTime <= v.buffered.end(i)) {
        bufferPercent.value = (v.buffered.end(i) / v.duration) * 100
        break
      }
    }
  }
}
const onMetaLoad = () => {
  totalDuration.value = videoPlayer.value?.duration || 0
}
const onDataLoad = () => {
  videoMeta.value.ready = true
  videoMeta.value.buffering = false
  updatePlaceholder()
}
const onWait = () => {
  videoMeta.value.buffering = true
}
const onPlay = () => {
  videoMeta.value.paused = false
  videoMeta.value.buffering = false
}
const onFail = () => {
  videoMeta.value.error = true
  videoMeta.value.ready = false
}

// ----- 播放/暂停切换 -----
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

// ----- 长按加速 -----
const startLongPress = () => {
  if (!videoPlayer.value || videoMeta.value.error) return
  pressTimer = setTimeout(() => {
    longPressActive.value = true
    actualSpeed.value = 3.0
    if (videoPlayer.value) videoPlayer.value.playbackRate = 3.0
  }, 500)
}
const endLongPress = () => {
  if (pressTimer) clearTimeout(pressTimer)
  if (longPressActive.value) {
    longPressActive.value = false
    actualSpeed.value = selectedSpeed.value
    if (videoPlayer.value) videoPlayer.value.playbackRate = selectedSpeed.value
  }
}
const cancelLongPress = endLongPress

// ----- 单击/双击处理 -----
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

// ----- 进度条拖动 -----
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

  const track = e.currentTarget.querySelector('.track') || e.currentTarget
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

// ----- 面板自动隐藏 -----
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

// ----- 倍速选择 -----
const setSpeed = (val) => {
  const num = parseFloat(val)
  selectedSpeed.value = num
  if (!longPressActive.value) {
    actualSpeed.value = num
    if (videoPlayer.value) videoPlayer.value.playbackRate = num
  }
  speedOpen.value = false
  resetPanelTimer()
}

// ----- 分辨率选择 -----
const setResolution = (val) => {
  selectedRes.value = val
  resOpen.value = false
  // 实际分辨率切换需要额外实现，这里留接口
  resetPanelTimer()
}

// ----- 菜单切换 -----
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

// ----- 按钮点击效果（延迟移除）-----
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
const onItemPress = () => {} // 使用CSS :active

// ----- 全屏 -----
const toggleFullscreen = () => {
  if (!videoSection.value) return
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    videoSection.value.requestFullscreen()
  }
  resetPanelTimer()
}

// ----- 返回上一级 -----
const goBack = () => window.history.back()

// ----- 点击外部关闭菜单 -----
const handleOutsideClick = (e) => {
  if (speedMenuRef.value && !speedMenuRef.value.contains(e.target)) speedOpen.value = false
  if (resMenuRef.value && !resMenuRef.value.contains(e.target)) resOpen.value = false
}

// ----- 粘性容器占位高度 -----
const sectionHeight = ref(0)
const updatePlaceholder = () => {
  if (!videoSection.value) return
  requestAnimationFrame(() => {
    sectionHeight.value = videoSection.value.getBoundingClientRect().height
  })
}

// ----- 生命周期 -----
onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  updatePlaceholder()
  window.addEventListener('resize', updatePlaceholder)
  const obs = new ResizeObserver(updatePlaceholder)
  if (videoSection.value) obs.observe(videoSection.value)
  onBeforeUnmount(() => {
    document.removeEventListener('click', handleOutsideClick)
    window.removeEventListener('resize', updatePlaceholder)
    obs.disconnect()
    clearTimeout(panelTimer)
    clearTimeout(pressTimer)
    clearTimeout(clickTimer)
  })
})

// 视频切换时更新占位
watch([() => videoMeta.value.ready, currentSource], () => nextTick(updatePlaceholder))
</script>

<style scoped>
/* 全局隐藏滚动条 */
:global(html), :global(body) {
  overflow: hidden;
  height: 100%;
  margin: 0;
  padding: 0;
}
.app-container {
  height: 100vh;
  overflow-y: auto;
  background: white;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.app-container::-webkit-scrollbar {
  display: none;
}

/* 头部导航 */
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: white;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  padding: 0 20px;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.nav-back {
  background: none;
  border: none;
  font-size: 16px;
  color: #333;
  cursor: pointer;
  width: 60px;
  text-align: left;
}
.nav-logo {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.nav-logo img {
  height: 60px;
  width: auto;
  pointer-events: none;
}
.nav-spacer {
  width: 60px;
}

/* 视频区域（粘性） */
.video-section {
  position: sticky;
  top: 60px;
  z-index: 90;
  background: black;
  width: 100%;
  overflow: visible;
}
.video-box {
  position: relative;
  width: 100%;
  background: black;
}
.video-box.ratio-fixed {
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
.loading-state .spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255,255,255,0.3);
  border-top: 5px solid #2563eb;
  border-radius: 50%;
  animation: rotate 1s linear infinite;
}
@keyframes rotate { to { transform: rotate(360deg); } }
.error-state {
  color: white;
  font-size: 16px;
  background: rgba(0,0,0,0.7);
}

/* 控制面板 */
.panel-fade-enter-active, .panel-fade-leave-active {
  transition: opacity 0.3s;
}
.panel-fade-enter-from, .panel-fade-leave-to {
  opacity: 0;
}
.control-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  z-index: 30;
}
.seek-bar {
  padding: 10px 12px 5px;
  cursor: pointer;
}
.track {
  position: relative;
  height: 6px;
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
}
.buffer-fill {
  position: absolute;
  height: 100%;
  background: rgba(255,255,255,0.3);
  border-radius: 3px;
  pointer-events: none;
}
.progress-fill {
  position: absolute;
  height: 100%;
  background: #2563eb;
  border-radius: 3px;
  pointer-events: none;
}
.thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background: #2563eb;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  transition: transform 0.2s;
}
.thumb.dragging {
  transform: translate(-50%, -50%) scale(1.5);
}
.controls-row {
  display: flex;
  align-items: center;
  padding: 5px 12px 10px;
  color: white;
  font-size: 14px;
}
.play-toggle {
  cursor: pointer;
  margin-right: 15px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}
.play-toggle:active {
  transform: scale(0.98);
}
.icon-play {
  width: 0;
  height: 0;
  border-left: 16px solid white;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  border-radius: 2px;
  margin-left: 4px;
  transition: border-left-color 0.2s;
}
.icon-play.hover {
  border-left-color: #2563eb;
}
.icon-pause {
  width: 16px;
  height: 20px;
  display: flex;
  justify-content: space-between;
}
.icon-pause::before, .icon-pause::after {
  content: '';
  width: 5px;
  height: 20px;
  background: white;
  border-radius: 2px;
  transition: background 0.2s;
}
.icon-pause.hover::before, .icon-pause.hover::after {
  background: #2563eb;
}
.time-info {
  margin-right: 15px;
}
.flex-grow {
  flex: 1;
}

/* 下拉菜单 */
.menu-container {
  position: relative;
  margin-right: 15px;
}
.menu-button {
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
.menu-button.active {
  color: #2563eb;
}
.menu-button.clicked {
  transform: scale(0.98);
}
.menu-fade-enter-active, .menu-fade-leave-active {
  transition: opacity 0.2s;
}
.menu-fade-enter-from, .menu-fade-leave-to {
  opacity: 0;
}
.menu-dropdown {
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
.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  color: #333;
  font-size: 14px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-item:hover {
  background: #e6f7ff;
}
.menu-item.selected {
  background: #2563eb;
  color: white;
}

/* 全屏按钮 */
.fullscreen-button {
  width: 32px;
  height: 32px;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s;
  margin-left: 10px;
}
.fullscreen-button.clicked {
  transform: scale(0.98);
}
.fullscreen-button.hover .full-icon {
  border-color: #2563eb;
}
.full-icon {
  position: absolute;
  inset: 0;
  border: 2px solid white;
  border-radius: 8px;
  box-sizing: border-box;
}
.full-icon::before {
  content: '';
  position: absolute;
  top: 4px;
  left: 4px;
  right: 4px;
  bottom: 4px;
  background: rgba(0,0,0,0.5);
  border-radius: 4px;
}
.full-icon::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  border: 2px solid white;
  border-radius: 6px;
}

/* 视频标题 */
.video-headline {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin: 0;
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  background: white;
}

/* 占位块 */
.section-placeholder {
  width: 100%;
  transition: height 0.2s;
}

/* 播放列表 */
.playlist {
  margin: 0 20px 20px;
}
.playlist-title {
  font-size: 18px;
  color: #666;
  margin-bottom: 10px;
}
.playlist-grid {
  list-style: none;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.playlist-grid li {
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  color: #333;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.playlist-grid li.current {
  background: #2563eb;
  color: white;
  cursor: default;
  pointer-events: none;
}
.playlist-grid li:not(.current).highlight {
  background: #2563eb;
  color: white;
}
.playlist-grid li:not(.current):active {
  transform: scale(0.98);
}
</style>
