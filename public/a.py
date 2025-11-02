#!/usr/bin/env python3
"""
proxy_browser.py

单文件 HTTP 代理 + 简易浏览器外观（PyQt5）。
代理端口: 60000

依赖: PyQt5 PyQtWebEngine requests beautifulsoup4
pip install PyQt5 PyQtWebEngine requests beautifulsoup4
"""

import sys
import threading
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import traceback

# PyQt imports
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QLineEdit, QToolBar, QAction, QMainWindow
from PyQt5.QtCore import QUrl

LISTEN_ADDR = "127.0.0.1"
LISTEN_PORT = 60000
PROXY_BASE = f"http://{LISTEN_ADDR}:{LISTEN_PORT}"

# ---- Utility functions ----
def quote_url(u: str) -> str:
    return urllib.parse.quote_plus(u)

def unquote_url(q: str) -> str:
    return urllib.parse.unquote_plus(q)

def join_url(base, link):
    try:
        return urllib.parse.urljoin(base, link)
    except Exception:
        return link

# JS snippet to inject into proxied pages:
# - intercept fetch() and XMLHttpRequest and rewrite absolute/relative URLs to go through proxy
# - also add a small toolbar to return to homepage? (we already have GUI Home)
INJECT_JS = r"""
// Proxy interceptor injected by local proxy_browser
(function(){
    function toProxyUrl(u){
        // if url already goes to our proxy, leave it
        try{
            const p = new URL(u, location.href);
            if(p.hostname === location.hostname && location.port === "%PORT%") return u;
            // build proxied path
            return "%PROXY_BASE%/proxy?url=" + encodeURIComponent(p.href);
        }catch(e){
            return "%PROXY_BASE%/proxy?url=" + encodeURIComponent(u);
        }
    }

    // patch fetch
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

    // patch XMLHttpRequest
    const _open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url){
        try{
            const prox = toProxyUrl(url);
            return _open.apply(this, [method, prox, ...Array.prototype.slice.call(arguments,2)]);
        }catch(e){
            return _open.apply(this, arguments);
        }
    };

    // intercept form submits to ensure they go to proxy
    document.addEventListener('submit', function(ev){
        try{
            var f = ev.target;
            var action = f.getAttribute('action') || location.href;
            var absolute = new URL(action, location.href).href;
            f.setAttribute('action', "%PROXY_BASE%/proxy?url=" + encodeURIComponent(absolute));
        }catch(e){}
    }, true);

    // intercept link clicks (just to be safe)
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


# ---- HTTP proxy server handler ----
class SimpleProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # minimal logging
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

            # fallback: return 404
            self.send_error(404, "Not Found")
        except Exception as e:
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
        except Exception as e:
            traceback.print_exc()
            self.send_error(500, "Internal error")

    def serve_index(self):
        html = f"""<!doctype html>
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
  <p>示例：<a href="/proxy?url={quote_url('https://www.baidu.com')}">打开百度</a></p>
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
        b = html.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def forward_request(self, target_url, method="GET", body=None, headers=None):
        """Forward request to target_url and stream back response.
        For text/html responses, rewrite resource links to route through our /proxy?url=..."""
        try:
            # prepare headers for upstream
            up_headers = {}
            # copy certain client headers
            for h in ['User-Agent', 'Accept', 'Accept-Language', 'Cookie', 'Referer']:
                if h in self.headers:
                    up_headers[h] = self.headers[h]
            # prefer to request compressed content (server may return gzip) - requests handles it
            # perform request
            sess = requests.Session()
            req_kwargs = dict(headers=up_headers, stream=True, timeout=20)
            if method.upper() == "GET":
                resp = sess.get(target_url, **req_kwargs)
            else:
                # POST (forward content-type)
                if headers and 'Content-Type' in headers:
                    req_kwargs['headers']['Content-Type'] = headers['Content-Type']
                resp = sess.post(target_url, data=body, **req_kwargs)
        except Exception as e:
            traceback.print_exc()
            self.send_error(502, f"Bad Gateway when contacting {target_url}: {e}")
            return

        # send response status and headers (strip hop-by-hop headers)
        try:
            status = resp.status_code
            self.send_response(status)
            excluded = ['Transfer-Encoding', 'Connection', 'Content-Encoding', 'Keep-Alive', 'Proxy-Authenticate', 'Proxy-Authorization', 'TE', 'Trailer', 'Upgrade']
            # Copy headers but override content-length later
            content_type = resp.headers.get('Content-Type','')
            for k,v in resp.headers.items():
                if k in excluded: continue
                # don't forward original server cookies as-is? we forward Set-Cookie so client (our embedded browser) receives them
                self.send_header(k, v)
            # We'll compute content-length when writing
        except Exception as e:
            traceback.print_exc()

        # Handle HTML specially
        lower_ct = content_type.lower()
        if 'text/html' in lower_ct or 'application/xhtml+xml' in lower_ct:
            # decode content
            try:
                # let requests decode content
                content = resp.content
                # Attempt to decode with apparent encoding
                encoding = resp.encoding if resp.encoding else 'utf-8'
                text = content.decode(encoding, errors='replace')
            except Exception:
                text = resp.text

            # rewrite HTML: all href/src/action/form/etc should be proxied
            try:
                soup = BeautifulSoup(text, "html.parser")

                base_url = resp.url  # after redirects

                # rewrite tags with url attributes
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
                                # handle srcset specially (could be multiple)
                                if attr == 'srcset':
                                    try:
                                        parts = []
                                        for part in val.split(','):
                                            urlpart = part.strip().split(' ')[0]
                                            full = join_url(base_url, urlpart)
                                            prox = PROXY_BASE + "/proxy?url=" + quote_url(full)
                                            # preserve descriptor if any
                                            desc = part.strip()[len(urlpart):]
                                            parts.append(prox + desc)
                                        t[attr] = ", ".join(parts)
                                    except Exception:
                                        pass
                                    continue

                                # forms: if action is empty, use base_url
                                if val is None or val.strip() == '':
                                    full = base_url
                                else:
                                    full = join_url(base_url, val)
                                prox = PROXY_BASE + "/proxy?url=" + quote_url(full)
                                t[attr] = prox

                # rewrite inline JS urls like location.href assignments? hard - we inject JS that intercepts fetch/XHR and rewrites links on click/submit
                # Inject our proxy interceptor JS before </body>
                script_tag = soup.new_tag("script")
                script_tag.string = INJECT_JS
                if soup.body:
                    soup.body.insert(len(soup.body.contents), script_tag)
                else:
                    soup.insert(len(soup.contents), script_tag)

                out = str(soup)
                out_bytes = out.encode('utf-8')

                # send headers
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(out_bytes)))
                self.end_headers()
                self.wfile.write(out_bytes)
                return
            except Exception as e:
                traceback.print_exc()
                # fallthrough to streaming original content

        # For non-HTML or fallback: stream raw content
        try:
            # set content-length if available
            cl = resp.headers.get('Content-Length')
            if cl:
                self.send_header("Content-Length", cl)
            self.end_headers()
            # stream in chunks
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    self.wfile.write(chunk)
            return
        except Exception as e:
            traceback.print_exc()
            return

# ---- Start server in thread ----
def start_proxy_server():
    server = ThreadingHTTPServer((LISTEN_ADDR, LISTEN_PORT), SimpleProxyHandler)
    print(f"Starting proxy server at http://{LISTEN_ADDR}:{LISTEN_PORT}/")
    server.serve_forever()

# ---- PyQt GUI ----
class ProxyBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local Proxy Browser")
        self.resize(1000, 700)

        # toolbar with address bar and navigation
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
        self.url_edit.setPlaceholderText("在此输入原始 URL（例如 https://www.baidu.com）然后回车")
        toolbar.addWidget(self.url_edit)

        open_act = QAction("打开", self)
        open_act.triggered.connect(self.on_go)
        toolbar.addAction(open_act)

        # Web view
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # load homepage
        self.home_url = PROXY_BASE + "/"
        self.load_proxy(self.home_url)

        # when view url changes, keep address bar showing mapped "original" URL if available
        # we'll parse query param url=... if loaded /proxy?url=...
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
        # if user typed plain domain without scheme, add http://
        if text.startswith("www.") or ('.' in text and not text.startswith('http')):
            text = "http://" + text
        if not text.startswith("http://") and not text.startswith("https://"):
            text = "http://" + text
        prox = PROXY_BASE + "/proxy?url=" + quote_url(text)
        self.load_proxy(prox)

    def load_proxy(self, prox_url):
        self.view.setUrl(QUrl(prox_url))

    def on_view_url_changed(self, qurl):
        # when proxy loads /proxy?url=..., show decoded target in address bar for user friendliness
        try:
            s = qurl.toString()
            parsed = urllib.parse.urlparse(s)
            if parsed.path == "/proxy":
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get("url", [""])[0]
                if target:
                    self.url_edit.setText(unquote_url(target))
                    return
            if parsed.path == "/" or parsed.path == "/index.html":
                self.url_edit.setText("")
                return
            # otherwise set the edit to raw url
            self.url_edit.setText(s)
        except Exception:
            self.url_edit.setText(qurl.toString())


def main():
    # start proxy server thread
    server_thread = threading.Thread(target=start_proxy_server, daemon=True)
    server_thread.start()

    # start qt app
    app = QApplication(sys.argv)
    win = ProxyBrowserWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
