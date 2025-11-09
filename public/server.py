#!/usr/bin/env python3
"""
HTTP代理服务器
运行端口: 60000
修复必应搜索变360和主页重复代理问题
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import http.server
import socketserver
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re
import time
import json

class FixedProxyHandler(http.server.BaseHTTPRequestHandler):
    """修复的代理处理器"""

    config = {
        'port': 60000,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'timeout': 30
    }

    def do_GET(self):
        """处理GET请求"""
        try:
            print(f"请求: {self.path}")
            
            if self.path == '/':
                self._serve_homepage()
            elif self.path.startswith('/proxy?url='):
                self._proxy_webpage()
            elif self.path.startswith('/proxy?') and 'url=' not in self.path:
                self._handle_search_result()
            else:
                self._proxy_resource()
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

    def do_POST(self):
        """处理POST请求"""
        try:
            if self.path.startswith('/proxy?url='):
                self._proxy_post_request()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

    def _proxy_webpage(self):
        """代理网页"""
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]

        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return

        if not target_url.startswith(('http://', 'https://')):
            target_url = 'http://' + target_url

        print(f"目标URL: {target_url}")

        headers = self._get_headers(target_url)

        try:
            response = requests.get(target_url, headers=headers, timeout=self.config['timeout'], verify=False)
        except requests.exceptions.RequestException as e:
            self.send_error(502, f"Failed to fetch: {str(e)}")
            return

        if response.status_code != 200:
            self._handle_response_error(response, target_url)
            return

        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html(response.text, target_url)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(rewritten_content.encode('utf-8'))
        else:
            self._proxy_raw_content(response)

    def _get_headers(self, url):
        """获取请求头"""
        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # 为特定网站设置Referer
        if 'bilibili.com' in url:
            headers['Referer'] = 'https://www.bilibili.com/'
            headers['Origin'] = 'https://www.bilibili.com'
        elif 'so.com' in url:
            headers['Referer'] = 'https://www.so.com/'
        elif 'bing.com' in url:
            headers['Referer'] = 'https://www.bing.com/'
        else:
            headers['Referer'] = url
            
        return headers

    def _rewrite_html(self, html_content, base_url):
        """重写HTML内容"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            print(f"HTML解析错误: {e}")
            return self._create_basic_page(html_content, base_url)

        # 添加导航栏
        self._add_navigation(soup, base_url)

        # 重写所有链接和资源
        self._rewrite_all_links(soup, base_url)

        # 特殊处理哔哩哔哩
        if 'bilibili.com' in base_url:
            self._fix_bilibili_issues(soup)

        # 注入拦截脚本
        self._inject_interception_script(soup)

        # 确保字符集
        self._ensure_charset(soup)

        return str(soup)

    def _create_basic_page(self, content, base_url):
        """创建基础页面"""
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>代理页面</title>
            <style>
                body {{ margin-top: 50px; font-family: Arial, sans-serif; }}
                .nav {{ background: #007cba; color: white; padding: 10px; position: fixed; top: 0; left: 0; right: 0; z-index: 10000; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/" style="color: white; text-decoration: none; font-weight: bold;">返回主页</a>
                <span style="margin-left: 15px;">代理: {base_url[:60] + '...' if len(base_url) > 60 else base_url}</span>
            </div>
            {content}
        </body>
        </html>
        '''

    def _add_navigation(self, soup, base_url):
        """添加导航栏"""
        # 使用特殊标记的主页链接，避免被重写
        nav_html = f'''
        <div style="background: #007cba; color: white; padding: 10px; margin: 0; text-align: center; position: fixed; top: 0; left: 0; right: 0; z-index: 10000;">
            <a href="/" style="color: white; text-decoration: none; font-weight: bold;" data-no-proxy="true">返回主页</a>
            <span style="margin-left: 15px;">代理: {base_url[:60] + '...' if len(base_url) > 60 else base_url}</span>
        </div>
        '''

        body_tag = soup.find('body')
        if body_tag:
            body_style = body_tag.get('style', '')
            if 'margin-top' not in body_style:
                body_tag['style'] = body_style + '; margin-top: 50px;' if body_style else 'margin-top: 50px;'
            
            nav_soup = BeautifulSoup(nav_html, 'html.parser')
            body_tag.insert(0, nav_soup.div)
        else:
            body_tag = soup.new_tag('body')
            body_tag['style'] = 'margin-top: 50px;'
            nav_soup = BeautifulSoup(nav_html, 'html.parser')
            body_tag.append(nav_soup.div)
            
            for content in soup.contents:
                if content.name != 'body':
                    body_tag.append(content)
            soup.append(body_tag)

    def _rewrite_all_links(self, soup, base_url):
        """重写所有链接和资源"""
        # 重写普通链接 - 跳过有data-no-proxy标记的链接
        for tag in soup.find_all('a', href=True):
            if tag.get('data-no-proxy') == 'true':
                continue
                
            href = tag['href']
            if self._should_rewrite_url(href):
                absolute_url = urllib.parse.urljoin(base_url, href)
                tag['href'] = "/proxy?url=" + urllib.parse.quote(absolute_url)

        # 重写表单
        for form in soup.find_all('form', action=True):
            action = form['action']
            if self._should_rewrite_url(action):
                absolute_url = urllib.parse.urljoin(base_url, action)
                form['action'] = "/proxy?url=" + urllib.parse.quote(absolute_url)

        # 重写所有资源
        resource_tags = soup.find_all(['img', 'script', 'link', 'iframe', 'source', 'embed', 'object'], 
                                    src=True) + soup.find_all('link', href=True)
        
        for tag in resource_tags:
            src_attr = 'src' if tag.get('src') else 'href'
            src = tag[src_attr]
            if self._should_rewrite_url(src):
                absolute_url = urllib.parse.urljoin(base_url, src)
                tag[src_attr] = "/proxy?url=" + urllib.parse.quote(absolute_url)

        # 重写CSS中的URL
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if style_tag.string:
                style_tag.string = self._rewrite_css_urls(style_tag.string, base_url)

        # 重写内联样式
        for tag in soup.find_all(style=True):
            style = tag['style']
            tag['style'] = self._rewrite_css_urls(style, base_url)

    def _fix_bilibili_issues(self, soup):
        """修复哔哩哔哩问题"""
        # 修复412错误：移除可能导致验证的脚本
        for script in soup.find_all('script'):
            script_content = script.string or ''
            if '412' in script_content or 'precondition' in script_content.lower():
                script.decompose()
        
        # 确保资源正确加载
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                link['href'] = link['href'] + '?t=' + str(int(time.time()))
        
        for script in soup.find_all('script', src=True):
            if script['src'] and not script['src'].startswith('http'):
                script['src'] = 'https:' + script['src'] if script['src'].startswith('//') else 'https://www.bilibili.com' + script['src']

    def _inject_interception_script(self, soup):
        """注入拦截脚本"""
        interception_script = '''
        // 修复的JavaScript拦截代码
        (function() {
            'use strict';
            
            // 拦截所有点击事件
            function interceptClickEvent(e) {
                var target = e.target;
                
                while (target && target !== document) {
                    if (target.tagName && target.tagName.toLowerCase() === 'a' && target.href) {
                        var href = target.href;
                        
                        // 检查是否是需要代理的链接 - 跳过有data-no-proxy标记的链接
                        if (href && 
                            !href.includes('/proxy?url=') && 
                            !href.startsWith('javascript:') && 
                            !href.startsWith('mailto:') && 
                            !href.startsWith('tel:') && 
                            !href.startsWith('#') &&
                            !href.startsWith('data:') &&
                            !target.hasAttribute('data-no-proxy')) {
                            
                            e.preventDefault();
                            e.stopImmediatePropagation();
                            e.stopPropagation();
                            
                            try {
                                var proxyUrl = '/proxy?url=' + encodeURIComponent(href);
                                window.location.href = proxyUrl;
                            } catch (err) {
                                console.log('拦截错误:', err);
                            }
                            return false;
                        }
                    }
                    target = target.parentNode;
                }
            }
            
            // 多事件监听确保捕获所有点击
            document.addEventListener('click', interceptClickEvent, true);
            document.addEventListener('auxclick', interceptClickEvent, true);
            
            // 拦截表单提交
            document.addEventListener('submit', function(e) {
                var form = e.target;
                if (form.tagName && form.tagName.toLowerCase() === 'form' && form.action) {
                    var action = form.action;
                    if (action && !action.includes('/proxy?url=')) {
                        e.preventDefault();
                        var proxyUrl = '/proxy?url=' + encodeURIComponent(action);
                        
                        // 创建隐藏表单进行提交
                        var hiddenForm = document.createElement('form');
                        hiddenForm.method = form.method || 'GET';
                        hiddenForm.action = proxyUrl;
                        hiddenForm.style.display = 'none';
                        
                        // 复制所有表单数据
                        var inputs = form.querySelectorAll('input, select, textarea');
                        for (var i = 0; i < inputs.length; i++) {
                            var input = inputs[i];
                            if (input.name) {
                                var newInput = document.createElement('input');
                                newInput.type = 'hidden';
                                newInput.name = input.name;
                                newInput.value = input.value;
                                hiddenForm.appendChild(newInput);
                            }
                        }
                        
                        document.body.appendChild(hiddenForm);
                        hiddenForm.submit();
                    }
                }
            }, true);
            
            console.log('拦截脚本已加载');
        })();
        '''
        
        script_tag = soup.new_tag('script')
        script_tag.string = interception_script
        
        body_tag = soup.find('body')
        if body_tag:
            body_tag.append(script_tag)
        else:
            soup.append(script_tag)

    def _ensure_charset(self, soup):
        """确保字符集声明"""
        head_tag = soup.find('head')
        if not head_tag:
            head_tag = soup.new_tag('head')
            soup.insert(0, head_tag)
        
        # 添加UTF-8 charset声明
        new_meta = soup.new_tag('meta', charset='utf-8')
        head_tag.insert(0, new_meta)

    def _should_rewrite_url(self, url):
        """判断URL是否需要重写"""
        if not url or url.strip() == '':
            return False
        if url.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'blob:')):
            return False
        if url.startswith(('/proxy?url=', '/resource/', 'http://localhost:', 'https://localhost:')):
            return False
        # 确保主页链接不会被重写
        if url == '/' or url.startswith('/?'):
            return False
        return True

    def _rewrite_css_urls(self, css_content, base_url):
        """重写CSS中的url()引用"""
        def replace_url(match):
            url_content = match.group(1)
            if url_content.startswith(('http://', 'https://', 'data:')):
                return match.group(0)

            absolute_url = urllib.parse.urljoin(base_url, url_content.strip('"\''))
            proxy_url = "/proxy?url=" + urllib.parse.quote(absolute_url)
            return 'url("' + proxy_url + '")'

        pattern = r'url\(["\']?([^"\'()]*)["\']?\)'
        return re.sub(pattern, replace_url, css_content)

    def _handle_response_error(self, response, target_url):
        """处理错误响应"""
        status_code = response.status_code
        
        # 处理重定向
        if status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get('Location', '')
            if location:
                if not location.startswith(('http://', 'https://')):
                    location = urllib.parse.urljoin(target_url, location)
                
                proxy_location = "/proxy?url=" + urllib.parse.quote(location)
                
                redirect_html = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>重定向中</title>
                    <meta http-equiv="refresh" content="0;url={proxy_location}">
                    <meta charset="utf-8">
                </head>
                <body>
                    <div style="background: #007cba; color: white; padding: 10px; text-align: center;">
                        <a href="/" style="color: white; text-decoration: none; font-weight: bold;" data-no-proxy="true">返回主页</a>
                    </div>
                    <div style="text-align: center; margin-top: 50px;">
                        <p>正在重定向... <a href="{proxy_location}">点击这里</a> 如果页面没有自动跳转。</p>
                    </div>
                </body>
                </html>
                '''
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(redirect_html.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(redirect_html.encode('utf-8'))
                return
        
        # 处理其他错误状态码
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>{status_code}错误</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; }}
                .nav {{ background: #007cba; color: white; padding: 10px; text-align: center; }}
                .error-container {{ max-width: 600px; margin: 50px auto; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="nav">
                <a href="/" style="color: white; text-decoration: none; font-weight: bold;" data-no-proxy="true">返回主页</a>
            </div>
            <div class="error-container">
                <h1>代理访问遇到问题</h1>
                <div>错误代码: {status_code}</div>
                <p>目标网站返回了错误响应。</p>
                <p><a href="/proxy?url={urllib.parse.quote(target_url)}">重新尝试访问此页面</a></p>
            </div>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(error_html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(error_html.encode('utf-8'))

    def _handle_search_result(self):
        """处理搜索结果 - 修复必应变360问题"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            print(f"搜索参数: {query_params}")
            
            referer = self.headers.get('Referer', '')
            if referer and '/proxy?url=' in referer:
                referer_parsed = urllib.parse.urlparse(referer)
                referer_query = urllib.parse.parse_qs(referer_parsed.query)
                base_search_url = referer_query.get('url', [''])[0]
                
                if base_search_url:
                    # 关键修复：保持原始搜索引擎，不强制转换
                    # 如果来源是必应，继续使用必应；如果是360，继续使用360
                    if 'so.com' in base_search_url:
                        search_result_url = "https://www.so.com/s"
                    elif 'bing.com' in base_search_url:
                        search_result_url = "https://www.bing.com/search"
                    else:
                        # 默认使用必应搜索，而不是360
                        search_result_url = "https://www.bing.com/search"
                    
                    # 构建搜索URL
                    if query_params:
                        search_result_url += "?" + urllib.parse.urlencode(query_params, doseq=True)
                    
                    print(f"搜索请求将发送到: {search_result_url}")
                    self._proxy_specific_url(search_result_url)
                    return
            
            # 如果没有Referer，使用默认搜索
            self._try_fix_search()
            
        except Exception as e:
            print(f"搜索处理错误: {str(e)}")
            self.send_error(500, f"Search processing error: {str(e)}")

    def _try_fix_search(self):
        """尝试修复搜索 - 修复默认使用360搜索的问题"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if 'q' in query_params or 'query' in query_params or 'keyword' in query_params:
                # 关键修复：默认使用必应搜索，而不是360搜索
                search_result_url = "https://www.bing.com/search"
                
                if query_params:
                    search_result_url += "?" + urllib.parse.urlencode(query_params, doseq=True)
                
                print(f"修复搜索URL: {search_result_url}")
                self._proxy_specific_url(search_result_url)
                return
            
            self.send_error(400, "无法处理的搜索请求")
            
        except Exception as e:
            print(f"搜索修复错误: {str(e)}")
            self.send_error(500, f"Search fix error: {str(e)}")

    def _proxy_specific_url(self, target_url):
        """代理特定URL"""
        print(f"代理URL: {target_url}")
        
        headers = self._get_headers(target_url)
        
        try:
            response = requests.get(target_url, headers=headers, timeout=self.config['timeout'], verify=False)
        except requests.exceptions.RequestException as e:
            self.send_error(502, f"Failed to fetch: {str(e)}")
            return
        
        if response.status_code != 200:
            self._handle_response_error(response, target_url)
            return
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            rewritten_content = self._rewrite_html(response.text, target_url)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(rewritten_content.encode('utf-8'))
        else:
            self._proxy_raw_content(response)

    def _proxy_post_request(self):
        """处理POST请求"""
        query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        target_url = query_params.get('url', [''])[0]
        
        if not target_url:
            self.send_error(400, "Missing URL parameter")
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''
        
        headers = self._get_headers(target_url)
        headers['Content-Type'] = self.headers.get('Content-Type', 'application/x-www-form-urlencoded')
        
        try:
            response = requests.post(target_url, data=post_data, headers=headers, 
                                   timeout=self.config['timeout'], verify=False, allow_redirects=False)
            
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', '')
                if location:
                    if not location.startswith(('http://', 'https://')):
                        location = urllib.parse.urljoin(target_url, location)
                    
                    proxy_location = "/proxy?url=" + urllib.parse.quote(location)
                    
                    redirect_html = f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>重定向中</title>
                        <meta http-equiv="refresh" content="0;url={proxy_location}">
                        <meta charset="utf-8">
                    </head>
                    <body>
                        <div style="background: #007cba; color: white; padding: 10px; text-align: center;">
                            <a href="/" style="color: white; text-decoration: none; font-weight: bold;" data-no-proxy="true">返回主页</a>
                        </div>
                        <div style="text-align: center; margin-top: 50px;">
                            <p>正在重定向... <a href="{proxy_location}">点击这里</a> 如果页面没有自动跳转。</p>
                        </div>
                    </body>
                    </html>
                    '''
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(redirect_html.encode('utf-8'))))
                    self.end_headers()
                    self.wfile.write(redirect_html.encode('utf-8'))
                    return
            
            if response.status_code != 200:
                self._handle_response_error(response, target_url)
                return
                
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                rewritten_content = self._rewrite_html(response.text, target_url)
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(rewritten_content.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(rewritten_content.encode('utf-8'))
            else:
                self._proxy_raw_content(response)
            
        except requests.exceptions.RequestException as e:
            self.send_error(502, f"Failed to POST: {str(e)}")

    def _serve_homepage(self):
        """提供主页"""
        homepage_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>代理服务 - 60000端口</title>
            <meta charset="utf-8">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    background: #f5f5f5;
                }
                .container { 
                    max-width: 600px; 
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
            </style>
        </head>
        <body>
            <div class="container">
                <h1>代理服务</h1>
                <p>输入要访问的网址：</p>
                
                <form action="/proxy" method="GET">
                    <div class="form-group">
                        <input type="url" name="url" placeholder="https://www.example.com" required>
                    </div>
                    <button type="submit">开始访问</button>
                </form>
                
                <div style="margin-top: 20px; text-align: center; color: #666;">
                    <small>作者:HY</small>
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

    def _proxy_resource(self):
        """代理资源文件"""
        referer = self.headers.get('Referer', '')

        if '/proxy?url=' in referer:
            referer_parsed = urllib.parse.urlparse(referer)
            referer_query = urllib.parse.parse_qs(referer_parsed.query)
            base_url = referer_query.get('url', [''])[0]

            if base_url:
                if self.path == '/':
                    self._serve_homepage()
                    return
                    
                resource_url = urllib.parse.urljoin(base_url, self.path)

                headers = {
                    'User-Agent': self.config['user_agent'],
                    'Referer': base_url
                }

                try:
                    response = requests.get(resource_url, headers=headers, timeout=15, verify=False)
                    if response.status_code == 200:
                        self._proxy_raw_content(response)
                    else:
                        self._send_empty_response()
                    return
                except requests.exceptions.RequestException:
                    self._send_empty_response()
                    return

        if self.path == '/':
            self._serve_homepage()
            return
            
        self._send_empty_response()

    def _send_empty_response(self):
        """发送空响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _proxy_raw_content(self, response):
        """代理原始内容"""
        self.send_response(response.status_code)
        
        excluded_headers = ['content-encoding', 'transfer-encoding', 'content-length', 'connection']
        for header, value in response.headers.items():
            if header.lower() not in excluded_headers:
                self.send_header(header, value)
        
        self.send_header('Content-Length', str(len(response.content)))
        self.end_headers()
        self.wfile.write(response.content)

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
    
    with socketserver.TCPServer(("", port), FixedProxyHandler) as httpd:
        print("代理服务器已启动在端口 " + str(port))
        print("访问地址: http://localhost:" + str(port))
        print("按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == "__main__":
    run_proxy_server()
