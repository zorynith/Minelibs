#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple HTTP Proxy Browser
Compatible with Python 3.6+
Port: 60000
"""

import sys
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import requests
from bs4 import BeautifulSoup
import traceback

LISTEN_ADDR = "127.0.0.1"
LISTEN_PORT = 60000
PROXY_BASE = "http://%s:%d" % (LISTEN_ADDR, LISTEN_PORT)

def quote_url(u):
    return urllib.parse.quote_plus(u)

def join_url(base, link):
    try:
        return urllib.parse.urljoin(base, link)
    except Exception:
        return link

# JS injection for proxying links, forms, fetch/XHR
INJECT_JS = """
(function(){
    function toProxyUrl(u){
        try{
            var p = new URL(u, location.href);
            if(p.hostname === location.hostname && location.port === "%PORT%") return u;
            return "%PROXY_BASE%/proxy?url=" + encodeURIComponent(p.href);
        }catch(e){
            return "%PROXY_BASE%/proxy?url=" + encodeURIComponent(u);
        }
    }

    var _fetch = window.fetch;
    window.fetch = function(input, init){
        try{
            if(typeof input === 'string' || input instanceof String){
                input = toProxyUrl(input);
            } else if(input && input.url){
                input = new Request(toProxyUrl(input.url), input);
            }
        }catch(e){}
        return _fetch.call(this, input, init);
    };

    var _open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url){
        try{
            var prox = toProxyUrl(url);
            return _open.apply(this, [method, prox].concat(Array.prototype.slice.call(arguments,2)));
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


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class SimpleProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format % args))

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
                self.forward_request(target, "GET")
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
                body = self.rfile.read(length) if length > 0 else b''
                qs = urllib.parse.parse_qs(parsed.query)
                target = qs.get("url", [""])[0]
                if not target:
                    self.send_error(400, "Missing url parameter")
                    return
                self.forward_request(target, "POST", body, self.headers)
                return
            self.send_error(404, "Not Found")
        except Exception:
            traceback.print_exc()
            self.send_error(500, "Internal error")

    def serve_index(self):
        html = """<!doctype html>
<html>
<head><meta charset="utf-8"><title>Local Proxy Browser</title></head>
<body style="font-family: sans-serif; max-width:900px; margin:30px auto;">
  <h2>Local Proxy Browser</h2>
  <form id="openform" action="/proxy" method="get" onsubmit="return openURL();">
    <input id="url" name="url" style="width:85%" placeholder="https://www.example.com/" />
    <button type="submit">Open</button>
  </form>
  <hr>
  <p>Example: <a href="/proxy?url={BAIDU_ENC}">Open Baidu</a></p>
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
        b = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def forward_request(self, target_url, method="GET", body=None, headers=None):
        try:
            up_headers = {}
            for h in ["User-Agent", "Accept", "Accept-Language", "Cookie", "Referer"]:
                if h in self.headers:
                    up_headers[h] = self.headers[h]

            sess = requests.Session()
            req_kwargs = dict(headers=up_headers, stream=True, timeout=20)
            if method.upper() == "GET":
                resp = sess.get(target_url, **req_kwargs)
            else:
                if headers and "Content-Type" in headers:
                    req_kwargs["headers"]["Content-Type"] = headers["Content-Type"]
                resp = sess.post(target_url, data=body, **req_kwargs)
        except Exception as e:
            traceback.print_exc()
            self.send_error(502, "Bad Gateway: %s" % e)
            return

        content_type = resp.headers.get("Content-Type", "")
        self.send_response(resp.status_code)
        for k, v in resp.headers.items():
            if k.lower() not in ["transfer-encoding", "connection", "content-encoding",
                                 "keep-alive", "proxy-authenticate", "proxy-authorization",
                                 "te", "trailer", "upgrade"]:
                self.send_header(k, v)

        if "text/html" in content_type.lower() or "application/xhtml+xml" in content_type.lower():
            try:
                text = resp.text
                soup = BeautifulSoup(text, "html.parser")
                base_url = resp.url
                url_attrs = {
                    "a": ["href"],
                    "link": ["href"],
                    "img": ["src", "srcset"],
                    "script": ["src"],
                    "iframe": ["src"],
                    "audio": ["src"],
                    "video": ["src", "poster"],
                    "source": ["src", "srcset"],
                    "form": ["action"],
                }
                for tag, attrs in url_attrs.items():
                    for t in soup.find_all(tag):
                        for attr in attrs:
                            if t.has_attr(attr):
                                val = t[attr]
                                if attr == "srcset":
                                    parts = []
                                    for part in val.split(","):
                                        urlpart = part.strip().split(" ")[0]
                                        full = join_url(base_url, urlpart)
                                        prox = PROXY_BASE + "/proxy?url=" + quote_url(full)
                                        desc = part.strip()[len(urlpart):]
                                        parts.append(prox + desc)
                                    t[attr] = ", ".join(parts)
                                    continue
                                full = join_url(base_url, val)
                                prox = PROXY_BASE + "/proxy?url=" + quote_url(full)
                                t[attr] = prox

                script_tag = soup.new_tag("script")
                script_tag.string = INJECT_JS
                if soup.body:
                    soup.body.insert(len(soup.body.contents), script_tag)
                else:
                    soup.insert(len(soup.contents), script_tag)

                out_bytes = str(soup).encode("utf-8")
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(out_bytes)))
                self.end_headers()
                self.wfile.write(out_bytes)
                return
            except Exception:
                traceback.print_exc()

        cl = resp.headers.get("Content-Length")
        if cl:
            self.send_header("Content-Length", cl)
        self.end_headers()
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                self.wfile.write(chunk)


def start_server():
    server = ThreadingHTTPServer((LISTEN_ADDR, LISTEN_PORT), SimpleProxyHandler)
    print("Proxy running at: %s:%d" % (LISTEN_ADDR, LISTEN_PORT))
    server.serve_forever()


if __name__ == "__main__":
    start_server()
