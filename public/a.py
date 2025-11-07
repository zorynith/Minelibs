#!/usr/bin/env python3
"""
HTTP代理服务器 - 阿里云CloudShell专用版
运行端口: 60000
全面解决跳转和连接问题
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import json
import ssl
import threading
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class CloudShellProxyHandler(http.server.BaseHTTPRequestHandler):
    """阿里云CloudShell专用代理处理器"""
    
    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'timeout': 30,
        'max_retries': 3
    }
    
    # 创建带重试机制的session
    @classmethod
    def create_session(cls):
        session = requests.Session()
        retry_strategy = Retry(
            total=cls.config['max_retries'],
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def do_GET(self):
        """处理GET请求"""
        try:
            print(f"请求路径: {self.path}")
            
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/nav/'):
                self._handle_navigation()
            elif self.path.startswith('/fetch/'):
                self._fetch_content()
            else:
                # 尝试作为静态资源处理
                self._handle_static_resource()
                
        except Exception as e:
            print(f"处理请求时出错: {str(e)}")
            self._send_error_page(500, f"服务器错误: {str(e)}")

    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path.startswith('/fetch/'):
                self._handle_post_request()
            else:
                self._send_error_page(404, "页面不存在")
        except Exception as e:
            print(f"处理POST请求时出错: {str(e)}")
            self._send_error_page(500, f"服务器错误: {str(e)}")

    def _serve_homepage(self):
        """提供主页"""
        homepage = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>CloudShell网页代理 - 端口60000</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container { 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 40px; 
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                }
                h1 { 
                    color: #333; 
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 2.5em;
                }
                .form-group { 
                    margin: 25px 0; 
                }
                input[type="url"] { 
                    width: 100%; 
                    padding: 15px; 
                    border: 2px solid #e1e5e9; 
                    border-radius: 8px; 
                    font-size: 16px;
                    transition: border-color 0.3s;
                }
                input[type="url"]:focus {
                    border-color: #667eea;
                    outline: none;
                }
                button { 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; 
                    border: none; 
                    padding: 15px 30px; 
                    border-radius: 8px; 
                    cursor: pointer; 
                    font-size: 16px;
                    width: 100%;
                    font-weight: 600;
                    transition: transform 0.2s;
                }
                button:hover { 
                    transform: translateY(-2px);
                }
                .info {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 25px 0;
                    border-left: 4px solid #667eea;
                }
                .quick-links {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin: 25px 0;
                }
                .quick-link {
                    display: block;
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 6px;
                    text-align: center;
                    text-decoration: none;
                    color: #333;
                    transition: all 0.3s;
                    border: 1px solid #e1e5e9;
                }
                .quick-link:hover {
                    background: #667eea;
                    color: white;
                    transform: translateY(-2px);
                }
                .status {
                    text-align: center;
                    color: #666;
                    margin-top: 25px;
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 CloudShell网页代理</h1>
                <div class="info">
                    <strong>专为阿里云CloudShell优化</strong><br>
                    • 全面解决页面跳转问题<br>
                    • 支持所有资源代理(CSS/JS/图片)<br>
                    • 表单提交和搜索功能正常<br>
                    • 自动处理连接错误
                </div>
                
                <form id="proxyForm">
                    <div class="form-group">
                        <input type="url" id="urlInput" 
                               placeholder="https://www.example.com" 
                               required value="https://">
                    </div>
                    <button type="submit">🚀 开始代理访问</button>
                </form>
                
                <div class="quick-links">
                    <a href="/nav/https://www.baidu.com" class="quick-link">百度搜索</a>
                    <a href="/nav/https://www.so.com" class="quick-link">360搜索</a>
                    <a href="/nav/https://news.sina.com.cn" class="quick-link">新浪新闻</a>
                    <a href="/nav/https://www.qq.com" class="quick-link">腾讯网</a>
                </div>
                
                <div class="status">
                    ✅ 代理服务运行在端口 60000 | 阿里云CloudShell专用
                </div>
            </div>
            
            <script>
                document.getElementById('proxyForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    const urlInput = document.getElementById('urlInput');
                    const url = urlInput.value.trim();
                    
                    if (!url) {
                        alert('请输入要访问的网址');
                        return;
                    }
                    
                    // 编码URL并跳转
                    const encodedUrl = encodeURIComponent(url);
                    window.location.href = '/nav/' + encodedUrl;
                });
                
                // 自动聚焦输入框
                document.getElementById('urlInput').focus();
            </script>
        </body>
        </html>
        '''
        
        self._send_response(200, homepage, 'text/html')

    def _handle_navigation(self):
        """处理页面导航"""
        try:
            encoded_url = self.path[5:]  # 去掉 '/nav/'
            target_url = urllib.parse.unquote(encoded_url)
            
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'https://' + target_url
                
            print(f"导航到: {target_url}")
            self._proxy_webpage(target_url)
            
        except Exception as e:
            print(f"导航处理错误: {str(e)}")
            self._send_error_page(400, f"无效的URL: {str(e)}")

    def _fetch_content(self):
        """获取网页内容"""
        try:
            encoded_url = self.path[7:]  # 去掉 '/fetch/'
            target_url = urllib.parse.unquote(encoded_url)
            
            print(f"获取内容: {target_url}")
            self._proxy_webpage(target_url, is_resource=False)
            
        except Exception as e:
            print(f"内容获取错误: {str(e)}")
            self._send_error_page(400, f"内容获取失败: {str(e)}")

    def _handle_static_resource(self):
        """处理静态资源"""
        try:
            # 从Referer推断原始页面URL
            referer = self.headers.get('Referer', '')
            if '/nav/' in referer:
                referer_path = urllib.parse.urlparse(referer).path
                if referer_path.startswith('/nav/'):
                    base_encoded_url = referer_path[5:]
                    base_url = urllib.parse.unquote(base_encoded_url)
                    
                    # 构建资源完整URL
                    resource_url = urllib.parse.urljoin(base_url, self.path)
                    print(f"获取资源: {resource_url}")
                    
                    self._fetch_and_proxy_resource(resource_url)
                    return
            
            self._send_error_page(404, "资源未找到")
            
        except Exception as e:
            print(f"资源处理错误: {str(e)}")
            self._send_error_page(404, f"资源加载失败: {str(e)}")

    def _handle_post_request(self):
        """处理POST请求"""
        try:
            encoded_url = self.path[7:]  # 去掉 '/fetch/'
            target_url = urllib.parse.unquote(encoded_url)
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            
            headers = {
                'User-Agent': self.config['user_agent'],
                'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
            }
            
            session = self.create_session()
            response = session.post(target_url, data=post_data, headers=headers, 
                                  timeout=self.config['timeout'], verify=False)
            
            # 处理重定向
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if location:
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    proxy_location = f'/nav/{urllib.parse.quote(location)}'
                    self.send_response(302)
                    self.send_header('Location', proxy_location)
                    self.end_headers()
                    return
            
            self._proxy_response(response)
            
        except Exception as e:
            print(f"POST请求错误: {str(e)}")
            self._send_error_page(502, f"请求失败: {str(e)}")

    def _proxy_webpage(self, target_url, is_resource=True):
        """代理网页内容"""
        try:
            headers = {
                'User-Agent': self.config['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
            }
            
            # 添加Referer
            referer = self.headers.get('Referer', '')
            if referer:
                headers['Referer'] = referer
            
            session = self.create_session()
            response = session.get(target_url, headers=headers, 
                                 timeout=self.config['timeout'], verify=False)
            
            if response.status_code != 200:
                self._send_error_page(response.status_code, 
                                    f"目标网站返回状态码: {response.status_code}")
                return
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type and is_resource:
                rewritten_content = self._rewrite_html_content(response.text, target_url)
                self._send_response(200, rewritten_content, 'text/html')
            else:
                self._proxy_response(response)
                
        except requests.exceptions.RequestException as e:
            print(f"网页代理错误: {str(e)}")
            self._send_error_page(502, f"无法连接到目标网站: {str(e)}")
        except Exception as e:
            print(f"网页处理异常: {str(e)}")
            self._send_error_page(500, f"网页处理失败: {str(e)}")

    def _fetch_and_proxy_resource(self, resource_url):
        """获取并代理资源"""
        try:
            headers = {
                'User-Agent': self.config['user_agent'],
            }
            
            referer = self.headers.get('Referer', '')
            if referer:
                headers['Referer'] = referer
            
            session = self.create_session()
            response = session.get(resource_url, headers=headers, 
                                 timeout=self.config['timeout'], verify=False)
            
            self._proxy_response(response)
            
        except Exception as e:
            print(f"资源获取失败: {resource_url}, 错误: {str(e)}")
            self._send_error_page(502, f"资源加载失败: {str(e)}")

    def _rewrite_html_content(self, html_content, base_url):
        """重写HTML内容"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 添加代理导航栏
            nav_html = f'''
            <div id="cloudshell-proxy-nav" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 12px; margin: 0; 
                text-align: center; position: sticky; top: 0; 
                z-index: 10000; font-family: Arial, sans-serif;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            ">
                <a href="/" style="color: white; text-decoration: none; 
                   font-weight: bold; margin-right: 20px; background: rgba(255,255,255,0.2); 
                   padding: 5px 10px; border-radius: 4px;">🏠 代理主页</a>
                <span style="margin: 0 15px;">|</span>
                <span style="font-size: 0.9em;">代理: {base_url}</span>
                <button onclick="window.location.href='/'" style="
                    margin-left: 20px; background: rgba(255,255,255,0.3); 
                    color: white; border: 1px solid rgba(255,255,255,0.5); 
                    padding: 4px 8px; border-radius: 3px; cursor: pointer;
                    font-size: 0.8em;">更换网址</button>
            </div>
            '''
            
            # 重写所有链接和资源
            self._rewrite_urls(soup, base_url)
            
            # 插入导航栏
            body_tag = soup.find('body')
            if body_tag:
                nav_soup = BeautifulSoup(nav_html, 'html.parser')
                body_tag.insert(0, nav_soup.div)
            else:
                soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
            
            # 注入增强的拦截脚本
            interception_script = self._get_enhanced_interception_script(base_url)
            script_tag = soup.new_tag('script')
            script_tag.string = interception_script
            
            if body_tag:
                body_tag.append(script_tag)
            else:
                soup.append(script_tag)
            
            return str(soup)
            
        except Exception as e:
            print(f"HTML重写错误: {str(e)}")
            return html_content  # 返回原始内容作为备选

    def _rewrite_urls(self, soup, base_url):
        """重写所有URL"""
        # 重写链接
        for tag in soup.find_all(['a', 'link']):
            if tag.get('href'):
                url = tag['href']
                if self._should_rewrite_url(url):
                    absolute_url = urllib.parse.urljoin(base_url, url)
                    tag['href'] = f'/nav/{urllib.parse.quote(absolute_url)}'
        
        # 重写资源
        for tag in soup.find_all(['img', 'script', 'iframe', 'embed', 'source', 'track']):
            src_attr = 'src' if tag.get('src') else 'data' if tag.get('data') else None
            if src_attr:
                url = tag[src_attr]
                if self._should_rewrite_url(url):
                    absolute_url = urllib.parse.urljoin(base_url, url)
                    tag[src_attr] = f'/fetch/{urllib.parse.quote(absolute_url)}'
        
        # 重写表单
        for form in soup.find_all('form'):
            if form.get('action'):
                url = form['action']
                if self._should_rewrite_url(url):
                    absolute_url = urllib.parse.urljoin(base_url, url)
                    form['action'] = f'/fetch/{urllib.parse.quote(absolute_url)}'
        
        # 重写CSS
        for style in soup.find_all('style'):
            if style.string:
                style.string = self._rewrite_css_urls(style.string, base_url)
        
        for tag in soup.find_all(style=True):
            tag['style'] = self._rewrite_css_urls(tag['style'], base_url)

    def _should_rewrite_url(self, url):
        """判断是否应该重写URL"""
        if not url or url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:')):
            return False
        if url.startswith('/nav/') or url.startswith('/fetch/'):
            return False
        return True

    def _rewrite_css_urls(self, css_content, base_url):
        """重写CSS中的URL"""
        def replace_url(match):
            url = match.group(1).strip('"\'')
            if self._should_rewrite_url(url) and not url.startswith(('http://', 'https://', 'data:')):
                absolute_url = urllib.parse.urljoin(base_url, url)
                return f'url("/fetch/{urllib.parse.quote(absolute_url)}")'
            return match.group(0)
        
        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)

    def _get_enhanced_interception_script(self, base_url):
        """获取增强的拦截脚本"""
        return f'''
        // 全面跳转拦截脚本
        (function() {{
            const baseUrl = "{base_url}";
            
            // 保存原始方法
            const originalHref = Object.getOwnPropertyDescriptor(Element.prototype, 'href');
            const originalLocation = window.location;
            const originalOpen = window.open;
            const originalFetch = window.fetch;
            
            // 拦截href设置
            Object.defineProperty(Element.prototype, 'href', {{
                get: function() {{
                    return originalHref.get.call(this);
                }},
                set: function(value) {{
                    if (this.tagName === 'A' && value && !value.includes('/nav/')) {{
                        const absoluteUrl = new URL(value, baseUrl).href;
                        value = '/nav/' + encodeURIComponent(absoluteUrl);
                    }}
                    originalHref.set.call(this, value);
                }}
            }});
            
            // 拦截window.location
            Object.defineProperty(window, 'location', {{
                get: function() {{
                    return originalLocation;
                }},
                set: function(value) {{
                    const absoluteUrl = new URL(value, baseUrl).href;
                    window.location.href = '/nav/' + encodeURIComponent(absoluteUrl);
                }}
            }});
            
            // 拦截window.open
            window.open = function(url, target, features) {{
                if (url && !url.includes('/nav/')) {{
                    const absoluteUrl = new URL(url, baseUrl).href;
                    url = '/nav/' + encodeURIComponent(absoluteUrl);
                }}
                return originalOpen.call(this, url, target, features);
            }};
            
            // 拦截fetch
            window.fetch = function(resource, options) {{
                if (typeof resource === 'string' && !resource.includes('/fetch/')) {{
                    const absoluteUrl = new URL(resource, baseUrl).href;
                    resource = '/fetch/' + encodeURIComponent(absoluteUrl);
                }}
                return originalFetch.call(this, resource, options);
            }};
            
            // 全面点击拦截
            document.addEventListener('click', function(e) {{
                let target = e.target;
                while (target && target.nodeName !== 'A') {{
                    target = target.parentElement;
                    if (!target) return;
                }}
                
                if (target && target.href && !target.href.includes('/nav/')) {{
                    e.preventDefault();
                    e.stopPropagation();
                    const absoluteUrl = new URL(target.href, baseUrl).href;
                    window.location.href = '/nav/' + encodeURIComponent(absoluteUrl);
                    return false;
                }}
            }}, true);
            
            // 拦截表单提交
            document.addEventListener('submit', function(e) {{
                const form = e.target;
                if (form.action && !form.action.includes('/fetch/')) {{
                    e.preventDefault();
                    const absoluteUrl = new URL(form.action, baseUrl).href;
                    
                    // 创建临时表单
                    const tempForm = document.createElement('form');
                    tempForm.method = form.method || 'GET';
                    tempForm.action = '/fetch/' + encodeURIComponent(absoluteUrl);
                    
                    // 复制表单数据
                    const inputs = form.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => {{
                        const newInput = document.createElement('input');
                        newInput.type = 'hidden';
                        newInput.name = input.name;
                        newInput.value = input.value;
                        tempForm.appendChild(newInput);
                    }});
                    
                    document.body.appendChild(tempForm);
                    tempForm.submit();
                }}
            }}, true);
            
            console.log('🔒 CloudShell代理拦截已激活');
        }})();
        '''

    def _proxy_response(self, response):
        """代理原始响应"""
        self.send_response(response.status_code)
        
        # 复制响应头
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)

    def _send_response(self, code, content, content_type='text/html'):
        """发送响应"""
        encoded_content = content.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded_content)))
        self.end_headers()
        self.wfile.write(encoded_content)

    def _send_error_page(self, code, message):
        """发送错误页面"""
        error_page = f'''
        <!DOCTYPE html>
        <html>
        <head><title>错误 {code}</title></head>
        <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
            <h1>❌ 错误 {code}</h1>
            <p>{message}</p>
            <a href="/" style="color: #667eea;">返回主页</a>
        </body>
        </html>
        '''
        self._send_response(code, error_page)

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_cloudshell_proxy():
    """运行CloudShell代理服务器"""
    port = 60000
    
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 设置更宽松的socket选项
    class CloudShellTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
        request_queue_size = 100
        
        def server_bind(self):
            import socket
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            super().server_bind()
    
    try:
        with CloudShellTCPServer(("", port), CloudShellProxyHandler) as httpd:
            print("=" * 60)
            print(f"🚀 CloudShell网页代理服务器已启动")
            print(f"📍 运行端口: {port}")
            print(f"🌐 访问地址: http://localhost:{port}")
            print("=" * 60)
            print("✨ 特性:")
            print("   • 全面解决页面跳转问题")
            print("   • 自动重试失败请求") 
            print("   • 增强的JavaScript拦截")
            print("   • 阿里云CloudShell优化")
            print("=" * 60)
            print("⏹️  按 Ctrl+C 停止服务器")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 服务器已安全停止")
                
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ 端口 {port} 已被占用，请先停止其他服务")
        else:
            print(f"❌ 启动失败: {e}")
    except Exception as e:
        print(f"❌ 服务器错误: {e}")

if __name__ == "__main__":
    run_cloudshell_proxy()
