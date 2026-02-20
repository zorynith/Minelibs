#!/usr/bin/env python3
"""
HTTP代理服务器 - 完整修复版
运行端口: 60000
同时修复新闻跳转和搜索问题
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import time

class CompleteFixProxyHandler(http.server.BaseHTTPRequestHandler):
    """完整修复的代理处理器 - 同时修复新闻跳转和搜索问题"""

    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def do_GET(self):
        """处理GET请求"""
        try:
            print(f"GET请求: {self.path}")
            
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/proxy?url='):
                self._proxy_webpage()
            elif self.path.startswith('/proxy?') and 'url=' not in self.path:
                # 关键修复：处理搜索后生成的URL（没有url参数的情况）
                self._handle_search_result()
            else:
                self._proxy_resource()
        except Exception as e:
            self.send_error(500, "Server Error: " + str(e))

    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request_fixed()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_error(500, "Server Error: " + str(e))

    def _handle_search_result(self):
        """专门处理搜索后生成的URL - 关键修复搜索问题"""
        try:
            # 解析当前路径中的参数
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            print(f"搜索参数: {query_params}")
            
            # 从Referer中获取原始搜索页面URL
            referer = self.headers.get('Referer', '')
            if referer and '/proxy?url=' in referer:
                # 提取原始搜索页面的URL
                referer_parsed = urllib.parse.urlparse(referer)
                referer_query = urllib.parse.parse_qs(referer_parsed.query)
                base_search_url = referer_query.get('url', [''])[0]
                
                if base_search_url:
                    # 构建搜索结果的完整URL
                    # 对于360搜索，搜索结果页通常是 www.so.com/s 加上参数
                    search_result_url = "https://www.so.com/s"
                    
                    # 添加所有搜索参数
                    if query_params:
                        search_result_url += "?" + urllib.parse.urlencode(query_params, doseq=True)
                    
                    print(f"构建搜索结果URL: {search_result_url}")
                    
                    # 代理这个搜索结果页面
                    self._proxy_specific_url(search_result_url)
                    return
            
            # 如果无法从Referer获取，尝试其他方法
            self._try_auto_fix_search()
            
        except Exception as e:
            print(f"搜索处理错误: {str(e)}")
            self.send_error(500, "Search processing error: " + str(e))

    def _try_auto_fix_search(self):
        """尝试自动修复搜索URL"""
        try:
            # 解析当前路径
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # 检查是否包含搜索参数
            if 'q' in query_params or 'query' in query_params or 'keyword' in query_params:
                # 假设是360搜索
                search_result_url = "https://www.so.com/s"
                
                if query_params:
                    search_result_url += "?" + urllib.parse.urlencode(query_params, doseq=True)
                
                print(f"自动修复搜索URL: {search_result_url}")
                self._proxy_specific_url(search_result_url)
                return
            
            # 如果无法修复，返回错误
            self.send_error(400, "无法处理的搜索请求")
            
        except Exception as e:
            print(f"自动修复错误: {str(e)}")
            self.send_error(500, "Auto-fix error: " + str(e))

    def _proxy_specific_url(self, target_url):
        """代理特定URL"""
        print(f"代理特定URL: {target_url}")
        
        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        try:
            response = requests.get(target_url, headers=headers, timeout=30, verify=False)
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to fetch: " + str(e))
            return
        
        if response.status_code != 200:
            self.send_error(response.status_code, "Target returned " + str(response.status_code))
            return
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_content_complete(response.text, target_url)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(rewritten_content.encode('utf-8'))
        else:
            self._proxy_raw_content(response)

    def _serve_homepage(self):
        """提供代理主页界面"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>完整修复代理 - 60000端口</title>
            <meta charset="utf-8">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    background: #f5f5f5;
                }
                .container { 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 30px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { 
                    color: #333; 
                    text-align: center;
                }
                .form-group { 
                    margin: 20px 0; 
                }
                input[type="url"] { 
                    width: 100%; 
                    padding: 12px; 
                    border: 1px solid #ddd; 
                    border-radius: 5px; 
                    font-size: 16px;
                    box-sizing: border-box;
                }
                button { 
                    background: #007cba; 
                    color: white; 
                    border: none; 
                    padding: 12px 24px; 
                    border-radius: 5px; 
                    cursor: pointer; 
                    font-size: 16px;
                    width: 100%;
                }
                button:hover { 
                    background: #005a87; 
                }
                .info {
                    background: #e7f3ff;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid #007cba;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 完整修复代理服务</h1>
                <div class="info">
                    <strong>修复内容：</strong> 同时解决新闻直接跳转和搜索问题。
                </div>
                <form action="/proxy" method="GET">
                    <div class="form-group">
                        <input type="url" name="url" placeholder="https://www.example.com" required value="https://www.so.com">
                    </div>
                    <button type="submit">开始代理访问</button>
                </form>
                <div style="margin-top: 20px; text-align: center; color: #666;">
                    <small>代理服务运行在端口 60000 | 新闻跳转与搜索问题已修复</small>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(homepage_html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(homepage_html.encode('utf-8'))

    def _proxy_webpage(self):
        """代理并重写网页内容"""
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]

        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return

        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url

        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        try:
            response = requests.get(target_url, headers=headers, timeout=30, verify=False)
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to fetch target website: " + str(e))
            return

        if response.status_code != 200:
            self.send_error(response.status_code, "Target website returned " + str(response.status_code))
            return

        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_content_complete(response.text, target_url)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(rewritten_content.encode('utf-8'))
        else:
            self._proxy_raw_content(response)

    def _proxy_resource(self):
        """代理静态资源 - 增强错误处理"""
        referer = self.headers.get('Referer', '')

        if '/proxy?url=' in referer:
            referer_parsed = urllib.parse.urlparse(referer)
            referer_query = urllib.parse.parse_qs(referer_parsed.query)
            base_url = referer_query.get('url', [''])[0]

            if base_url:
                # 处理返回主页的特殊情况
                if self.path == '/':
                    self._serve_homepage()
                    return
                    
                resource_url = urllib.parse.urljoin(base_url, self.path)

                headers = {
                    'User-Agent': self.config['user_agent'],
                    'Referer': base_url
                }

                try:
                    response = requests.get(resource_url, headers=headers, timeout=15, verify=False)
                    # 关键增强：检查资源是否成功加载
                    if response.status_code == 200:
                        self._proxy_raw_content(response)
                    else:
                        # 资源加载失败时返回空内容而不是404，避免阻塞页面渲染
                        self._send_empty_response()
                    return
                except requests.exceptions.RequestException:
                    # 网络错误时返回空响应
                    self._send_empty_response()
                    return

        # 如果是直接访问根路径，返回主页
        if self.path == '/':
            self._serve_homepage()
            return
            
        # 无法找到资源时返回空响应而不是404
        self._send_empty_response()

    def _send_empty_response(self):
        """发送空响应，用于资源加载失败时"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _proxy_post_request_fixed(self):
        """修复的POST请求处理 - 使用旧版本的工作逻辑"""
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        headers = {
            'User-Agent': self.config['user_agent'],
            'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
        }
        
        try:
            response = requests.post(target_url, data=post_data, headers=headers, 
                                   timeout=30, verify=False, allow_redirects=False)
            
            print(f"POST响应状态码: {response.status_code}")
            
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if location:
                    print(f"拦截到重定向: {location}")
                    
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    proxy_location = "/proxy?url=" + urllib.parse.quote(location)
                    print(f"重写为代理重定向: {proxy_location}")
                    
                    self.send_response(302)
                    self.send_header('Location', proxy_location)
                    self.end_headers()
                    return
            
            self._proxy_raw_content(response)
            
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to POST to target website: " + str(e))

    def _proxy_raw_content(self, response):
        """代理原始内容"""
        self.send_response(response.status_code)
        
        # 过滤掉可能引起问题的头部
        excluded_headers = ['content-encoding', 'transfer-encoding', 'content-length', 'connection']
        for header, value in response.headers.items():
            if header.lower() not in excluded_headers:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)

    def _rewrite_html_content_complete(self, html_content, base_url):
        """完整的HTML内容重写 - 同时修复新闻跳转和搜索"""
        soup = BeautifulSoup(html_content, 'html.parser')

        nav_html = '''
        <div style="background: #007cba; color: white; padding: 10px; margin: 0; text-align: center; position: fixed; top: 0; left: 0; right: 0; z-index: 10000;">
            <a href="/" style="color: white; text-decoration: none; font-weight: bold; margin-right: 15px;">🏠 返回代理主页</a>
            <span>当前代理: {}</span>
        </div>
        '''.format(base_url[:50] + '...' if len(base_url) > 50 else base_url)

        # 增强的链接重写 - 修复新闻跳转，但保护返回主页链接
        self._rewrite_links_complete(soup, base_url)

        # 重写CSS中的url()引用
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                style_tag.string = self._rewrite_css_urls(style_tag.string, base_url)

        # 插入导航栏并添加顶部边距
        body_tag = soup.find('body')
        if body_tag:
            # 为body添加顶部边距以容纳固定导航栏
            body_style = body_tag.get('style', '')
            if 'margin-top' not in body_style:
                body_tag['style'] = body_style + '; margin-top: 50px;' if body_style else 'margin-top: 50px;'
            
            nav_soup = BeautifulSoup(nav_html, 'html.parser')
            body_tag.insert(0, nav_soup.div)
        else:
            # 如果没有body标签，创建一个并插入导航栏
            body_tag = soup.new_tag('body')
            body_tag['style'] = 'margin-top: 50px;'
            nav_soup = BeautifulSoup(nav_html, 'html.parser')
            body_tag.append(nav_soup.div)
            
            # 将原有内容移动到body中
            for content in soup.contents:
                if content.name != 'body':
                    body_tag.append(content)
            soup.append(body_tag)

        # 注入增强的JavaScript拦截代码 - 关键修复新闻跳转
        interception_script = self._get_enhanced_interception_script(base_url)
        script_tag = soup.new_tag('script')
        script_tag.string = interception_script
        if body_tag:
            body_tag.append(script_tag)
        else:
            soup.append(script_tag)

        return str(soup)

    def _rewrite_links_complete(self, soup, base_url):
        """完整的链接重写 - 修复新闻跳转，保护返回主页链接"""
        # 重写普通链接 - 跳过返回主页链接
        for tag in soup.find_all('a'):
            if tag.get('href'):
                href = tag['href']
                # 特别保护返回主页的链接
                if href == '/' or href.startswith('/?'):
                    continue
                if self._should_rewrite_url(href):
                    absolute_url = urllib.parse.urljoin(base_url, href)
                    tag['href'] = "/proxy?url=" + urllib.parse.quote(absolute_url)

        # 重写表单
        for form in soup.find_all('form'):
            if form.get('action'):
                action = form['action']
                if self._should_rewrite_url(action):
                    absolute_url = urllib.parse.urljoin(base_url, action)
                    form['action'] = "/proxy?url=" + urllib.parse.quote(absolute_url)

        # 重写资源
        for tag in soup.find_all(['img', 'script', 'link', 'iframe']):
            src_attr = 'src' if tag.get('src') else 'href' if tag.get('href') else None
            if src_attr:
                src = tag[src_attr]
                if self._should_rewrite_url(src):
                    absolute_url = urllib.parse.urljoin(base_url, src)
                    tag[src_attr] = "/proxy?url=" + urllib.parse.quote(absolute_url)

        # 重写meta refresh
        for meta in soup.find_all('meta', attrs={'http-equiv': re.compile('refresh', re.I)}):
            content = meta.get('content', '')
            if 'url=' in content.lower():
                parts = content.split(';', 1)
                if len(parts) == 2:
                    timeout, url_part = parts
                    if url_part.strip().lower().startswith('url='):
                        original_url = url_part[4:].strip()
                        if self._should_rewrite_url(original_url):
                            absolute_url = urllib.parse.urljoin(base_url, original_url)
                            proxy_url = "/proxy?url=" + urllib.parse.quote(absolute_url)
                            meta['content'] = f"{timeout}; URL={proxy_url}"

    def _should_rewrite_url(self, url):
        """判断URL是否需要重写"""
        if not url or url.strip() == '':
            return False
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'blob:')):
            return False
        if url.startswith(('/proxy?url=', '/resource/', 'http://localhost:', 'https://localhost:')):
            return False
        if url == '/' or url.startswith('/?'):
            return False
        return True

    def _rewrite_css_urls(self, css_content, base_url):
        """重写CSS中的url()引用"""
        import re

        def replace_url(match):
            url_content = match.group(1)
            if url_content.startswith(('http://', 'https://', 'data:')):
                return match.group(0)

            absolute_url = urllib.parse.urljoin(base_url, url_content.strip('"\''))
            proxy_url = "/proxy?url=" + urllib.parse.quote(absolute_url)
            return 'url("' + proxy_url + '")'

        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)

    def _get_enhanced_interception_script(self, base_url):
        """获取增强的JavaScript拦截代码 - 彻底修复新闻跳转"""
        return '''
        // 增强的JavaScript拦截代码 - 专门修复新闻跳转
        (function() {
            'use strict';
            
            var baseUrl = "''' + base_url + '''";
            
            // 1. 增强的点击事件拦截 - 处理所有可能的新闻链接
            function interceptClickEvent(e) {
                var target = e.target;
                
                // 向上遍历所有父元素，查找链接
                while (target && target !== document) {
                    if (target.tagName && target.tagName.toLowerCase() === 'a' && target.href) {
                        var href = target.href;
                        
                        // 检查是否是需要代理的外部链接（特别保护返回主页链接）
                        if (href && 
                            !href.includes('/proxy?url=') && 
                            !href.startsWith('javascript:') && 
                            !href.startsWith('mailto:') && 
                            !href.startsWith('tel:') && 
                            !href.startsWith('#') &&
                            !href.startsWith('data:') &&
                            !(target.getAttribute('href') === '/') && // 保护返回主页链接
                            !(target.textContent && target.textContent.includes('返回代理主页'))) {
                            
                            e.preventDefault();
                            e.stopImmediatePropagation();
                            e.stopPropagation();
                            
                            // 转换为代理URL
                            try {
                                var fullUrl = new URL(href, baseUrl).href;
                                var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                                window.location.href = proxyUrl;
                            } catch (err) {
                                console.log('拦截错误:', err);
                            }
                            return false;
                        }
                    }
                    target = target.parentNode;
                }
            }
            
            // 2. 多层级事件监听 - 确保捕获所有点击
            document.addEventListener('click', interceptClickEvent, true);
            document.addEventListener('auxclick', interceptClickEvent, true); // 中键点击
            document.addEventListener('contextmenu', interceptClickEvent, true); // 右键菜单
            
            // 3. 拦截动态创建的链接
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            // 检查新增的链接
                            if (node.tagName === 'A' && node.href && !node.href.includes('/proxy?url=')) {
                                var fullUrl = new URL(node.href, baseUrl).href;
                                node.href = '/proxy?url=' + encodeURIComponent(fullUrl);
                            }
                            
                            // 检查子元素中的链接
                            var links = node.querySelectorAll ? node.querySelectorAll('a') : [];
                            for (var i = 0; i < links.length; i++) {
                                var link = links[i];
                                if (link.href && !link.href.includes('/proxy?url=')) {
                                    var fullUrl = new URL(link.href, baseUrl).href;
                                    link.href = '/proxy?url=' + encodeURIComponent(fullUrl);
                                }
                            }
                        }
                    });
                });
            });
            
            // 4. 开始观察DOM变化
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // 5. 拦截window.open等方法
            var originalWindowOpen = window.open;
            window.open = function(url, target, features) {
                if (url && !url.includes('/proxy?url=')) {
                    var fullUrl = new URL(url, baseUrl).href;
                    url = '/proxy?url=' + encodeURIComponent(fullUrl);
                }
                return originalWindowOpen.call(this, url, target, features);
            };
            
            console.log('🔒 增强拦截脚本已加载 - 新闻跳转已修复');
        })();
        '''

    def log_message(self, format, *args):
        """自定义日志格式"""
        print("[" + self.log_date_time_string() + "] " + format % args)

def run_proxy_server():
    """运行代理服务器"""
    port = 60000
    
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass
    
    with socketserver.TCPServer(("", port), CompleteFixProxyHandler) as httpd:
        print("🚀 完整修复代理服务器已启动在端口 " + str(port))
        print("📧 访问地址: http://localhost:" + str(port))
        print("🔧 修复内容: 新闻直接跳转 + 搜索问题 + 主页循环")
        print("⏹️ 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_proxy_server()
