#!/usr/bin/env python3
"""
HTTP代理服务器 - 修复搜索跳转版本
运行端口: 60000
修复搜索表单提交后的重定向问题
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import time

class FixedSearchProxyHandler(http.server.BaseHTTPRequestHandler):
    """修复搜索跳转的HTTP请求处理器"""
    
    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def do_GET(self):
        """处理GET请求"""
        try:
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/proxy?url='):
                self._proxy_webpage()
            elif self.path.startswith('/resource/'):
                self._proxy_resource_new()
            elif self.path.startswith('/favicon.ico'):
                self.send_response(204)
                self.end_headers()
                return
            else:
                self._proxy_resource()
        except Exception as e:
            print("请求处理错误: " + str(e))
            self.send_error(500, "Server Error: " + str(e))
    
    def do_POST(self):
        """处理POST请求 - 关键修复"""
        try:
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request_fixed()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            print("POST处理错误: " + str(e))
            self.send_error(500, "Server Error: " + str(e))
    
    def _proxy_post_request_fixed(self):
        """修复的表单POST请求处理"""
        # 解析目标URL
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        # 读取POST数据
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        # 解析POST数据以获取原始参数
        original_params = {}
        try:
            decoded_data = post_data.decode('utf-8')
            original_params = urllib.parse.parse_qs(decoded_data)
        except:
            pass
        
        print(f"表单提交到: {target_url}")
        print(f"POST参数: {original_params}")
        
        # 设置请求头
        headers = {
            'User-Agent': self.config['user_agent'],
            'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
        }
        
        # 转发POST请求
        try:
            response = requests.post(target_url, data=post_data, headers=headers, timeout=30, verify=False)
            
            # 关键修复：处理所有重定向状态码
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if location:
                    print(f"原始重定向地址: {location}")
                    
                    # 将重定向地址转换为绝对URL
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    # 重写为代理URL
                    proxy_location = "/proxy?url=" + urllib.parse.quote(location)
                    print(f"代理重定向地址: {proxy_location}")
                    
                    self.send_response(302)
                    self.send_header('Location', proxy_location)
                    self.end_headers()
                    return
            
            # 如果不是重定向，正常代理内容
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                rewritten_content = self._rewrite_html_content_fixed(response.text, target_url)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(rewritten_content.encode('utf-8'))
            else:
                self._proxy_raw_content(response)
                
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to POST to target website: " + str(e))
    
    def _serve_homepage(self):
        """提供代理主页界面"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>修复搜索跳转代理 - 60000端口</title>
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
                <h1>🌐 修复搜索跳转代理服务</h1>
                <div class="info">
                    <strong>修复内容：</strong> 已解决搜索框提交后直接跳转的问题，支持360搜索等表单重定向。
                </div>
                <form action="/proxy" method="GET">
                    <div class="form-group">
                        <input type="url" name="url" placeholder="https://www.so.com" required value="https://www.so.com">
                    </div>
                    <button type="submit">开始代理访问</button>
                </form>
                <div style="margin-top: 20px; text-align: center; color: #666;">
                    <small>代理服务运行在端口 60000 | 搜索重定向已修复</small>
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
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url
        
        print("正在代理: " + target_url)
        
        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        
        try:
            response = requests.get(target_url, headers=headers, timeout=30, verify=False)
        except requests.exceptions.RequestException as e:
            self.send_error(502, "Failed to fetch target website: " + str(e))
            return
        
        if response.status_code != 200:
            self.send_error(response.status_code, "Target website returned " + str(response.status_code))
            return
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_content_fixed(response.text, target_url)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(rewritten_content.encode('utf-8'))
        else:
            self._proxy_raw_content(response)
    
    def _proxy_resource_new(self):
        """资源代理方法"""
        try:
            encoded_url = self.path[10:]
            resource_url = urllib.parse.unquote(encoded_url)
            
            if resource_url.startswith('https:/') and not resource_url.startswith('https://'):
                resource_url = resource_url.replace('https:/', 'https://', 1)
            if resource_url.startswith('http:/') and not resource_url.startswith('http://'):
                resource_url = resource_url.replace('http:/', 'http://', 1)
            
            headers = {'User-Agent': self.config['user_agent']}
            
            referer = self.headers.get('Referer', '')
            if referer:
                headers['Referer'] = referer
            
            response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
            self._proxy_raw_content(response)
            
        except Exception as e:
            print("资源代理错误: " + str(e))
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Content-Length', '0')
            self.end_headers()
    
    def _proxy_resource(self):
        """回退资源代理"""
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
                    response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
                    self._proxy_raw_content(response)
                    return
                except requests.exceptions.RequestException as e:
                    print("资源代理失败: " + str(e))
        
        self.send_error(404, "Resource not found")
    
    def _proxy_raw_content(self, response):
        """代理原始内容"""
        self.send_response(response.status_code)
        
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)
    
    def _rewrite_html_content_fixed(self, html_content, base_url):
        """重写HTML内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        nav_html = '''
        <div style="background: #007cba; color: white; padding: 10px; margin: 0; text-align: center; position: sticky; top: 0; z-index: 10000;">
            <a href="/" style="color: white; text-decoration: none; font-weight: bold;">🏠 返回代理主页</a>
            <span style="margin: 0 10px;">|</span>
            <span>当前代理: {}</span>
        </div>
        '''.format(base_url)
        
        # 重写链接和资源
        for tag in soup.find_all('a'):
            if tag.get('href'):
                href = tag['href']
                if self._should_rewrite_url(href):
                    absolute_url = urllib.parse.urljoin(base_url, href)
                    tag['href'] = "/proxy?url=" + urllib.parse.quote(absolute_url)
        
        for form in soup.find_all('form'):
            if form.get('action'):
                action = form['action']
                if self._should_rewrite_url(action):
                    absolute_url = urllib.parse.urljoin(base_url, action)
                    form['action'] = "/proxy?url=" + urllib.parse.quote(absolute_url)
        
        for tag in soup.find_all(['img', 'script', 'link', 'iframe']):
            src_attr = 'src' if tag.get('src') else 'href' if tag.get('href') else None
            if src_attr:
                src = tag[src_attr]
                if self._should_rewrite_url(src):
                    absolute_url = urllib.parse.urljoin(base_url, src)
                    tag[src_attr] = "/resource/" + urllib.parse.quote(absolute_url)
        
        # 插入导航栏
        body_tag = soup.find('body')
        if body_tag:
            nav_soup = BeautifulSoup(nav_html, 'html.parser')
            body_tag.insert(0, nav_soup.div)
        else:
            soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
        
        # 注入拦截脚本
        interception_script = self._get_enhanced_interception_code(base_url)
        script_tag = soup.new_tag('script')
        script_tag.string = interception_script
        if body_tag:
            body_tag.append(script_tag)
        else:
            soup.append(script_tag)
        
        return str(soup)
    
    def _should_rewrite_url(self, url):
        """判断URL是否需要重写"""
        if not url or url.strip() == '':
            return False
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'blob:')):
            return False
        if url.startswith(('/proxy?url=', '/resource/', 'http://localhost:', 'https://localhost:')):
            return False
        return True
    
    def _get_enhanced_interception_code(self, base_url):
        """获取增强的JavaScript拦截代码"""
        return '''
        // 增强的JavaScript拦截代码
        (function() {
            'use strict';
            
            var baseUrl = "''' + base_url + '''";
            
            // 拦截所有链接点击
            document.addEventListener('click', function(e) {
                var target = e.target;
                while (target && target.nodeName !== 'A') {
                    target = target.parentElement;
                    if (!target) return;
                }
                
                if (target && target.href && !target.href.includes('/proxy?url=')) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    var fullUrl = new URL(target.href, baseUrl).href;
                    var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                    window.location.href = proxyUrl;
                    return false;
                }
            }, true);
            
            // 拦截表单提交
            document.addEventListener('submit', function(e) {
                var form = e.target;
                if (form.action && !form.action.includes('/proxy?url=')) {
                    e.preventDefault();
                    var fullUrl = new URL(form.action, baseUrl).href;
                    var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                    
                    // 创建临时表单
                    var tempForm = document.createElement('form');
                    tempForm.method = form.method || 'GET';
                    tempForm.action = proxyUrl;
                    tempForm.style.display = 'none';
                    
                    // 复制表单数据
                    var inputs = form.querySelectorAll('input, select, textarea');
                    for (var i = 0; i < inputs.length; i++) {
                        var input = inputs[i];
                        if (input.name) {
                            var newInput = document.createElement('input');
                            newInput.type = 'hidden';
                            newInput.name = input.name;
                            newInput.value = input.value;
                            tempForm.appendChild(newInput);
                        }
                    }
                    
                    document.body.appendChild(tempForm);
                    tempForm.submit();
                }
            }, true);
            
            console.log('🔒 搜索跳转拦截脚本已加载');
        })();
        '''
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print("[" + self.log_date_time_string() + "] " + format % args)

def run_proxy_server():
    """运行代理服务器"""
    port = 60000
    
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass
    
    with socketserver.TCPServer(("", port), FixedSearchProxyHandler) as httpd:
        print("🚀 修复搜索跳转代理服务器已启动在端口 " + str(port))
        print("📧 访问地址: http://localhost:" + str(port))
        print("🔧 修复内容: 搜索表单重定向拦截")
        print("⏹️ 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_proxy_server()
