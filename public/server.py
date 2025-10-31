import http.server
import socketserver
import urllib.request
import urllib.parse
import re
import gzip
import zlib

class UniversalProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.target_url = kwargs.pop('target_url')
        self.target_base = urllib.parse.urlparse(self.target_url)
        self.target_domain = self.target_base.netloc
        self.target_scheme = self.target_base.scheme
        super().__init__(*args, **kwargs)
    
    def rewrite_content(self, content, content_type, current_path=""):
        """根据内容类型重写内容中的URL"""
        if not content:
            return content
            
        # 解码内容
        try:
            decoded_content = content.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            # 如果不是文本内容，直接返回
            return content
        
        # HTML重写
        if 'text/html' in content_type:
            return self.rewrite_html_content(decoded_content, current_path).encode('utf-8')
        
        # CSS重写
        elif 'text/css' in content_type:
            return self.rewrite_css_content(decoded_content, current_path).encode('utf-8')
        
        # JavaScript重写（谨慎处理）
        elif 'javascript' in content_type or content_type.endswith('/javascript'):
            return self.rewrite_js_content(decoded_content, current_path).encode('utf-8')
        
        # SVG重写（SVG内可能包含链接）
        elif 'image/svg+xml' in content_type:
            return self.rewrite_svg_content(decoded_content, current_path).encode('utf-8')
        
        # 其他文本类型（如XML等）
        elif content_type.startswith('text/'):
            return self.rewrite_generic_text_content(decoded_content, current_path).encode('utf-8')
        
        # 非文本内容不重写
        else:
            return content
    
    def rewrite_html_content(self, html_content, current_path=""):
        """重写HTML内容中的所有资源引用"""
        # 重写各种HTML属性
        patterns = [
            # 标准属性
            (r'href=(["\'])(.*?)\1', 'href'),
            (r'src=(["\'])(.*?)\1', 'src'),
            (r'action=(["\'])(.*?)\1', 'action'),
            (r'background=(["\'])(.*?)\1', 'background'),
            (r'poster=(["\'])(.*?)\1', 'poster'),
            (r'cite=(["\'])(.*?)\1', 'cite'),
            (r'data=(["\'])(.*?)\1', 'data'),
            (r'formaction=(["\'])(.*?)\1', 'formaction'),
            (r'icon=(["\'])(.*?)\1', 'icon'),
            (r'manifest=(["\'])(.*?)\1', 'manifest'),
            (r'archive=(["\'])(.*?)\1', 'archive'),
            
            # CSS相关
            (r'style=(["\'])(.*?)\1', 'style'),
            
            # 元标签
            (r'content=(["\'])(.*?)\1', 'content'),
        ]
        
        for pattern, attr_type in patterns:
            def replace_match(match):
                if attr_type == 'style':
                    # 处理内联样式
                    style_content = match.group(2)
                    # 重写style中的url()
                    style_content = re.sub(
                        r'url\((["\']?)(.*?)(["\']?)\)',
                        lambda m: f'url({m.group(1)}{self.rewrite_url(m.group(2).strip(), current_path)}{m.group(3)})',
                        style_content
                    )
                    return f'style={match.group(1)}{style_content}{match.group(1)}'
                else:
                    url = match.group(2)
                    new_url = self.rewrite_url(url, current_path)
                    return f'{attr_type}={match.group(1)}{new_url}{match.group(1)}'
            
            html_content = re.sub(pattern, replace_match, html_content, flags=re.IGNORECASE)
        
        # 处理srcset属性（特殊格式）
        srcset_pattern = r'srcset=(["\'])(.*?)\1'
        def replace_srcset(match):
            srcset_content = match.group(2)
            parts = re.split(r',\s*', srcset_content)
            new_parts = []
            for part in parts:
                if part.strip():
                    if ' ' in part:
                        url_descriptor = part.split(' ', 1)
                        url = url_descriptor[0].strip()
                        descriptor = url_descriptor[1].strip()
                        new_url = self.rewrite_url(url, current_path)
                        new_parts.append(f'{new_url} {descriptor}')
                    else:
                        new_url = self.rewrite_url(part.strip(), current_path)
                        new_parts.append(new_url)
            return f'srcset={match.group(1)}{", ".join(new_parts)}{match.group(1)}'
        
        html_content = re.sub(srcset_pattern, replace_srcset, html_content, flags=re.IGNORECASE)
        
        return html_content
    
    def rewrite_css_content(self, css_content, current_path=""):
        """重写CSS内容中的所有URL"""
        # 重写url()函数
        css_content = re.sub(
            r'url\((["\']?)(.*?)(["\']?)\)',
            lambda m: f'url({m.group(1)}{self.rewrite_url(m.group(2).strip(), current_path)}{m.group(3)})',
            css_content
        )
        
        # 重写@import规则
        css_content = re.sub(
            r'@import\s+(["\'])(.*?)\1',
            lambda m: f'@import {m.group(1)}{self.rewrite_url(m.group(2).strip(), current_path)}{m.group(1)}',
            css_content
        )
        
        return css_content
    
    def rewrite_js_content(self, js_content, current_path=""):
        """重写JavaScript内容中的URL（谨慎处理）"""
        # 只重写明显的URL字符串，避免破坏代码逻辑
        target_domain_escaped = re.escape(self.target_domain)
        
        # 匹配字符串中的完整URL
        js_content = re.sub(
            rf'(["\'])(https?:\\?/\\?/{target_domain_escaped}[^"\']*?)(["\'])',
            lambda m: f'{m.group(1)}{self.rewrite_url(m.group(2).replace("\\", ""), current_path)}{m.group(3)}',
            js_content
        )
        
        # 匹配字符串中的相对路径（以/开头）
        js_content = re.sub(
            r'(["\'])(\/[^"\']*?)(["\'])',
            lambda m: f'{m.group(1)}{self.rewrite_url(m.group(2), current_path)}{m.group(3)}',
            js_content
        )
        
        return js_content
    
    def rewrite_svg_content(self, svg_content, current_path=""):
        """重写SVG内容中的链接"""
        # SVG中可能包含xlink:href等属性
        patterns = [
            (r'xlink:href=(["\'])(.*?)\1', 'xlink:href'),
            (r'href=(["\'])(.*?)\1', 'href'),
        ]
        
        for pattern, attr_type in patterns:
            svg_content = re.sub(
                pattern,
                lambda m: f'{attr_type}={m.group(1)}{self.rewrite_url(m.group(2), current_path)}{m.group(1)}',
                svg_content
            )
        
        # 重写SVG中的样式
        svg_content = re.sub(
            r'style=(["\'])(.*?)\1',
            lambda m: f'style={m.group(1)}{self.rewrite_css_content(m.group(2), current_path)}{m.group(1)}',
            svg_content
        )
        
        return svg_content
    
    def rewrite_generic_text_content(self, text_content, current_path=""):
        """重写通用文本内容中的URL"""
        # 重写明显的URL模式
        target_domain_escaped = re.escape(self.target_domain)
        text_content = re.sub(
            rf'https?:\\?/\\?/{target_domain_escaped}[^\s<>"\'\)]*',
            lambda m: self.rewrite_url(m.group(0).replace("\\", ""), current_path),
            text_content
        )
        
        return text_content
    
    def rewrite_url(self, url, current_path=""):
        """重写单个URL"""
        if not url or url.startswith(('data:', 'javascript:', 'mailto:', 'tel:', '#')):
            return url
        
        # 解析当前请求路径
        if current_path.startswith('/proxy/'):
            base_path = current_path[7:]  # 移除'/proxy/'前缀
        else:
            base_path = current_path
        
        # 解析URL
        parsed = urllib.parse.urlparse(url)
        
        # 处理不同类型的URL
        if parsed.netloc:  # 绝对URL
            if self.target_domain in parsed.netloc:
                # 目标域名的资源 - 重写为代理URL
                path = parsed.path
                if parsed.query:
                    path += f"?{parsed.query}"
                if parsed.fragment:
                    path += f"#{parsed.fragment}"
                return f"/proxy/{path.lstrip('/')}"
            else:
                # 外部资源 - 保持原样
                return url
        elif url.startswith('//'):  # 协议相对URL
            absolute_url = f"{self.target_scheme}:{url}"
            return self.rewrite_url(absolute_url, current_path)
        elif url.startswith('/'):  # 根相对路径
            return f"/proxy/{url.lstrip('/')}"
        else:  # 文档相对路径
            # 构建基于当前路径的绝对路径
            if base_path and not base_path.startswith('/'):
                base_path = f"/{base_path}"
            
            base_dir = '/'.join(base_path.split('/')[:-1]) if '/' in base_path else ''
            if base_dir:
                absolute_path = f"/{base_dir}/{url}"
            else:
                absolute_path = f"/{url}"
            
            # 规范化路径
            absolute_path = re.sub(r'/+/', '/', absolute_path)
            return f"/proxy/{absolute_path.lstrip('/')}"
    
    def do_GET(self):
        # 记录请求
        print(f"收到请求: {self.path}")
        
        # 处理代理路径
        if self.path.startswith('/proxy/'):
            original_path = self.path[7:]  # 移除'/proxy/'前缀
            target_full_url = f"{self.target_url.rstrip('/')}/{original_path.lstrip('/')}"
            current_path = self.path
        elif self.path == '/':
            target_full_url = self.target_url
            current_path = self.path
        else:
            target_full_url = f"{self.target_url.rstrip('/')}{self.path}"
            current_path = self.path
        
        print(f"代理到: {target_full_url}")
        
        try:
            # 设置请求头
            headers = {
                'Host': self.target_domain,
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # 添加Referer头（如果适用）
            if current_path and current_path != '/':
                referer_path = current_path.replace('/proxy/', '/')
                headers['Referer'] = f"{self.target_url}{referer_path}"
            
            # 创建请求
            req = urllib.request.Request(target_full_url, headers=headers)
            
            # 发起请求
            with urllib.request.urlopen(req, timeout=30) as response:
                # 读取响应内容
                content = response.read()
                content_type = response.headers.get('Content-Type', '').lower()
                
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
                
                # 重写内容（如果是文本类型）
                content = self.rewrite_content(content, content_type, current_path)
                
                # 发送响应
                self.send_response(response.status)
                
                # 复制响应头
                for key, value in response.headers.items():
                    key_lower = key.lower()
                    # 过滤不合适的头
                    if key_lower not in ['connection', 'transfer-encoding', 'content-encoding', 
                                       'content-length', 'strict-transport-security']:
                        # 重写一些特定的头
                        if key_lower == 'location':
                            value = self.rewrite_url(value, current_path)
                        self.send_header(key, value)
                
                # 更新内容长度
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                
                # 返回响应内容
                self.wfile.write(content)
                
                print(f"代理成功: {response.status} - {len(content)} bytes - {content_type}")
                
        except urllib.error.HTTPError as e:
            print(f"HTTP错误: {e.code} - {e.reason}")
            self.send_error(e.code, f"Proxy HTTP Error: {e.reason}")
        except urllib.error.URLError as e:
            print(f"URL错误: {e.reason}")
            self.send_error(502, f"Proxy URL Error: {e.reason}")
        except Exception as e:
            print(f"未知错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Proxy Error: {str(e)}")
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        message = format % args
        print(f"访问日志: {message}")


def get_target_url():
    """获取用户输入的代理目标网址"""
    print("=" * 60)
    print("   Cloud Shell 完整资源代理服务")
    print("=" * 60)
    
    while True:
        url = input("请输入要代理的完整网址 (例如: https://me.bendy.eu.org): ").strip()
        
        if not url:
            print("错误: 网址不能为空，请重新输入")
            continue
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"提示: 自动添加 https:// 前缀: {url}")
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            print("错误: 网址格式不正确，请重新输入")
            continue
            
        print(f"成功: 目标网址已设置: {url}")
        return url


def main():
    target_url = get_target_url()
    PORT = 60000
    
    # 创建自定义处理类
    class Handler(UniversalProxyHTTPRequestHandler):
        pass
    
    # 设置目标URL
    Handler.target_url = target_url
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("\n" + "=" * 60)
            print("完整资源代理服务已启动!")
            print(f"监听端口: {PORT}")
            print(f"代理目标: {target_url}")
            print("支持的资源类型:")
            print("  - HTML (href, src, action, style, data-* 等所有属性)")
            print("  - CSS (url(), @import, 内联样式)")
            print("  - JavaScript (字符串中的URL)")
            print("  - SVG (xlink:href, 样式等)")
            print("  - 图片 (img, srcset, 背景图)")
            print("  - 字体 (CSS @font-face)")
            print("  - 重定向 (Location头)")
            print("=" * 60)
            print("按 Ctrl+C 停止服务")
            print("=" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"\n\n错误: 端口 {PORT} 已被占用，请使用其他端口")
        else:
            print(f"\n\n系统错误: {str(e)}")
    except Exception as e:
        print(f"\n\n启动失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
