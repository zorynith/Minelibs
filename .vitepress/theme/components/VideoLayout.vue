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

    <!-- 视频播放器区域 -->
    <div class="player-container" ref="playerContainer">
      <video-player
        ref="videoPlayer"
        class="video-player vjs-custom-skin"
        :options="playerOptions"
        @ready="onPlayerReady"
        @play="onPlay"
        @pause="onPause"
        @timeupdate="onTimeUpdate"
        @waiting="onWaiting"
        @playing="onPlaying"
        @dblclick="onDblClick"
      />
      <!-- 加载动画（缓冲时显示） -->
      <div v-if="isBuffering && !videoPaused" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>
    </div>

    <!-- 视频标题 -->
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
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useData } from 'vitepress'
import 'video.js/dist/video-js.css'
import { videoPlayer } from 'vue-video-player'

const router = useRouter()
const { frontmatter, page } = useData()

// 播放器实例
const videoPlayer = ref(null)
const playerContainer = ref(null)
let player = null

// 视频状态
const currentVideo = ref({ url: '', name: '' })
const currentTime = ref(0)
const duration = ref(0)
const videoPaused = ref(true)
const isBuffering = ref(false)
const selectedPlaybackRate = ref(1.0)
const selectedResolution = ref('720p')
const speedMenuOpen = ref(false)
const resolutionMenuOpen = ref(false)
const speedDropdown = ref(null)
const resolutionDropdown = ref(null)

// 按钮悬停/点击状态（仅用于分辨率菜单）
const resolutionBtnHovered = ref(false)
const resolutionBtnClicked = ref(false)
const hoveredListItem = ref(null)

// 长按加速定时器
let longPressTimer = null
let hideResolutionTimer = null

// 分辨率选项
const resolutions = [
  { value: '1080p', label: '1080P 高清' },
  { value: '720p', label: '720P 准高清' },
  { value: '480p', label: '480P 标清' },
  { value: '360p', label: '360P 流畅' }
]

// 页面标题
const pageTitle = computed(() => frontmatter.value.title || currentVideo.value.name)

// 分辨率按钮显示文字
const resolutionButtonText = computed(() => {
  const res = resolutions.find(r => r.value === selectedResolution.value)
  return res ? res.label : '720P 准高清'
})

// 视频播放器配置
const playerOptions = ref({
  autoplay: false,
  controls: true,               // 显示原生控制栏
  preload: 'auto',
  fluid: true,                 // 自适应容器
  aspectRatio: '16:9',         // 强制 16:9
  controlBar: {
    // 保留所有原生控件，但可以通过 children 自定义顺序
    children: [
      'playToggle',
      'currentTimeDisplay',
      'timeDivider',
      'durationDisplay',
      'progressControl',
      'remainingTimeDisplay',
      'volumePanel',
      'playbackRateMenuButton', // 原生倍速菜单
      'fullscreenToggle'
    ],
    volumePanel: { inline: false }
  },
  playbackRates: [0.5, 0.75, 1.0, 1.25, 1.5, 2.0], // 原生倍速选项
  userActions: {
    hotkeys: true               // 启用热键（空格、左右箭头等）
  },
  // 自定义主题色（可选）
  // 通过 CSS 覆盖即可，不用在此配置
})

// ---------- 获取所有视频文件 ----------
const videoModules = import.meta.glob(
  ['/**/*.mp4', '/**/*.webm', '/**/*.ogg', '/**/*.mov', '/**/*.avi', '/**/*.mkv', '/**/*.flv'],
  { eager: true, as: 'url' }
)

const currentDir = computed(() => {
  const filePath = page.value.filePath
  if (!filePath) return ''
  const lastSlash = filePath.lastIndexOf('/')
  if (lastSlash === -1) return ''
  return filePath.substring(0, lastSlash + 1)
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

// 播放指定视频
const playVideo = (videoItem) => {
  if (currentVideo.value.url === videoItem.url) return
  currentVideo.value = videoItem
  if (player) {
    player.src(videoItem.url)
    player.load()
    player.play()
  }
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

// 播放器准备就绪
const onPlayerReady = (playerInstance) => {
  player = playerInstance
  player.src(currentVideo.value.url)
  player.load()
  // 设置初始倍速
  player.playbackRate(selectedPlaybackRate.value)
  // 监听倍速变化（原生控件改变时同步）
  player.on('ratechange', () => {
    selectedPlaybackRate.value = player.playbackRate()
  })
  // 监听全屏变化（可选）
  player.on('fullscreenchange', () => {})
  // 监听播放暂停
  player.on('play', () => { videoPaused.value = false })
  player.on('pause', () => { videoPaused.value = true })
  player.on('timeupdate', () => { currentTime.value = player.currentTime() })
  player.on('loadedmetadata', () => { duration.value = player.duration() })
  player.on('waiting', () => { isBuffering.value = true })
  player.on('playing', () => { isBuffering.value = false })
}

const onPlay = () => { videoPaused.value = false }
const onPause = () => { videoPaused.value = true }
const onTimeUpdate = () => { if (player) currentTime.value = player.currentTime() }
const onWaiting = () => { isBuffering.value = true }
const onPlaying = () => { isBuffering.value = false }

// 双击暂停/播放（覆盖原生双击全屏行为）
const onDblClick = (event) => {
  // 阻止原生双击全屏
  event.preventDefault()
  if (player.paused()) {
    player.play()
  } else {
    player.pause()
  }
}

// 长按加速（长按 500ms 后倍速变为 3.0，松开恢复）
let isLongPressing = false
const onMouseDown = () => {
  if (!player) return
  longPressTimer = setTimeout(() => {
    isLongPressing = true
    // 记录原倍速
    const originalRate = player.playbackRate()
    player.playbackRate(3.0)
    // 保存原倍速，待松开时恢复
    window.__originalPlaybackRate = originalRate
  }, 500)
}
const onMouseUp = () => {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
  if (isLongPressing) {
    isLongPressing = false
    const originalRate = window.__originalPlaybackRate
    if (originalRate !== undefined) {
      player.playbackRate(originalRate)
      selectedPlaybackRate.value = originalRate
      delete window.__originalPlaybackRate
    }
  }
}
const onMouseLeave = () => {
  onMouseUp()
}

// 分辨率切换（改变视频源）
const selectResolution = (res) => {
  selectedResolution.value = res
  resolutionMenuOpen.value = false
  // 这里可以根据分辨率切换不同的视频源，但需要预先准备不同分辨率的视频文件
  // 简单起见，我们假设同一视频有多种分辨率文件，命名规则如：video_1080p.mp4
  // 根据当前视频的基础名，拼接分辨率后缀
  if (player) {
    const baseName = currentVideo.value.url.replace(/\.[^/.]+$/, '')
    const ext = currentVideo.value.url.match(/\.[^/.]+$/)[0]
    const newUrl = `${baseName}_${res}${ext}`
    // 检查文件是否存在，如果存在则切换，否则提示或不做处理
    // 由于无法在客户端直接检查文件是否存在，这里简单尝试切换，若失败则忽略
    player.src(newUrl)
    player.load()
    player.play()
  }
}

// 分辨率下拉菜单显示/隐藏
const toggleResolutionMenu = () => {
  resolutionMenuOpen.value = !resolutionMenuOpen.value
  if (resolutionMenuOpen.value) {
    // 自动隐藏菜单的定时器（可选）
    if (hideResolutionTimer) clearTimeout(hideResolutionTimer)
    hideResolutionTimer = setTimeout(() => {
      resolutionMenuOpen.value = false
    }, 5000)
  }
}

// 点击外部关闭分辨率菜单
const handleClickOutside = (e) => {
  if (resolutionDropdown.value && !resolutionDropdown.value.contains(e.target)) {
    resolutionMenuOpen.value = false
  }
}
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // 监听视频容器鼠标事件以实现长按加速
  if (playerContainer.value) {
    playerContainer.value.addEventListener('mousedown', onMouseDown)
    playerContainer.value.addEventListener('mouseup', onMouseUp)
    playerContainer.value.addEventListener('mouseleave', onMouseLeave)
  }
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  if (playerContainer.value) {
    playerContainer.value.removeEventListener('mousedown', onMouseDown)
    playerContainer.value.removeEventListener('mouseup', onMouseUp)
    playerContainer.value.removeEventListener('mouseleave', onMouseLeave)
  }
  if (player) {
    player.dispose()
  }
})

// 分辨率按钮鼠标效果
const onResolutionMouseEnter = () => { resolutionBtnHovered.value = true }
const onResolutionMouseLeave = () => { resolutionBtnHovered.value = false }
const onResolutionMouseDown = () => {
  resolutionBtnClicked.value = true
  setTimeout(() => {
    if (!resolutionBtnHovered.value) resolutionBtnClicked.value = false
  }, 300)
}
const onResolutionMouseUp = () => {}

// 列表项效果
const onListItemMouseEnter = (video) => { hoveredListItem.value = video.url }
const onListItemMouseLeave = (video) => {
  if (hoveredListItem.value === video.url) hoveredListItem.value = null
}
const onListItemMouseDown = () => {}
const onListItemMouseUp = () => {}

// 返回上一页
const goBack = () => {
  window.history.back()
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
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.video-page::-webkit-scrollbar {
  display: none;
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
  height: 60px;
  width: auto;
  pointer-events: none;
}

.navbar-placeholder {
  width: 60px;
}

/* 视频播放器区域 */
.player-container {
  position: sticky;
  top: 60px;
  z-index: 90;
  background-color: #000;
  width: 100%;
  overflow: hidden;
}

/* 覆盖 video.js 默认样式，使其适应容器 */
.video-player {
  width: 100%;
  height: auto;
}
.video-js {
  width: 100% !important;
  height: auto !important;
  aspect-ratio: 16 / 9;
}
/* 自定义加载动画覆盖层 */
.loading-overlay {
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
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 视频标题 */
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

/* 分辨率自定义菜单（放在视频区域外，与播放器同级） */
.resolution-dropdown {
  position: absolute;
  bottom: 70px;
  right: 20px;
  z-index: 200;
}
.resolution-btn {
  background: rgba(0,0,0,0.7);
  color: white;
  border: none;
  font-weight: bold;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: color 0.2s, background 0.2s;
}
.resolution-btn.hovered {
  background: rgba(0,0,0,0.9);
  color: #2563eb;
}
.resolution-btn.clicked {
  transform: scale(0.98);
}
.resolution-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  margin-bottom: 5px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 120px;
  overflow: hidden;
}
.resolution-item {
  padding: 8px 16px;
  cursor: pointer;
  color: #333;
  font-size: 14px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}
.resolution-item:last-child {
  border-bottom: none;
}
.resolution-item:hover {
  background-color: #e6f7ff;
}
.resolution-item.active {
  background-color: #2563eb;
  color: white;
}
</style>

<!-- 添加自定义分辨率菜单（在模板末尾） -->
<template>
  <!-- ... 原有内容 ... -->
  <div class="resolution-dropdown" ref="resolutionDropdown">
    <button
      class="resolution-btn"
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
    <div v-if="resolutionMenuOpen" class="resolution-menu">
      <div
        v-for="res in resolutions"
        :key="res.value"
        class="resolution-item"
        :class="{ active: selectedResolution === res.value }"
        @click="selectResolution(res.value)"
      >
        {{ res.label }}
      </div>
    </div>
  </div>
</template>

<!-- 注意：上述 template 代码应合并到主 template 中，请将分辨率菜单放到 player-container 之外，但为了视觉位置，可以放在 player-container 内部底部。实际实现中，请将这部分插入到适当位置。此处为清晰，我们已在 script 中定义了相关变量和函数，模板需包含该部分。 -->