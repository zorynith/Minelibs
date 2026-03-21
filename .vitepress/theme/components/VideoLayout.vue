<template>
  <div class="video-page">
    <!-- 导航栏 -->
    <nav class="custom-navbar">
      <button class="back-btn" @click="goBack">← 返回</button>
      <div class="logo"><img src="https://minelibs.eu.org/Minelibs.png" alt="Logo" /></div>
      <div class="navbar-placeholder"></div>
    </nav>

    <!-- 播放器容器 -->
    <div class="player-container" ref="playerContainer">
      <VideoPlayer
        ref="videoPlayerComp"
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
      <!-- 缓冲加载动画 -->
      <div v-if="isBuffering && !videoPaused" class="loading-overlay">
        <div class="loading-spinner"></div>
      </div>

      <!-- 分辨率菜单 -->
      <div class="resolution-dropdown" ref="resolutionDropdown">
        <button
          class="resolution-btn"
          :class="{ hovered: resolutionBtnHovered && !resolutionBtnClicked, clicked: resolutionBtnClicked }"
          @click="toggleResolutionMenu"
          @mouseenter="resolutionBtnHovered = true"
          @mouseleave="resolutionBtnHovered = false"
          @mousedown="handleResolutionBtnMouseDown"
          @mouseup="handleResolutionBtnMouseUp"
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
    </div>

    <!-- 视频标题 -->
    <h1 class="video-title">{{ pageTitle }}</h1>

    <!-- 视频选集 -->
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
import VideoPlayer from 'vue-video-player'   // 默认导入（避免命名冲突）

const router = useRouter()
const { frontmatter, page } = useData()

// 播放器相关
const videoPlayerComp = ref(null)
const playerContainer = ref(null)
let player = null

// 视频数据
const currentVideo = ref({ url: '', name: '' })
const videoPaused = ref(true)
const isBuffering = ref(false)
const selectedPlaybackRate = ref(1.0)
const selectedResolution = ref('720p')
const resolutionMenuOpen = ref(false)
const resolutionDropdown = ref(null)

// UI 状态
const resolutionBtnHovered = ref(false)
const resolutionBtnClicked = ref(false)
const hoveredListItem = ref(null)

// 定时器
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

// 分辨率按钮文字
const resolutionButtonText = computed(() => {
  const res = resolutions.find(r => r.value === selectedResolution.value)
  return res ? res.label : '720P 准高清'
})

// 播放器配置
const playerOptions = ref({
  autoplay: false,
  controls: true,
  preload: 'auto',
  fluid: true,
  aspectRatio: '16:9',
  controlBar: {
    children: [
      'playToggle',
      'currentTimeDisplay',
      'timeDivider',
      'durationDisplay',
      'progressControl',
      'remainingTimeDisplay',
      'volumePanel',
      'playbackRateMenuButton',
      'fullscreenToggle'
    ]
  },
  playbackRates: [0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
  userActions: { hotkeys: true }
})

// ---------- 获取视频文件 ----------
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

// 播放视频
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

// 播放器就绪
const onPlayerReady = (p) => {
  player = p
  player.src(currentVideo.value.url)
  player.load()
  player.playbackRate(selectedPlaybackRate.value)
  player.on('ratechange', () => {
    selectedPlaybackRate.value = player.playbackRate()
  })
  player.on('play', () => { videoPaused.value = false })
  player.on('pause', () => { videoPaused.value = true })
  player.on('waiting', () => { isBuffering.value = true })
  player.on('playing', () => { isBuffering.value = false })
}
const onPlay = () => { videoPaused.value = false }
const onPause = () => { videoPaused.value = true }
const onTimeUpdate = () => {}
const onWaiting = () => { isBuffering.value = true }
const onPlaying = () => { isBuffering.value = false }

// 双击暂停/播放
const onDblClick = (event) => {
  event.preventDefault()
  if (player.paused()) player.play()
  else player.pause()
}

// 长按加速
let isLongPressing = false
const onMouseDown = () => {
  if (!player) return
  longPressTimer = setTimeout(() => {
    isLongPressing = true
    const original = player.playbackRate()
    player.playbackRate(3.0)
    window.__originalRate = original
  }, 500)
}
const onMouseUp = () => {
  if (longPressTimer) clearTimeout(longPressTimer)
  if (isLongPressing) {
    isLongPressing = false
    const original = window.__originalRate
    if (original !== undefined) {
      player.playbackRate(original)
      selectedPlaybackRate.value = original
      delete window.__originalRate
    }
  }
}
const onMouseLeave = () => onMouseUp()

// 分辨率切换（假设文件命名：basename_1080p.mp4）
const selectResolution = (res) => {
  selectedResolution.value = res
  resolutionMenuOpen.value = false
  if (player) {
    const base = currentVideo.value.url.replace(/\.[^/.]+$/, '')
    const ext = currentVideo.value.url.match(/\.[^/.]+$/)[0]
    const newUrl = `${base}_${res}${ext}`
    player.src(newUrl)
    player.load()
    player.play()
  }
}

// 菜单显示/隐藏
const toggleResolutionMenu = () => {
  resolutionMenuOpen.value = !resolutionMenuOpen.value
  if (resolutionMenuOpen.value) {
    if (hideResolutionTimer) clearTimeout(hideResolutionTimer)
    hideResolutionTimer = setTimeout(() => {
      resolutionMenuOpen.value = false
    }, 5000)
  }
}

// 分辨率按钮点击效果
const handleResolutionBtnMouseDown = () => {
  resolutionBtnClicked.value = true
  setTimeout(() => {
    if (!resolutionBtnHovered.value) resolutionBtnClicked.value = false
  }, 300)
}
const handleResolutionBtnMouseUp = () => {}

// 点击外部关闭菜单
const handleClickOutside = (e) => {
  if (resolutionDropdown.value && !resolutionDropdown.value.contains(e.target)) {
    resolutionMenuOpen.value = false
  }
}
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
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
  if (player) player.dispose()
})

// 返回
const goBack = () => window.history.back()
</script>

<style scoped>
/* 隐藏全局滚动条（同上） */
:global(html), :global(body) { overflow: hidden; height: 100%; margin: 0; padding: 0; }
.video-page { max-width: 100%; margin: 0; padding: 0; background-color: #fff; height: 100vh; overflow-y: auto; scrollbar-width: none; -ms-overflow-style: none; }
.video-page::-webkit-scrollbar { display: none; }

.custom-navbar { position: fixed; top: 0; left: 0; right: 0; height: 60px; background: white; border-bottom: 1px solid #eee; display: flex; align-items: center; padding: 0 20px; z-index: 100; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.back-btn { background: none; border: none; font-size: 16px; color: #333; cursor: pointer; width: 60px; text-align: left; }
.logo { position: absolute; left: 50%; transform: translateX(-50%); }
.logo img { height: 60px; width: auto; pointer-events: none; }
.navbar-placeholder { width: 60px; }

.player-container { position: sticky; top: 60px; z-index: 90; background: #000; width: 100%; overflow: visible; }
.video-player { width: 100%; height: auto; }
.video-js { width: 100% !important; height: auto !important; aspect-ratio: 16 / 9; }

.loading-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.5); z-index: 20; pointer-events: none; }
.loading-spinner { width: 50px; height: 50px; border: 5px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: #2563eb; animation: spin 1s infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.resolution-dropdown { position: absolute; bottom: 70px; right: 20px; z-index: 200; }
.resolution-btn { background: rgba(0,0,0,0.7); color: white; border: none; font-weight: bold; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 14px; transition: 0.2s; }
.resolution-btn.hovered { background: rgba(0,0,0,0.9); color: #2563eb; }
.resolution-btn.clicked { transform: scale(0.98); }
.resolution-menu { position: absolute; bottom: 100%; right: 0; margin-bottom: 5px; background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); min-width: 120px; overflow: hidden; }
.resolution-item { padding: 8px 16px; cursor: pointer; color: #333; font-size: 14px; border-bottom: 1px solid #f0f0f0; transition: 0.2s; }
.resolution-item:last-child { border-bottom: none; }
.resolution-item:hover { background-color: #e6f7ff; }
.resolution-item.active { background-color: #2563eb; color: white; }

.video-title { font-size: 24px; font-weight: bold; color: #333; margin: 0; padding: 15px 20px; border-top: 1px solid #e0e0e0; border-bottom: 1px solid #e0e0e0; background-color: #fff; }
.video-list { margin: 0 20px 20px; }
.video-list h2 { font-size: 18px; color: #666; margin-bottom: 10px; }
.video-list ul { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.video-list li { padding: 12px 16px; background: #f5f5f5; border-radius: 12px; cursor: pointer; transition: 0.2s; color: #333; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.video-list li.active { background: #2563eb; color: white; cursor: default; pointer-events: none; }
.video-list li:not(.active).hovered { background: #2563eb; color: white; }
.video-list li:not(.active):active { transform: scale(0.98); }
</style>
