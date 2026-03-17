<template>
  <div class="video-page">
    <!-- 悬浮导航栏 -->
    <nav class="custom-navbar">
      <button class="back-btn" @click="goBack">← 返回</button>
      <div class="logo">
        <img src="https://minelibs.eu.org/Minelibs.png" alt="Logo" />
      </div>
      <div class="navbar-placeholder"></div>
    </nav>

    <!-- 视频播放器区域（粘性定位） -->
    <div class="player-container" ref="playerContainer">
      <!-- 16:9 占位容器 -->
      <div class="video-wrapper" :class="{ 'video-loaded': videoLoaded }">
        <!-- 加载动画（视频加载或缓冲时显示） -->
        <div v-if="!videoLoaded || isBuffering" class="loading-placeholder">
          <div class="loading-spinner"></div>
        </div>
        <video
          ref="video"
          class="video-player"
          :src="currentVideo.url"
          preload="auto"
          @timeupdate="onTimeUpdate"
          @loadedmetadata="onLoadedMetadata"
          @loadeddata="onLoadedData"
          @waiting="onWaiting"
          @playing="onPlaying"
          @dblclick="onDblClick"
          @mousedown="onMouseDown"
          @mouseup="onMouseUp"
          @mouseleave="onMouseLeave"
          @click="onVideoClick"
        ></video>
      </div>

      <!-- 自定义控制栏 -->
      <Transition name="fade">
        <div v-if="controlsVisible" class="controls-overlay" @mousedown.stop>
          <!-- 进度条 -->
          <div class="progress-bar-container" @mousedown="onProgressMouseDown">
            <div class="progress-wrapper" ref="progressWrapper">
              <div class="progress-played" :style="{ width: playedPercent + '%' }"></div>
              <div
                class="progress-handle"
                :style="{ left: playedPercent + '%' }"
                @mousedown.stop="onProgressMouseDown"
              ></div>
            </div>
          </div>

          <!-- 底部控件条 -->
          <div class="controls">
            <!-- 播放/暂停按钮 -->
            <div
              class="play-pause"
              @click="togglePlay"
              @mouseenter="onPlayPauseMouseEnter"
              @mouseleave="onPlayPauseMouseLeave"
            >
              <span v-if="videoPaused" class="play-icon" :class="{ hovered: playPauseHovered }"></span>
              <span v-else class="pause-icon" :class="{ hovered: playPauseHovered }"></span>
            </div>

            <div class="time-display">
              {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
            </div>

            <div class="spacer"></div>

            <!-- 倍速下拉菜单（新样式：无边框，加粗，悬停仅文字变蓝） -->
            <div class="dropdown speed-dropdown" ref="speedDropdown">
              <button
                class="dropdown-btn speed-btn"
                :class="{
                  hovered: speedBtnHovered && !speedBtnClicked,
                  clicked: speedBtnClicked
                }"
                @click="toggleSpeedMenu"
                @mouseenter="onSpeedMouseEnter"
                @mouseleave="onSpeedMouseLeave"
                @mousedown="onSpeedMouseDown"
                @mouseup="onSpeedMouseUp"
              >
                {{ speedButtonText }}
              </button>
              <Transition name="dropdown-fade">
                <div v-if="speedMenuOpen" class="dropdown-menu" :class="{ show: speedMenuOpen }">
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

            <!-- 分辨率下拉菜单（新样式：无边框，加粗，悬停仅文字变蓝） -->
            <div class="dropdown resolution-dropdown" ref="resolutionDropdown">
              <button
                class="dropdown-btn resolution-btn"
                :class="{
                  hovered: resolutionBtnHovered && !resolutionBtnClicked,
                  clicked: resolutionBtnClicked
                }"
                @click="toggleResolutionMenu"
                @mouseenter="onResolutionMouseEnter"
                @mouseleave="onResolutionMouseLeave"
                @mousedown="onResolutionMouseDown"
                @mouseup="onResolutionMouseUp"
              >
                {{ resolutionButtonText }}
              </button>
              <Transition name="dropdown-fade">
                <div v-if="resolutionMenuOpen" class="dropdown-menu" :class="{ show: resolutionMenuOpen }">
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

            <!-- 全屏按钮（保留原样式） -->
            <div
              class="fullscreen-btn-custom"
              :class="{
                hovered: fullscreenBtnHovered && !fullscreenBtnClicked,
                clicked: fullscreenBtnClicked
              }"
              @click="toggleFullscreen"
              @mouseenter="onFullscreenMouseEnter"
              @mouseleave="onFullscreenMouseLeave"
              @mousedown="onFullscreenMouseDown"
              @mouseup="onFullscreenMouseUp"
            >
              <div class="fullscreen-border"></div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 视频标题（紧贴视频下方） -->
    <h1 class="video-title">{{ pageTitle }}</h1>

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
          @mouseenter="onListItemMouseEnter(video)"
          @mouseleave="onListItemMouseLeave(video)"
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

// 视频相关 ref
const video = ref(null)
const playerContainer = ref(null)
const progressWrapper = ref(null)
const currentTime = ref(0)
const duration = ref(0)
const videoPaused = ref(true)
const playbackRate = ref(1.0)
const selectedPlaybackRate = ref(1.0)
const controlsVisible = ref(false)
const videoLoaded = ref(false)
const isLongPressing = ref(false)
const isBuffering = ref(false) // 缓冲状态

// 定时器
let longPressTimer = null
let hideControlsTimer = null
let clickTimer = null

// 下拉菜单状态
const speedMenuOpen = ref(false)
const resolutionMenuOpen = ref(false)
const speedDropdown = ref(null)
const resolutionDropdown = ref(null)

// 按钮状态
const speedBtnClicked = ref(false)
const resolutionBtnClicked = ref(false)
const fullscreenBtnClicked = ref(false)
const speedBtnHovered = ref(false)
const resolutionBtnHovered = ref(false)
const fullscreenBtnHovered = ref(false)
const playPauseHovered = ref(false)

// 列表项悬浮状态
const hoveredListItem = ref(null)

// 分辨率选项
const resolutions = [
  { value: '1080p', label: '1080P 高清' },
  { value: '720p', label: '720P 准高清' },
  { value: '480p', label: '480P 标清' },
  { value: '360p', label: '360P 流畅' }
]
const selectedResolution = ref('720p')

// 倍速选项
const playbackRates = ['2.0', '1.5', '1.25', '1.0', '0.75', '0.5']

// 当前视频信息
const currentVideo = ref({
  url: '',
  name: ''
})

// 页面标题
const pageTitle = computed(() => frontmatter.value.title || currentVideo.value.name)

// 播放进度百分比
const playedPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

// 格式化时间
const formatTime = (seconds) => {
  if (isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 倍速按钮显示文字
const speedButtonText = computed(() => {
  if (isLongPressing.value) return '3.0x'
  return selectedPlaybackRate.value === 1.0 ? '倍速' : selectedPlaybackRate.value + 'x'
})

// 分辨率按钮显示文字
const resolutionButtonText = computed(() => {
  const res = resolutions.find(r => r.value === selectedResolution.value)
  return res ? res.label : '720P 准高清'
})

// ---------- 获取所有视频文件 ----------
const videoModules = import.meta.glob(
  ['/**/*.mp4', '/**/*.webm', '/**/*.ogg', '/**/*.mov', '/**/*.avi', '/**/*.mkv', '/**/*.flv'],
  { eager: true, as: 'url' }
)

// 当前目录
const currentDir = computed(() => {
  const filePath = page.value.filePath
  if (!filePath) return ''
  const lastSlash = filePath.lastIndexOf('/')
  if (lastSlash === -1) return ''
  return filePath.substring(0, lastSlash + 1)
})

// 同目录视频列表
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

// 播放指定视频
const playVideo = (videoItem) => {
  currentVideo.value = videoItem
  videoLoaded.value = false
  isBuffering.value = false
  nextTick(() => {
    if (video.value) {
      video.value.load()
      video.value.play().catch(e => console.log('自动播放失败:', e))
    }
  })
  controlsVisible.value = true
  resetHideControlsTimer()
}

// 初始化当前视频
const initCurrentVideo = () => {
  const list = videoList.value
  if (list.length === 0) return

  let initialVideo = list[0]
  if (frontmatter.value.video) {
    const matched = list.find(v => v.url.endsWith('/' + frontmatter.value.video) || v.name === frontmatter.value.video)
    if (matched) initialVideo = matched
  }
  currentVideo.value = initialVideo
}

watch(videoList, initCurrentVideo, { immediate: true })

// 视频事件
const onTimeUpdate = () => {
  if (video.value) currentTime.value = video.value.currentTime
}
const onLoadedMetadata = () => {
  if (video.value) duration.value = video.value.duration
}
const onLoadedData = () => {
  videoLoaded.value = true
  isBuffering.value = false
}
const onWaiting = () => {
  isBuffering.value = true
}
const onPlaying = () => {
  isBuffering.value = false
}

// 播放/暂停切换
const togglePlay = () => {
  if (!video.value) return
  if (video.value.paused) {
    video.value.play()
  } else {
    video.value.pause()
  }
  videoPaused.value = video.value.paused
  resetHideControlsTimer()
}

// 改变倍速
const selectPlaybackRate = (rate) => {
  selectedPlaybackRate.value = rate
  if (!isLongPressing.value) {
    playbackRate.value = rate
    if (video.value) video.value.playbackRate = rate
  }
  speedMenuOpen.value = false
  resetHideControlsTimer()
}

// 选择分辨率
const selectResolution = (res) => {
  selectedResolution.value = res
  resolutionMenuOpen.value = false
  resetHideControlsTimer()
}

// 长按加速
const onMouseDown = () => {
  if (!video.value) return
  longPressTimer = setTimeout(() => {
    isLongPressing.value = true
    playbackRate.value = 3.0
    if (video.value) video.value.playbackRate = 3.0
  }, 500)
  resetHideControlsTimer()
}
const onMouseUp = () => {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
  if (isLongPressing.value) {
    isLongPressing.value = false
    playbackRate.value = selectedPlaybackRate.value
    if (video.value) video.value.playbackRate = selectedPlaybackRate.value
  }
  resetHideControlsTimer()
}
const onMouseLeave = () => {
  onMouseUp()
}

// 单击视频（延迟处理）
const onVideoClick = () => {
  if (clickTimer) clearTimeout(clickTimer)
  clickTimer = setTimeout(() => {
    controlsVisible.value = !controlsVisible.value
    if (controlsVisible.value) {
      resetHideControlsTimer()
    } else {
      if (hideControlsTimer) clearTimeout(hideControlsTimer)
    }
    clickTimer = null
  }, 250)
}

// 双击视频
const onDblClick = () => {
  if (clickTimer) {
    clearTimeout(clickTimer)
    clickTimer = null
  }
  togglePlay()
}

// 进度条拖拽
const onProgressMouseDown = (e) => {
  e.preventDefault()
  controlsVisible.value = true
  resetHideControlsTimer()

  const wrapper = progressWrapper.value
  if (!wrapper) return

  const updateCurrentTime = (clientX) => {
    const rect = wrapper.getBoundingClientRect()
    let percent = (clientX - rect.left) / rect.width
    percent = Math.max(0, Math.min(1, percent))
    if (video.value && duration.value) {
      video.value.currentTime = percent * duration.value
    }
  }

  updateCurrentTime(e.clientX)

  const onMouseMove = (e) => {
    updateCurrentTime(e.clientX)
    resetHideControlsTimer()
  }
  const onMouseUp = () => {
    resetHideControlsTimer()
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// 重置控制栏隐藏定时器
const resetHideControlsTimer = () => {
  if (hideControlsTimer) clearTimeout(hideControlsTimer)
  hideControlsTimer = setTimeout(() => {
    controlsVisible.value = false
  }, 5000)
}

// 全屏
const toggleFullscreen = () => {
  if (!playerContainer.value) return
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    playerContainer.value.requestFullscreen()
  }
  resetHideControlsTimer()
}

// 返回上一页
const goBack = () => {
  window.history.back()
}

// 下拉菜单切换
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

// 点击外部关闭下拉菜单
const handleClickOutside = (e) => {
  if (speedDropdown.value && !speedDropdown.value.contains(e.target)) {
    speedMenuOpen.value = false
  }
  if (resolutionDropdown.value && !resolutionDropdown.value.contains(e.target)) {
    resolutionMenuOpen.value = false
  }
}
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// ---- 按钮视觉效果 ----
const onPlayPauseMouseEnter = () => { playPauseHovered.value = true }
const onPlayPauseMouseLeave = () => { playPauseHovered.value = false }

const onSpeedMouseEnter = () => { speedBtnHovered.value = true }
const onSpeedMouseLeave = () => { speedBtnHovered.value = false }
const onSpeedMouseDown = () => {
  speedBtnClicked.value = true
  setTimeout(() => {
    if (!speedBtnHovered.value) speedBtnClicked.value = false
  }, 300)
}
const onSpeedMouseUp = () => {}

const onResolutionMouseEnter = () => { resolutionBtnHovered.value = true }
const onResolutionMouseLeave = () => { resolutionBtnHovered.value = false }
const onResolutionMouseDown = () => {
  resolutionBtnClicked.value = true
  setTimeout(() => {
    if (!resolutionBtnHovered.value) resolutionBtnClicked.value = false
  }, 300)
}
const onResolutionMouseUp = () => {}

const onFullscreenMouseEnter = () => { fullscreenBtnHovered.value = true }
const onFullscreenMouseLeave = () => { fullscreenBtnHovered.value = false }
const onFullscreenMouseDown = () => {
  fullscreenBtnClicked.value = true
  setTimeout(() => {
    if (!fullscreenBtnHovered.value) fullscreenBtnClicked.value = false
  }, 300)
}
const onFullscreenMouseUp = () => {}

const onListItemMouseDown = () => {}
const onListItemMouseUp = () => {}
const onListItemMouseEnter = (video) => { hoveredListItem.value = video.url }
const onListItemMouseLeave = (video) => {
  if (hoveredListItem.value === video.url) hoveredListItem.value = null
}
</script>

<style scoped>
/* 隐藏全局滚动条 */
:global(html),
:global(body) {
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
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}
.video-page::-webkit-scrollbar {
  display: none; /* Chrome/Safari/Opera */
}

/* 悬浮导航栏 */
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
  height: 60px; /* 调大logo */
  width: auto;
  pointer-events: none; /* 防止鼠标事件影响，避免任何悬停效果 */
}

.navbar-placeholder {
  width: 60px;
}

/* 视频播放器区域 - 粘性定位 */
.player-container {
  position: sticky;
  top: 60px;
  z-index: 90;
  background-color: #000;
  width: 100%;
  overflow: hidden;
}

/* 16:9 视频包装器 */
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

/* 加载占位（显示于视频上方） */
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
  z-index: 20; /* 确保在视频之上 */
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #2563eb;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 控制栏淡入淡出过渡 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.controls-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  z-index: 10;
}

/* 进度条容器 */
.progress-bar-container {
  padding: 10px 12px 5px;
  cursor: pointer;
}

.progress-wrapper {
  position: relative;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  cursor: pointer;
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
}

/* 底部控件条 */
.controls {
  display: flex;
  align-items: center;
  padding: 5px 12px 10px;
  color: white;
  font-size: 14px;
}

/* 播放/暂停按钮 */
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
.play-pause:active {
  transform: scale(0.98);
}

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
.play-icon.hovered {
  border-left-color: #2563eb;
}

.pause-icon {
  width: 16px;
  height: 20px;
  display: flex;
  justify-content: space-between;
}
.pause-icon::before,
.pause-icon::after {
  content: '';
  width: 5px;
  height: 20px;
  background-color: white;
  border-radius: 2px;
  transition: background-color 0.2s;
}
.pause-icon.hovered::before,
.pause-icon.hovered::after {
  background-color: #2563eb;
}

.time-display {
  margin-right: 15px;
}

.spacer {
  flex: 1;
}

/* 下拉菜单容器 */
.dropdown {
  position: relative;
  margin-right: 15px;
}

/* 下拉菜单按钮（新样式：无边框，加粗，悬停仅文字变蓝） */
.dropdown-btn {
  background: transparent;        /* 无背景 */
  border: none;                   /* 无边框 */
  color: white;
  font-weight: bold;              /* 加粗 */
  padding: 6px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: color 0.2s;
  outline: none;
}
.dropdown-btn.hovered {
  color: #2563eb;                 /* 悬停仅文字变蓝 */
}
.dropdown-btn.clicked {
  transform: scale(0.98);
}

/* 下拉菜单淡入淡出 */
.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
  transition: opacity 0.2s ease;
}
.dropdown-fade-enter-from,
.dropdown-fade-leave-to {
  opacity: 0;
}

.dropdown-menu {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);    /* 水平居中 */
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
.dropdown-item:last-child {
  border-bottom: none;
}
.dropdown-item:hover {
  background-color: #e6f7ff;
}
.dropdown-item.active {
  background-color: #2563eb;
  color: white;
}

/* 全屏按钮（保留原样式） */
.fullscreen-btn-custom {
  width: 32px;
  height: 32px;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s;
  margin-left: 10px;
}
.fullscreen-btn-custom.clicked {
  transform: scale(0.98);
}
.fullscreen-btn-custom.hovered .fullscreen-border {
  border-color: #2563eb;
}
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

/* 视频标题（紧贴视频下方） */
.video-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin: 0;                      /* 清除默认边距 */
  padding: 15px 20px;
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fff;
}

/* 视频选集列表 */
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
