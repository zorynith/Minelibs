import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import './style.css'
import VersionSelector from './components/VersionSelector.vue' // 检查路径

export default {
  extends: DefaultTheme,
  Layout: () => {
    return h(DefaultTheme.Layout, null, {})
  },
  enhanceApp({ app }) {
    app.component('VersionSelector', VersionSelector)
  }
}
