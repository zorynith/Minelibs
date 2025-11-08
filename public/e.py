#!/usr/bin/env python3
"""
HTTP代理服务器 - 基于最初稳定版本的精确修复
运行端口: 60000
只修复搜索跳转和主页循环问题，保持其他功能不变
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import time

class ExactFixProxyHandler(http.server.BaseHTTPRequestHandler):
    """基于最初稳定版本的精确修复处理器"""
    
    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def do_GET(self):
        """处理GET请求 - 保持原样"""
        try:
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/proxy?url='):
                self._proxy_webpage()
            else:
                self._proxy_resource()
        except Exception as e:
            self.send_error(500, "Server Error: " + str(e))
    
    def do_POST(self):
        """处理POST请求 - 只修改这里解决搜索跳转"""
        try:
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request_fixed()  # 使用修复的POST处理
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_error(500, "Server Error: " + str(e))
    
    def _serve_homepage(self):
        """提供代理主页界面 - 保持原样"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>精确修复代理 - 60000端口</title>
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
        """代理并重写网页内容 - 保持原样"""
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
        
        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = requests.get(target_url, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to fetch target website: " + str(e))
            return
        
        if response.status_code != 200:
            self.send_error(response.status_code, "Target website returned " + str(response.status_code))
            return
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_content_fixed(response.text, target_url)  # 使用修复的重写
        else:
            self._proxy_raw_content(response)
            return
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(rewritten_content.encode('utf-8'))
    
    def _proxy_resource(self):
        """代理静态资源 - 保持原样"""
        referer = self.headers.get('Referer', '')
        
        if '/proxy?url=' in referer:
            referer_parsed = urllib.parse.urlparse(referer)
            referer_query = urllib.parse.parse_qs(referer_parsed.query)
            base_url = referer_query.get('url', [''])[0]
            
            if base_url:
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
    
    def _proxy_post_request_fixed(self):
        """修复的POST请求处理 - 专门解决搜索跳转问题"""
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        headers = {
            'User-Agent': self.config['user_agent'],
            'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
            'Content-Length': str(len(post_data)),
        }
        
        # 关键修复：禁用自动重定向，手动处理
        try:
            response = requests.post(target_url, data=post_data, headers=headers, 
                                   timeout=30, allow_redirects=False)  # 重要：allow_redirects=False
            
            print(f"POST响应状态码: {response.status_code}")
            
            # 处理重定向
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if location:
                    print(f"拦截到重定向: {location}")
                    
                    # 转换为绝对URL
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    # 重写为代理URL
                    proxy_location = "/proxy?url=" + urllib.parse.quote(location)
                    print(f"重写为代理重定向: {proxy_location}")
                    
                    self.send_response(302)
                    self.send_header('Location', proxy_location)
                    self.end_headers()
                    return
            
            # 如果不是重定向，正常处理
            self._proxy_raw_content(response)
            
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to POST to target website: " + str(e))
    
    def _proxy_raw_content(self, response):
        """代理原始内容 - 保持原样"""
        self.send_response(response.status_code)
        
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)
    
    def _rewrite_html_content_fixed(self, html_content, base_url):
        """修复的HTML内容重写 - 解决主页循环问题"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 在页面顶部添加返回主页的导航栏
        nav_html = '''
        <div style="background: #007cba; color: white; padding: 10px; margin: 0; text-align: center;">
            <a href="/" style="color: white; text-decoration: none; font-weight: bold;">🏠 返回代理主页</a>
            <span style="margin: 0 10px;">|</span>
            <span>当前代理: {}</span>
        </div>
        '''.format(base_url)
        
        # 重写各种链接和资源引用 - 使用修复的方法
        self._rewrite_attributes_fixed(soup, 'a', 'href', base_url)
        self._rewrite_attributes_fixed(soup, 'img', 'src', base_url)
        self._rewrite_attributes_fixed(soup, 'script', 'src', base_url)
        self._rewrite_attributes_fixed(soup, 'link', 'href', base_url)
        self._rewrite_attributes_fixed(soup, 'form', 'action', base_url)
        self._rewrite_attributes_fixed(soup, 'iframe', 'src', base_url)
        
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
            soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
        
        return str(soup)
    
    def _rewrite_attributes_fixed(self, soup, tag_name, attr_name, base_url):
        """修复的属性重写 - 解决主页循环问题"""
        tags = soup.find_all(tag_name)
        for tag in tags:
            if tag.has_attr(attr_name):
                original_url = tag[attr_name]
                
                # 跳过空链接和锚点链接
                if not original_url or original_url.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # 关键修复：跳过主页链接，防止循环代理
                if original_url == '/' or original_url.startswith('/?'):
                    continue
                
                # 转换为绝对URL
                absolute_url = urllib.parse.urljoin(base_url, original_url)
                
                # 重写为代理URL
                proxy_url = "/proxy?url=" + urllib.parse.quote(absolute_url)
                tag[attr_name] = proxy_url
    
    def _rewrite_css_urls(self, css_content, base_url):
        """重写CSS中的url()引用 - 保持原样"""
        import re
        
        def replace_url(match):
            url_content = match.group(1)
            if url_content.startswith(('http://', 'https://', 'data:')):
                return match.group(0)
            
            absolute_url = urllib.parse.urljoin(base_url, url_content.strip('"\''))
            proxy_url = "/proxy?url=" + urllib.parse.quote(absolute_url)
            return 'url("' + proxy_url + '")'
        
        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print("[" + self.log_date_time_string() + "] " + format % args)

def run_proxy_server():
    """运行代理服务器"""
    port = 60000
    
    with socketserver.TCPServer(("", port), ExactFixProxyHandler) as httpd:
        print("🚀 精确修复代理服务器已启动在端口 " + str(port))
        print("📧 访问地址: http://localhost:" + str(port))
        print("🔧 修复内容: 搜索跳转404 + 主页循环代理")
        print("⏹️ 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_proxy_server()
