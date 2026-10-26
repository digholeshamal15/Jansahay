"""Assignment 1: fetch ONE public HTML page with robots.txt and attribution.
Run manually; no automatic scheduled scraping or network access from the UI.
"""
import argparse
from datetime import datetime,timezone
import ipaddress
import json
from pathlib import Path
import socket
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

AGENT='JanSahayStudentProject/1.0'

def public_url(url):
    u=urlsplit(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.port not in (None,443):
        raise ValueError('Use a public https:// URL without credentials or a custom port')
    addresses=socket.getaddrinfo(u.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Only public hosts are supported')
    return u

def fetch(url,limit=2_000_000):
    public_url(url)
    with requests.get(url,headers={'User-Agent':AGENT},timeout=(5,15),allow_redirects=False,stream=True) as response:
        if response.status_code==404:return '',404,''
        if 300<=response.status_code<400:raise ValueError('Redirect encountered. Supply the final public HTTPS URL explicitly.')
        response.raise_for_status(); chunks=[];size=0
        for chunk in response.iter_content(8192):
            size+=len(chunk)
            if size>limit:raise ValueError('Page too large')
            chunks.append(chunk)
        return b''.join(chunks).decode(response.encoding or 'utf-8',errors='replace'),response.status_code,response.headers.get('Content-Type','')

def extract(html):
    soup=BeautifulSoup(html,'html.parser');title=soup.title.get_text(' ',strip=True) if soup.title else 'Imported page'
    for tag in soup(['script','style','noscript','nav','header','footer']):tag.decompose()
    main=soup.find('main') or soup.find('article') or soup.body or soup
    return title,' '.join(main.stripped_strings)[:12000]

def scrape(url,lang,output):
    u=public_url(url);robots_url=urlunsplit((u.scheme,u.netloc,'/robots.txt','',''))
    content,status,_=fetch(robots_url,500_000)
    if status!=404:
        robot=RobotFileParser();robot.parse(content.splitlines())
        if not robot.can_fetch(AGENT,url):raise ValueError('robots.txt disallows this page')
    html,status,mime=fetch(url)
    if status!=200 or 'text/html' not in mime.lower():raise ValueError('An HTML page returning HTTP 200 is required')
    title,text=extract(html)
    if not text:raise ValueError('No readable text found; JavaScript-only pages are unsupported')
    path=Path(output);rows=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    rows=[r for r in rows if r.get('source')!=url]
    rows.append(dict(title=title,text=text,display=text[:600],lang=lang,source=url,fetched_at=datetime.now(timezone.utc).isoformat(),category='external'))
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    return len(text)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('url');p.add_argument('--lang',choices=['en','hi','mr'],required=True);p.add_argument('--output',default=str(Path(__file__).resolve().parents[1]/'data/scraped.json'));a=p.parse_args()
    try:print(f'Saved {scrape(a.url,a.lang,a.output)} characters with source attribution. Restart the app to index the page.')
    except (ValueError,OSError,requests.RequestException) as e:raise SystemExit(f'Scraping failed: {e}')
