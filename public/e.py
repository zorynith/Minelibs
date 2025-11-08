#!/usr/bin/env python3
"""
HTTP代理服务器 - 极简修复版本
运行端口: 60000
专注于解决搜索跳转和主页循环问题
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re

class SimpleProxyHandler(http.server.BaseHTTPRequestHandler):
    """极简代理处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        try:
            print(f"GET: {self.path}")
            
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/proxy/'):
                self._handle_proxy()
            elif self.path.startswith('/res/'):
                self._handle_resource()
            else:
                # 其他路径重定向到主页
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
                
        except Exception as e:
            print(f"GET错误: {str(e)}")
            self._send_error(500, f"服务器错误: {str(e)}")
    
    def do_POST(self):
        """处理POST请求"""
        try:
            print(f"POST: {self.path}")
            
            if self.path.startswith('/proxy/'):
                self._handle_post()
            else:
                self._send_error(404, "页面不存在")
        except Exception as e:
            print(f"POST错误: {str(e)}")
            self._send_error(500, f"服务器错误: {str(e)}")
    
    def _serve_homepage(self):
        """提供主页"""
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>极简代理 - 60000端口</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f0f2f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #1890ff; text-align: center; margin-bottom: 20px; }
                .input-group { margin: 20px 0; }
                input[type="url"] { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
                button { background: #1890ff; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }
                button:hover { background: #096dd9; }
                .quick-links { text-align: center; margin: 20px 0; }
                .quick-link { display: inline-block; margin: 0 10px; color: #1890ff; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 极简网页代理</h1>
                <form id="proxyForm">
                    <div class="input-group">
                        <input type="url" id="urlInput" placeholder="https://www.example.com" required value="https://www.so.com">
                    </div>
                    <button type="submit">开始代理访问</button>
                </form>
                <div class="quick-links">
                    <a href="/proxy/https://www.so.com" class="quick-link">360搜索</a>
                    <a href="/proxy/https://www.baidu.com" class="quick-link">百度搜索</a>
                </div>
                <div style="text-align: center; color: #666; margin-top: 20px;">
                    <small>端口 60000 | 极简修复版</small>
                </div>
            </div>
            <script>
                document.getElementById('proxyForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    const url = document.getElementById('urlInput').value.trim();
                    if (url) {
                        const encoded = encodeURIComponent(url);
                        window.location.href = '/proxy/' + encoded;
                    }
                });
            </script>
        </body>
        </html>
        '''
        
        self._send_html(html)
    
    def _handle_proxy(self):
        """处理代理请求"""
        try:
            # 提取目标URL
            encoded_url = self.path[7:]  # 去掉 '/proxy/'
            if '?' in encoded_url:
                encoded_url = encoded_url.split('?')[0]
            
            target_url = urllib.parse.unquote(encoded_url)
            
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'https://' + target_url
            
            print(f"代理访问: {target_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(target_url, headers=headers, timeout=30, verify=False)
            
            if response.status_code != 200:
                self._send_error(response.status_code, f"目标网站返回: {response.status_code}")
                return
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type:
                rewritten = self._rewrite_html(response.text, target_url)
                self._send_html(rewritten)
            else:
                self._send_response(response)
                
        except Exception as e:
            print(f"代理错误: {str(e)}")
            self._send_error(502, f"无法访问网站: {str(e)}")
    
    def _handle_post(self):
        """处理POST请求 - 关键修复"""
        try:
            # 提取目标URL
            encoded_url = self.path[7:]  # 去掉 '/proxy/'
            target_url = urllib.parse.unquote(encoded_url)
            
            # 读取POST数据
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
            }
            
            print(f"POST到: {target_url}")
            
            # 关键：禁用自动重定向，手动处理
            response = requests.post(target_url, data=post_data, headers=headers, 
                                   timeout=30, verify=False, allow_redirects=False)
            
            print(f"POST响应状态: {response.status_code}")
            
            # 处理重定向
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if location:
                    print(f"拦截重定向: {location}")
                    
                    # 转换为绝对URL
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    # 重写为代理URL
                    proxy_url = f"/proxy/{urllib.parse.quote(location)}"
                    print(f"重定向到: {proxy_url}")
                    
                    self.send_response(302)
                    self.send_header('Location', proxy_url)
                    self.end_headers()
                    return
            
            # 处理正常响应
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type:
                rewritten = self._rewrite_html(response.text, target_url)
                self._send_html(rewritten)
            else:
                self._send_response(response)
                
        except Exception as e:
            print(f"POST错误: {str(e)}")
            self._send_error(502, f"提交失败: {str(e)}")
    
    def _handle_resource(self):
        """处理资源请求"""
        try:
            encoded_url = self.path[5:]  # 去掉 '/res/'
            resource_url = urllib.parse.unquote(encoded_url)
            
            # 修复URL格式
            if resource_url.startswith('https:/') and not resource_url.startswith('https://'):
                resource_url = resource_url.replace('https:/', 'https://', 1)
            if resource_url.startswith('http:/') and not resource_url.startswith('http://'):
                resource_url = resource_url.replace('http:/', 'http://', 1)
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            referer = self.headers.get('Referer', '')
            if referer:
                headers['Referer'] = referer
            
            response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
            self._send_response(response)
            
        except Exception as e:
            print(f"资源错误: {str(e)}")
            # 返回空响应避免阻塞页面
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.end_headers()
    
    def _rewrite_html(self, html, base_url):
        """重写HTML内容"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 添加导航栏 - 使用绝对路径避免循环
        nav_html = '''
        <div style="background: #1890ff; color: white; padding: 10px; text-align: center; position: sticky; top: 0; z-index: 10000;">
            <a href="/" style="color: white; text-decoration: none; font-weight: bold; margin-right: 20px;">🏠 代理主页</a>
            <span>|</span>
            <a href="javascript:history.back()" style="color: white; text-decoration: none; margin-left: 20px;">↩ 返回</a>
        </div>
        '''
        
        # 重写链接
        for tag in soup.find_all('a'):
            if tag.get('href'):
                href = tag['href']
                if self._should_proxy(href):
                    absolute = urllib.parse.urljoin(base_url, href)
                    tag['href'] = f"/proxy/{urllib.parse.quote(absolute)}"
        
        # 重写表单
        for form in soup.find_all('form'):
            if form.get('action'):
                action = form['action']
                if self._should_proxy(action):
                    absolute = urllib.parse.urljoin(base_url, action)
                    form['action'] = f"/proxy/{urllib.parse.quote(absolute)}"
        
        # 重写资源
        for tag in soup.find_all(['img', 'script', 'link']):
            attr = 'src' if tag.get('src') else 'href' if tag.get('href') else None
            if attr and tag[attr]:
                src = tag[attr]
                if self._should_proxy(src) and not src.startswith('data:'):
                    absolute = urllib.parse.urljoin(base_url, src)
                    tag[attr] = f"/res/{urllib.parse.quote(absolute)}"
        
        # 插入导航栏
        body = soup.find('body')
        if body:
            body.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
        else:
            soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
        
        # 添加基础拦截脚本
        script = soup.new_tag('script')
        script.string = self._get_interception_script(base_url)
        if body:
            body.append(script)
        
        return str(soup)
    
    def _should_proxy(self, url):
        """判断URL是否需要代理"""
        if not url or url.strip() == '':
            return False
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'blob:')):
            return False
        if url.startswith(('/proxy/', '/res/', 'http://localhost', 'https://localhost')):
            return False
        if url == '/':
            return False
        return True
    
    def _get_interception_script(self, base_url):
        """获取拦截脚本"""
        return f'''
        document.addEventListener('click', function(e) {{
            let target = e.target;
            while (target && target.nodeName !== 'A') {{
                target = target.parentElement;
                if (!target) return;
            }}
            if (target && target.href && !target.href.includes('/proxy/')) {{
                e.preventDefault();
                const fullUrl = new URL(target.href, "{base_url}").href;
                window.location.href = '/proxy/' + encodeURIComponent(fullUrl);
            }}
        }});
        
        document.addEventListener('submit', function(e) {{
            const form = e.target;
            if (form.action && !form.action.includes('/proxy/')) {{
                e.preventDefault();
                const fullUrl = new URL(form.action, "{base_url}").href;
                const proxyUrl = '/proxy/' + encodeURIComponent(fullUrl);
                
                const tempForm = document.createElement('form');
                tempForm.method = form.method;
                tempForm.action = proxyUrl;
                
                const inputs = form.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {{
                    if (input.name) {{
                        const newInput = document.createElement('input');
                        newInput.type = 'hidden';
                        newInput.name = input.name;
                        newInput.value = input.value;
                        tempForm.appendChild(newInput);
                    }}
                }});
                
                document.body.appendChild(tempForm);
                tempForm.submit();
            }}
        }});
        '''
    
    def _send_html(self, content):
        """发送HTML响应"""
        encoded = content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
    
    def _send_response(self, response):
        """发送原始响应"""
        self.send_response(response.status_code)
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                self.send_header(header, value)
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)
    
    def _send_error(self, code, message):
        """发送错误页面"""
        html = f'''
        <!DOCTYPE html>
        <html>
        <head><title>错误 {code}</title></head>
        <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
            <h1>❌ 错误 {code}</h1>
            <p>{message}</p>
            <a href="/" style="color: #1890ff;">返回主页</a>
        </body>
        </html>
        '''
        self._send_html(html)
    
    def log_message(self, format, *args):
        """自定义日志"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_simple_proxy():
    """运行极简代理"""
    port = 60000
    
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass
    
    with socketserver.TCPServer(("", port), SimpleProxyHandler) as httpd:
        print("=" * 50)
        print(f"🚀 极简代理服务器已启动")
        print(f"📍 端口: {port}")
        print(f"🌐 地址: http://localhost:{port}")
        print("=" * 50)
        print("✨ 特性:")
        print("   • 全新URL结构: /proxy/encoded_url")
        print("   • 强制重定向拦截")
        print("   • 简化资源处理")
        print("   • 避免循环代理")
        print("=" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_simple_proxy()
