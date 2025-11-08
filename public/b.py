#!/usr/bin/env python3
"""
HTTP代理服务器 - 修复跳转和URL处理版本
运行端口: 60000
修复URL解析和跳转问题
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import time

class FixedProxyHandler(http.server.BaseHTTPRequestHandler):
    """修复的HTTP请求处理器"""
    
    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/proxy?url='):
                self._proxy_webpage()
            elif self.path.startswith('/resource/'):
                self._proxy_resource_new()
            elif self.path.startswith('/favicon.ico'):
                # 直接返回空favicon响应
                self.send_response(204)
                self.end_headers()
                return
            else:
                self._proxy_resource()
        except Exception as e:
            print("请求处理错误: " + str(e))
            self.send_error(500, "Server Error: " + str(e))
    
    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            print("POST处理错误: " + str(e))
            self.send_error(500, "Server Error: " + str(e))
    
    def _serve_homepage(self):
        """提供代理主页界面"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>修复版网页代理 - 60000端口</title>
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
                <h1>🌐 修复版网页代理服务</h1>
                <div class="info">
                    <strong>修复内容：</strong> 修复URL解析错误，增强跳转拦截，改进资源加载。
                </div>
                <form action="/proxy" method="GET">
                    <div class="form-group">
                        <input type="url" name="url" placeholder="https://www.example.com" required value="https://">
                    </div>
                    <button type="submit">开始代理访问</button>
                </form>
                <div style="margin-top: 20px; text-align: center; color: #666;">
                    <small>代理服务运行在端口 60000 | URL解析已修复</small>
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
        # 解析目标URL
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        # 添加协议前缀如果缺失
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
        
        print("正在代理: " + target_url)
        
        # 设置请求头模拟真实浏览器
        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 发送请求到目标网站
        try:
            response = requests.get(target_url, headers=headers, timeout=30, verify=False)
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to fetch target website: " + str(e))
            return
        
        # 检查响应状态
        if response.status_code != 200:
            self.send_error(response.status_code, "Target website returned " + str(response.status_code))
            return
        
        # 重写网页内容
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_content_fixed(response.text, target_url)
        else:
            # 非HTML内容直接传递
            self._proxy_raw_content(response)
            return
        
        # 发送重写后的内容
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(rewritten_content.encode('utf-8'))
    
    def _proxy_resource(self):
        """代理静态资源（CSS、JS、图片等）"""
        # 从路径中提取原始资源URL
        referer = self.headers.get('Referer', '')
        
        if '/proxy?url=' in referer:
            # 从referer中提取基础URL
            referer_parsed = urllib.parse.urlparse(referer)
            referer_query = urllib.parse.parse_qs(referer_parsed.query)
            base_url = referer_query.get('url', [''])[0]
            
            if base_url:
                # 构建资源的完整URL
                resource_url = urllib.parse.urljoin(base_url, self.path)
                
                headers = {
                    'User-Agent': self.config['user_agent'],
                    'Referer': base_url
                }
                
                try:
                    response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
                    self._proxy_raw_content(response)
                    return
                except requests.exceptions.RequestException as e:
                    print("资源代理失败: " + str(e))
        
        self.send_error(404, "Resource not found")
    
    def _proxy_resource_new(self):
        """新的资源代理方法 - 修复URL处理"""
        try:
            # 从路径中提取编码的资源URL
            encoded_url = self.path[10:]  # 去掉 '/resource/'
            
            # 修复URL解码
            resource_url = urllib.parse.unquote(encoded_url)
            
            # 修复URL格式问题 - 确保有正确的协议和主机
            if resource_url.startswith('https:/') and not resource_url.startswith('https://'):
                resource_url = resource_url.replace('https:/', 'https://', 1)
            if resource_url.startswith('http:/') and not resource_url.startswith('http://'):
                resource_url = resource_url.replace('http:/', 'http://', 1)
            
            # 再次URL编码以确保格式正确
            resource_url = self._fix_url_format(resource_url)
            
            headers = {
                'User-Agent': self.config['user_agent'],
            }
            
            # 添加Referer
            referer = self.headers.get('Referer', '')
            if referer:
                headers['Referer'] = referer
            
            print("获取资源: " + resource_url)
            response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
            self._proxy_raw_content(response)
            
        except Exception as e:
            print("资源代理错误: " + str(e))
            # 不返回404，而是返回空内容避免页面错误
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Content-Length', '0')
            self.end_headers()
    
    def _fix_url_format(self, url):
        """修复URL格式"""
        # 处理双斜杠缺失的问题
        if url.startswith('https:/') and not url.startswith('https://'):
            url = url.replace('https:/', 'https://', 1)
        elif url.startswith('http:/') and not url.startswith('http://'):
            url = url.replace('http:/', 'http://', 1)
        
        # 确保URL有正确的格式
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:  # 没有主机名
            # 尝试从路径中提取主机名
            path_parts = parsed.path.split('/')
            if len(path_parts) > 1 and '.' in path_parts[1]:
                # 假设第一个路径段是主机名
                netloc = path_parts[1]
                new_path = '/' + '/'.join(path_parts[2:])
                url = f"{parsed.scheme}://{netloc}{new_path}"
                if parsed.query:
                    url += '?' + parsed.query
        
        return url
    
    def _proxy_post_request(self):
        """处理POST请求"""
        # 解析目标URL
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        # 读取POST数据
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        # 设置请求头
        headers = {
            'User-Agent': self.config['user_agent'],
            'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
        }
        
        # 转发POST请求
        try:
            response = requests.post(target_url, data=post_data, headers=headers, timeout=30, verify=False)
            
            # 处理重定向
            if response.status_code in [301, 302, 303]:
                location = response.headers.get('Location', '')
                if location:
                    # 将重定向转换为代理URL
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    proxy_location = "/proxy?url=" + urllib.parse.quote(location)
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
        
        # 复制重要的响应头
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)
    
    def _rewrite_html_content_fixed(self, html_content, base_url):
        """修复的HTML内容重写"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 在页面顶部添加返回主页的导航栏
        nav_html = '''
        <div style="background: #007cba; color: white; padding: 10px; margin: 0; text-align: center; position: sticky; top: 0; z-index: 10000;">
            <a href="/" style="color: white; text-decoration: none; font-weight: bold;">🏠 返回代理主页</a>
            <span style="margin: 0 10px;">|</span>
            <span>当前代理: {}</span>
            <button onclick="window.location.href='/'" style="margin-left: 20px; background: #005a87; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">重新输入网址</button>
        </div>
        '''.format(base_url)
        
        # 重写各种链接和资源引用
        self._rewrite_attributes_fixed(soup, base_url)
        
        # 重写CSS中的url()引用
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                style_tag.string = self._rewrite_css_urls_fixed(style_tag.string, base_url)
        
        # 重写style属性中的URL
        for tag in soup.find_all(style=True):
            tag['style'] = self._rewrite_css_urls_fixed(tag['style'], base_url)
        
        # 重写meta refresh
        meta_tags = soup.find_all('meta', attrs={'http-equiv': True})
        for meta_tag in meta_tags:
            if meta_tag.get('http-equiv', '').lower() == 'refresh':
                content = meta_tag.get('content', '')
                if 'url=' in content.lower():
                    parts = content.split(';', 1)
                    if len(parts) == 2:
                        timeout, url_part = parts
                        if url_part.strip().lower().startswith('url='):
                            original_url = url_part[4:].strip()
                            absolute_url = urllib.parse.urljoin(base_url, original_url)
                            proxy_url = "/proxy?url=" + urllib.parse.quote(absolute_url)
                            meta_tag['content'] = timeout + "; URL=" + proxy_url
        
        # 插入导航栏
        body_tag = soup.find('body')
        if body_tag:
            nav_soup = BeautifulSoup(nav_html, 'html.parser')
            body_tag.insert(0, nav_soup.div)
        else:
            soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
        
        # 注入增强的JavaScript拦截代码
        interception_script = self._get_enhanced_interception_code(base_url)
        script_tag = soup.new_tag('script')
        script_tag.string = interception_script
        if body_tag:
            body_tag.append(script_tag)
        else:
            soup.append(script_tag)
        
        return str(soup)
    
    def _rewrite_attributes_fixed(self, soup, base_url):
        """修复的属性重写"""
        # 链接
        for tag in soup.find_all('a'):
            if tag.get('href'):
                href = tag['href']
                if self._should_rewrite_url(href):
                    absolute_url = urllib.parse.urljoin(base_url, href)
                    tag['href'] = "/proxy?url=" + urllib.parse.quote(absolute_url)
        
        # 表单
        for form in soup.find_all('form'):
            if form.get('action'):
                action = form['action']
                if self._should_rewrite_url(action):
                    absolute_url = urllib.parse.urljoin(base_url, action)
                    form['action'] = "/proxy?url=" + urllib.parse.quote(absolute_url)
        
        # 资源
        for tag in soup.find_all(['img', 'script', 'link', 'iframe', 'frame', 'embed', 'source', 'track', 'video', 'audio']):
            src_attr = 'src' if tag.get('src') else 'href' if tag.get('href') else 'data' if tag.get('data') else None
            if src_attr:
                src = tag[src_attr]
                if self._should_rewrite_url(src):
                    absolute_url = urllib.parse.urljoin(base_url, src)
                    tag[src_attr] = "/resource/" + urllib.parse.quote(absolute_url)
    
    def _should_rewrite_url(self, url):
        """判断URL是否需要重写"""
        if not url or url.strip() == '':
            return False
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'blob:')):
            return False
        if url.startswith(('/proxy?url=', '/resource/', 'http://localhost:', 'https://localhost:')):
            return False
        return True
    
    def _rewrite_css_urls_fixed(self, css_content, base_url):
        """修复的CSS URL重写"""
        import re
        
        def replace_url(match):
            url_content = match.group(1).strip('"\'')
            if not self._should_rewrite_url(url_content):
                return match.group(0)
            
            # 转换为绝对URL
            absolute_url = urllib.parse.urljoin(base_url, url_content)
            proxy_url = "/resource/" + urllib.parse.quote(absolute_url)
            return 'url("' + proxy_url + '")'
        
        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)
    
    def _get_enhanced_interception_code(self, base_url):
        """获取增强的JavaScript拦截代码"""
        return '''
        // 增强的JavaScript拦截代码
        (function() {
            'use strict';
            
            var baseUrl = "''' + base_url + '''";
            
            // 1. 拦截所有链接点击
            document.addEventListener('click', function(e) {
                var target = e.target;
                while (target && target.nodeName !== 'A') {
                    target = target.parentElement;
                    if (!target) return;
                }
                
                if (target && target.href && !target.href.includes('/proxy?url=')) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    var fullUrl = new URL(target.href, baseUrl).href;
                    var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                    window.location.href = proxyUrl;
                    return false;
                }
            }, true);
            
            // 2. 拦截window.location操作
            var originalLocation = window.location;
            Object.defineProperty(window, 'location', {
                get: function() {
                    return originalLocation;
                },
                set: function(value) {
                    if (typeof value === 'string') {
                        var fullUrl = new URL(value, baseUrl).href;
                        var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                        originalLocation.href = proxyUrl;
                    }
                    return originalLocation;
                }
            });
            
            // 3. 重写location方法
            var originalReplace = originalLocation.replace;
            var originalAssign = originalLocation.assign;
            
            originalLocation.replace = function(url) {
                var fullUrl = new URL(url, baseUrl).href;
                var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                originalReplace.call(originalLocation, proxyUrl);
            };
            
            originalLocation.assign = function(url) {
                var fullUrl = new URL(url, baseUrl).href;
                var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                originalAssign.call(originalLocation, proxyUrl);
            };
            
            // 4. 拦截表单提交
            document.addEventListener('submit', function(e) {
                var form = e.target;
                if (form.action && !form.action.includes('/proxy?url=')) {
                    e.preventDefault();
                    var fullUrl = new URL(form.action, baseUrl).href;
                    var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                    
                    // 创建临时表单
                    var tempForm = document.createElement('form');
                    tempForm.method = form.method || 'GET';
                    tempForm.action = proxyUrl;
                    tempForm.style.display = 'none';
                    
                    // 复制表单数据
                    var inputs = form.querySelectorAll('input, select, textarea');
                    for (var i = 0; i < inputs.length; i++) {
                        var input = inputs[i];
                        if (input.name) {
                            var newInput = document.createElement('input');
                            newInput.type = 'hidden';
                            newInput.name = input.name;
                            newInput.value = input.value;
                            tempForm.appendChild(newInput);
                        }
                    }
                    
                    document.body.appendChild(tempForm);
                    tempForm.submit();
                }
            }, true);
            
            // 5. 拦截动态创建的链接
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            if (node.tagName === 'A' && node.href && !node.href.includes('/proxy?url=')) {
                                var fullUrl = new URL(node.href, baseUrl).href;
                                node.href = '/proxy?url=' + encodeURIComponent(fullUrl);
                            }
                            // 检查子元素
                            var links = node.querySelectorAll('a');
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
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            console.log('🔒 增强拦截脚本已加载');
        })();
        '''
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print("[" + self.log_date_time_string() + "] " + format % args)

def run_proxy_server():
    """运行代理服务器"""
    port = 60000
    
    # 禁用SSL警告
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass
    
    with socketserver.TCPServer(("", port), FixedProxyHandler) as httpd:
        print("🚀 修复版HTTP代理服务器已启动在端口 " + str(port))
        print("📧 访问地址: http://localhost:" + str(port))
        print("🔧 修复内容: URL解析、资源加载、跳转拦截")
        print("⏹️ 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_proxy_server()
