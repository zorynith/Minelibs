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

    <!-- 视频播放器区域（粘性定位，悬浮在导航栏下方） -->
    <div class="player-container" ref="playerContainer">
      <!-- 16:9 占位容器 -->
      <div class="video-wrapper" :class="{ 'video-loaded': videoLoaded }">
        <div v-if="!videoLoaded" class="loading-placeholder">
          <div class="loading-spinner"></div>
        </div>
        <video
          ref="video"
          class="video-player"
          :src="currentVideo.url"
          preload="metadata"
          @timeupdate="onTimeUpdate"
          @loadedmetadata="onLoadedMetadata"
          @loadeddata="onLoadedData"
          @dblclick="onDblClick"
          @mousedown="onMouseDown"
          @mouseup="onMouseUp"
          @mouseleave="onMouseLeave"
          @click="onVideoClick"
        ></video>
      </div>

      <!-- 自定义控制栏（使用 Transition 实现淡入淡出） -->
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
            <div class="play-pause" @click="togglePlay">
              <span v-if="videoPaused" class="play-icon"></span>
              <span v-else class="pause-icon"></span>
            </div>
            <div class="time-display">
              {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
            </div>
            <div class="spacer"></div>
            <div class="speed-control">
              <span class="speed-label">倍速</span>
              <select v-model="playbackRate" @change="changeSpeed">
                <option value="0.25">0.25x</option>
                <option value="0.5">0.5x</option>
                <option value="1.0" selected>1.0x</option>
                <option value="1.25">1.25x</option>
                <option value="1.5">1.5x</option>
                <option value="2.0">2.0x</option>
              </select>
            </div>
            <div class="fullscreen-btn" @click="toggleFullscreen">全屏</div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- 视频标题（上下带横线） -->
    <h1 class="video-title">{{ pageTitle }}</h1>

    <!-- 同目录视频列表 -->
    <div class="video-list">
      <h2>当前目录下的视频</h2>
      <ul>
        <li
          v-for="video in videoList"
          :key="video.url"
          :class="{ active: video.url === currentVideo.url }"
          @click="video.url !== currentVideo.url && playVideo(video)"
        >
          {{ video.name }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
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
const controlsVisible = ref(false)
const videoLoaded = ref(false)

// 定时器
let longPressTimer = null
let hideControlsTimer = null
let clickTimer = null          // 用于延迟显示/隐藏控制栏

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
const changeSpeed = () => {
  if (video.value) video.value.playbackRate = playbackRate.value
  resetHideControlsTimer()
}

// 长按加速
const onMouseDown = () => {
  if (!video.value) return
  longPressTimer = setTimeout(() => {
    video.value.playbackRate = 3.0
  }, 500)
  resetHideControlsTimer()
}
const onMouseUp = () => {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
  if (video.value) video.value.playbackRate = playbackRate.value
  resetHideControlsTimer()
}
const onMouseLeave = onMouseUp

// 单击视频（延迟执行，避免与双击冲突）
const onVideoClick = () => {
  if (clickTimer) clearTimeout(clickTimer)
  clickTimer = setTimeout(() => {
    // 切换控制栏显示状态
    controlsVisible.value = !controlsVisible.value
    if (controlsVisible.value) {
      resetHideControlsTimer()
    } else {
      if (hideControlsTimer) {
        clearTimeout(hideControlsTimer)
        hideControlsTimer = null
      }
    }
    clickTimer = null
  }, 250) // 250ms 延迟，略大于双击间隔
}

// 双击视频（立即暂停，并取消单击的延迟操作）
const onDblClick = () => {
  if (clickTimer) {
    clearTimeout(clickTimer)
    clickTimer = null
  }
  togglePlay() // 双击暂停/播放
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
</script>

<style scoped>
.video-page {
  max-width: 100%;
  margin: 0;
  padding: 0;
  background-color: #fff;
  min-height: 100vh;
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
  height: 50px; /* 调大logo */
  width: auto;
}

.navbar-placeholder {
  width: 60px;
}

/* 视频播放器区域 - 粘性定位，悬浮在导航栏下方 */
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

/* 加载占位 */
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
  z-index: 5;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #1e90ff;
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
  background-color: #1e90ff;
  border-radius: 3px;
  pointer-events: none;
}

.progress-handle {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background-color: #1e90ff;
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

.play-pause {
  cursor: pointer;
  margin-right: 15px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 播放图标（右三角）- 使用圆角风格，通过旋转正方形实现 */
.play-icon {
  width: 0;
  height: 0;
  border-left: 16px solid white;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  border-radius: 2px; /* 给三角形添加轻微圆角效果（作用于border的角，不明显） */
  margin-left: 4px;
}

/* 暂停图标（两条竖线）- 已圆角 */
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

.time-display {
  margin-right: 15px;
}

.spacer {
  flex: 1;
}

.speed-control {
  display: flex;
  align-items: center;
  margin-right: 15px;
}

.speed-label {
  margin-right: 5px;
  color: white;
}

.speed-control select {
  background: rgba(0,0,0,0.5);
  color: white;
  border: 1px solid #1e90ff;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
}

.fullscreen-btn {
  cursor: pointer;
}

/* 视频标题 - 上下加横线，紧贴两端 */
.video-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin: 20px 0; /* 上下边距，左右为0 */
  padding: 15px 20px; /* 左右内边距保持内容与边缘距离，但横线紧贴两端 */
  border-top: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fff;
}

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
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.video-list li {
  padding: 8px 16px;
  background-color: #f5f5f5;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: #333;
}

.video-list li.active {
  background-color: #1e90ff;
  color: white;
  cursor: default;
  pointer-events: none;
}

.video-list li:not(.active):hover {
  background-color: #e0e0e0;
}
</style>
