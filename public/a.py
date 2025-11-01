#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Cloud Shell 网页代理服务
    简化版本，解决空白页面问题
"""
import http.server
import socketserver
import urllib.request
import urllib.parse
import re
import gzip
import zlib
import threading

class SimpleProxyHandler(http.server.SimpleHTTPRequestHandler):
    """
    简单的HTTP代理处理器
    """
    
    def do_GET(self):
        print(f"收到请求: {self.path}")
        
        # 解析路径和查询参数
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        # 根路径 - 显示导航页面
        if parsed_path.path == '/':
            self.send_navigation_page()
            return
            
        # 导航请求 - 代理目标网站
        elif parsed_path.path == '/navigate' and 'url' in query_params:
            target_url = query_params['url'][0]
            self.proxy_website(target_url)
            return
            
        # 其他路径 - 尝试代理
        else:
            # 从路径中提取目标URL
            if parsed_path.path.startswith('/proxy/'):
                encoded_url = parsed_path.path[7:]
                target_url = urllib.parse.unquote(encoded_url)
                self.proxy_website(target_url)
                return
            else:
                self.send_error(404, "页面未找到")
                return
    
    def send_navigation_page(self):
        """发送导航页面"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cloud Shell 网页代理</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container {
                    max-width: 600px;
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
                    font-size: 2em;
                }
                .content {
                    padding: 30px;
                }
                .input-group {
                    display: flex;
                    margin-bottom: 20px;
                    border: 2px solid #e1e5e9;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .url-input {
                    flex: 1;
                    padding: 15px;
                    border: none;
                    outline: none;
                    font-size: 16px;
                }
                .submit-btn {
                    background: #4facfe;
                    color: white;
                    border: none;
                    padding: 0 25px;
                    cursor: pointer;
                    font-size: 16px;
                }
                .quick-links {
                    margin-top: 30px;
                }
                .quick-link {
                    display: block;
                    padding: 12px 15px;
                    margin: 8px 0;
                    background: #f7fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    text-decoration: none;
                    color: #4a5568;
                    transition: all 0.2s;
                }
                .quick-link:hover {
                    background: #4facfe;
                    color: white;
                }
                .loading {
                    text-align: center;
                    padding: 50px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌐 Cloud Shell 网页代理</h1>
                    <p>输入网址开始浏览</p>
                </div>
                
                <div class="content">
                    <form action="/navigate" method="get" target="_blank">
                        <div class="input-group">
                            <input type="url" name="url" class="url-input" 
                                   placeholder="https://www.example.com" 
                                   required>
                            <button type="submit" class="submit-btn">访问</button>
                        </div>
                    </form>
                    
                    <div class="quick-links">
                        <strong>常用网站:</strong>
                        <a href="/navigate?url=https://www.so.com" class="quick-link" target="_blank">🔍 360搜索</a>
                        <a href="/navigate?url=https://www.baidu.com" class="quick-link" target="_blank">🔍 百度</a>
                        <a href="/navigate?url=https://www.google.com" class="quick-link" target="_blank">🔍 Google</a>
                        <a href="/navigate?url=https://github.com" class="quick-link" target="_blank">💻 GitHub</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def proxy_website(self, target_url):
        """代理目标网站"""
        print(f"开始代理: {target_url}")
        
        try:
            # 验证和修复URL
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'https://' + target_url
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # 创建请求
            req = urllib.request.Request(target_url, headers=headers)
            
            # 发起请求
            response = urllib.request.urlopen(req, timeout=30)
            
            # 读取响应内容
            content = response.read()
            content_type = response.headers.get('Content-Type', 'text/html')
            
            # 处理压缩内容
            content_encoding = response.headers.get('Content-Encoding', '').lower()
            if 'gzip' in content_encoding:
                try:
                    content = gzip.decompress(content)
                except (gzip.BadGzipFile, EOFError):
                    pass
            elif 'deflate' in content_encoding:
                try:
                    content = zlib.decompress(content)
                except zlib.error:
                    pass
            
            # 重写内容中的链接
            if 'text/html' in content_type.lower():
                content = self.rewrite_content(content, target_url)
            
            # 发送响应
            self.send_response(response.status)
            
            # 复制响应头（过滤不合适的头）
            for key, value in response.headers.items():
                key_lower = key.lower()
                if key_lower not in ['connection', 'transfer-encoding', 'content-encoding', 
                                   'content-length', 'strict-transport-security']:
                    self.send_header(key, value)
            
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            
            # 返回响应内容
            self.wfile.write(content)
            
            print(f"代理成功: {target_url}")
            
        except Exception as e:
            print(f"代理错误: {e}")
            self.send_error_page(f"无法访问 {target_url}", str(e))
    
    def rewrite_content(self, content, base_url):
        """重写HTML内容中的链接"""
        try:
            # 解码内容
            html_content = content.decode('utf-8')
            
            # 解析基础URL
            parsed_base = urllib.parse.urlparse(base_url)
            base_domain = parsed_base.netloc
            
            # 重写各种链接
            patterns = [
                # href属性
                (r'href=(["\'])(https?://[^"\']*?)\1', 
                 lambda m: f'href={m.group(1)}/proxy/{urllib.parse.quote(m.group(2))}{m.group(1)}'),
                
                # src属性
                (r'src=(["\'])(https?://[^"\']*?)\1',
                 lambda m: f'src={m.group(1)}/proxy/{urllib.parse.quote(m.group(2))}{m.group(1)}'),
                
                # action属性
                (r'action=(["\'])(https?://[^"\']*?)\1',
                 lambda m: f'action={m.group(1)}/proxy/{urllib.parse.quote(m.group(2))}{m.group(1)}'),
            ]
            
            for pattern, replacement in patterns:
                html_content = re.sub(pattern, replacement, html_content)
            
            # 重写相对路径（转换为绝对路径）
            def make_absolute(match):
                tag, attr, quote, path = match.groups()
                if path.startswith('//'):
                    # 协议相对URL
                    absolute_url = f"https:{path}"
                elif path.startswith('/'):
                    # 根相对路径
                    absolute_url = f"{parsed_base.scheme}://{base_domain}{path}"
                else:
                    # 文档相对路径
                    absolute_url = urllib.parse.urljoin(base_url, path)
                
                return f'{tag}{attr}={quote}/proxy/{urllib.parse.quote(absolute_url)}{quote}'
            
            # 重写相对路径的href
            html_content = re.sub(
                r'(\w+)href=(["\'])([^"\'#]*?)(["\'])',
                make_absolute,
                html_content
            )
            
            # 重写相对路径的src
            html_content = re.sub(
                r'(\w+src)=(["\'])([^"\'#]*?)(["\'])',
                make_absolute,
                html_content
            )
            
            return html_content.encode('utf-8')
            
        except Exception as e:
            print(f"内容重写错误: {e}")
            return content
    
    def send_error_page(self, title, message):
        """发送错误页面"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误 - {title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #ffecec; border: 1px solid #f5aca6; padding: 20px; border-radius: 5px; }}
                a {{ color: #0066cc; }}
            </style>
        </head>
        <body>
            <h1>😕 {title}</h1>
            <div class="error">
                <p><strong>错误信息:</strong> {message}</p>
            </div>
            <p><a href="/">返回首页</a></p>
        </body>
        </html>
        """
        
        self.send_response(500)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

def main():
    """主函数"""
    PORT = 60000
    
    print("=" * 60)
    print("🌐 Cloud Shell 网页代理服务")
    print("=" * 60)
    print(f"📡 服务启动在端口: {PORT}")
    print("💡 请在Cloud Shell中点击'网页预览' -> '预览端口 60000'")
    print("⏹️  按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), SimpleProxyHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")

if __name__ == "__main__":
    main()
