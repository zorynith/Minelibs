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

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    # 重写send_error方法以支持UTF-8编码
    def send_error(self, code, message=None, explain=None):
        """重写send_error方法以支持UTF-8编码"""
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
                <title>错误 {code}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #d32f2f; }}
                </style>
            </head>
            <body>
                <h1>错误 {code}</h1>
                <p><strong>{message}</strong></p>
                <p>{explain if explain else ''}</p>
            </body>
            </html>
            """
            self.wfile.write(error_content.encode('utf-8'))
        except Exception as e:
            print(f"发送错误页面失败: {e}")

    def do_GET(self):
        try:
            # 解析URL
            url = self.path[1:]  # 去掉开头的/
            
            # 如果URL为空，显示主页
            if not url:
                self.show_homepage()
                return
                
            # 代理请求
            self.proxy_request(url)
            
        except Exception as e:
            print(f"处理GET请求时出错: {e}")
            self.send_error(500, f"服务器内部错误: {str(e)}")

    def do_POST(self):
        try:
            # 获取POST数据
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            
            # 解析URL
            url = self.path[1:]
            
            if not url:
                self.send_error(400, "缺少目标URL")
                return
                
            # 代理POST请求
            self.proxy_post_request(url, post_data)
            
        except Exception as e:
            print(f"处理POST请求时出错: {e}")
            self.send_error(500, f"服务器内部错误: {str(e)}")

    def show_homepage(self):
        """显示代理服务器主页"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            homepage = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>网页代理服务器</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 40px; 
                        background-color: #f5f5f5;
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
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🌐 网页代理服务器</h1>
                    
                    <form id="searchForm" onsubmit="return handleSearch()">
                        <div class="search-box">
                            <input type="text" id="url" class="search-input" 
                                   placeholder="输入网址 (例如: https://www.example.com)" 
                                   value="https://">
                            <button type="submit" class="search-button">访问</button>
                        </div>
                    </form>
                    
                    <div class="quick-links">
                        <strong>快速访问:</strong><br>
                        <a href="#" onclick="quickVisit('https://www.baidu.com')">百度</a>
                        <a href="#" onclick="quickVisit('https://www.google.com')">Google</a>
                        <a href="#" onclick="quickVisit('https://github.com')">GitHub</a>
                        <a href="#" onclick="quickVisit('https://www.bilibili.com')">B站</a>
                    </div>
                    
                    <div class="info">
                        <strong>使用说明:</strong><br>
                        1. 在输入框中输入完整的网址（包含 https:// 或 http://）<br>
                        2. 点击"访问"按钮或按回车键<br>
                        3. 支持大多数网站的代理访问
                    </div>
                </div>
                
                <script>
                    function handleSearch() {
                        let url = document.getElementById('url').value.trim();
                        if (!url) {
                            alert('请输入网址');
                            return false;
                        }
                        
                        // 确保URL包含协议
                        if (!url.startsWith('http://') && !url.startsWith('https://')) {
                            url = 'https://' + url;
                        }
                        
                        // 使用代理访问
                        window.location.href = '/' + encodeURIComponent(url);
                        return false;
                    }
                    
                    function quickVisit(url) {
                        document.getElementById('url').value = url;
                        handleSearch();
                    }
                    
                    // 回车键提交
                    document.getElementById('url').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            handleSearch();
                        }
                    });
                </script>
            </body>
            </html>
            """
            self.wfile.write(homepage.encode('utf-8'))
            
        except Exception as e:
            print(f"显示主页时出错: {e}")
            self.send_error(500, f"显示主页时出错: {str(e)}")

    def proxy_request(self, url):
        """代理HTTP请求"""
        try:
            # 解码URL（可能被编码过）
            try:
                url = urllib.parse.unquote(url)
            except:
                pass
                
            print(f"正在代理访问: {url}")
            
            # 设置请求头
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'connection', 'accept-encoding']:
                    headers[key] = value
            
            # 添加常见的浏览器头
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
            
            # 创建请求
            req = urllib.request.Request(url, headers=headers)
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=30) as response:
                # 获取响应数据
                content = response.read()
                
                # 处理gzip压缩
                if response.headers.get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                # 发送响应头
                self.send_response(response.getcode())
                
                # 复制响应头（排除一些不合适的头）
                for key, value in response.headers.items():
                    key_lower = key.lower()
                    if key_lower not in ['content-encoding', 'transfer-encoding', 'connection']:
                        self.send_header(key, value)
                
                # 确保使用UTF-8编码
                if 'content-type' in response.headers and 'charset' not in response.headers['content-type'].lower():
                    content_type = response.headers['content-type']
                    if content_type.startswith('text/'):
                        self.send_header('Content-Type', content_type + '; charset=utf-8')
                
                self.end_headers()
                
                # 发送响应内容
                self.wfile.write(content)
                
        except urllib.error.HTTPError as e:
            print(f"HTTP错误: {e.code} - {e.reason}")
            self.send_error(e.code, f"代理请求失败: {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL错误: {e.reason}")
            self.send_error(502, f"无法连接到目标网站: {str(e.reason)}")
        except socket.timeout:
            print("请求超时")
            self.send_error(504, "请求超时")
        except Exception as e:
            print(f"代理请求时出错: {e}")
            self.send_error(500, f"代理请求时出错: {str(e)}")

    def proxy_post_request(self, url, post_data):
        """代理POST请求"""
        try:
            # 解码URL
            try:
                url = urllib.parse.unquote(url)
            except:
                pass
                
            print(f"正在代理POST访问: {url}")
            
            # 设置请求头
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'connection', 'content-length']:
                    headers[key] = value
            
            # 添加常见的浏览器头
            headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            # 创建POST请求
            req = urllib.request.Request(url, data=post_data, headers=headers, method='POST')
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=30) as response:
                # 获取响应数据
                content = response.read()
                
                # 处理gzip压缩
                if response.headers.get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                # 发送响应头
                self.send_response(response.getcode())
                
                # 复制响应头
                for key, value in response.headers.items():
                    key_lower = key.lower()
                    if key_lower not in ['content-encoding', 'transfer-encoding', 'connection']:
                        self.send_header(key, value)
                
                self.end_headers()
                
                # 发送响应内容
                self.wfile.write(content)
                
        except Exception as e:
            print(f"代理POST请求时出错: {e}")
            self.send_error(500, f"代理POST请求时出错: {str(e)}")

    def log_message(self, format, *args):
        """重写日志方法，使用UTF-8编码输出"""
        message = format % args
        try:
            print(f"[{self.client_address[0]}] {message}")
        except UnicodeEncodeError:
            safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
            print(f"[{self.client_address[0]}] {safe_message}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """支持多线程的HTTP服务器"""
    daemon_threads = True
    allow_reuse_address = True  # 允许地址重用

def find_available_port(start_port=60000, max_attempts=10):
    """查找可用的端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # 尝试绑定端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    return None

def run_proxy_server(port=60000):
    """运行代理服务器"""
    # 先尝试杀死占用端口的进程
    try:
        os.system(f"fuser -k {port}/tcp > /dev/null 2>&1")
        time.sleep(1)  # 等待端口释放
    except:
        pass
    
    # 查找可用端口
    available_port = find_available_port(port)
    
    if available_port is None:
        print("❌ 找不到可用端口，请手动关闭占用端口的进程")
        return
    
    try:
        server = ThreadedHTTPServer(('', available_port), ProxyRequestHandler)
        print(f"🌐 代理服务器已启动在端口 {available_port}")
        print(f"📱 请在浏览器中访问: http://localhost:{available_port}")
        print("⏹️  要停止服务器，请按 Ctrl+C")
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器正在关闭...")
        server.shutdown()
        server.server_close()
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")

if __name__ == '__main__':
    # 在Cloud Shell中使用端口60000
    run_proxy_server(60000)
