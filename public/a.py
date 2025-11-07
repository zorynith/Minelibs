#!/usr/bin/env python3
"""
HTTP代理服务器 - 支持网页界面和完整内容代理
运行端口: 60000
适用于阿里云CloudShell环境
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import threading
import time

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
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
            else:
                # 其他资源请求（CSS、JS、图片等）
                self._proxy_resource()
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")
    
    def do_POST(self):
        """处理POST请求（如表单提交）"""
        try:
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")
    
    def _serve_homepage(self):
        """提供代理主页界面"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>简易网页代理 - 60000端口</title>
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
                <h1>🌐 网页代理服务</h1>
                <div class="info">
                    <strong>使用说明：</strong> 输入您要访问的网页URL，代理服务将获取内容并在当前环境显示。
                    所有链接和资源都会通过代理处理，避免直接跳转到原网站。
                </div>
                <form action="/proxy" method="GET">
                    <div class="form-group">
                        <input type="url" name="url" placeholder="https://www.example.com" required value="https://">
                    </div>
                    <button type="submit">开始代理访问</button>
                </form>
                <div style="margin-top: 20px; text-align: center; color: #666;">
                    <small>代理服务运行在端口 60000 | 适用于阿里云CloudShell</small>
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
        
        # 设置请求头模拟真实浏览器[citation:1][citation:9]
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
            response = requests.get(target_url, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            self.send_error(502, f"Failed to fetch target website: {str(e)}")
            return
        
        # 检查响应状态
        if response.status_code != 200:
            self.send_error(response.status_code, f"Target website returned {response.status_code}")
            return
        
        # 重写网页内容
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_content(response.text, target_url)
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
        # 从路径中提取原始资源URL（这里需要根据您的URL设计来解析）
        # 简化实现：直接使用referer来构建资源URL
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
                    response = requests.get(resource_url, headers=headers, timeout=30)
                    self._proxy_raw_content(response)
                    return
                except requests.exceptions.RequestException:
                    pass
        
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
            'Content-Length': str(len(post_data)),
        }
        
        # 转发POST请求
        try:
            response = requests.post(target_url, data=post_data, headers=headers, timeout=30)
            self._proxy_raw_content(response)
        except requests.exceptions.RequestException as e:
            self.send_error(502, f"Failed to POST to target website: {str(e)}")
    
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
    
    def _rewrite_html_content(self, html_content, base_url):
        """重写HTML内容，修改所有链接通过代理"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 在页面顶部添加返回主页的导航栏
        nav_html = '''
        <div style="background: #007cba; color: white; padding: 10px; margin: 0; text-align: center;">
            <a href="/" style="color: white; text-decoration: none; font-weight: bold;">🏠 返回代理主页</a>
            <span style="margin: 0 10px;">|</span>
            <span>当前代理: {}</span>
        </div>
        '''.format(base_url)
        
        # 重写各种链接和资源引用
        self._rewrite_attributes(soup, 'a', 'href', base_url)
        self._rewrite_attributes(soup, 'img', 'src', base_url)
        self._rewrite_attributes(soup, 'script', 'src', base_url)
        self._rewrite_attributes(soup, 'link', 'href', base_url)
        self._rewrite_attributes(soup, 'form', 'action', base_url)
        self._rewrite_attributes(soup, 'iframe', 'src', base_url)
        
        # 重写CSS中的url()引用
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                style_tag.string = self._rewrite_css_urls(style_tag.string, base_url)
        
        # 插入导航栏
        body_tag = soup.find('body')
        if body_tag:
            nav_soup = BeautifulSoup(nav_html, 'html.parser')
            body_tag.insert(0, nav_soup.div)
        else:
            # 如果没有body标签，在开头添加
            soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
        
        return str(soup)
    
    def _rewrite_attributes(self, soup, tag_name, attr_name, base_url):
        """重写指定标签的属性"""
        tags = soup.find_all(tag_name)
        for tag in tags:
            if tag.has_attr(attr_name):
                original_url = tag[attr_name]
                
                # 跳过空链接和锚点链接
                if not original_url or original_url.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # 转换为绝对URL
                absolute_url = urllib.parse.urljoin(base_url, original_url)
                
                # 重写为代理URL
                proxy_url = f"/proxy?url={urllib.parse.quote(absolute_url)}"
                tag[attr_name] = proxy_url
    
    def _rewrite_css_urls(self, css_content, base_url):
        """重写CSS中的url()引用"""
        import re
        
        def replace_url(match):
            url_content = match.group(1)
            if url_content.startswith(('http://', 'https://', 'data:')):
                return match.group(0)
            
            # 转换为绝对URL
            absolute_url = urllib.parse.urljoin(base_url, url_content.strip('"\''))
            proxy_url = f"/proxy?url={urllib.parse.quote(absolute_url)}"
            return f'url("{proxy_url}")'
        
        # 匹配CSS中的url()引用
        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_proxy_server():
    """运行代理服务器"""
    port = 60000
    
    with socketserver.TCPServer(("", port), ProxyHandler) as httpd:
        print(f"🚀 HTTP代理服务器已启动在端口 {port}")
        print(f"📧 访问地址: http://localhost:{port}")
        print("⏹️ 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_proxy_server()
