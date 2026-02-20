<template>
  <div 
    class="mine-version-selector" 
    @contextmenu.prevent 
    @dragstart.prevent 
    @selectstart.prevent
  >
    <!-- 预加载下载按钮 -->
    <div style="display: none;">
      <img src="https://minelibs.eu.org/resources/button/CLOUDFLARE_CDN.svg" alt="preload" loading="eager" fetchpriority="high">
      <img src="https://minelibs.eu.org/resources/button/EDGEONE_CDN.svg" alt="preload" loading="eager" fetchpriority="high">
      <img src="https://minelibs.eu.org/resources/button/DIRECT_DOWNLOAD.svg" alt="preload" loading="eager" fetchpriority="high">
    </div>

    <!-- 页面切换过渡（平台/版本列表） -->
    <Transition name="mine-page" mode="out-in" appear>
      <!-- 平台选择界面 -->
      <div v-if="!selectedPlatform" key="platform" class="mine-platform-selection">
        <h2>选择你的平台</h2>
        <div class="mine-platform-buttons">
          <button
            v-for="platform in platforms"
            :key="platform"
            class="mine-platform-btn"
            @click="choosePlatform(platform)"
            draggable="false"
          >
            <span class="mine-platform-icon" v-html="platformSvg[platform]"></span>
            <div class="mine-platform-info">
              <span class="mine-platform-name">{{ platformNames[platform] }}</span>
              <span class="mine-platform-desc">{{ platformDescs[platform] }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- 版本列表界面 -->
      <div v-else key="versions" class="mine-versions-page">
        <!-- 顶部导航 -->
        <div class="mine-content-header">
          <button class="mine-back-btn" @click="goBack" draggable="false">切换平台</button>
          <h2>Minecraft For {{ platformNames[selectedPlatform] }}</h2>
          <div class="mine-header-line"></div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="mine-loading-container">
          <div class="mine-loader">
            <div class="mine-loader-inner">
              <img src="https://minelibs.eu.org/minelibs.svg" alt="Loading" draggable="false">
              <div class="mine-spacer"></div>
              <div class="mine-progress-line">
                <div class="mine-slider"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 错误提示 -->
        <div v-else-if="error" class="mine-error-card">
          <p>{{ error }}</p>
          <button class="mine-retry-btn" @click="fetchData" draggable="false">重试</button>
        </div>

        <!-- 内容区域 -->
        <div v-else class="mine-content">
          <!-- 最新版本卡片 -->
          <div v-if="latestVersion" class="mine-latest-version">
            <div class="mine-version-badge">最新版本</div>
            <div class="mine-version-number">{{ latestVersion.version }}</div>
            <div class="mine-version-meta">
              <span>大小：{{ latestVersion.size }}</span>
              <span>类型：{{ getFileType(latestVersion.fileName) }}</span>
            </div>
            <button class="mine-download-btn" @click="openModal(latestVersion)" draggable="false">下载</button>
          </div>

          <!-- 所有版本列表 -->
          <div class="mine-history-versions">
            <h3>所有版本</h3>
            <div class="mine-history-header-line"></div>
            <div v-if="currentPlatformVersions.length === 0" class="mine-empty">暂无版本</div>
            
            <!-- 翻页列表整体淡入淡出 -->
            <Transition :name="'mine-list-fade'" mode="out-in">
              <ul :key="currentPage" class="mine-version-list">
                <li v-for="ver in paginatedVersions" :key="ver.version" class="mine-version-item">
                  <span class="mine-ver-number">{{ ver.version }}</span>
                  <span class="mine-ver-size">{{ ver.size }}</span>
                  <span class="mine-ver-type">{{ getFileType(ver.fileName) }}</span>
                  <button class="mine-download-link" @click="openModal(ver)" draggable="false">下载</button>
                </li>
              </ul>
            </Transition>

            <!-- 分页按钮 -->
            <div v-if="totalPages > 1" class="mine-pagination">
              <button @click="currentPage--" :disabled="currentPage === 1" class="mine-page-btn" draggable="false">上一页</button>
              <span class="mine-page-info">{{ currentPage }} / {{ totalPages }}</span>
              <button @click="currentPage++" :disabled="currentPage === totalPages" class="mine-page-btn" draggable="false">下一页</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 下载模态框 -->
    <Transition name="mine-modal">
      <div v-if="modalVisible" class="mine-modal-overlay" @click.self="closeModal">
        <div class="mine-modal-container">
          <div class="mine-modal-header">
            <span class="mine-modal-title">选择下载线路</span>
            <button class="mine-modal-close" @click="closeModal" draggable="false">×</button>
          </div>
          <div class="mine-modal-body">
            <div class="mine-file-info">
              <div class="mine-file-name">{{ selectedVersion?.version }}</div>
              <div class="mine-file-meta">{{ selectedVersion?.size }} • {{ getFileType(selectedVersion?.fileName) }}</div>
            </div>
            <div class="mine-download-options">
              <button class="mine-download-option" @click="download(selectedVersion, 'cdn1')" draggable="false">
                <img src="https://minelibs.eu.org/resources/button/CLOUDFLARE_CDN.svg" alt="Cloudflare CDN" draggable="false" oncontextmenu="return false">
              </button>
              <button class="mine-download-option" @click="download(selectedVersion, 'cdn2')" draggable="false">
                <img src="https://minelibs.eu.org/resources/button/EDGEONE_CDN.svg" alt="EdgeOne CDN" draggable="false" oncontextmenu="return false">
              </button>
              <button class="mine-download-option" @click="download(selectedVersion, 'direct')" draggable="false">
                <img src="https://minelibs.eu.org/resources/button/DIRECT_DOWNLOAD.svg" alt="Direct Download" draggable="false" oncontextmenu="return false">
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 下载错误提示 -->
    <div class="mine-download-error-toast" :class="{ show: showErrorToast }">
      <svg t="1771386121797" viewBox="0 0 1287 1024" width="60" height="60">
        <path d="M1271.149714 325.9392c-15.842743 20.114286-45.2608 20.114286-63.356343 4.534857-600.912457-526.7456-1109.050514-22.381714-1131.680914 0-9.069714 8.791771-20.3776 13.312-31.685486 13.312-11.307886 0-22.6304-4.520229-31.685485-13.312-15.828114-15.594057-18.095543-44.514743 0-62.610286 4.534857-6.787657 589.604571-587.088457 1255.892114-4.534857 18.358857 15.594057 20.626286 44.763429 2.516114 62.610286z" fill="#d81e06"></path>
        <path d="M1090.369829 455.182629c15.579429 12.068571 19.104914 31.919543 12.580571 48.771657a296.5504 296.5504 0 0 0-70.407314-8.543086c-10.561829 0-20.874971 0.497371-30.9248 1.506743-408.078629-328.118857-731.413943 12.317257-744.491886 27.648-9.040457 11.073829-22.6304 15.594057-33.938286 15.594057-9.055086 0-20.362971-4.534857-29.403428-11.0592-18.110171-15.594057-18.110171-44.500114-2.282057-62.610286 4.534857-4.534857 413.359543-437.482057 898.8672-11.307885z m-462.877258 80.457142c64.6144-2.779429 127.707429 15.067429 187.816229 52.809143-21.123657 21.855086-38.473143 47.0016-52.297143 74.415543-43.256686-26.155886-86.747429-39.233829-131.247543-37.975771-112.888686 2.267429-196.608 100.322743-196.608 100.322743-15.857371 20.114286-45.012114 22.381714-63.370971 6.787657-20.362971-15.579429-22.6304-42.232686-6.787657-62.610286 4.768914-6.524343 108.865829-126.976 262.495085-133.749029z m13.312 238.855315c23.639771 0 47.279543 9.552457 63.868343 26.141257a89.2928 89.2928 0 0 1 26.404572 63.107657c0 23.391086-9.552457 46.518857-26.404572 63.107657a91.896686 91.896686 0 0 1-63.868343 26.155886c-23.625143 0-47.250286-9.552457-63.853714-26.155886a89.2928 89.2928 0 0 1-26.404571-63.107657c0-23.376457 9.552457-46.518857 26.404571-63.107657a91.896686 91.896686 0 0 1 63.853714-26.141257zM1040.5888 573.586286c-123.201829 0-223.275886 99.810743-223.275886 223.012571 0 123.201829 100.059429 223.275886 223.275886 223.275886 123.201829 0 223.261257-99.825371 223.261257-223.012572 0-123.201829-99.810743-223.275886-223.261257-223.275885z m114.146743 276.816457c9.303771 9.303771 3.262171 30.178743-13.575314 47.030857-16.603429 16.5888-37.712457 22.615771-47.016229 13.575314l-53.818514-53.803885-53.803886 53.803885c-9.303771 9.303771-30.164114 3.262171-47.016229-13.575314-16.5888-16.603429-22.6304-37.727086-13.575314-47.030857l53.803886-53.803886-53.803886-53.803886c-9.303771-9.303771-3.262171-30.164114 13.575314-47.016228 16.603429-16.5888 37.712457-22.6304 47.016229-13.575314l53.803886 53.803885 53.818514-53.803885c9.303771-9.303771 30.164114-3.262171 47.016229 13.575314 16.5888 16.603429 22.6304 37.712457 13.575314 47.016228l-53.803886 53.803886 53.803886 53.803886z" fill="#d81e06"></path>
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// 平台定义
const platforms = ['windows', 'ios', 'android']
const platformNames = {
  windows: 'Windows',
  ios: 'iOS',
  android: 'Android'
}
const platformDescs = {
  windows: '适用于 Windows 10/11 的应用包',
  ios: '适用于 iPhone/iPad 的安装包',
  android: '适用于 Android 设备的 APK 文件'
}

// 文件类型映射
const typeMap = {
  '.apk': 'Android Application Package',
  '.appx': 'Windows App Package',
  '.exe': 'Windows Executable',
  '.ipa': 'iOS App Store Package'
}

// SVG 图标
const platformSvg = {
  windows: `<svg viewBox="0 0 1024 1024" width="48" height="48"><path d="M490.666667 128v362.666667H128V128h362.666667z m0 768H128v-362.666667h362.666667V896z m42.666666-768H896v362.666667h-362.666667V128z m362.666667 405.333333V896h-362.666667v-362.666667H896z" fill="currentColor"></path></svg>`,
  ios: `<svg viewBox="0 0 1088 1024" width="48" height="48"><path d="M821.248 544c-1.28-129.728 105.792-191.904 110.56-194.976-60.096-88.032-153.792-100.128-187.264-101.536-79.808-7.968-155.584 46.976-196 46.976s-102.816-45.696-168.992-44.544c-86.88 1.28-167.04 50.592-211.84 128.448-90.336 156.768-23.168 388.928 64.864 515.968 42.976 62.176 94.336 132.032 161.632 129.6 64.864-2.56 89.312-41.952 167.712-41.952s100.384 41.952 169.12 40.672c69.76-1.28 114.016-63.456 156.768-125.856 49.408-72.192 69.76-142.08 70.912-145.568-1.536-0.768-136.16-52.256-137.44-207.2z m-128.96-380.544c35.776-43.36 59.84-103.488 53.28-163.456-51.488 2.048-113.888 34.24-150.848 77.472-33.088 38.496-62.176 99.744-54.304 158.432 57.408 4.512 116.096-29.216 151.872-72.448z" fill="currentColor"></path></svg>`,
  android: `<svg viewBox="0 0 1024 1024" width="48" height="48"><path d="M808.398269 218.955161c20.458525 11.691232 27.566623 37.753501 15.876521 58.213157l-65.330296 114.329713c119.461015 74.88989 203.198446 202.202702 217.966199 350.95283 2.492185 25.107214-17.227161 46.882472-42.457572 46.882472H85.333333c-25.230411 0-44.949757-21.775258-42.457571-46.882472 14.120124-142.220715 91.287453-264.84528 202.445704-340.790817l-71.137484-124.491726c-11.691232-20.459656-4.583135-46.521925 15.876521-58.213157 20.459656-11.691232 46.523055-4.583135 58.214287 15.876521l71.589581 125.281766c58.218808-25.812486 122.559011-40.113448 190.028856-40.113448 60.891832 0 119.233837 11.648283 172.825431 32.893457l67.465324-118.061775c11.691232-20.459656 37.754631-27.567753 58.214287-15.876521zM317.895488 554.666667c-23.563302 0-42.666667 19.102234-42.666667 42.666666s19.103364 42.666667 42.666667 42.666667c23.565563 0 42.666667-19.102234 42.666667-42.666667s-19.101104-42.666667-42.666667-42.666666z m384 0c-23.563302 0-42.666667 19.102234-42.666667 42.666666s19.103364 42.666667 42.666667 42.666667c23.565563 0 42.666667-19.102234 42.666667-42.666667s-19.101104-42.666667-42.666667-42.666666z" fill="currentColor"></path></svg>`
}

// 状态
const selectedPlatform = ref(null)
const versionsData = ref({ windows: [], ios: [], android: [] })
const loading = ref(false)
const error = ref(null)
const currentPage = ref(1)
const pageSize = 10

// 模态框
const modalVisible = ref(false)
const selectedVersion = ref(null)

// 下载错误提示
const showErrorToast = ref(false)
let toastTimer = null

// 计算当前平台的所有版本
const currentPlatformVersions = computed(() => versionsData.value[selectedPlatform.value] || [])

// 最新版本
const latestVersion = computed(() => currentPlatformVersions.value[0] || null)

// 分页数据
const paginatedVersions = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return currentPlatformVersions.value.slice(start, start + pageSize)
})

const totalPages = computed(() => Math.ceil(currentPlatformVersions.value.length / pageSize))

// 获取文件类型
function getFileType(fileName) {
  if (!fileName) return '文件'
  const ext = fileName.substring(fileName.lastIndexOf('.')).toLowerCase()
  return typeMap[ext] || (ext ? ext.substring(1).toUpperCase() : '文件')
}

// 选择平台
function choosePlatform(platform) {
  selectedPlatform.value = platform
  currentPage.value = 1
  if (versionsData.value[platform].length === 0) {
    fetchData()
  }
}

// 返回平台选择
function goBack() {
  selectedPlatform.value = null
  error.value = null
}

// 获取数据
async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const [res1, res2] = await Promise.all([
      fetch('https://files.minelibs.eu.org/api/versions', { cache: 'force-cache' }),
      fetch('https://files.bendy.eu.org/api/versions', { cache: 'force-cache' })
    ])

    if (!res1.ok) throw new Error('Windows 加载失败')
    if (!res2.ok) throw new Error('iOS/Android 加载失败')

    const data1 = await res1.json()
    const data2 = await res2.json()

    versionsData.value = {
      windows: data1.windows || [],
      ios: data2.ios || [],
      android: data2.android || []
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// 打开模态框
function openModal(version) {
  selectedVersion.value = version
  modalVisible.value = true
  document.body.style.overflow = 'hidden'
}

// 关闭模态框
function closeModal() {
  modalVisible.value = false
  document.body.style.overflow = ''
}

// 显示下载错误
function showError() {
  if (toastTimer) {
    clearTimeout(toastTimer)
    showErrorToast.value = false
  }
  showErrorToast.value = true
  toastTimer = setTimeout(() => {
    showErrorToast.value = false
    toastTimer = null
  }, 3000)
}

// 下载处理
async function download(version, type) {
  if (!version) return
  let baseUrl = ''
  const platform = selectedPlatform.value
  
  if (type === 'cdn1') {
    baseUrl = platform === 'windows' 
      ? 'https://files.bendy.minelibs.eu.org' 
      : 'https://files.minelibs.bendy.eu.org'
  } else if (type === 'cdn2') {
    baseUrl = platform === 'windows'
      ? 'https://edgeone.files.minelibs.eu.org'
      : 'https://1.edgeone.files.minelibs.eu.org'
  } else {
    baseUrl = platform === 'windows'
      ? 'https://files.minelibs.eu.org'
      : 'https://files.bendy.eu.org'
  }
  
  const url = baseUrl + version.downloadUrl
  try {
    await fetch(url, { method: 'HEAD', mode: 'no-cors', cache: 'no-store' })
    const iframe = document.createElement('iframe')
    iframe.style.display = 'none'
    iframe.src = url
    document.body.appendChild(iframe)
    setTimeout(() => {
      if (iframe.parentNode) iframe.remove()
    }, 60000)
    closeModal()
  } catch (error) {
    console.warn('下载失败', error)
    showError()
  }
}
</script>

<style>
/* 全局禁止选中、拖拽、右键菜单 */
.mine-version-selector,
.mine-version-selector * {
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
  user-select: none !important;
  -webkit-touch-callout: none !important;
  -webkit-user-drag: none !important;
  -khtml-user-drag: none !important;
  -moz-user-drag: none !important;
  -o-user-drag: none !important;
  user-drag: none !important;
}

.mine-version-selector img {
  -webkit-user-drag: none !important;
  -khtml-user-drag: none !important;
  -moz-user-drag: none !important;
  -o-user-drag: none !important;
  user-drag: none !important;
  pointer-events: none;
}

.mine-version-selector button {
  -webkit-touch-callout: none !important;
}

/* 全局根样式 */
.mine-version-selector {
  --primary: #2563eb !important;
  --border: rgba(0, 0, 0, 0.15) !important;
  --text-primary: #707070 !important;
  --text-secondary: #909090 !important;
  --hover-bg: #f5f5f5 !important;

  width: 100% !important;
  background: transparent !important;
  color: var(--text-primary) !important;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif !important;
}

/* 深色模式 */
.dark .mine-version-selector {
  --border: rgba(255, 255, 255, 0.2) !important;
  --text-primary: #b0b0b0 !important;
  --text-secondary: #888 !important;
  --hover-bg: #2a2a2a !important;
}

/* ===== 平台选择 ===== */
.mine-platform-selection {
  text-align: center !important;
  padding: 20px 0 !important;
}

.mine-platform-selection h2 {
  font-size: 2rem !important;
  margin-bottom: 30px !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  border-top: none !important;
  border-bottom: 1.5px solid var(--border) !important;
  border-left: none !important;
  border-right: none !important;
  padding-bottom: 15px !important;
  margin-top: 0 !important;
}

.mine-platform-buttons {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  gap: 20px !important;
  max-width: 600px !important;
  margin: 0 auto !important;
  padding: 0 20px !important;
}

.mine-platform-btn {
  display: flex !important;
  align-items: center !important;
  gap: 24px !important;
  width: 100% !important;
  padding: 16px 24px !important;
  background: transparent !important;
  border: 2px solid var(--primary) !important;
  border-radius: 16px !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  color: var(--primary) !important;
  box-shadow: none !important;
  outline: none !important;
}

.mine-platform-btn:hover {
  background: var(--primary) !important;
  color: #ffffff !important;
  border-color: var(--primary) !important;
  transform: none !important;
}

.mine-platform-btn:hover .mine-platform-icon svg {
  color: #ffffff !important;
}

.mine-platform-btn:active {
  transform: scale(0.98) !important;
}

.mine-platform-icon {
  flex-shrink: 0 !important;
  width: 48px !important;
  height: 48px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.mine-platform-icon svg {
  width: 100% !important;
  height: 100% !important;
  transition: color 0.15s ease !important;
  color: currentColor !important;
}

.mine-platform-info {
  flex: 1 !important;
  text-align: left !important;
}

.mine-platform-name {
  display: block !important;
  font-size: 1.5rem !important;
  font-weight: 600 !important;
  margin-bottom: 4px !important;
}

.mine-platform-desc {
  display: block !important;
  font-size: 0.9rem !important;
  color: inherit !important;
  opacity: 0.9 !important;
}

/* ===== 版本列表 ===== */
.mine-versions-page {
  width: 100% !important;
}

/* 顶部导航 */
.mine-content-header {
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-start !important;
  gap: 10px !important;
  margin-bottom: 30px !important;
  border: none !important;
  padding-bottom: 0 !important;
}

.mine-back-btn {
  background: transparent !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 30px !important;
  padding: 8px 16px !important;
  font-size: 0.95rem !important;
  color: var(--text-primary) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.mine-back-btn:hover {
  border-color: var(--primary) !important;
  color: var(--primary) !important;
}

.mine-back-btn:active {
  transform: scale(0.97) !important;
}

.mine-content-header h2 {
  margin: 0 !important;
  font-size: 1.8rem !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  border: none !important;
  width: 100% !important;
}

.mine-header-line {
  width: 100% !important;
  height: 1.5px !important;
  background: var(--border) !important;
  margin-top: 5px !important;
}

/* 加载动画 */
.mine-loading-container {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  min-height: 300px !important;
}

.mine-loader .mine-loader-inner {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  width: fit-content !important;
  max-width: 90vw !important;
  transform: translateY(-15px) !important;
}

.mine-loader img {
  display: block !important;
  width: 80px !important;
  height: auto !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  vertical-align: bottom !important;
  border: 0 !important;
}

.mine-spacer {
  width: 100% !important;
  height: 56px !important;
  flex-shrink: 0 !important;
}

.mine-progress-line {
  position: relative !important;
  width: 120px !important;
  max-width: 100% !important;
  height: 5px !important;
  background: #e5e5e5 !important;
  border-radius: 9999px !important;
  overflow: hidden !important;
}

.mine-slider {
  position: absolute !important;
  top: 0 !important;
  left: -37.5% !important;
  width: 37.5% !important;
  height: 100% !important;
  background: linear-gradient(90deg, #70eeee, #6acd77) !important;
  border-radius: 9999px !important;
  animation: mine-slideShuttle 1.8s linear infinite !important;
  z-index: 2 !important;
}

.mine-slider::before,
.mine-slider::after {
  content: '' !important;
  position: absolute !important;
  top: 0 !important;
  width: 45% !important;
  height: 100% !important;
  pointer-events: none !important;
  z-index: 3 !important;
}

.mine-slider::before {
  left: 0 !important;
  background: linear-gradient(90deg, #e5e5e5, rgba(112,238,238,0)) !important;
  border-radius: 9999px 0 0 9999px !important;
}

.mine-slider::after {
  right: 0 !important;
  background: linear-gradient(90deg, rgba(106,205,119,0), #e5e5e5) !important;
  border-radius: 0 9999px 9999px 0 !important;
}

@keyframes mine-slideShuttle {
  0% { left: -37.5%; }
  33.33% { left: 100%; }
  50% { left: 100%; }
  83.33% { left: -37.5%; }
  100% { left: -37.5%; }
}

/* 错误卡片 */
.mine-error-card {
  text-align: center !important;
  padding: 40px 20px !important;
  background: transparent !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--text-secondary) !important;
}

.mine-error-card p {
  font-size: 1.2rem !important;
  margin-bottom: 20px !important;
}

.mine-retry-btn {
  background: var(--primary) !important;
  color: #ffffff !important;
  border: none !important;
  padding: 10px 30px !important;
  border-radius: 9999px !important;
  font-size: 1rem !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.mine-retry-btn:active {
  transform: scale(0.95) !important;
}

/* 最新版本卡片 */
.mine-latest-version {
  background: transparent !important;
  border: 2px solid var(--primary) !important;
  border-radius: 20px !important;
  padding: 30px !important;
  margin-bottom: 40px !important;
  text-align: center !important;
  position: relative !important;
  overflow: hidden !important;
}

.mine-version-badge {
  position: absolute !important;
  top: 15px !important;
  right: 15px !important;
  background: var(--primary) !important;
  color: #ffffff !important;
  padding: 4px 12px !important;
  border-radius: 9999px !important;
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.mine-version-number {
  font-size: 3rem !important;
  font-weight: 700 !important;
  color: var(--primary) !important;
  margin-bottom: 10px !important;
}

.mine-version-meta {
  display: flex !important;
  justify-content: center !important;
  gap: 30px !important;
  color: var(--text-secondary) !important;
  font-size: 1.1rem !important;
  margin-bottom: 25px !important;
}

/* 下载按钮 */
.mine-download-btn {
  display: inline-block !important;
  background: transparent !important;
  color: var(--primary) !important;
  text-decoration: none !important;
  padding: 12px 40px !important;
  border-radius: 9999px !important;
  font-weight: 600 !important;
  font-size: 1.2rem !important;
  transition: all 0.15s ease !important;
  border: 2px solid var(--primary) !important;
  cursor: pointer !important;
}

.mine-download-btn:hover {
  background: var(--primary) !important;
  color: #ffffff !important;
  border-color: var(--primary) !important;
}

.mine-download-btn:active {
  transform: scale(0.97) !important;
}

/* 所有版本区域 */
.mine-history-versions {
  margin-top: 20px !important;
}

.mine-history-versions h3 {
  font-size: 1.5rem !important;
  margin-bottom: 10px !important;
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  border: none !important;
}

.mine-history-header-line {
  width: 100% !important;
  height: 1.5px !important;
  background: var(--border) !important;
  margin-bottom: 20px !important;
}

.mine-version-list {
  list-style: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
}

.mine-version-item {
  display: flex !important;
  align-items: center !important;
  padding: 15px 20px !important;
  margin: 0 !important;
  border-bottom: 1px solid var(--border) !important;
  background: transparent !important;
  transition: background 0.15s !important;
}

.mine-version-item:last-child {
  border-bottom: none !important;
}

.mine-version-item:hover {
  background: var(--hover-bg) !important;
}

.mine-ver-number {
  flex: 2 !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}

.mine-ver-size {
  flex: 1 !important;
  color: var(--text-secondary) !important;
  margin-right: 15px !important;
}

.mine-ver-type {
  flex: 1 !important;
  color: var(--text-secondary) !important;
  margin-right: 15px !important;
}

.mine-download-link {
  width: 80px !important;
  flex: none !important;
  text-align: center !important;
  background: transparent !important;
  border: 2px solid var(--border) !important;
  border-radius: 9999px !important;
  color: var(--text-primary) !important;
  font-weight: normal !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  padding: 5px 0 !important;
  font-size: 0.9rem !important;
  line-height: 1.2 !important;
}

.mine-download-link:hover {
  background: transparent !important;
  color: var(--primary) !important;
  border-color: var(--primary) !important;
}

.mine-download-link:active {
  transform: scale(0.95) !important;
}

.mine-empty {
  text-align: center !important;
  padding: 30px !important;
  color: var(--text-secondary) !important;
  border: 1.5px dashed var(--border) !important;
  border-radius: 12px !important;
}

/* 分页按钮 */
.mine-pagination {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  gap: 20px !important;
  margin-top: 30px !important;
}

.mine-page-btn {
  background: transparent !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 9999px !important;
  padding: 8px 20px !important;
  color: var(--text-primary) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

.mine-page-btn:hover:not(:disabled) {
  border-color: var(--primary) !important;
  color: var(--primary) !important;
}

.mine-page-btn:active:not(:disabled) {
  transform: scale(0.97) !important;
}

.mine-page-btn:disabled {
  opacity: 0.4 !important;
  cursor: not-allowed !important;
}

.mine-page-info {
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
}

/* 列表整体淡入淡出动画 */
.mine-list-fade-enter-active,
.mine-list-fade-leave-active {
  transition: opacity 0.3s ease !important;
}
.mine-list-fade-enter-from,
.mine-list-fade-leave-to {
  opacity: 0 !important;
}

/* 页面切换 */
.mine-page-enter-active,
.mine-page-leave-active {
  transition: opacity 0.4s ease, transform 0.4s ease !important;
}
.mine-page-enter-from {
  opacity: 0 !important;
  transform: translateY(15px) !important;
}
.mine-page-leave-to {
  opacity: 0 !important;
  transform: translateY(-15px) !important;
}

/* 模态框 */
.mine-modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  background: rgba(0, 0, 0, 0.5) !important;
  display: flex !important;
  align-items: flex-end !important;
  justify-content: center !important;
  z-index: 1000 !important;
}

.mine-modal-container {
  width: 100% !important;
  max-width: 500px !important;
  background: #ffffff !important;
  border-radius: 30px 30px 0 0 !important;
  transform: translateY(0) !important;
  transition: transform 0.3s ease-out !important;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15) !important;
  overflow: hidden !important;
}

.dark .mine-modal-container {
  background: #1e1e1e !important;
  color: #e0e0e0 !important;
}

.mine-modal-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  padding: 20px 24px !important;
  border-bottom: 1.5px solid var(--border) !important;
}

.mine-modal-title {
  font-size: 1.2rem !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}

.mine-modal-close {
  width: 40px !important;
  height: 40px !important;
  border: 1.5px solid var(--border) !important;
  background: transparent !important;
  border-radius: 50% !important;
  font-size: 1.8rem !important;
  line-height: 1 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  color: var(--text-primary) !important;
  transition: all 0.15s ease !important;
  padding: 0 !important;
  font-family: Arial, sans-serif !important;
}

.mine-modal-close:hover {
  border-color: var(--primary) !important;
  color: var(--primary) !important;
}

.mine-modal-close:active {
  transform: scale(0.95) !important;
}

.mine-modal-body {
  padding: 24px !important;
}

.mine-file-info {
  text-align: center !important;
  margin-bottom: 20px !important;
}

.mine-file-name {
  font-size: 1.8rem !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  margin-bottom: 5px !important;
}

.mine-file-meta {
  color: var(--text-secondary) !important;
  font-size: 1rem !important;
}

.mine-download-options {
  display: flex !important;
  flex-direction: column !important;
  gap: 15px !important;
}

.mine-download-option {
  width: 100% !important;
  border: none !important;
  background: transparent !important;
  cursor: pointer !important;
  transition: transform 0.15s ease !important;
  padding: 0 !important;
}

.mine-download-option:hover {
  transform: scale(1.02) !important;
}

.mine-download-option:active {
  transform: scale(0.98) !important;
}

.mine-download-option img {
  width: 60% !important;
  height: auto !important;
  display: block !important;
  border-radius: 14px !important;
  border: 1.5px solid var(--border) !important;
  transition: border-color 0.15s !important;
  margin: 0 auto;
}

.mine-download-option:hover img {
  border-color: var(--primary) !important;
}

/* 模态框过渡 */
.mine-modal-enter-active,
.mine-modal-leave-active {
  transition: opacity 0.3s ease !important;
}
.mine-modal-enter-active .mine-modal-container,
.mine-modal-leave-active .mine-modal-container {
  transition: transform 0.3s ease-out !important;
}
.mine-modal-enter-from {
  opacity: 0 !important;
}
.mine-modal-enter-from .mine-modal-container {
  transform: translateY(100%) !important;
}
.mine-modal-leave-to {
  opacity: 0 !important;
}
.mine-modal-leave-to .mine-modal-container {
  transform: translateY(100%) !important;
}

/* 下载错误提示 */
.mine-download-error-toast {
  position: fixed !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) scale(0.9) !important;
  width: 120px !important;
  height: 120px !important;
  background: #ffffff !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 20px !important;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 2000 !important;
  opacity: 0 !important;
  visibility: hidden !important;
  transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s !important;
  pointer-events: none !important;
}
.mine-download-error-toast.show {
  opacity: 1 !important;
  visibility: visible !important;
  transform: translate(-50%, -50%) scale(1) !important;
}
.mine-download-error-toast svg {
  width: 60px !important;
  height: 60px !important;
  display: block !important;
}

/* 电脑端模态框宽度加大 */
@media (min-width: 769px) {
  .mine-modal-container {
    max-width: 600px !important;
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .mine-platform-btn {
    padding: 14px 20px !important;
  }
  .mine-platform-icon {
    width: 40px !important;
    height: 40px !important;
  }
  .mine-platform-name {
    font-size: 1.3rem !important;
  }
  .mine-platform-desc {
    font-size: 0.8rem !important;
  }
  .mine-version-number {
    font-size: 2rem !important;
  }
  .mine-version-meta {
    flex-direction: column !important;
    gap: 5px !important;
  }
  .mine-version-item {
    flex-wrap: wrap !important;
    gap: 8px !important;
  }
  .mine-ver-number,
  .mine-ver-size,
  .mine-ver-type {
    flex: auto !important;
    width: 100% !important;
    margin-right: 0 !important;
  }
  .mine-download-link {
    width: 80px !important;
    flex: none !important;
    text-align: center !important;
    margin-left: 0 !important;
  }
  .mine-modal-container {
    max-width: 100% !important;
    border-radius: 20px 20px 0 0 !important;
  }
}

@media (max-width: 480px) {
  .mine-content-header {
    align-items: flex-start !important;
  }
}
</style>
