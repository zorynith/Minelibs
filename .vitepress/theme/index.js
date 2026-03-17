import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import './style.css'
import VersionSelector from './components/VersionSelector.vue'
import VideoLayout from './components/VideoLayout.vue' // 导入自定义布局

export default {
  extends: DefaultTheme,
  Layout: () => {
    return h(DefaultTheme.Layout, null, {})
  },
  enhanceApp({ app }) {
    // 注册全局组件
    app.component('VersionSelector', VersionSelector)
    app.component('VideoLayout', VideoLayout) // 注册 VideoLayout
  }
}
