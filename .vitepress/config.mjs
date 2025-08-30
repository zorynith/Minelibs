import { defineConfig } from 'vitepress'
import { withSidebar } from 'vitepress-sidebar';

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Minelibs",
  description: "A Minecraft Version Library",
    head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['link', { rel: 'stylesheet', href: '/custom.css' }]
  ],
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    logo: "/Logo.svg",
    siteTitle: false,
    nav: [
      { text: 'Home', link: '/' },
      { text: 'All Versions', link: '/versions/0.1' },
      { text: 'Bedrock Edition', link: '/docs/bedrock-edition' },
      { text: 'Java Edition', link: '/docs/java-edition' }
    ],

    sidebar: {
      '/docs/': [
        {
          text: 'Minecraft Edition',
          items: [
            { text: 'Bedrock Edition', link: '/docs/bedrock-edition' },
            { text: 'Pocket Edition', link: '/docs/pocket-edition' },
            { text: 'Java Edition', link: '/docs/java-edition' }
          ]
        }
      ],
      '/versions/': [
        {
          text: 'Versions',
          items: [
            { text: '0.1', link: '/versions/0.1' },
            { text: '0.2', link: '/versions/0.2' },
            { text: '0.3', link: '/versions/0.3' }
          ]
        }
      ]
    },

    socialLinks: [
      { 
        icon: {
          svg: '<svg t="1755695950433" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="11203" width="200" height="200"><path d="M808.398269 218.955161c20.458525 11.691232 27.566623 37.753501 15.876521 58.213157l-65.330296 114.329713c119.461015 74.88989 203.198446 202.202702 217.966199 350.95283 2.492185 25.107214-17.227161 46.882472-42.457572 46.882472H85.333333c-25.230411 0-44.949757-21.775258-42.457571-46.882472 14.120124-142.220715 91.287453-264.84528 202.445704-340.790817l-71.137484-124.491726c-11.691232-20.459656-4.583135-46.521925 15.876521-58.213157 20.459656-11.691232 46.523055-4.583135 58.214287 15.876521l71.589581 125.281766c58.218808-25.812486 122.559011-40.113448 190.028856-40.113448 60.891832 0 119.233837 11.648283 172.825431 32.893457l67.465324-118.061775c11.691232-20.459656 37.754631-27.567753 58.214287-15.876521zM317.895488 554.666667c-23.563302 0-42.666667 19.102234-42.666667 42.666666s19.103364 42.666667 42.666667 42.666667c23.565563 0 42.666667-19.102234 42.666667-42.666667s-19.101104-42.666667-42.666667-42.666666z m384 0c-23.563302 0-42.666667 19.102234-42.666667 42.666666s19.103364 42.666667 42.666667 42.666667c23.565563 0 42.666667-19.102234 42.666667-42.666667s-19.101104-42.666667-42.666667-42.666666z" p-id="11204" fill="#707070"></path></svg>'
        },
        link: 'https://files.bendy.eu.org/Minecraft/Minecraft%20For%20Android/' 
      },
      {
        icon: {
          svg: '<svg t="1755696405508" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="13258" width="200" height="200"><path d="M490.666667 128v362.666667H128V128h362.666667z m0 768H128v-362.666667h362.666667V896z m42.666666-768H896v362.666667h-362.666667V128z m362.666667 405.333333V896h-362.666667v-362.666667H896z" p-id="13259" fill="#707070"></path></svg>'
        },
        link: 'https://files.minelibs.eu.org/Minecraft/Minecraft%20for%20Windows/'
      },
      {
        icon: {
          svg: '<svg t="1755696829390" class="icon" viewBox="0 0 1088 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="14254" width="200" height="200"><path d="M821.248 544c-1.28-129.728 105.792-191.904 110.56-194.976-60.096-88.032-153.792-100.128-187.264-101.536-79.808-7.968-155.584 46.976-196 46.976s-102.816-45.696-168.992-44.544c-86.88 1.28-167.04 50.592-211.84 128.448-90.336 156.768-23.168 388.928 64.864 515.968 42.976 62.176 94.336 132.032 161.632 129.6 64.864-2.56 89.312-41.952 167.712-41.952s100.384 41.952 169.12 40.672c69.76-1.28 114.016-63.456 156.768-125.856 49.408-72.192 69.76-142.08 70.912-145.568-1.536-0.768-136.16-52.256-137.44-207.2z m-128.96-380.544c35.776-43.36 59.84-103.488 53.28-163.456-51.488 2.048-113.888 34.24-150.848 77.472-33.088 38.496-62.176 99.744-54.304 158.432 57.408 4.512 116.096-29.216 151.872-72.448z" p-id="14255" fill="#707070"></path></svg>'
        },
        link: 'https://files.bendy.eu.org/Minecraft/Minecraft%20For%20iOS/'
      }
    ],

    search: {
      provider: "local",
      options: {
        translations: {
          button: {
            buttonText: "搜索版本",
            buttonAriaLabel: "搜索版本",
          },
          modal: {
            noResultsText: "无法找到相关结果",
            resetButtonTitle: "清除查询条件",
            footer: {
              selectText: "选择",
              navigateText: "切换",
              closeText: "关闭",
            },
          },
        },
      },
    },

    footer: {
      copyright: "Copyright@ 2025 Minelibs"
    }
  }
})
