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
import re

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            path = self.path
            
            if path == '/' or not path:
                self.show_homepage()
                return
            
            if path == '/favicon.ico':
                self.send_error(404, "Favicon not found")
                return
            
            print(f"Request path: {path}")
            
            # 解析路径
            if path.startswith('/proxy/'):
                # 代理模式：/proxy/https://www.baidu.com
                url = path[7:]  # 去掉 /proxy/ 前缀
                url = urllib.parse.unquote(url)
                print(f"Proxy URL: {url}")
                self.proxy_request(url)
            else:
                # 直接模式：/www.baidu.com
                url = path[1:]  # 去掉开头的 /
                url = urllib.parse.unquote(url)
                
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                print(f"Direct URL: {url}")
                self.proxy_request(url)
                
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

    def proxy_request(self, url):
        try:
            print(f"Proxying: {url}")
            
            # 确保URL是完整的
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # 解析URL获取基础信息
            parsed_url = urllib.parse.urlparse(url)
            base_domain = parsed_url.netloc
            base_url = f"{parsed_url.scheme}://{base_domain}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Host': base_domain  # 重要：设置正确的Host头
            }
            
            # 添加原始请求头（排除一些不需要的）
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
                
                # 获取内容类型
                content_type = response.headers.get('Content-Type', '').lower()
                
                # 处理HTML内容
                if 'text/html' in content_type:
                    # 重写页面中的所有链接
                    content = self.rewrite_html_links(content, base_url)
                    
                    # 插入返回首页按钮
                    content = self.add_home_button(content)
                
                # 处理CSS内容
                elif 'text/css' in content_type:
                    content = self.rewrite_css_urls(content, base_url)
                
                # 发送响应头
                self.send_response(response.getcode())
                
                # 复制响应头，但移除或修改一些可能引起问题的头
                for key, value in response.headers.items():
                    key_lower = key.lower()
                    
                    # 移除可能引起问题的头
                    if key_lower in ['content-security-policy', 'x-frame-options', 'x-content-type-options']:
                        continue
                    
                    # 修改内容类型
                    if key_lower == 'content-type':
                        if 'text/html' in value.lower():
                            self.send_header('Content-Type', 'text/html; charset=utf-8')
                        elif 'text/css' in value.lower():
                            self.send_header('Content-Type', 'text/css; charset=utf-8')
                        else:
                            self.send_header(key, value)
                    else:
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

    def rewrite_html_links(self, content, base_url):
        """重写HTML中的所有链接"""
        try:
            # 将字节内容转换为字符串
            html_content = content.decode('utf-8', errors='ignore')
            
            # 获取基础域名
            parsed_base = urllib.parse.urlparse(base_url)
            base_domain = parsed_base.netloc
            
            # 重写各种类型的链接
            patterns = [
                # href 属性
                (r'href="/([^"]*)"', f'href="/proxy/{base_url}/\\1"'),
                (r'href="//([^"]*)"', f'href="/proxy/https://\\1"'),
                (r'href="http://([^"]*)"', f'href="/proxy/http://\\1"'),
                (r'href="https://([^"]*)"', f'href="/proxy/https://\\1"'),
                
                # src 属性
                (r'src="/([^"]*)"', f'src="/proxy/{base_url}/\\1"'),
                (r'src="//([^"]*)"', f'src="/proxy/https://\\1"'),
                (r'src="http://([^"]*)"', f'src="/proxy/http://\\1"'),
                (r'src="https://([^"]*)"', f'src="/proxy/https://\\1"'),
                
                # action 属性（表单）
                (r'action="/([^"]*)"', f'action="/proxy/{base_url}/\\1"'),
                (r'action="//([^"]*)"', f'action="/proxy/https://\\1"'),
                (r'action="http://([^"]*)"', f'action="/proxy/http://\\1"'),
                (r'action="https://([^"]*)"', f'action="/proxy/https://\\1"'),
                
                # meta refresh
                (r'content="\d+;url=/([^"]*)"', f'content="0;url=/proxy/{base_url}/\\1"'),
                (r'content="\d+;url=//([^"]*)"', f'content="0;url=/proxy/https://\\1"'),
                (r'content="\d+;url=http://([^"]*)"', f'content="0;url=/proxy/http://\\1"'),
                (r'content="\d+;url=https://([^"]*)"', f'content="0;url=/proxy/https://\\1"'),
            ]
            
            for pattern, replacement in patterns:
                html_content = re.sub(pattern, replacement, html_content)
            
            # 重写JavaScript中的URL（简单处理）
            js_patterns = [
                (r'location\.href\s*=\s*"/([^"]*)"', f'location.href = "/proxy/{base_url}/\\1"'),
                (r'location\.href\s*=\s*"//([^"]*)"', f'location.href = "/proxy/https://\\1"'),
                (r'window\.location\s*=\s*"/([^"]*)"', f'window.location = "/proxy/{base_url}/\\1"'),
                (r'window\.location\s*=\s*"//([^"]*)"', f'window.location = "/proxy/https://\\1"'),
            ]
            
            for pattern, replacement in js_patterns:
                html_content = re.sub(pattern, replacement, html_content)
            
            return html_content.encode('utf-8')
            
        except Exception as e:
            print(f"Error rewriting HTML links: {e}")
            return content

    def rewrite_css_urls(self, content, base_url):
        """重写CSS中的URL"""
        try:
            # 将字节内容转换为字符串
            css_content = content.decode('utf-8', errors='ignore')
            
            # 重写CSS中的url()引用
            patterns = [
                # 相对路径
                (r'url\("/([^"]*)"\)', f'url("/proxy/{base_url}/\\1")'),
                (r'url\(\'/([^\']*)\'\)', f'url(\'/proxy/{base_url}/\\1\')'),
                (r'url\(/([^)]*)\)', f'url(/proxy/{base_url}/\\1)'),
                
                # 协议相对路径
                (r'url\("//([^"]*)"\)', f'url("/proxy/https://\\1")'),
                (r'url\(\'//([^\']*)\'\)', f'url(\'/proxy/https://\\1\')'),
                (r'url\(//([^)]*)\)', f'url(/proxy/https://\\1)'),
                
                # 绝对路径
                (r'url\("http://([^"]*)"\)', f'url("/proxy/http://\\1")'),
                (r'url\("https://([^"]*)"\)', f'url("/proxy/https://\\1")'),
                (r'url\(\'http://([^\']*)\'\)', f'url(\'/proxy/http://\\1\')'),
                (r'url\(\'https://([^\']*)\'\)', f'url(\'/proxy/https://\\1\')'),
            ]
            
            for pattern, replacement in patterns:
                css_content = re.sub(pattern, replacement, css_content)
            
            return css_content.encode('utf-8')
            
        except Exception as e:
            print(f"Error rewriting CSS URLs: {e}")
            return content

    def add_home_button(self, content):
        """在所有HTML页面中添加返回首页按钮"""
        try:
            html_content = content.decode('utf-8', errors='ignore')
            
            # 创建返回首页按钮的HTML
            home_button = '''
            <div id="proxy-home-button" style="position:fixed;top:10px;right:10px;z-index:10000;background:rgba(255,255,255,0.9);padding:5px;border-radius:5px;box-shadow:0 2px 10px rgba(0,0,0,0.2);border:1px solid #ccc;">
                <a href="/" style="display:block;padding:8px 15px;background:#007cba;color:white;text-decoration:none;border-radius:3px;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;">Home</a>
            </div>
            '''
            
            # 在body标签开始后插入按钮
            body_start = html_content.find('<body')
            if body_start != -1:
                body_end = html_content.find('>', body_start) + 1
                html_content = html_content[:body_end] + home_button + html_content[body_end:]
            
            return html_content.encode('utf-8')
            
        except Exception as e:
            print(f"Error adding home button: {e}")
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
