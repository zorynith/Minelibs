#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import urllib.parse
import http.server
import socketserver
import urllib.request
import gzip
import io
import sys
import os
import time
import ssl
import select

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 使用类变量来跟踪当前会话
        self.session_data = {}

    def send_error(self, code, message=None, explain=None):
        try:
            if message is None:
                if code in self.responses:
                    message = self.responses[code][0]
                else:
                    message = ''
            
            self.send_response(code)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Connection', 'close')
            self.end_headers()
            
            error_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Error {code}</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 40px; 
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h1 {{ color: #d32f2f; }}
                    .home-button {{
                        display: inline-block;
                        padding: 10px 20px;
                        background: #007cba;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin-top: 20px;
                    }}
                    .home-button:hover {{
                        background: #005a87;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Error {code}</h1>
                    <p><strong>{message}</strong></p>
                    <p>{explain if explain else ''}</p>
                    <a href="/" class="home-button">Return to Home</a>
                </div>
            </body>
            </html>
            """
            self.wfile.write(error_content.encode('utf-8'))
        except Exception as e:
            print(f"Error sending error page: {e}")

    def do_GET(self):
        try:
            # 获取URL路径
            path = self.path
            
            # 如果URL为空或是根路径，显示主页
            if path == '/' or not path:
                self.show_homepage()
                return
            
            # 处理favicon请求
            if path == '/favicon.ico':
                self.send_error(404, "Favicon not found")
                return
            
            print(f"Request path: {path}")
            
            # 解析URL参数
            parsed_path = urllib.parse.urlparse(path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # 检查是否有当前网站的cookie
            current_site = self.headers.get('Cookie', '').replace('current_site=', '')
            
            # 如果是代理路径格式 (/proxy/url)
            if path.startswith('/proxy/'):
                url = path[7:]  # 去掉 /proxy/ 前缀
                url = urllib.parse.unquote(url)
                print(f"Proxy URL: {url}")
                self.proxy_request(url, set_cookie=True)
                return
            
            # 如果是直接访问的URL
            if len(path) > 1 and not path.startswith('/proxy/'):
                url = path[1:]  # 去掉开头的 /
                url = urllib.parse.unquote(url)
                
                # 检查是否是相对路径（如百度搜索路径）
                if not url.startswith(('http://', 'https://')):
                    # 如果有当前网站的cookie，使用它作为基础URL
                    if current_site:
                        base_url = current_site
                        if not base_url.endswith('/') and not url.startswith('/'):
                            full_url = base_url + '/' + url
                        else:
                            full_url = base_url + url
                        print(f"Relative path, using cookie base: {base_url}")
                        print(f"Full URL: {full_url}")
                        self.proxy_request(full_url, set_cookie=False)
                        return
                    else:
                        # 没有基础URL，显示错误
                        self.show_url_help(url)
                        return
                
                # 完整的URL，直接代理
                print(f"Full URL request: {url}")
                self.proxy_request(url, set_cookie=True)
                return
                
            self.send_error(404, "Page not found")
            
        except Exception as e:
            print(f"Error processing GET request: {e}")
            self.send_error(500, f"Server error: {str(e)}")

    def show_homepage(self):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            homepage = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Web Proxy Server</title>
                <style>
                    * {
                        box-sizing: border-box;
                    }
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 0;
                        padding: 0;
                        background-color: #f5f5f5;
                        position: relative;
                        min-height: 100vh;
                    }
                    .fixed-home-button {
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 10px 20px;
                        background: #007cba;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        z-index: 1000;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    }
                    .fixed-home-button:hover {
                        background: #005a87;
                    }
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        margin-top: 20px;
                        margin-bottom: 20px;
                    }
                    h1 { 
                        color: #333; 
                        text-align: center;
                        margin-top: 0;
                    }
                    .search-box {
                        display: flex;
                        margin: 20px 0;
                    }
                    .search-input {
                        flex: 1;
                        padding: 10px;
                        font-size: 16px;
                        border: 2px solid #ddd;
                        border-radius: 5px 0 0 5px;
                    }
                    .search-button {
                        padding: 10px 20px;
                        background: #007cba;
                        color: white;
                        border: none;
                        border-radius: 0 5px 5px 0;
                        cursor: pointer;
                        font-size: 16px;
                    }
                    .search-button:hover {
                        background: #005a87;
                    }
                    .quick-links {
                        margin-top: 30px;
                    }
                    .quick-links a {
                        display: inline-block;
                        margin: 5px 10px 5px 0;
                        padding: 8px 15px;
                        background: #eee;
                        border-radius: 5px;
                        text-decoration: none;
                        color: #333;
                    }
                    .quick-links a:hover {
                        background: #ddd;
                    }
                    .info {
                        margin-top: 20px;
                        padding: 15px;
                        background: #e7f3ff;
                        border-radius: 5px;
                        font-size: 14px;
                    }
                    .warning {
                        margin-top: 20px;
                        padding: 15px;
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 5px;
                        color: #856404;
                    }
                </style>
            </head>
            <body>
                <a href="/" class="fixed-home-button">Home</a>
                
                <div class="container">
                    <h1>Web Proxy Server</h1>
                    
                    <form id="searchForm" onsubmit="return handleSearch()">
                        <div class="search-box">
                            <input type="text" id="url" class="search-input" 
                                   placeholder="Enter website (e.g. www.baidu.com)" 
                                   value="">
                            <button type="submit" class="search-button">Visit</button>
                        </div>
                    </form>
                    
                    <div class="warning">
                        <strong>Note:</strong> Just enter the domain, no need for https://
                    </div>
                    
                    <div class="quick-links">
                        <strong>Quick Links:</strong><br>
                        <a href="#" onclick="quickVisit('www.baidu.com')">Baidu</a>
                        <a href="#" onclick="quickVisit('www.google.com')">Google</a>
                        <a href="#" onclick="quickVisit('github.com')">GitHub</a>
                        <a href="#" onclick="quickVisit('www.bilibili.com')">Bilibili</a>
                        <a href="#" onclick="quickVisit('www.zhihu.com')">Zhihu</a>
                        <a href="#" onclick="quickVisit('weibo.com')">Weibo</a>
                    </div>
                    
                    <div class="info">
                        <strong>Instructions:</strong><br>
                        1. Enter domain in the box (e.g. www.baidu.com)<br>
                        2. Click "Visit" or press Enter<br>
                        3. System will add https:// automatically<br>
                        4. Fixed "Home" button in top right to return here
                    </div>
                </div>
                
                <script>
                    function handleSearch() {
                        let url = document.getElementById('url').value.trim();
                        if (!url) {
                            alert('Please enter a URL');
                            return false;
                        }
                        
                        // Remove any existing protocol
                        url = url.replace(/^https?:\\/\\//, '');
                        
                        // Use proxy format
                        window.location.href = '/proxy/https://' + url;
                        return false;
                    }
                    
                    function quickVisit(url) {
                        document.getElementById('url').value = url;
                        handleSearch();
                    }
                    
                    document.getElementById('url').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            handleSearch();
                        }
                    });
                    
                    window.onload = function() {
                        document.getElementById('url').focus();
                    };
                </script>
            </body>
            </html>
            """
            self.wfile.write(homepage.encode('utf-8'))
            
        except Exception as e:
            print(f"Error showing homepage: {e}")
            self.send_error(500, f"Error showing homepage: {str(e)}")

    def show_url_help(self, bad_url):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            help_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>URL Format Error</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 40px; 
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .home-button {{
                        display: inline-block;
                        padding: 10px 20px;
                        background: #007cba;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin-top: 20px;
                    }}
                    .home-button:hover {{
                        background: #005a87;
                    }}
                    .warning {{
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .fixed-home-button {{
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 10px 20px;
                        background: #007cba;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        z-index: 1000;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    }}
                </style>
            </head>
            <body>
                <a href="/" class="fixed-home-button">Home</a>
                
                <div class="container">
                    <h1>URL Format Error</h1>
                    
                    <div class="warning">
                        <strong>Cannot process your URL:</strong> {bad_url}
                    </div>
                    
                    <p>This appears to be a relative URL from a website. Please start from the homepage and enter a full domain name.</p>
                    
                    <p>Please enter URLs in this format:</p>
                    <ul>
                        <li><code>www.baidu.com</code></li>
                        <li><code>github.com</code></li>
                        <li><code>www.bilibili.com</code></li>
                    </ul>
                    
                    <p>System will automatically add <code>https://</code> prefix</p>
                    
                    <a href="/" class="home-button">Return to Home</a>
                </div>
            </body>
            </html>
            """
            self.wfile.write(help_page.encode('utf-8'))
            
        except Exception as e:
            print(f"Error showing URL help: {e}")
            self.send_error(500, f"Error showing URL help: {str(e)}")

    def proxy_request(self, url, set_cookie=False):
        try:
            print(f"Proxying: {url}")
            
            # 确保URL是完整的
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 添加原始请求头
            for key, value in self.headers.items():
                key_lower = key.lower()
                if key_lower not in ['host', 'connection', 'accept-encoding', 'content-length', 'cookie']:
                    headers[key] = value
            
            # SSL上下文
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 创建请求
            req = urllib.request.Request(url, headers=headers)
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                content = response.read()
                
                # 处理gzip压缩
                if response.headers.get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                # 获取基础URL用于重写相对链接
                parsed_url = urllib.parse.urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                # 在所有HTML页面中插入返回首页按钮和重写链接
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    # 重写相对链接为绝对链接
                    content = self.rewrite_links(content, base_url)
                    
                    # 插入返回首页按钮
                    home_button = b'''
                    <div style="position:fixed;top:10px;right:10px;z-index:10000;background:white;padding:5px;border-radius:5px;box-shadow:0 2px 10px rgba(0,0,0,0.2);">
                        <a href="/" style="display:block;padding:8px 15px;background:#007cba;color:white;text-decoration:none;border-radius:3px;font-family:Arial,sans-serif;font-size:14px;">Home</a>
                    </div>
                    '''
                    
                    # 在body标签开始后插入按钮
                    body_start = content.find(b'<body')
                    if body_start != -1:
                        body_end = content.find(b'>', body_start) + 1
                        content = content[:body_end] + home_button + content[body_end:]
                
                # 发送响应头
                self.send_response(response.getcode())
                
                # 设置cookie来跟踪当前网站
                if set_cookie:
                    self.send_header('Set-Cookie', f'current_site={base_url}')
                
                # 复制响应头
                for key, value in response.headers.items():
                    key_lower = key.lower()
                    if key_lower not in ['content-encoding', 'transfer-encoding', 'connection', 'content-length', 'set-cookie']:
                        self.send_header(key, value)
                
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                
                # 发送响应内容
                self.wfile.write(content)
                
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            self.send_error(e.code, f"Proxy request failed: {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
            self.send_error(502, f"Cannot connect to target: {str(e.reason)}")
        except socket.timeout:
            print("Request timeout")
            self.send_error(504, "Request timeout")
        except Exception as e:
            print(f"Proxy request error: {e}")
            self.send_error(500, f"Proxy request error: {str(e)}")

    def rewrite_links(self, content, base_url):
        """重写HTML中的相对链接为绝对链接"""
        try:
            # 将字节内容转换为字符串
            html_content = content.decode('utf-8', errors='ignore')
            
            # 重写各种类型的链接
            import re
            
            # 重写 href 属性
            html_content = re.sub(
                r'href="/([^"]*)"',
                f'href="/proxy/{base_url}/\\1"',
                html_content
            )
            
            # 重写以 // 开头的协议相对URL
            html_content = re.sub(
                r'href="//([^"]*)"',
                f'href="/proxy/https://\\1"',
                html_content
            )
            
            # 重写相对路径（不以/开头）
            html_content = re.sub(
                r'href="([^"/][^"]*)"',
                f'href="/proxy/{base_url}/\\1"',
                html_content
            )
            
            # 重写 action 属性（表单）
            html_content = re.sub(
                r'action="/([^"]*)"',
                f'action="/proxy/{base_url}/\\1"',
                html_content
            )
            
            # 重写 src 属性
            html_content = re.sub(
                r'src="/([^"]*)"',
                f'src="/proxy/{base_url}/\\1"',
                html_content
            )
            
            return html_content.encode('utf-8')
            
        except Exception as e:
            print(f"Error rewriting links: {e}")
            return content

    def log_message(self, format, *args):
        message = format % args
        try:
            print(f"[{self.client_address[0]}] {message}")
        except UnicodeEncodeError:
            safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
            print(f"[{self.client_address[0]}] {safe_message}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def run_proxy_server():
    ports = [60000, 61000, 62000, 63000, 64000, 65000]
    
    for port in ports:
        try:
            # 清理端口
            try:
                os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")
                time.sleep(1)
            except:
                pass
            
            server = ThreadedHTTPServer(('', port), ProxyRequestHandler)
            print(f"Proxy server started on port {port}")
            print(f"Visit: http://localhost:{port}")
            print("Type 'exit' and press Enter to stop the server")
            
            # 启动服务器线程
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # 监听退出命令
            while True:
                try:
                    # 使用select检查是否有输入可用
                    if select.select([sys.stdin], [], [], 0.5)[0]:
                        command = sys.stdin.readline().strip().lower()
                        if command in ['exit', 'quit', 'stop']:
                            print("Shutting down server...")
                            server.shutdown()
                            server.server_close()
                            return
                except (KeyboardInterrupt, EOFError):
                    print("\nShutting down server...")
                    server.shutdown()
                    server.server_close()
                    return
                    
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} in use, trying next...")
                continue
            else:
                print(f"Port {port} error: {e}")
                continue
        except Exception as e:
            print(f"Server startup error: {e}")
            continue
    
    print("All ports unavailable, please check system")

if __name__ == '__main__':
    run_proxy_server()
