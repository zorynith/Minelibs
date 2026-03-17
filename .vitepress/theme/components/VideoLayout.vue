<template>
  <div class="video-page">
    <!-- 自定义导航栏 -->
    <nav class="custom-navbar">
      <button class="back-btn" @click="goBack">← 返回</button>
      <div class="logo">
        <img src="https://minelibs.eu.org/Minelibs.png" alt="Logo" />
      </div>
    </nav>

    <!-- 视频播放器区域 -->
    <div class="player-container" ref="playerContainer">
      <video
        ref="video"
        class="video-player"
        :src="currentVideo.url"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @dblclick="togglePlay"
        @mousedown="onMouseDown"
        @mouseup="onMouseUp"
        @mouseleave="onMouseLeave"
        @click="onVideoClick"
      ></video>

      <!-- 自定义进度条（单击视频后显示，5秒无操作自动隐藏） -->
      <div
        class="progress-bar-container"
        v-show="showProgressBar"
        @mousedown="onProgressMouseDown"
        @mouseup="onProgressMouseUp"
      >
        <div class="progress-wrapper" ref="progressWrapper">
          <div class="progress-played" :style="{ width: playedPercent + '%' }"></div>
          <div
            class="progress-handle"
            :style="{ left: playedPercent + '%' }"
            @mousedown.stop="onProgressMouseDown"
          ></div>
        </div>
      </div>

      <!-- 底部控件条（始终显示） -->
      <div class="controls">
        <div class="play-pause" @click="togglePlay">
          {{ videoPaused ? '播放' : '暂停' }}
        </div>
        <div class="time-display">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </div>
        <div class="spacer"></div>
        <div class="speed-control">
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

    <!-- 视频标题 -->
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
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useData, useRouter } from 'vitepress'

// 获取当前页面数据
const { frontmatter, page } = useData()
const router = useRouter()

// 视频相关 ref
const video = ref(null)
const playerContainer = ref(null)
const progressWrapper = ref(null)
const currentTime = ref(0)
const duration = ref(0)
const videoPaused = ref(true)
const playbackRate = ref(1.0)
const showProgressBar = ref(false) // 是否显示进度条

// 长按加速计时器
let longPressTimer = null

// 进度条自动隐藏计时器
let hideProgressTimer = null

// 当前视频信息
const currentVideo = ref({
  url: '',
  name: ''
})

// 页面标题：优先使用 frontmatter 中的 title，否则使用当前视频文件名
const pageTitle = computed(() => frontmatter.value.title || currentVideo.value.name)

// 计算播放进度百分比
const playedPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

// 格式化时间为 mm:ss
const formatTime = (seconds) => {
  if (isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// ---------- 获取所有视频文件（支持常见格式）----------
const videoModules = import.meta.glob(
  ['/**/*.mp4', '/**/*.webm', '/**/*.ogg', '/**/*.mov', '/**/*.avi', '/**/*.mkv', '/**/*.flv'],
  { eager: true, as: 'url' }
)

// 获取当前页面的源文件目录
const currentDir = computed(() => {
  const filePath = page.value.filePath // 例如 'mmb/some/page.md'
  if (!filePath) return ''
  const lastSlash = filePath.lastIndexOf('/')
  if (lastSlash === -1) return ''
  return filePath.substring(0, lastSlash + 1) // 包含末尾斜杠，如 'mmb/some/'
})

// 过滤出同目录的视频列表
const videoList = computed(() => {
  const dir = currentDir.value
  if (!dir) return []
  const list = []
  for (const [filePath, url] of Object.entries(videoModules)) {
    // filePath 是相对于项目根目录的路径，如 '/mmb/some/video.mp4'（注意前面的斜杠）
    // 移除开头的斜杠以便与 currentDir 比较
    const relativePath = filePath.startsWith('/') ? filePath.slice(1) : filePath
    if (relativePath.startsWith(dir)) {
      // 提取文件名（不含扩展名）作为显示名称
      const fileName = filePath.split('/').pop().replace(/\.[^/.]+$/, '')
      list.push({ url, name: fileName })
    }
  }
  return list
})

// 设置当前播放的视频
const playVideo = (videoItem) => {
  currentVideo.value = videoItem
  // 更新视频源后需要等待视频加载，然后自动播放
  nextTick(() => {
    if (video.value) {
      video.value.load()
      video.value.play().catch(e => console.log('自动播放失败:', e))
    }
  })
}

// 初始化当前视频：优先使用 frontmatter 中指定的视频文件名，否则取列表第一个
const initCurrentVideo = () => {
  const list = videoList.value
  if (list.length === 0) return

  let initialVideo = list[0]
  if (frontmatter.value.video) {
    // frontmatter 中指定的视频文件名（如 'myvideo.mp4'），需要找到匹配的
    const matched = list.find(v => v.url.endsWith('/' + frontmatter.value.video) || v.name === frontmatter.value.video)
    if (matched) initialVideo = matched
  }
  currentVideo.value = initialVideo
}

watch(videoList, initCurrentVideo, { immediate: true })

// 视频事件处理
const onTimeUpdate = () => {
  if (video.value) currentTime.value = video.value.currentTime
}
const onLoadedMetadata = () => {
  if (video.value) duration.value = video.value.duration
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
}

// 改变播放速度
const changeSpeed = () => {
  if (video.value) video.value.playbackRate = playbackRate.value
}

// 长按加速逻辑
const onMouseDown = () => {
  if (!video.value) return
  longPressTimer = setTimeout(() => {
    video.value.playbackRate = 3.0
  }, 500)
}
const onMouseUp = () => {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
  if (video.value) video.value.playbackRate = playbackRate.value
}
const onMouseLeave = () => {
  onMouseUp()
}

// 单击视频：显示进度条并重置隐藏计时器
const onVideoClick = () => {
  showProgressBar.value = true
  resetHideProgressTimer()
}

// 进度条拖拽相关
const onProgressMouseDown = (e) => {
  e.preventDefault()
  // 显示进度条并重置计时器（防止自动隐藏）
  showProgressBar.value = true
  resetHideProgressTimer()

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
    // 拖动时重置计时器
    resetHideProgressTimer()
  }
  const onMouseUp = () => {
    // 松开鼠标后重置计时器
    resetHideProgressTimer()
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

const onProgressMouseUp = () => {
  // 松开鼠标时重置计时器（已在 onMouseUp 中处理）
}

// 重置进度条隐藏计时器：清除旧定时器，5秒后隐藏
const resetHideProgressTimer = () => {
  if (hideProgressTimer) {
    clearTimeout(hideProgressTimer)
  }
  hideProgressTimer = setTimeout(() => {
    showProgressBar.value = false
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
}

// 返回按钮：跳转到上一级目录
const goBack = () => {
  // 获取当前页面的路径（不带 .html）
  const currentPath = router.route.path // 例如 '/mmb/some/page'
  const parentPath = currentPath.substring(0, currentPath.lastIndexOf('/')) || '/'
  router.go(parentPath)
}
</script>

<style scoped>
.video-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  background-color: #fff;
  min-height: 100vh;
}

.custom-navbar {
  display: flex;
  align-items: center;
  padding: 10px 0;
  background-color: white;
  border-bottom: 1px solid #eee;
}

.back-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: #333;
  cursor: pointer;
  margin-right: 20px;
}

.logo img {
  height: 40px;
  width: auto;
}

.player-container {
  position: relative;
  background-color: #000;
  margin: 20px 0;
  border-radius: 8px;
  overflow: hidden;
}

.video-player {
  width: 100%;
  display: block;
  cursor: pointer;
}

.progress-bar-container {
  position: absolute;
  bottom: 50px;
  left: 0;
  right: 0;
  padding: 10px;
  background: rgba(0, 0, 0, 0.6);
  transition: opacity 0.2s;
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
  background-color: #1e90ff; /* 纯蓝色 */
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

.controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: white;
  font-size: 14px;
}

.play-pause {
  cursor: pointer;
  margin-right: 15px;
  user-select: none;
}

.time-display {
  margin-right: 15px;
}

.spacer {
  flex: 1;
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
  margin-left: 15px;
}

.video-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin: 20px 0;
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
