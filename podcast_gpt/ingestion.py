"""Bounded local source text extraction and opt-in public HTTPS retrieval.

Only trusted user-selected documents. No OCR, macros, Javascript, browser,
redirects, credentials, proxy, or local/private network URLs. No AI calls.
"""
from __future__ import annotations

import hashlib
import http.client
import io
import ipaddress
import re
import socket
import ssl
import stat
import time
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

from . import source

MAX_FILE=8_000_000
MAX_WEB=1_000_000
MAX_TEXT=12_000
MAX_PAGES=30
INPUT_KINDS=("pdf","document","custom_script","url")


def _sha(data:bytes):
    return hashlib.sha256(data).hexdigest()


def _clean(text):
    if not isinstance(text,str):raise ValueError("No readable source text")
    text=text.replace("\r\n","\n").replace("\r","\n").strip()
    if not text or "\x00" in text:raise ValueError("No readable source text; scanned files need manual transcription")
    if len(text)>MAX_TEXT:raise ValueError("Source exceeds 12000 characters; select a smaller excerpt (no silent truncation)")
    return text


def _file(path:Path):
    path=Path(path).expanduser().absolute()
    for item in (path,*path.parents):
        st=item.lstat()
        if stat.S_ISLNK(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:
            raise ValueError("Source symlink/reparse point refused")
    if not path.is_file() or path.stat().st_size>MAX_FILE:
        raise ValueError("Select a regular source file of at most 8 MB")
    with path.open("rb") as handle:
        raw=handle.read(MAX_FILE+1)
    if len(raw)>MAX_FILE:raise ValueError("Source file size limit exceeded")
    return path,raw


def _docx(raw):
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            entries=z.infolist()
            if len(entries)>1000 or sum(i.file_size for i in entries)>24_000_000:
                raise ValueError("DOCX decompressed size limit exceeded")
            names=z.namelist()
            if len(names)!=len(set(names)) or "word/document.xml" not in names:
                raise ValueError("Invalid DOCX document package")
            xml=z.read("word/document.xml")
            if len(xml)>4_000_000:raise ValueError("Unsafe or oversized DOCX XML")
            try:text=xml.decode("utf-8-sig")
            except UnicodeError:raise ValueError("DOCX XML must be UTF-8") from None
            if "\x00" in text or re.search(r"<!\s*(?:DOCTYPE|ENTITY)",text,re.I):
                raise ValueError("Unsafe DOCX XML")
            root=ElementTree.fromstring(text)
    except (zipfile.BadZipFile,ElementTree.ParseError,RuntimeError,KeyError):
        raise ValueError("Unable to parse DOCX text") from None
    ns="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    return "\n".join("".join(t.text or "" for t in p.iter(ns+"t")) for p in root.iter(ns+"p"))


def _pdf(raw):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ValueError("Install optional free document extra: python -m pip install -e .[documents]") from None
    try:
        reader=PdfReader(io.BytesIO(raw),strict=True)
        if reader.is_encrypted:raise ValueError("Encrypted PDF unsupported")
        if len(reader.pages)>MAX_PAGES:raise ValueError("Select at most 30 PDF pages")
        parts=[];count=0
        for page in reader.pages:
            text=page.extract_text() or ""
            count+=len(text)
            if count>MAX_TEXT:raise ValueError("PDF text exceeds 12000 characters")
            parts.append(text)
        return "\n".join(parts)
    except ValueError:raise
    except Exception:
        raise ValueError("Unable to extract PDF text; use a trusted text-based PDF") from None


class _HTML(HTMLParser):
    SKIP={"script","style","noscript","template","svg","head","iframe"}
    BLOCK={"p","div","br","li","article","section","h1","h2","h3","tr","blockquote"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignored=[]
        self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in self.SKIP:self.ignored.append(tag)
        elif not self.ignored and tag in self.BLOCK:self.parts.append("\n")
    def handle_endtag(self,tag):
        if self.ignored:
            if tag==self.ignored[-1]:self.ignored.pop()
        elif tag in self.BLOCK:self.parts.append("\n")
    def handle_data(self,data):
        if not self.ignored:self.parts.append(data)


def _public_ip(value):
    ip=ipaddress.ip_address(value)
    return (ip.is_global and not ip.is_multicast and not ip.is_reserved
            and not ip.is_loopback and not ip.is_link_local
            and not getattr(ip,"ipv4_mapped",None) and not getattr(ip,"scope_id",None))


def _target(url,resolver=socket.getaddrinfo):
    if not isinstance(url,str) or len(url)>2048 or any(ord(c)<33 or ord(c)>126 for c in url) or "\\" in url:
        raise ValueError("Use a plain ASCII public HTTPS URL")
    u=urlsplit(url)
    if (u.scheme!="https" or not u.hostname or u.username is not None or u.password is not None
            or u.port not in (None,443) or u.fragment or u.query):
        raise ValueError("Public HTTPS only; no credentials, nonstandard port, fragment or query")
    host=u.hostname
    if not re.fullmatch(r"[a-zA-Z0-9.-]{1,253}",host) or "." not in host or host.endswith("."):
        raise ValueError("Public HTTPS hostname required")
    try:
        addresses=resolver(host,443,type=socket.SOCK_STREAM)
        ips=sorted({a[4][0] for a in addresses})
    except OSError:
        raise ValueError("Public source DNS resolution failed") from None
    if not ips or not all(_public_ip(ip) for ip in ips):
        raise ValueError("Private, local, reserved or mixed DNS addresses refused")
    return host,u.path or "/",ips[0]


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,ip):
        super().__init__(host,443,timeout=12,context=ssl.create_default_context())
        self.ip=ip
    def connect(self):
        # DNS is checked once and the connection is pinned to that numeric IP.
        # TLS certificate and SNI still use the original public hostname.
        sock=socket.create_connection((self.ip,443),timeout=12)
        try:self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def fetch_public(url):
    host,path,ip=_target(url)
    conn=_PinnedHTTPS(host,ip)
    try:
        conn.request("GET",path,headers={"Accept":"text/html,text/plain","Accept-Encoding":"identity",
                     "User-Agent":"PodcastGPT-PersonalSourceReader/1.0","Connection":"close"})
        with conn.getresponse() as r:
            if r.status!=200:raise ValueError("Source HTTP response must be 200; redirects not followed")
            if r.getheader("Content-Encoding","identity").lower()!="identity":
                raise ValueError("Compressed HTTP response unsupported")
            content=r.headers.get_content_type()
            charset=r.headers.get_content_charset() or "utf-8"
            if content not in ("text/html","text/plain"):raise ValueError("URL must return HTML or plain text")
            if charset.lower() not in ("utf-8","utf8","us-ascii","ascii","iso-8859-1","windows-1252"):
                raise ValueError("Unsupported source charset")
            parts=[];size=0;start=time.monotonic()
            while True:
                if time.monotonic()-start>30:raise ValueError("Source read time limit exceeded")
                chunk=r.read1(min(65536,MAX_WEB+1-size))
                if not chunk:break
                size+=len(chunk)
                if size>MAX_WEB:raise ValueError("Public source exceeds 1 MB")
                parts.append(chunk)
            return b"".join(parts),content,charset
    except (OSError,http.client.HTTPException,UnicodeError):
        raise ValueError("Public HTTPS retrieval failed") from None
    finally:conn.close()


def extract(kind,*,path=None,url=None,allow_web_fetch=False,fetcher=None):
    if kind not in INPUT_KINDS:raise ValueError("Unsupported input kind")
    if kind=="url":
        if path is not None or not url or allow_web_fetch is not True:
            raise ValueError("URL source requires explicit --allow-web-fetch and URL only")
        raw,mime,charset=(fetcher or fetch_public)(url)
        if len(raw)>MAX_WEB:raise ValueError("Public source exceeds 1 MB")
        text=raw.decode(charset,errors="strict")
        if mime=="text/html":
            parser=_HTML();parser.feed(text);parser.close()
            text="\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())
        elif mime!="text/plain":raise ValueError("Unsupported public text content")
        locator=url
    else:
        if path is None or url is not None:raise ValueError("Select one local source file")
        p,raw=_file(path)
        ext=p.suffix.lower()
        if kind=="pdf" and ext==".pdf":text=_pdf(raw)
        elif kind=="document" and ext==".docx":text=_docx(raw)
        elif kind in ("document","custom_script") and ext in (".txt",".md"):
            text=raw.decode("utf-8-sig",errors="strict")
        else:raise ValueError("Select matching PDF, DOCX, UTF-8 TXT or Markdown")
        locator=p.name
    text=_clean(text)
    return {"schema":1,"kind":kind,"locator":locator,"raw_sha256":_sha(raw),
            "text_sha256":_sha(text.encode("utf-8")),"text":text,
            "captured_utc":datetime.now(timezone.utc).isoformat()}


def validate(record,kind):
    keys={"schema","kind","locator","raw_sha256","text_sha256","text","captured_utc"}
    if not isinstance(record,dict) or set(record)!=keys or record.get("schema")!=1 or record.get("kind")!=kind:
        raise ValueError("Invalid source evidence record")
    if any(not isinstance(record[k],str) or not record[k] for k in keys-{"schema"}):
        raise ValueError("Invalid source metadata")
    text=_clean(record["text"])
    if text!=record["text"] or _sha(text.encode("utf-8"))!=record["text_sha256"] or not re.fullmatch(r"[0-9a-f]{64}",record["raw_sha256"]):
        raise ValueError("Source evidence text hash differs")
    return record
