#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proxy_browser.py
兼容旧版 Python 的本地代理 + 简易浏览器外观
端口: 60000
"""

import sys
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import requests
from bs4 import BeautifulSoup
import traceback

# PyQt imports (如果在无 GUI 的服务器上运行，请不要启动 GUI)
from PyQt5 import QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QLineEdit, QToolBar, QAction, QMainWindow
from PyQt5.QtCore import QUrl

LISTEN_ADDR = "127.0.0.1"
LISTEN_PORT = 60000
PROXY_BASE = f"http://{LISTEN_ADDR}:{LISTEN_PORT}"

# Utility
def quote_url(u: str) -> str:
    return urllib.parse.quote_plus(u)

def unquote_url(q: str) -> str:
    return urllib.parse.unquote_plus(q)

def join_url(base, link):
    try:
        return urllib.parse.urljoin(base, link)
    except Exception:
        return link

# JS to inject
INJECT_JS = r"""
(function(){
    function toProxyUrl(u){
        try{
            const p = new URL(u, location.href);
            if(p.hostname === location.hostname && location.port === "%PORT%") return u;
            return "%PROXY_BASE%/proxy?url=" + encodeURIComponent(p.href);
        }catch(e){
            return "%PROXY_BASE%/proxy?url=" + encodeURIComponent(u);
        }
    }

    const _fetch = window.fetch;
    window.fetch = function(input, init){
        try{
            if(typeof input === 'string' || input instanceof String){
                input = toProxyUrl(input);
            } else if(input && input.url){
                input = new Request(toProxyUrl(input.url), input);
            }
        }catch(e){}
        return _fetch.call(this, input, init);
    }

    const _open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url){
        try{
            const prox = toProxyUrl(url);
            return _open.apply(this, [method, prox, ...Array.prototype.slice.call(arguments,2)]);
        }catch(e){
            return _open.apply(this, arguments);
        }
    };

    document.addEventListener('submit', function(ev){
        try{
            var f = ev.target;
            var action = f.getAttribute('action') || location.href;
            var absolute = new URL(action, location.href).href;
            f.setAttribute('action', "%PROXY_BASE%/proxy?url=" + encodeURIComponent(absolute));
        }catch(e){}
    }, true);

    document.addEventListener('click', function(ev){
        try{
            var a = ev.target.closest('a');
            if(!a) return;
            var href = a.getAttribute('href');
            if(!href) return;
            var absolute = new URL(href, location.href).href;
            a.setAttribute('href', "%PROXY_BASE%/proxy?url=" + encodeURIComponent(absolute));
        }catch(e){}
    }, true);
})();
""".replace("%PROXY_BASE%", PROXY_BASE).replace("%PORT%", str(LISTEN_PORT))


# Backwards-compatible Threading HTTPServer
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    # allow_reuse_address could be set if desired:
    allow_reuse_address = True

# HTTP handler (same logic as before)
class SimpleProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format%args))

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/" or parsed.path == "/index.html":
                self.serve_index()
                return
            if parsed.path == "/proxy":
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get("url", [""])[0]
                if not target:
                    self.send_error(400, "Missing url parameter")
                    return
                self.forward_request(target, method="GET")
                return
            self.send_error(404, "Not Found")
        except Exception:
            traceback.print_exc()
            self.send_error(500, "Internal error")

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/proxy":
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length>0 else b''
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get("url", [""])[0]
                if not target:
                    self.send_error(400, "Missing url parameter")
                    return
                self.forward_request(target, method="POST", body=body, headers=self.headers)
                return
            self.send_error(404, "Not Found")
        except Exception:
            traceback.print_exc()
            self.send_error(500, "Internal error")

    def serve_index(self):
        html = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Local Proxy Browser Home</title></head>
<body style="font-family: sans-serif; max-width:900px; margin:30px auto;">
  <h2>本地代理浏览器主页</h2>
  <p>在下面输入你要代理访问的完整 URL（以 http/https 开头），然后按 Enter 或点击“打开”。</p>
  <form id="openform" action="/proxy" method="get" onsubmit="return openURL();">
    <input id="url" name="url" style="width:85%" placeholder="https://www.example.com/" />
    <button type="submit">打开</button>
  </form>
  <hr>
  <p>示例：<a href="/proxy?url={BAIDU_ENC}">打开百度</a></p>
  <script>
    function openURL(){
      var u = document.getElementById('url').value;
      if(!u) return false;
      window.location = '/proxy?url=' + encodeURIComponent(u);
      return false;
    }
  </script>
</body>
</html>
"""
        html = html.replace("{BAIDU_ENC}", quote_url("https://www.baidu.com"))
        b = html.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def forward_request(self, target_url, method="GET", body=None, headers=None):
        try:
            up_headers = {}
            for h in ['User-Agent', 'Accept', 'Accept-Language', 'Cookie', 'Referer']:
                if h in self.headers:
                    up_headers[h] = self.headers[h]

            sess = requests.Session()
            req_kwargs = dict(headers=up_headers, stream=True, timeout=20)
            if method.upper() == "GET":
                resp = sess.get(target_url, **req_kwargs)
            else:
                if headers and 'Content-Type' in headers:
                    req_kwargs['headers']['Content-Type'] = headers['Content-Type']
                resp = sess.post(target_url, data=body, **req_kwargs)
        except Exception as e:
            traceback.print_exc()
            self.send_error(502, f"Bad Gateway when contacting {target_url}: {e}")
            return

        try:
            self.send_response(resp.status_code)
            excluded = ['Transfer-Encoding', 'Connection', 'Content-Encoding',
                        'Keep-Alive', 'Proxy-Authenticate', 'Proxy-Authorization',
                        'TE', 'Trailer', 'Upgrade']
            content_type = resp.headers.get('Content-Type','')
            for k,v in resp.headers.items():
                if k not in excluded:
                    self.send_header(k, v)
        except Exception:
            pass

        if 'text/html' in (content_type := resp.headers.get('Content-Type','')).lower() or 'application/xhtml+xml' in content_type.lower():
            try:
                content = resp.content
                encoding = resp.encoding if resp.encoding else 'utf-8'
                text = content.decode(encoding, errors='replace')
            except Exception:
                text = resp.text

            try:
                soup = BeautifulSoup(text, "html.parser")
                base_url = resp.url
                url_attrs = {
                    'a': ['href'],
                    'link': ['href'],
                    'img': ['src', 'srcset'],
                    'script': ['src'],
                    'iframe': ['src'],
                    'audio': ['src'],
                    'video': ['src', 'poster'],
                    'source': ['src', 'srcset'],
                    'form': ['action'],
                }
                for tag, attrs in url_attrs.items():
                    for t in soup.find_all(tag):
                        for attr in attrs:
                            if t.has_attr(attr):
                                val = t[attr]
                                if attr == 'srcset':
                                    parts = []
                                    for part in val.split(','):
                                        urlpart = part.strip().split(' ')[0]
                                        full = join_url(base_url, urlpart)
                                        prox = PROXY_BASE + "/proxy?url=" + quote_url(full)
                                        desc = part.strip()[len(urlpart):]
                                        parts.append(prox + desc)
                                    t[attr] = ", ".join(parts)
                                    continue
                                if not str(val).strip():
                                    full = base_url
                                else:
                                    full = join_url(base_url, val)
                                prox = PROXY_BASE + "/proxy?url=" + quote_url(full)
                                t[attr] = prox

                script_tag = soup.new_tag("script")
                script_tag.string = INJECT_JS
                if soup.body:
                    soup.body.insert(len(soup.body.contents), script_tag)
                else:
                    soup.insert(len(soup.contents), script_tag)

                out = str(soup)
                out_bytes = out.encode('utf-8')
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(out_bytes)))
                self.end_headers()
                self.wfile.write(out_bytes)
                return
            except Exception:
                traceback.print_exc()

        # fallback: stream binary content
        try:
            cl = resp.headers.get('Content-Length')
            if cl:
                self.send_header("Content-Length", cl)
            self.end_headers()
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    self.wfile.write(chunk)
        except Exception:
            traceback.print_exc()


# Start server thread
def start_proxy_server():
    server = ThreadingHTTPServer((LISTEN_ADDR, LISTEN_PORT), SimpleProxyHandler)
    print(f"代理服务器运行中：http://{LISTEN_ADDR}:{LISTEN_PORT}/")
    server.serve_forever()

# PyQt GUI
class ProxyBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("本地代理浏览器")
        self.resize(1000, 700)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        back_act = QAction("◀", self)
        back_act.triggered.connect(self.on_back)
        toolbar.addAction(back_act)

        forward_act = QAction("▶", self)
        forward_act.triggered.connect(self.on_forward)
        toolbar.addAction(forward_act)

        home_act = QAction("🏠", self)
        home_act.triggered.connect(self.on_home)
        toolbar.addAction(home_act)

        self.url_edit = QLineEdit()
        self.url_edit.returnPressed.connect(self.on_go)
        self.url_edit.setPlaceholderText("输入网址，如 https://www.baidu.com")
        toolbar.addWidget(self.url_edit)

        open_act = QAction("打开", self)
        open_act.triggered.connect(self.on_go)
        toolbar.addAction(open_act)

        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        self.home_url = PROXY_BASE + "/"
        self.load_proxy(self.home_url)
        self.view.urlChanged.connect(self.on_view_url_changed)

    def on_back(self):
        self.view.back()

    def on_forward(self):
        self.view.forward()

    def on_home(self):
        self.load_proxy(self.home_url)
        self.url_edit.setText("")

    def on_go(self):
        text = self.url_edit.text().strip()
        if not text:
            return
        if text.startswith("www.") or ('.' in text and not text.startswith('http')):
            text = "http://" + text
        if not text.startswith("http://") and not text.startswith("https://"):
            text = "http://" + text
        prox = PROXY_BASE + "/proxy?url=" + quote_url(text)
        self.load_proxy(prox)

    def load_proxy(self, prox_url):
        self.view.setUrl(QUrl(prox_url))

    def on_view_url_changed(self, qurl):
        try:
            s = qurl.toString()
            parsed = urllib.parse.urlparse(s)
            if parsed.path == "/proxy":
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get("url", [""])[0]
                if target:
                    self.url_edit.setText(unquote_url(target))
                    return
            if parsed.path in ["/", "/index.html"]:
                self.url_edit.setText("")
                return
            self.url_edit.setText(s)
        except Exception:
            self.url_edit.setText(qurl.toString())

def main():
    server_thread = threading.Thread(target=start_proxy_server, daemon=True)
    server_thread.start()
    app = QApplication(sys.argv)
    win = ProxyBrowserWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
