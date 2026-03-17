import { h, defineComponent } from 'vue'
import DefaultTheme from 'vitepress/theme'
import { useData } from 'vitepress'
import './style.css'
import VersionSelector from './components/VersionSelector.vue'
import VideoLayout from './components/VideoLayout.vue'

export default {
  extends: DefaultTheme,
  Layout: defineComponent({
    setup() {
      const { frontmatter } = useData()
      return () => {
        // 如果 frontmatter 中指定了 layout: VideoLayout，则使用自定义视频布局
        if (frontmatter.value?.layout === 'VideoLayout') {
          return h(VideoLayout)
        }
        // 否则使用默认主题布局
        return h(DefaultTheme.Layout)
      }
    }
  }),
  enhanceApp({ app }) {
    app.component('VersionSelector', VersionSelector)
    app.component('VideoLayout', VideoLayout)
  }
}
