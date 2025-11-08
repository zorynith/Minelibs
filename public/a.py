#!/usr/bin/env python3
"""
HTTP代理服务器 - 增强跳转处理版本
运行端口: 60000
在稳定版本基础上增强跳转处理
"""

import http.server
import socketserver
import urllib.parse
import requests
from bsoup import BeautifulSoup
import re
import time

class EnhancedProxyHandler(http.server.BaseHTTPRequestHandler):
    """增强的HTTP请求处理器"""
    
    # 存储配置信息
    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if self.path == '/':
                # 返回主页界面
                self._serve_homepage()
            elif self.path.startswith('/proxy?url='):
                # 代理网页请求
                self._proxy_webpage()
            elif self.path.startswith('/resource/'):
                # 资源代理
                self._proxy_resource_new()
            else:
                # 其他资源请求（CSS、JS、图片等）
                self._proxy_resource()
        except Exception as e:
            self.send_error(500, "Server Error: " + str(e))
    
    def do_POST(self):
        """处理POST请求（如表单提交）"""
        try:
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_error(500, "Server Error: " + str(e))
    
    def _serve_homepage(self):
        """提供代理主页界面"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>增强版网页代理 - 60000端口</title>
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
                <h1>🌐 增强版网页代理服务</h1>
                <div class="info">
                    <strong>增强功能：</strong> 改进了跳转处理，支持JavaScript链接拦截，防止直接跳转到原网站。
                </div>
                <form action="/proxy" method="GET">
                    <div class="form-group">
                        <input type="url" name="url" placeholder="https://www.example.com" required value="https://">
                    </div>
                    <button type="submit">开始代理访问</button>
                </form>
                <div style="margin-top: 20px; text-align: center; color: #666;">
                    <small>代理服务运行在端口 60000 | 跳转拦截已启用</small>
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
            rewritten_content = self._rewrite_html_content_enhanced(response.text, target_url)
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
                except requests.exceptions.RequestException:
                    pass
        
        self.send_error(404, "Resource not found")
    
    def _proxy_resource_new(self):
        """新的资源代理方法"""
        try:
            # 从路径中提取编码的资源URL
            encoded_url = self.path[10:]  # 去掉 '/resource/'
            resource_url = urllib.parse.unquote(encoded_url)
            
            headers = {
                'User-Agent': self.config['user_agent'],
            }
            
            # 添加Referer
            referer = self.headers.get('Referer', '')
            if referer:
                headers['Referer'] = referer
            
            response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
            self._proxy_raw_content(response)
            
        except Exception as e:
            print("资源代理错误: " + str(e))
            self.send_error(404, "Resource not found")
    
    def _proxy_post_request(self):
        """处理POST请求（如表单提交）"""
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
        """代理原始内容（不重写）"""
        self.send_response(response.status_code)
        
        # 复制重要的响应头
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)
    
    def _rewrite_html_content_enhanced(self, html_content, base_url):
        """增强的HTML内容重写，解决跳转问题"""
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
        self._rewrite_attributes_enhanced(soup, 'a', 'href', base_url)
        self._rewrite_attributes_enhanced(soup, 'img', 'src', base_url)
        self._rewrite_attributes_enhanced(soup, 'script', 'src', base_url)
        self._rewrite_attributes_enhanced(soup, 'link', 'href', base_url)
        self._rewrite_attributes_enhanced(soup, 'form', 'action', base_url)
        self._rewrite_attributes_enhanced(soup, 'iframe', 'src', base_url)
        self._rewrite_attributes_enhanced(soup, 'frame', 'src', base_url)
        self._rewrite_attributes_enhanced(soup, 'embed', 'src', base_url)
        self._rewrite_attributes_enhanced(soup, 'object', 'data', base_url)
        
        # 重写CSS中的url()引用
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                style_tag.string = self._rewrite_css_urls_enhanced(style_tag.string, base_url)
        
        # 重写style属性中的URL
        for tag in soup.find_all(style=True):
            tag['style'] = self._rewrite_css_urls_enhanced(tag['style'], base_url)
        
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
            # 如果没有body标签，在开头添加
            soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
        
        # 注入JavaScript拦截代码
        interception_script = self._get_javascript_interception_code(base_url)
        script_tag = soup.new_tag('script')
        script_tag.string = interception_script
        if body_tag:
            body_tag.append(script_tag)
        else:
            soup.append(script_tag)
        
        return str(soup)
    
    def _rewrite_attributes_enhanced(self, soup, tag_name, attr_name, base_url):
        """增强的属性重写，处理更多情况"""
        tags = soup.find_all(tag_name)
        for tag in tags:
            if tag.has_attr(attr_name):
                original_url = tag[attr_name]
                
                # 跳过空链接和特殊协议
                if not original_url or original_url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:')):
                    continue
                
                # 转换为绝对URL
                absolute_url = urllib.parse.urljoin(base_url, original_url)
                
                # 重写为代理URL
                if attr_name == 'href' and tag_name == 'a':
                    proxy_url = "/proxy?url=" + urllib.parse.quote(absolute_url)
                elif attr_name in ['src', 'data', 'action']:
                    # 使用新的资源代理路径
                    proxy_url = "/resource/" + urllib.parse.quote(absolute_url)
                else:
                    proxy_url = "/resource/" + urllib.parse.quote(absolute_url)
                
                tag[attr_name] = proxy_url
    
    def _rewrite_css_urls_enhanced(self, css_content, base_url):
        """增强的CSS URL重写"""
        import re
        
        def replace_url(match):
            url_content = match.group(1)
            if url_content.startswith(('http://', 'https://', 'data:')):
                return match.group(0)
            
            # 转换为绝对URL
            absolute_url = urllib.parse.urljoin(base_url, url_content.strip('"\''))
            proxy_url = "/resource/" + urllib.parse.quote(absolute_url)
            return 'url("' + proxy_url + '")'
        
        # 匹配CSS中的url()引用
        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)
    
    def _get_javascript_interception_code(self, base_url):
        """获取JavaScript拦截代码，防止直接跳转"""
        return '''
        // JavaScript拦截 - 防止直接跳转
        (function() {
            var originalBaseUrl = "''' + base_url + '''";
            
            // 拦截window.location操作
            var originalLocation = window.location;
            Object.defineProperty(window, 'location', {
                get: function() {
                    return originalLocation;
                },
                set: function(value) {
                    if (typeof value === 'string') {
                        var absoluteUrl = new URL(value, originalBaseUrl).href;
                        var proxyUrl = '/proxy?url=' + encodeURIComponent(absoluteUrl);
                        originalLocation.href = proxyUrl;
                    }
                    return originalLocation;
                }
            });
            
            // 重写location方法
            var originalReplace = originalLocation.replace;
            var originalAssign = originalLocation.assign;
            
            originalLocation.replace = function(url) {
                var absoluteUrl = new URL(url, originalBaseUrl).href;
                var proxyUrl = '/proxy?url=' + encodeURIComponent(absoluteUrl);
                originalReplace.call(originalLocation, proxyUrl);
            };
            
            originalLocation.assign = function(url) {
                var absoluteUrl = new URL(url, originalBaseUrl).href;
                var proxyUrl = '/proxy?url=' + encodeURIComponent(absoluteUrl);
                originalAssign.call(originalLocation, proxyUrl);
            };
            
            // 拦截所有链接点击事件
            document.addEventListener('click', function(e) {
                var target = e.target;
                while (target && target.nodeName !== 'A') {
                    target = target.parentElement;
                    if (!target) return;
                }
                
                if (target && target.href && !target.href.includes('/proxy?url=')) {
                    e.preventDefault();
                    var proxyUrl = '/proxy?url=' + encodeURIComponent(target.href);
                    window.location.href = proxyUrl;
                }
            }, true);
            
            // 拦截表单提交
            document.addEventListener('submit', function(e) {
                var form = e.target;
                if (form.action && !form.action.includes('/proxy?url=')) {
                    e.preventDefault();
                    var absoluteUrl = new URL(form.action, originalBaseUrl).href;
                    var proxyUrl = '/proxy?url=' + encodeURIComponent(absoluteUrl);
                    
                    // 创建隐藏表单进行提交
                    var hiddenForm = document.createElement('form');
                    hiddenForm.method = form.method || 'GET';
                    hiddenForm.action = proxyUrl;
                    
                    // 复制所有表单数据
                    var formData = new FormData(form);
                    for (var pair of formData.entries()) {
                        var input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = pair[0];
                        input.value = pair[1];
                        hiddenForm.appendChild(input);
                    }
                    
                    document.body.appendChild(hiddenForm);
                    hiddenForm.submit();
                }
            }, true);
            
            console.log('代理拦截脚本已加载，所有跳转将被拦截');
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
    
    with socketserver.TCPServer(("", port), EnhancedProxyHandler) as httpd:
        print("🚀 增强版HTTP代理服务器已启动在端口 " + str(port))
        print("📧 访问地址: http://localhost:" + str(port))
        print("🔒 跳转拦截已启用")
        print("⏹️ 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_proxy_server()
