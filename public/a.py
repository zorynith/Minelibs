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
        self.current_host = None
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
            
            # 使用纯ASCII字符的错误页面
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
            url = self.path[1:]
            
            if not url:
                self.show_homepage()
                return
            
            try:
                url = urllib.parse.unquote(url)
            except:
                pass
            
            print(f"Request URL: {url}")
            
            if url == 'favicon.ico':
                self.send_error(404, "Favicon not found")
                return
            
            # 处理相对路径
            if not url.startswith(('http://', 'https://')) and self.current_host:
                full_url = self.current_host + url
                print(f"Relative path, combined to: {full_url}")
                self.proxy_request(full_url)
                return
                
            fixed_url = self.fix_url(url)
            if not fixed_url:
                self.show_url_help(url)
                return
                
            print(f"Fixed URL: {fixed_url}")
            
            parsed_url = urllib.parse.urlparse(fixed_url)
            self.current_host = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            self.proxy_request(fixed_url)
            
        except Exception as e:
            print(f"Error processing GET request: {e}")
            self.send_error(500, f"Server error: {str(e)}")

    def fix_url(self, url):
        if url.startswith(('http://', 'https://')):
            return url
            
        url = url.strip()
        
        if '.' in url and not url.startswith(('http://', 'https://')):
            return 'https://' + url
            
        return None

    def show_homepage(self):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 使用纯ASCII字符的主页
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
                        
                        url = url.replace(/^https?:\\/\\//, '');
                        
                        window.location.href = '/' + encodeURIComponent(url);
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

    def proxy_request(self, url):
        try:
            print(f"Proxying: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            for key, value in self.headers.items():
                key_lower = key.lower()
                if key_lower not in ['host', 'connection', 'accept-encoding', 'content-length']:
                    headers[key] = value
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                content = response.read()
                
                if response.headers.get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                # 在所有HTML页面中插入返回首页按钮
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    # 创建返回首页按钮的HTML
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
                
                self.send_response(response.getcode())
                
                for key, value in response.headers.items():
                    key_lower = key.lower()
                    if key_lower not in ['content-encoding', 'transfer-encoding', 'connection', 'content-length']:
                        self.send_header(key, value)
                
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                
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
