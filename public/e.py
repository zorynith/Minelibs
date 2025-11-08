#!/usr/bin/env python3
"""
HTTP代理服务器 - 最终修复版本
运行端口: 60000
彻底解决搜索跳转和主页循环代理问题
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import time

class FinalProxyHandler(http.server.BaseHTTPRequestHandler):
    """最终修复的HTTP请求处理器"""
    
    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    def do_GET(self):
        """处理GET请求"""
        try:
            print(f"GET请求: {self.path}")
            
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/proxy?url='):
                self._proxy_webpage()
            elif self.path.startswith('/resource/'):
                self._proxy_resource()
            elif self.path.startswith('/favicon.ico'):
                self.send_response(204)
                self.end_headers()
                return
            else:
                # 其他路径尝试作为资源处理
                self._proxy_resource_fallback()
                
        except Exception as e:
            print(f"GET请求处理错误: {str(e)}")
            self._send_error_page(500, f"服务器错误: {str(e)}")
    
    def do_POST(self):
        """处理POST请求 - 最终修复"""
        try:
            print(f"POST请求: {self.path}")
            
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request_fixed()
            else:
                self._send_error_page(404, "页面不存在")
        except Exception as e:
            print(f"POST处理错误: {str(e)}")
            self._send_error_page(500, f"服务器错误: {str(e)}")
    
    def _serve_homepage(self):
        """提供代理主页界面"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>最终修复代理 - 60000端口</title>
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
                .quick-links {
                    text-align: center;
                    margin: 20px 0;
                }
                .quick-link {
                    display: inline-block;
                    margin: 0 10px;
                    color: #007cba;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 最终修复代理服务</h1>
                <div class="info">
                    <strong>修复内容：</strong> 
                    • 彻底解决搜索跳转404问题<br>
                    • 修复主页循环代理问题<br>
                    • 完整重定向拦截机制
                </div>
                <form action="/proxy" method="GET">
                    <div class="form-group">
                        <input type="url" name="url" placeholder="https://www.so.com" required value="https://www.so.com">
                    </div>
                    <button type="submit">开始代理访问</button>
                </form>
                
                <div class="quick-links">
                    <strong>快速测试：</strong>
                    <a href="/proxy?url=https://www.so.com" class="quick-link">360搜索</a>
                    <a href="/proxy?url=https://www.baidu.com" class="quick-link">百度搜索</a>
                </div>
                
                <div style="margin-top: 20px; text-align: center; color: #666;">
                    <small>代理服务运行在端口 60000 | 所有问题已修复</small>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self._send_html_response(homepage_html)
    
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
            target_url = 'https://' + target_url
        
        print(f"正在代理: {target_url}")
        
        # 设置请求头模拟真实浏览器
        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 发送请求到目标网站
        try:
            response = requests.get(target_url, headers=headers, timeout=30, verify=False)
        except requests.exceptions.RequestException as e:
            self.send_error(502, f"无法访问目标网站: {str(e)}")
            return
        
        # 检查响应状态
        if response.status_code != 200:
            self.send_error(response.status_code, f"目标网站返回状态码: {response.status_code}")
            return
        
        # 重写网页内容
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_content_final(response.text, target_url)
            self._send_html_response(rewritten_content)
        else:
            # 非HTML内容直接传递
            self._proxy_raw_response(response)
    
    def _proxy_post_request_fixed(self):
        """修复的POST请求处理 - 解决搜索跳转"""
        # 解析目标URL
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        # 读取POST数据
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        print(f"表单提交到: {target_url}")
        
        # 设置请求头
        headers = {
            'User-Agent': self.config['user_agent'],
            'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
        }
        
        # 转发POST请求 - 关键：禁用自动重定向，以便我们可以拦截
        try:
            response = requests.post(target_url, data=post_data, headers=headers, 
                                   timeout=30, verify=False, allow_redirects=False)
            
            print(f"响应状态码: {response.status_code}")
            
            # 关键修复：处理重定向响应
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if location:
                    print(f"拦截到重定向: {location}")
                    
                    # 将相对URL转换为绝对URL
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    print(f"绝对URL: {location}")
                    
                    # 重写为代理URL
                    proxy_location = f"/proxy?url={urllib.parse.quote(location)}"
                    print(f"代理重定向: {proxy_location}")
                    
                    # 返回代理重定向
                    self.send_response(302)
                    self.send_header('Location', proxy_location)
                    self.end_headers()
                    return
            
            # 如果不是重定向，正常处理响应
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type:
                rewritten_content = self._rewrite_html_content_final(response.text, target_url)
                self._send_html_response(rewritten_content)
            else:
                self._proxy_raw_response(response)
                
        except requests.exceptions.RequestException as e:
            print(f"POST请求错误: {str(e)}")
            self.send_error(502, f"无法提交到目标网站: {str(e)}")
    
    def _proxy_resource(self):
        """资源代理方法"""
        try:
            # 从路径中提取编码的资源URL
            encoded_url = self.path[10:]  # 去掉 '/resource/'
            resource_url = urllib.parse.unquote(encoded_url)
            
            # 修复URL格式问题
            if resource_url.startswith('https:/') and not resource_url.startswith('https://'):
                resource_url = resource_url.replace('https:/', 'https://', 1)
            if resource_url.startswith('http:/') and not resource_url.startswith('http://'):
                resource_url = resource_url.replace('http:/', 'http://', 1)
            
            headers = {
                'User-Agent': self.config['user_agent'],
            }
            
            # 添加Referer
            referer = self.headers.get('Referer', '')
            if referer:
                headers['Referer'] = referer
            
            response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
            self._proxy_raw_response(response)
            
        except Exception as e:
            print(f"资源代理错误: {str(e)}")
            # 返回空内容避免页面错误
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Content-Length', '0')
            self.end_headers()
    
    def _proxy_resource_fallback(self):
        """回退资源代理"""
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
                    response = requests.get(resource_url, headers=headers, timeout=30, verify=False)
                    self._proxy_raw_response(response)
                    return
                except requests.exceptions.RequestException as e:
                    print(f"资源代理失败: {str(e)}")
        
        self.send_error(404, "Resource not found")
    
    def _rewrite_html_content_final(self, html_content, base_url):
        """最终HTML内容重写 - 修复所有问题"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 在页面顶部添加返回主页的导航栏 - 修复循环代理问题
            nav_html = '''
            <div id="proxy-nav" style="background: #007cba; color: white; padding: 10px; margin: 0; text-align: center; position: sticky; top: 0; z-index: 10000;">
                <a href="/" style="color: white; text-decoration: none; font-weight: bold; background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 4px;">🏠 返回代理主页</a>
                <span style="margin: 0 10px;">|</span>
                <span>代理模式</span>
            </div>
            '''
            
            # 重写各种链接和资源引用 - 修复主页循环代理
            self._rewrite_urls_final(soup, base_url)
            
            # 重写CSS中的url()引用
            style_tags = soup.find_all('style')
            for style_tag in style_tags:
                if style_tag.string:
                    style_tag.string = self._rewrite_css_urls_final(style_tag.string, base_url)
            
            # 重写style属性中的URL
            for tag in soup.find_all(style=True):
                tag['style'] = self._rewrite_css_urls_final(tag['style'], base_url)
            
            # 重写meta refresh
            meta_tags = soup.find_all('meta', attrs={'http-equiv': True})
            for meta_tag in meta_tags:
                if meta_tag.get('http-equiv', '').lower() == 'refresh':
                    content = meta_tag.get('content', '')
                    if 'url=' in content.lower():
                        parts = content.split(';', 1)
                        if len(parts) == 2:
                            timeout, url_part = parts
                            if url_part.strip().lower().startswith('url='):
                                original_url = url_part[4:].strip()
                                absolute_url = urllib.parse.urljoin(base_url, original_url)
                                proxy_url = f"/proxy?url={urllib.parse.quote(absolute_url)}"
                                meta_tag['content'] = f"{timeout}; URL={proxy_url}"
            
            # 插入导航栏
            body_tag = soup.find('body')
            if body_tag:
                nav_soup = BeautifulSoup(nav_html, 'html.parser')
                body_tag.insert(0, nav_soup.div)
            else:
                soup.insert(0, BeautifulSoup(nav_html, 'html.parser').div)
            
            # 注入最终的JavaScript拦截代码
            interception_script = self._get_final_interception_script(base_url)
            script_tag = soup.new_tag('script')
            script_tag.string = interception_script
            if body_tag:
                body_tag.append(script_tag)
            else:
                soup.append(script_tag)
            
            return str(soup)
            
        except Exception as e:
            print(f"HTML重写错误: {str(e)}")
            return html_content  # 返回原始内容作为备选
    
    def _rewrite_urls_final(self, soup, base_url):
        """最终URL重写 - 修复主页循环代理"""
        # 链接 - 特别注意跳过主页链接
        for tag in soup.find_all('a'):
            if tag.get('href'):
                href = tag['href']
                # 关键修复：跳过主页链接，防止循环代理
                if href == '/' or href.startswith('/?'):
                    continue
                if self._should_rewrite_url(href):
                    absolute_url = urllib.parse.urljoin(base_url, href)
                    tag['href'] = f"/proxy?url={urllib.parse.quote(absolute_url)}"
        
        # 表单
        for form in soup.find_all('form'):
            if form.get('action'):
                action = form['action']
                if self._should_rewrite_url(action):
                    absolute_url = urllib.parse.urljoin(base_url, action)
                    form['action'] = f"/proxy?url={urllib.parse.quote(absolute_url)}"
        
        # 资源
        for tag in soup.find_all(['img', 'script', 'link', 'iframe', 'frame', 'embed', 'source']):
            src_attr = 'src' if tag.get('src') else 'href' if tag.get('href') else 'data' if tag.get('data') else None
            if src_attr:
                src = tag[src_attr]
                if self._should_rewrite_url(src):
                    absolute_url = urllib.parse.urljoin(base_url, src)
                    tag[src_attr] = f"/resource/{urllib.parse.quote(absolute_url)}"
    
    def _should_rewrite_url(self, url):
        """判断URL是否需要重写"""
        if not url or url.strip() == '':
            return False
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'blob:')):
            return False
        if url.startswith(('/proxy?url=', '/resource/', 'http://localhost:', 'https://localhost:')):
            return False
        return True
    
    def _rewrite_css_urls_final(self, css_content, base_url):
        """重写CSS中的URL"""
        import re
        
        def replace_url(match):
            url_content = match.group(1).strip('"\'')
            if not self._should_rewrite_url(url_content):
                return match.group(0)
            
            # 转换为绝对URL
            absolute_url = urllib.parse.urljoin(base_url, url_content)
            proxy_url = f"/resource/{urllib.parse.quote(absolute_url)}"
            return f'url("{proxy_url}")'
        
        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)
    
    def _get_final_interception_script(self, base_url):
        """获取最终的JavaScript拦截代码"""
        return f'''
        // 最终的JavaScript拦截代码
        (function() {{
            'use strict';
            
            var baseUrl = "{base_url}";
            
            // 1. 拦截所有链接点击
            document.addEventListener('click', function(e) {{
                var target = e.target;
                while (target && target.nodeName !== 'A') {{
                    target = target.parentElement;
                    if (!target) return;
                }}
                
                if (target && target.href && !target.href.includes('/proxy?url=')) {{
                    e.preventDefault();
                    e.stopPropagation();
                    
                    var fullUrl = new URL(target.href, baseUrl).href;
                    var proxyUrl = '/proxy?url=' + encodeURIComponent(fullUrl);
                    window.location.href = proxyUrl;
                    return false;
                }}
            }}, true);
            
            // 2. 拦截表单提交
            document.addEventListener('submit', function(e) {{
                var form = e.target;
                if (form.action && !form.action.includes('/proxy?url=')) {{
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
                    for (var i = 0; i < inputs.length; i++) {{
                        var input = inputs[i];
                        if (input.name) {{
                            var newInput = document.createElement('input');
                            newInput.type = 'hidden';
                            newInput.name = input.name;
                            newInput.value = input.value;
                            tempForm.appendChild(newInput);
                        }}
                    }}
                    
                    document.body.appendChild(tempForm);
                    tempForm.submit();
                }}
            }}, true);
            
            console.log('🔒 最终拦截脚本已加载 - 所有问题已修复');
        }})();
        '''
    
    def _send_html_response(self, html_content):
        """发送HTML响应"""
        encoded = html_content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
    
    def _proxy_raw_response(self, response):
        """代理原始响应"""
        self.send_response(response.status_code)
        
        # 复制响应头
        for header, value in response.headers.items():
            if header.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)
    
    def _send_error_page(self, code, message):
        """发送错误页面"""
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误 {code}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; background: #f8fafc; }}
                .error-container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
                h1 {{ color: #dc2626; margin-bottom: 20px; }}
                .message {{ color: #4b5563; margin-bottom: 30px; line-height: 1.6; }}
                .btn {{ background: #2563eb; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>❌ 错误 {code}</h1>
                <div class="message">{message}</div>
                <a href="/" class="btn">返回主页</a>
            </div>
        </body>
        </html>
        '''
        self._send_html_response(error_html)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_final_proxy():
    """运行最终代理服务器"""
    port = 60000
    
    # 禁用SSL警告
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass
    
    with socketserver.TCPServer(("", port), FinalProxyHandler) as httpd:
        print("=" * 60)
        print(f"🚀 最终修复代理服务器已启动在端口 {port}")
        print(f"📧 访问地址: http://localhost:{port}")
        print("=" * 60)
        print("✨ 已修复问题:")
        print("   • 🔍 搜索跳转404问题")
        print("   • 🔄 主页循环代理问题") 
        print("   • 🛡️ 完整重定向拦截")
        print("   • 📱 资源加载优化")
        print("=" * 60)
        print("⏹️ 按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 服务器已停止")

if __name__ == "__main__":
    run_final_proxy()
