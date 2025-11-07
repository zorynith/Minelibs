#!/usr/bin/env python3
"""
CloudShell HTTP代理 - 终极解决方案
使用隧道技术和完全重写策略
"""

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import json
import base64
import gzip
import io
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class TunnelProxyHandler(http.server.BaseHTTPRequestHandler):
    """隧道代理处理器 - 彻底解决跳转问题"""
    
    config = {
        'port': 60000,
        'timeout': 30,
        'max_retries': 3,
        'user_agents': [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    }
    
    def do_GET(self):
        """处理所有GET请求"""
        try:
            print(f"请求: {self.path}")
            
            if self.path == '/':
                self._serve_control_panel()
            elif self.path.startswith('/tunnel/'):
                self._handle_tunnel_request()
            elif self.path.startswith('/direct/'):
                self._handle_direct_proxy()
            elif self.path.startswith('/static/'):
                self._serve_static_resource()
            else:
                # 默认显示控制面板
                self._serve_control_panel()
                
        except Exception as e:
            print(f"请求处理错误: {str(e)}")
            self._send_error(500, f"内部服务器错误: {str(e)}")

    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path.startswith('/tunnel/'):
                self._handle_tunnel_post()
            elif self.path.startswith('/direct/'):
                self._handle_direct_post()
            else:
                self._send_error(404, "页面不存在")
        except Exception as e:
            print(f"POST处理错误: {str(e)}")
            self._send_error(500, f"内部服务器错误: {str(e)}")

    def _serve_control_panel(self):
        """提供控制面板"""
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>CloudShell终极代理解决方案</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                :root { --primary: #2563eb; --secondary: #1e40af; }
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { 
                    font-family: system-ui, -apple-system, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                    line-height: 1.6;
                }
                .container { 
                    max-width: 1000px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 40px; 
                    border-radius: 20px;
                    box-shadow: 0 25px 50px rgba(0,0,0,0.15);
                }
                h1 { 
                    color: #1f2937; 
                    text-align: center;
                    margin-bottom: 10px;
                    font-size: 2.5em;
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .subtitle {
                    text-align: center;
                    color: #6b7280;
                    margin-bottom: 40px;
                    font-size: 1.1em;
                }
                .mode-selector {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin: 30px 0;
                }
                .mode-card {
                    border: 2px solid #e5e7eb;
                    border-radius: 12px;
                    padding: 25px;
                    cursor: pointer;
                    transition: all 0.3s;
                    text-align: center;
                }
                .mode-card:hover {
                    border-color: var(--primary);
                    transform: translateY(-5px);
                    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.1);
                }
                .mode-card.active {
                    border-color: var(--primary);
                    background: #f0f7ff;
                }
                .mode-icon {
                    font-size: 2.5em;
                    margin-bottom: 15px;
                }
                .mode-title {
                    font-size: 1.3em;
                    font-weight: 600;
                    color: #1f2937;
                    margin-bottom: 10px;
                }
                .mode-desc {
                    color: #6b7280;
                    font-size: 0.95em;
                }
                .input-group {
                    margin: 30px 0;
                }
                .url-input {
                    width: 100%;
                    padding: 18px 20px;
                    border: 2px solid #e5e7eb;
                    border-radius: 12px;
                    font-size: 16px;
                    transition: all 0.3s;
                    background: #fafafa;
                }
                .url-input:focus {
                    border-color: var(--primary);
                    background: white;
                    outline: none;
                    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                }
                .submit-btn {
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    color: white;
                    border: none;
                    padding: 18px 30px;
                    border-radius: 12px;
                    cursor: pointer;
                    font-size: 16px;
                    width: 100%;
                    font-weight: 600;
                    transition: all 0.3s;
                }
                .submit-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3);
                }
                .quick-links {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 30px 0;
                }
                .quick-link {
                    display: flex;
                    align-items: center;
                    padding: 15px;
                    background: #f8fafc;
                    border-radius: 10px;
                    text-decoration: none;
                    color: #374151;
                    transition: all 0.3s;
                    border: 1px solid #e5e7eb;
                }
                .quick-link:hover {
                    background: white;
                    border-color: var(--primary);
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }
                .quick-link-icon {
                    font-size: 1.5em;
                    margin-right: 12px;
                }
                .status-bar {
                    background: #f0f7ff;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 25px 0;
                    border-left: 4px solid var(--primary);
                }
                .feature-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin: 25px 0;
                }
                .feature {
                    display: flex;
                    align-items: center;
                    padding: 12px;
                    background: #f8fafc;
                    border-radius: 8px;
                }
                .feature-icon {
                    color: var(--primary);
                    margin-right: 10px;
                    font-size: 1.2em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 CloudShell终极代理</h1>
                <div class="subtitle">专为阿里云CloudShell环境优化的高级网页代理解决方案</div>
                
                <div class="status-bar">
                    <strong>🚀 服务状态：运行中 | 端口：60000 | 模式：双重代理隧道</strong>
                </div>
                
                <div class="mode-selector">
                    <div class="mode-card active" data-mode="tunnel">
                        <div class="mode-icon">🔒</div>
                        <div class="mode-title">隧道模式</div>
                        <div class="mode-desc">完全重写所有链接和资源，彻底防止跳转</div>
                    </div>
                    <div class="mode-card" data-mode="direct">
                        <div class="mode-icon">⚡</div>
                        <div class="mode-title">直连模式</div>
                        <div class="mode-desc">快速代理，适用于简单页面</div>
                    </div>
                </div>
                
                <form id="proxyForm">
                    <div class="input-group">
                        <input type="url" class="url-input" id="urlInput" 
                               placeholder="https://www.example.com" 
                               required value="https://">
                    </div>
                    <button type="submit" class="submit-btn" id="submitBtn">
                        <span id="btnText">🚀 开始安全代理访问</span>
                        <div id="btnSpinner" style="display: none;">⏳ 连接中...</div>
                    </button>
                </form>
                
                <div class="quick-links">
                    <a href="/tunnel/https://www.baidu.com" class="quick-link">
                        <span class="quick-link-icon">🔍</span>
                        <span>百度搜索</span>
                    </a>
                    <a href="/tunnel/https://www.so.com" class="quick-link">
                        <span class="quick-link-icon">🛡️</span>
                        <span>360搜索</span>
                    </a>
                    <a href="/tunnel/https://news.sina.com.cn" class="quick-link">
                        <span class="quick-link-icon">📰</span>
                        <span>新浪新闻</span>
                    </a>
                    <a href="/tunnel/https://www.qq.com" class="quick-link">
                        <span class="quick-link-icon">💬</span>
                        <span>腾讯网</span>
                    </a>
                </div>
                
                <div class="feature-list">
                    <div class="feature">
                        <span class="feature-icon">✅</span>
                        <span>彻底解决页面跳转问题</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">✅</span>
                        <span>支持所有JS/CSS/图片资源</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">✅</span>
                        <span>表单提交和搜索正常</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">✅</span>
                        <span>自动错误重试和恢复</span>
                    </div>
                </div>
            </div>
            
            <script>
                let currentMode = 'tunnel';
                
                // 模式选择
                document.querySelectorAll('.mode-card').forEach(card => {
                    card.addEventListener('click', function() {
                        document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('active'));
                        this.classList.add('active');
                        currentMode = this.dataset.mode;
                        updateSubmitButton();
                    });
                });
                
                function updateSubmitButton() {
                    const btn = document.getElementById('submitBtn');
                    const btnText = document.getElementById('btnText');
                    if (currentMode === 'tunnel') {
                        btnText.textContent = '🚀 开始安全代理访问';
                    } else {
                        btnText.textContent = '⚡ 开始快速代理访问';
                    }
                }
                
                // 表单提交
                document.getElementById('proxyForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    const urlInput = document.getElementById('urlInput');
                    const url = urlInput.value.trim();
                    
                    if (!url) {
                        alert('请输入要访问的网址');
                        return;
                    }
                    
                    const encodedUrl = encodeURIComponent(url);
                    const targetUrl = `/${currentMode}/${encodedUrl}`;
                    
                    // 显示加载状态
                    const btnText = document.getElementById('btnText');
                    const btnSpinner = document.getElementById('btnSpinner');
                    btnText.style.display = 'none';
                    btnSpinner.style.display = 'block';
                    
                    window.location.href = targetUrl;
                });
                
                // 自动聚焦输入框
                document.getElementById('urlInput').focus();
            </script>
        </body>
        </html>
        '''
        
        self._send_html(html)

    def _handle_tunnel_request(self):
        """处理隧道代理请求"""
        try:
            encoded_url = self.path[8:]  # 去掉 '/tunnel/'
            if '?' in encoded_url:
                encoded_url = encoded_url.split('?')[0]
                
            target_url = urllib.parse.unquote(encoded_url)
            
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'https://' + target_url
                
            print(f"隧道模式请求: {target_url}")
            self._proxy_with_tunnel(target_url)
            
        except Exception as e:
            print(f"隧道请求错误: {str(e)}")
            self._send_error(500, f"隧道代理失败: {str(e)}")

    def _handle_direct_proxy(self):
        """处理直连代理请求"""
        try:
            encoded_url = self.path[8:]  # 去掉 '/direct/'
            if '?' in encoded_url:
                encoded_url = encoded_url.split('?')[0]
                
            target_url = urllib.parse.unquote(encoded_url)
            
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'https://' + target_url
                
            print(f"直连模式请求: {target_url}")
            self._proxy_direct(target_url)
            
        except Exception as e:
            print(f"直连请求错误: {str(e)}")
            self._send_error(500, f"直连代理失败: {str(e)}")

    def _handle_tunnel_post(self):
        """处理隧道POST请求"""
        try:
            encoded_url = self.path[8:]
            target_url = urllib.parse.unquote(encoded_url)
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            headers = {
                'User-Agent': self.config['user_agents'][0],
                'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
            }
            
            response = self._make_request('POST', target_url, data=post_data, headers=headers)
            self._proxy_tunnel_response(response, target_url)
            
        except Exception as e:
            print(f"隧道POST错误: {str(e)}")
            self._send_error(500, f"表单提交失败: {str(e)}")

    def _handle_direct_post(self):
        """处理直连POST请求"""
        try:
            encoded_url = self.path[8:]
            target_url = urllib.parse.unquote(encoded_url)
            
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            headers = {
                'User-Agent': self.config['user_agents'][0],
                'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded'),
            }
            
            response = self._make_request('POST', target_url, data=post_data, headers=headers)
            self._proxy_direct_response(response)
            
        except Exception as e:
            print(f"直连POST错误: {str(e)}")
            self._send_error(500, f"表单提交失败: {str(e)}")

    def _serve_static_resource(self):
        """处理静态资源请求"""
        try:
            # 从路径中提取资源信息
            resource_path = self.path[8:]  # 去掉 '/static/'
            parts = resource_path.split('/', 1)
            if len(parts) != 2:
                self._send_error(404, "资源路径无效")
                return
                
            encoded_base_url, resource_url_encoded = parts
            base_url = urllib.parse.unquote(encoded_base_url)
            resource_url = urllib.parse.unquote(resource_url_encoded)
            
            # 构建完整资源URL
            full_resource_url = urllib.parse.urljoin(base_url, resource_url)
            print(f"获取静态资源: {full_resource_url}")
            
            headers = {
                'User-Agent': self.config['user_agents'][0],
                'Referer': base_url
            }
            
            response = self._make_request('GET', full_resource_url, headers=headers)
            self._proxy_direct_response(response)
            
        except Exception as e:
            print(f"静态资源错误: {str(e)}")
            self._send_error(404, f"资源加载失败: {str(e)}")

    def _proxy_with_tunnel(self, target_url):
        """使用隧道技术代理网页"""
        try:
            headers = {
                'User-Agent': self.config['user_agents'][0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            response = self._make_request('GET', target_url, headers=headers)
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type:
                # 完全重写HTML内容
                rewritten_content = self._rewrite_html_completely(response.text, target_url)
                self._send_response(200, rewritten_content, 'text/html; charset=utf-8')
            else:
                # 其他类型内容直接代理
                self._proxy_direct_response(response)
                
        except Exception as e:
            print(f"隧道代理错误: {str(e)}")
            self._send_error(502, f"无法访问目标网站: {str(e)}")

    def _proxy_direct(self, target_url):
        """直接代理网页"""
        try:
            headers = {
                'User-Agent': self.config['user_agents'][0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = self._make_request('GET', target_url, headers=headers)
            self._proxy_direct_response(response)
            
        except Exception as e:
            print(f"直连代理错误: {str(e)}")
            self._send_error(502, f"无法访问目标网站: {str(e)}")

    def _make_request(self, method, url, **kwargs):
        """发送HTTP请求"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.config['max_retries'],
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认参数
        kwargs.setdefault('timeout', self.config['timeout'])
        kwargs.setdefault('verify', False)  # 忽略SSL证书验证
        kwargs.setdefault('allow_redirects', True)
        
        return session.request(method, url, **kwargs)

    def _rewrite_html_completely(self, html_content, base_url):
        """完全重写HTML内容"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 添加控制面板
            control_panel = self._create_control_panel(base_url)
            body_tag = soup.find('body')
            if body_tag:
                body_tag.insert(0, BeautifulSoup(control_panel, 'html.parser').div)
            else:
                soup.insert(0, BeautifulSoup(control_panel, 'html.parser').div)
            
            # 重写所有URL
            self._rewrite_all_urls(soup, base_url)
            
            # 注入超级拦截脚本
            super_script = self._create_super_interception_script(base_url)
            script_tag = soup.new_tag('script')
            script_tag.string = super_script
            if body_tag:
                body_tag.append(script_tag)
            else:
                soup.append(script_tag)
            
            return str(soup)
            
        except Exception as e:
            print(f"HTML重写错误: {str(e)}")
            # 返回原始内容作为备选
            return html_content

    def _create_control_panel(self, base_url):
        """创建控制面板"""
        return f'''
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 15px; margin: 0; 
            border-bottom: 3px solid #4c51bf;
            font-family: system-ui, -apple-system, sans-serif;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            position: sticky; top: 0; z-index: 10000;
        ">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div style="display: flex; align-items: center;">
                    <a href="/" style="
                        color: white; text-decoration: none; font-weight: bold; 
                        background: rgba(255,255,255,0.2); padding: 8px 16px; 
                        border-radius: 8px; margin-right: 20px; font-size: 14px;
                    ">🏠 代理主页</a>
                    <span style="font-size: 13px; opacity: 0.9;">隧道模式 | {base_url}</span>
                </div>
                <div>
                    <button onclick="window.location.href='/'" style="
                        background: rgba(255,255,255,0.2); color: white; 
                        border: 1px solid rgba(255,255,255,0.4); padding: 6px 12px; 
                        border-radius: 6px; cursor: pointer; font-size: 12px;
                        margin-left: 10px;
                    ">更换网址</button>
                </div>
            </div>
        </div>
        '''

    def _rewrite_all_urls(self, soup, base_url):
        """重写所有URL"""
        # 编码基础URL用于静态资源路径
        encoded_base = urllib.parse.quote(base_url)
        
        # 重写链接
        for tag in soup.find_all(['a', 'link', 'area']):
            if tag.get('href'):
                url = tag['href']
                if self._is_rewritable_url(url):
                    absolute_url = urllib.parse.urljoin(base_url, url)
                    tag['href'] = f'/tunnel/{urllib.parse.quote(absolute_url)}'
        
        # 重写资源
        for tag in soup.find_all(['img', 'script', 'iframe', 'embed', 'source', 'track', 'video', 'audio']):
            for attr in ['src', 'data', 'poster']:
                if tag.get(attr):
                    url = tag[attr]
                    if self._is_rewritable_url(url):
                        absolute_url = urllib.parse.urljoin(base_url, url)
                        tag[attr] = f'/static/{encoded_base}/{urllib.parse.quote(absolute_url)}'
        
        # 重写表单
        for form in soup.find_all('form'):
            if form.get('action'):
                url = form['action']
                if self._is_rewritable_url(url):
                    absolute_url = urllib.parse.urljoin(base_url, url)
                    form['action'] = f'/tunnel/{urllib.parse.quote(absolute_url)}'
        
        # 重写CSS
        for style in soup.find_all('style'):
            if style.string:
                style.string = self._rewrite_css_completely(style.string, base_url, encoded_base)
        
        for tag in soup.find_all(style=True):
            tag['style'] = self._rewrite_css_completely(tag['style'], base_url, encoded_base)

    def _is_rewritable_url(self, url):
        """判断URL是否需要重写"""
        if not url or url.strip() == '':
            return False
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'blob:')):
            return False
        if url.startswith(('/tunnel/', '/direct/', '/static/')):
            return False
        return True

    def _rewrite_css_completely(self, css_content, base_url, encoded_base):
        """完全重写CSS中的URL"""
        def replace_url(match):
            url = match.group(1).strip('"\'')
            if self._is_rewritable_url(url) and not url.startswith(('http://', 'https://', 'data:')):
                absolute_url = urllib.parse.urljoin(base_url, url)
                return f'url("/static/{encoded_base}/{urllib.parse.quote(absolute_url)}")'
            return match.group(0)
        
        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)

    def _create_super_interception_script(self, base_url):
        """创建超级拦截脚本"""
        return f'''
        // 超级拦截脚本 - 彻底防止跳转
        (function() {{
            'use strict';
            
            const baseUrl = "{base_url}";
            let interceptionActive = true;
            
            // 保存原始方法
            const originalMethods = {{
                location: window.location,
                open: window.open,
                fetch: window.fetch,
                assign: window.location.assign,
                replace: window.location.replace,
                href: Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'href')
            }};
            
            // 1. 拦截window.location
            Object.defineProperty(window, 'location', {{
                get: function() {{
                    const loc = originalMethods.location;
                    return new Proxy(loc, {{
                        get: function(target, prop) {{
                            if (prop === 'href') {{
                                return target.href;
                            }}
                            if (prop === 'assign') {{
                                return function(url) {{
                                    if (interceptionActive) {{
                                        const fullUrl = new URL(url, baseUrl).href;
                                        window.location.href = '/tunnel/' + encodeURIComponent(fullUrl);
                                        return;
                                    }}
                                    return originalMethods.assign.call(target, url);
                                }};
                            }}
                            if (prop === 'replace') {{
                                return function(url) {{
                                    if (interceptionActive) {{
                                        const fullUrl = new URL(url, baseUrl).href;
                                        window.location.href = '/tunnel/' + encodeURIComponent(fullUrl);
                                        return;
                                    }}
                                    return originalMethods.replace.call(target, url);
                                }};
                            }}
                            return target[prop];
                        }},
                        set: function(target, prop, value) {{
                            if (prop === 'href' && interceptionActive) {{
                                const fullUrl = new URL(value, baseUrl).href;
                                target.href = '/tunnel/' + encodeURIComponent(fullUrl);
                                return true;
                            }}
                            target[prop] = value;
                            return true;
                        }}
                    }});
                }},
                set: function(value) {{
                    if (interceptionActive) {{
                        const fullUrl = new URL(value, baseUrl).href;
                        originalMethods.location.href = '/tunnel/' + encodeURIComponent(fullUrl);
                        return true;
                    }}
                    originalMethods.location.href = value;
                    return true;
                }}
            }});
            
            // 2. 拦截window.open
            window.open = function(url, target, features) {{
                if (interceptionActive && url && typeof url === 'string') {{
                    const fullUrl = new URL(url, baseUrl).href;
                    return originalMethods.open.call(this, '/tunnel/' + encodeURIComponent(fullUrl), target, features);
                }}
                return originalMethods.open.apply(this, arguments);
            }};
            
            // 3. 拦截fetch
            window.fetch = function(resource, options) {{
                if (interceptionActive && typeof resource === 'string' && 
                    !resource.startsWith('/tunnel/') && !resource.startsWith('/static/')) {{
                    const fullUrl = new URL(resource, baseUrl).href;
                    resource = '/static/' + encodeURIComponent(baseUrl) + '/' + encodeURIComponent(fullUrl);
                }}
                return originalMethods.fetch.call(this, resource, options);
            }};
            
            // 4. 拦截所有链接点击
            document.addEventListener('click', function(e) {{
                if (!interceptionActive) return;
                
                let target = e.target;
                while (target && target.nodeName !== 'A') {{
                    target = target.parentElement;
                    if (!target) return;
                }}
                
                if (target && target.href && !target.href.includes('/tunnel/')) {{
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    const fullUrl = new URL(target.href, baseUrl).href;
                    window.location.href = '/tunnel/' + encodeURIComponent(fullUrl);
                    return false;
                }}
            }}, true);
            
            // 5. 拦截表单提交
            document.addEventListener('submit', function(e) {{
                if (!interceptionActive) return;
                
                const form = e.target;
                if (form.action && !form.action.includes('/tunnel/')) {{
                    e.preventDefault();
                    const fullUrl = new URL(form.action, baseUrl).href;
                    
                    // 创建临时表单
                    const tempForm = document.createElement('form');
                    tempForm.method = form.method || 'GET';
                    tempForm.action = '/tunnel/' + encodeURIComponent(fullUrl);
                    tempForm.style.display = 'none';
                    
                    // 复制所有表单数据
                    const formData = new FormData(form);
                    for (let [name, value] of formData.entries()) {{
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = name;
                        input.value = value;
                        tempForm.appendChild(input);
                    }}
                    
                    document.body.appendChild(tempForm);
                    tempForm.submit();
                }}
            }}, true);
            
            // 6. 拦截所有动态创建的链接
            const observer = new MutationObserver(function(mutations) {{
                mutations.forEach(function(mutation) {{
                    mutation.addedNodes.forEach(function(node) {{
                        if (node.nodeType === 1) {{ // Element node
                            if (node.tagName === 'A' && node.href && !node.href.includes('/tunnel/')) {{
                                const fullUrl = new URL(node.href, baseUrl).href;
                                node.href = '/tunnel/' + encodeURIComponent(fullUrl);
                            }}
                            // 检查子元素
                            node.querySelectorAll('a').forEach(function(link) {{
                                if (link.href && !link.href.includes('/tunnel/')) {{
                                    const fullUrl = new URL(link.href, baseUrl).href;
                                    link.href = '/tunnel/' + encodeURIComponent(fullUrl);
                                }}
                            }});
                        }}
                    }});
                }});
            }});
            
            observer.observe(document.body, {{
                childList: true,
                subtree: true
            }});
            
            console.log('🛡️ 超级拦截脚本已激活 - 所有跳转已被锁定');
        }})();
        '''

    def _proxy_tunnel_response(self, response, base_url):
        """代理隧道响应"""
        content_type = response.headers.get('Content-Type', '').lower()
        
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html_completely(response.text, base_url)
            self._send_response(response.status_code, rewritten_content, 'text/html; charset=utf-8')
        else:
            self._proxy_direct_response(response)

    def _proxy_direct_response(self, response):
        """直接代理响应"""
        self.send_response(response.status_code)
        
        # 复制响应头
        for header, value in response.headers.items():
            header_lower = header.lower()
            if header_lower not in ['content-encoding', 'transfer-encoding', 'content-length', 'connection']:
                self.send_header(header, value)
        
        content = response.content
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_html(self, html_content):
        """发送HTML响应"""
        self._send_response(200, html_content, 'text/html; charset=utf-8')

    def _send_response(self, code, content, content_type):
        """发送响应"""
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_error(self, code, message):
        """发送错误页面"""
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误 {code}</title>
            <style>
                body {{ font-family: system-ui, sans-serif; padding: 40px; text-align: center; background: #f8fafc; }}
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
        self._send_response(code, error_html)

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def run_tunnel_proxy():
    """运行隧道代理服务器"""
    port = 60000
    
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # 配置服务器
    class CloudShellServer(socketserver.TCPServer):
        allow_reuse_address = True
        request_queue_size = 50
        
        def server_bind(self):
            import socket
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            super().server_bind()
    
    try:
        with CloudShellServer(("", port), TunnelProxyHandler) as httpd:
            print("=" * 70)
            print("🚀 CloudShell终极代理服务器已启动")
            print(f"📍 运行端口: {port}")
            print(f"🌐 访问地址: http://localhost:{port}")
            print("=" * 70)
            print("✨ 核心特性:")
            print("   • 🔒 隧道模式 - 彻底防止页面跳转")
            print("   • ⚡ 直连模式 - 快速简单代理") 
            print("   • 🛡️ 超级拦截 - 全面覆盖所有跳转方式")
            print("   • 🔄 自动重试 - 智能错误恢复")
            print("   • 📱 响应式UI - 完美适配各种设备")
            print("=" * 70)
            print("⏹️  按 Ctrl+C 停止服务器")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 服务器已安全停止")
                
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    run_tunnel_proxy()
