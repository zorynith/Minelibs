#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Cloud Shell HTTP 代理网关
    基于 simple-http-proxy 修改，添加网页界面支持
"""
from __future__ import print_function

import socket
import select
import time
import threading
import http.server
import socketserver
import urllib.parse

def debug(tag, msg):
    print('[%s] %s' % (tag, msg))

class HttpRequestPacket(object):
    '''
    HTTP请求包
    '''
    def __init__(self, data):
        self.__parse(data)

    def __parse(self, data):
        '''
        解析一个HTTP请求数据包
        '''
        i0 = data.find(b'\r\n') # 请求行与请求头的分隔位置
        i1 = data.find(b'\r\n\r\n') # 请求头与请求数据的分隔位置
    
        # 请求行 Request-Line
        self.req_line = data[:i0]
        parts = self.req_line.split()
        if len(parts) >= 3:
            self.method, self.req_uri, self.version = parts
        else:
            self.method, self.req_uri, self.version = b'', b'', b''
        
        # 请求头域 Request Header Fields
        self.req_header = data[i0+2:i1]
        self.headers = {}
        for header in self.req_header.split(b'\r\n'):
            if b': ' in header:
                k, v = header.split(b': ', 1)
                self.headers[k] = v
        self.host = self.headers.get(b'Host', b'')
        
        # 请求数据
        self.req_data = data[i1+4:]

class SimpleHttpProxy(object):
    '''
    简单的HTTP代理
    '''
    def __init__(self, host='0.0.0.0', port=60000, listen=10, bufsize=8, delay=1):
        '''
        初始化代理套接字
        '''
        self.socket_proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_proxy.bind((host, port))
        self.socket_proxy.listen(listen)

        self.socket_recv_bufsize = bufsize*1024
        self.delay = delay/1000.0

        debug('info', '代理服务器启动在 %s:%s' % (host, port))
        debug('info', '监听数=%s, 缓冲区=%skb, 延迟=%sms' % (listen, bufsize, delay))

    def __del__(self):
        self.socket_proxy.close()
    
    def __connect(self, host, port):
        '''
        解析DNS得到套接字地址并与之建立连接
        '''
        try:
            # 解析DNS获取对应协议簇、socket类型、目标地址
            (family, sockettype, _, _, target_addr) = socket.getaddrinfo(host, port)[0]
            
            tmp_socket = socket.socket(family, sockettype)
            tmp_socket.setblocking(0)
            tmp_socket.settimeout(5)
            tmp_socket.connect(target_addr)
            return tmp_socket
        except Exception as e:
            debug('error', f'连接失败 {host}:{port} - {e}')
            return None
         
    def __proxy(self, socket_client):
        '''
        代理核心程序
        '''
        try:
            # 接收客户端请求数据
            req_data = socket_client.recv(self.socket_recv_bufsize)
            if req_data == b'':
                return

            # 解析http请求数据
            http_packet = HttpRequestPacket(req_data)
            
            debug('info', f'请求: {http_packet.method} {http_packet.req_uri}')

            # 获取服务端host、port
            if http_packet.host:
                if b':' in http_packet.host:
                    server_host, server_port = http_packet.host.split(b':')
                    server_port = int(server_port)
                else:
                    server_host, server_port = http_packet.host, 80
            else:
                debug('error', '没有Host头')
                socket_client.close()
                return

            # 修正http请求数据 - 移除代理格式的URI
            if http_packet.req_uri.startswith(b'http://') or http_packet.req_uri.startswith(b'https://'):
                tmp = b'%s//%s' % (http_packet.req_uri.split(b'//')[0], http_packet.host)
                req_data = req_data.replace(tmp, b'')

            # HTTP方法
            if http_packet.method in [b'GET', b'POST', b'PUT', b'DELETE', b'HEAD', b'OPTIONS']:
                socket_server = self.__connect(server_host.decode(), server_port)
                if socket_server is None:
                    socket_client.close()
                    return
                    
                socket_server.send(req_data) # 将客户端请求数据发给服务端

            # HTTPS，会先通过CONNECT方法建立TCP连接
            elif http_packet.method == b'CONNECT':
                socket_server = self.__connect(server_host.decode(), server_port)
                if socket_server is None:
                    socket_client.close()
                    return

                success_msg = b'%s %d Connection Established\r\nConnection: close\r\n\r\n'\
                    %(http_packet.version, 200)
                socket_client.send(success_msg) # 完成连接，通知客户端
                
                # 客户端得知连接建立，会将真实请求数据发送给代理服务端
                req_data = socket_client.recv(self.socket_recv_bufsize) # 接收客户端真实数据
                socket_server.send(req_data) # 将客户端真实请求数据发给服务端

            # 使用select异步处理，不阻塞
            self.__nonblocking(socket_client, socket_server)
            
        except Exception as e:
            debug('error', f'代理处理错误: {e}')
            try:
                socket_client.close()
            except:
                pass

    def __nonblocking(self, socket_client, socket_server):
        '''
        使用select实现异步处理数据
        '''
        _rlist = [socket_client, socket_server]
        is_recv = True
        while is_recv:
            try:
                rlist, _, elist = select.select(_rlist, [], [], 2)
                if elist:
                    break
                for tmp_socket in rlist:
                    is_recv = True
                    # 接收数据
                    data = tmp_socket.recv(self.socket_recv_bufsize)
                    if data == b'':
                        is_recv = False
                        continue
                    
                    # socket_client状态为readable, 当前接收的数据来自客户端
                    if tmp_socket is socket_client: 
                        socket_server.send(data) # 将客户端请求数据发往服务端

                    # socket_server状态为readable, 当前接收的数据来自服务端
                    elif tmp_socket is socket_server:
                        socket_client.send(data) # 将服务端响应数据发往客户端
                        
                time.sleep(self.delay) # 适当延迟以降低CPU占用
            except Exception as e:
                break

        try:
            socket_client.close()
        except:
            pass
        try:
            socket_server.close()
        except:
            pass

    def start_proxy(self):
        '''
        启动代理服务器
        '''
        debug('info', 'HTTP代理服务器运行中...')
        while True:
            try:
                socket_client, addr = self.socket_proxy.accept()
                debug('info', '接受客户端连接: %s:%s' % addr)
                # 在新线程中处理客户端请求
                client_thread = threading.Thread(target=self.__proxy, args=(socket_client,))
                client_thread.daemon = True
                client_thread.start()
            except KeyboardInterrupt:
                debug('info', '代理服务器停止')
                break
            except Exception as e:
                debug('error', f'接受连接错误: {e}')
                continue

class ProxyGateway(http.server.SimpleHTTPRequestHandler):
    '''
    HTTP网关界面，提供网页输入界面
    '''
    def do_GET(self):
        # 解析查询参数
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # 如果是根路径，显示导航页面
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cloud Shell HTTP 代理网关</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    * { box-sizing: border-box; }
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                        margin: 0; padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                    }
                    .container { 
                        max-width: 800px; 
                        margin: 0 auto; 
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        overflow: hidden;
                    }
                    .header {
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }
                    .header h1 { 
                        margin: 0; 
                        font-size: 2.2em;
                        font-weight: 300;
                    }
                    .header p { 
                        margin: 10px 0 0; 
                        opacity: 0.9;
                        font-size: 1.1em;
                    }
                    .content {
                        padding: 40px;
                    }
                    .input-group {
                        display: flex;
                        margin-bottom: 25px;
                        border: 2px solid #e1e5e9;
                        border-radius: 8px;
                        overflow: hidden;
                        transition: border-color 0.3s;
                    }
                    .input-group:focus-within {
                        border-color: #4facfe;
                    }
                    .url-input {
                        flex: 1;
                        padding: 15px 20px;
                        border: none;
                        outline: none;
                        font-size: 16px;
                    }
                    .submit-btn {
                        background: #4facfe;
                        color: white;
                        border: none;
                        padding: 0 30px;
                        cursor: pointer;
                        font-size: 16px;
                        font-weight: 500;
                        transition: background 0.3s;
                    }
                    .submit-btn:hover {
                        background: #3a9bf4;
                    }
                    .quick-links {
                        margin-top: 40px;
                    }
                    .section-title {
                        font-size: 1.2em;
                        color: #2d3748;
                        margin-bottom: 20px;
                        font-weight: 500;
                    }
                    .link-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                    }
                    .quick-link {
                        display: block;
                        padding: 15px 20px;
                        background: #f7fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        text-decoration: none;
                        color: #4a5568;
                        transition: all 0.3s;
                        font-weight: 500;
                    }
                    .quick-link:hover {
                        background: #4facfe;
                        color: white;
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(79, 172, 254, 0.3);
                    }
                    .instructions {
                        background: #f0f9ff;
                        border-left: 4px solid #4facfe;
                        padding: 20px;
                        margin-top: 30px;
                        border-radius: 0 8px 8px 0;
                    }
                    .instructions h3 {
                        margin-top: 0;
                        color: #2d3748;
                    }
                    .instructions ol {
                        padding-left: 20px;
                        color: #4a5568;
                    }
                    .instructions li {
                        margin-bottom: 8px;
                    }
                    .proxy-info {
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        padding: 15px;
                        border-radius: 8px;
                        margin-top: 20px;
                        color: #856404;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🌐 Cloud Shell HTTP 代理</h1>
                        <p>安全、快速、简单的网页代理服务</p>
                    </div>
                    
                    <div class="content">
                        <form action="/navigate" method="get">
                            <div class="input-group">
                                <input type="url" name="url" class="url-input" 
                                       placeholder="请输入完整的网址 (例如: https://www.example.com)" 
                                       required>
                                <button type="submit" class="submit-btn">访问</button>
                            </div>
                        </form>
                        
                        <div class="quick-links">
                            <div class="section-title">🚀 常用网站</div>
                            <div class="link-grid">
                                <a href="/navigate?url=https://www.so.com" class="quick-link">🔍 360搜索</a>
                                <a href="/navigate?url=https://www.baidu.com" class="quick-link">🔍 百度</a>
                                <a href="/navigate?url=https://www.google.com" class="quick-link">🔍 Google</a>
                                <a href="/navigate?url=https://github.com" class="quick-link">💻 GitHub</a>
                                <a href="/navigate?url=https://stackoverflow.com" class="quick-link">📚 Stack Overflow</a>
                                <a href="/navigate?url=https://news.ycombinator.com" class="quick-link">📰 Hacker News</a>
                            </div>
                        </div>
                        
                        <div class="instructions">
                            <h3>📖 使用说明</h3>
                            <ol>
                                <li>在上方输入框中输入完整的网址（包含 https:// 或 http://）</li>
                                <li>点击"访问"按钮或选择常用网站快捷链接</li>
                                <li>网页将通过 Cloud Shell 代理安全加载</li>
                                <li>支持大多数网站的浏览和交互功能</li>
                            </ol>
                        </div>
                        
                        <div class="proxy-info">
                            <strong>💡 提示：</strong> 
                            此代理服务运行在 Cloud Shell 环境中，为您提供安全的网页访问体验。
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return
            
        # 如果是导航请求，显示代理页面
        elif parsed_path.path == '/navigate' and 'url' in query_params:
            target_url = query_params['url'][0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # 创建一个iframe来显示目标网站，通过代理访问
            proxy_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>正在访问: {target_url}</title>
                <style>
                    body {{ margin: 0; padding: 0; }}
                    .header {{ 
                        background: #4facfe; 
                        color: white; 
                        padding: 15px; 
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        z-index: 1000;
                    }}
                    .header a {{ color: white; text-decoration: none; font-weight: bold; }}
                    iframe {{
                        width: 100%;
                        height: 100vh;
                        border: none;
                        margin-top: 50px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <a href="/">← 返回首页</a> | 正在访问: {target_url}
                </div>
                <iframe src="http://127.0.0.1:60001/http/{urllib.parse.quote(target_url)}"></iframe>
            </body>
            </html>
            """
            self.wfile.write(proxy_html.encode('utf-8'))
            return
            
        # 其他请求转发给代理服务器
        else:
            self.send_response(302)
            redirect_url = f"http://127.0.0.1:60001{self.path}"
            self.send_header('Location', redirect_url)
            self.end_headers()
            return

def start_gateway():
    '''
    启动网页网关
    '''
    PORT = 60000
    with socketserver.TCPServer(("", PORT), ProxyGateway) as httpd:
        debug('info', f'网页网关启动在端口 {PORT}')
        debug('info', '请在Cloud Shell中点击"网页预览" -> "预览端口 60000"')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            debug('info', '网页网关停止')

def start_proxy_server():
    '''
    启动代理服务器
    '''
    proxy = SimpleHttpProxy(host='127.0.0.1', port=60001, listen=50, bufsize=16, delay=0.5)
    proxy.start_proxy()

if __name__ == '__main__':
    debug('info', '启动 Cloud Shell HTTP 代理服务...')
    
    # 在后台线程中启动代理服务器
    proxy_thread = threading.Thread(target=start_proxy_server)
    proxy_thread.daemon = True
    proxy_thread.start()
    
    # 在主线程中启动网页网关
    time.sleep(1)  # 等待代理服务器启动
    start_gateway()
