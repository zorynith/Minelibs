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

class ProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.current_host = None
        super().__init__(*args, **kwargs)

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
                    <h1>错误 {code}</h1>
                    <p><strong>{message}</strong></p>
                    <p>{explain if explain else ''}</p>
                    <a href="/" class="home-button">返回首页</a>
                </div>
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
            
            # 解码URL
            try:
                url = urllib.parse.unquote(url)
            except:
                pass
            
            print(f"原始请求URL: {url}")
            
            # 处理favicon请求
            if url == 'favicon.ico':
                self.send_error(404, "Favicon not found")
                return
            
            # 检查是否是相对路径（如百度搜索路径）
            if not url.startswith(('http://', 'https://')) and self.current_host:
                # 这是相对路径，需要与当前主机组合
                full_url = self.current_host + url
                print(f"相对路径，组合为完整URL: {full_url}")
                self.proxy_request(full_url)
                return
                
            # 检查URL格式并修复
            fixed_url = self.fix_url(url)
            if not fixed_url:
                self.show_url_help(url)
                return
                
            print(f"修复后URL: {fixed_url}")
            
            # 更新当前主机
            parsed_url = urllib.parse.urlparse(fixed_url)
            self.current_host = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 代理请求
            self.proxy_request(fixed_url)
            
        except Exception as e:
            print(f"处理GET请求时出错: {e}")
            self.send_error(500, f"服务器内部错误: {str(e)}")

    def fix_url(self, url):
        """修复URL格式"""
        # 如果URL已经是完整的，直接返回
        if url.startswith(('http://', 'https://')):
            return url
            
        # 如果URL包含空格或其他问题，进行清理
        url = url.strip()
        
        # 检查是否包含常见域名特征
        if '.' in url and not url.startswith(('http://', 'https://')):
            # 添加https://前缀
            return 'https://' + url
            
        return None

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
                <!-- 固定在右上角的返回首页按钮 -->
                <a href="/" class="fixed-home-button">返回首页</a>
                
                <div class="container">
                    <h1>网页代理服务器</h1>
                    
                    <form id="searchForm" onsubmit="return handleSearch()">
                        <div class="search-box">
                            <input type="text" id="url" class="search-input" 
                                   placeholder="输入完整网址 (例如: www.baidu.com)" 
                                   value="">
                            <button type="submit" class="search-button">访问</button>
                        </div>
                    </form>
                    
                    <div class="warning">
                        <strong>注意:</strong> 请直接输入域名，不需要输入 https://，系统会自动添加
                    </div>
                    
                    <div class="quick-links">
                        <strong>快速访问:</strong><br>
                        <a href="#" onclick="quickVisit('www.baidu.com')">百度</a>
                        <a href="#" onclick="quickVisit('www.google.com')">Google</a>
                        <a href="#" onclick="quickVisit('github.com')">GitHub</a>
                        <a href="#" onclick="quickVisit('www.bilibili.com')">B站</a>
                        <a href="#" onclick="quickVisit('www.zhihu.com')">知乎</a>
                        <a href="#" onclick="quickVisit('weibo.com')">微博</a>
                    </div>
                    
                    <div class="info">
                        <strong>使用说明:</strong><br>
                        1. 在输入框中输入域名（例如: www.baidu.com）<br>
                        2. 点击"访问"按钮或按回车键<br>
                        3. 系统会自动添加 https:// 前缀<br>
                        4. 右上角有固定的"返回首页"按钮，随时可以回到此页面
                    </div>
                </div>
                
                <script>
                    function handleSearch() {
                        let url = document.getElementById('url').value.trim();
                        if (!url) {
                            alert('请输入网址');
                            return false;
                        }
                        
                        // 清理URL，移除可能的多余协议
                        url = url.replace(/^https?:\\/\\//, '');
                        
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
                    
                    // 页面加载后自动聚焦输入框
                    window.onload = function() {
                        document.getElementById('url').focus();
                    };
                </script>
            </body>
            </html>
            """
            self.wfile.write(homepage.encode('utf-8'))
            
        except Exception as e:
            print(f"显示主页时出错: {e}")
            self.send_error(500, f"显示主页时出错: {str(e)}")

    def show_url_help(self, bad_url):
        """显示URL格式帮助"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            help_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>URL格式错误</title>
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
                <a href="/" class="fixed-home-button">返回首页</a>
                
                <div class="container">
                    <h1>URL格式错误</h1>
                    
                    <div class="warning">
                        <strong>无法处理您输入的URL:</strong> {bad_url}
                    </div>
                    
                    <p>请按照以下格式输入网址：</p>
                    <ul>
                        <li><code>www.baidu.com</code></li>
                        <li><code>github.com</code></li>
                        <li><code>www.bilibili.com</code></li>
                    </ul>
                    
                    <p>系统会自动为您添加 <code>https://</code> 前缀</p>
                    
                    <a href="/" class="home-button">返回首页重新输入</a>
                </div>
            </body>
            </html>
            """
            self.wfile.write(help_page.encode('utf-8'))
            
        except Exception as e:
            print(f"显示URL帮助时出错: {e}")
            self.send_error(500, f"显示URL帮助时出错: {str(e)}")

    def proxy_request(self, url):
        """代理HTTP请求"""
        try:
            print(f"正在代理访问: {url}")
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 添加原始请求头（排除一些不需要的）
            for key, value in self.headers.items():
                key_lower = key.lower()
                if key_lower not in ['host', 'connection', 'accept-encoding', 'content-length']:
                    headers[key] = value
            
            # 创建SSL上下文，忽略证书验证
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 创建请求
            req = urllib.request.Request(url, headers=headers)
            
            # 发送请求，忽略SSL证书验证
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                # 获取响应数据
                content = response.read()
                
                # 处理gzip压缩
                if response.headers.get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(content)
                
                # 修改HTML内容，添加返回首页按钮
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    # 在HTML中插入返回首页按钮
                    home_button = b'''
                    <div style="position:fixed;top:20px;right:20px;z-index:9999;">
                        <a href="/" style="padding:10px 20px;background:#007cba;color:white;text-decoration:none;border-radius:5px;font-family:Arial,sans-serif;">返回首页</a>
                    </div>
                    '''
                    # 在body标签后插入按钮
                    if b'<body' in content:
                        # 找到body标签的位置
                        body_pos = content.find(b'<body')
                        if body_pos != -1:
                            # 找到body标签结束的位置
                            body_end_pos = content.find(b'>', body_pos) + 1
                            # 在body标签后插入按钮
                            content = content[:body_end_pos] + home_button + content[body_end_pos:]
                
                # 发送响应头
                self.send_response(response.getcode())
                
                # 复制响应头（排除一些不合适的头）
                for key, value in response.headers.items():
                    key_lower = key.lower()
                    if key_lower not in ['content-encoding', 'transfer-encoding', 'connection', 'content-length']:
                        self.send_header(key, value)
                
                # 更新内容长度
                self.send_header('Content-Length', str(len(content)))
                
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
    allow_reuse_address = True

def run_proxy_server():
    """运行代理服务器"""
    # 使用指定的端口范围
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
            print(f"代理服务器已启动在端口 {port}")
            print(f"请在浏览器中访问: http://localhost:{port}")
            print("要停止服务器，请按 Ctrl+C")
            
            server.serve_forever()
            return
                    
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"端口 {port} 被占用，尝试下一个端口...")
                continue
            else:
                print(f"端口 {port} 错误: {e}")
                continue
        except Exception as e:
            print(f"启动服务器时出错: {e}")
            continue
    
    print("所有端口都不可用，请检查系统状态")

if __name__ == '__main__':
    run_proxy_server()
