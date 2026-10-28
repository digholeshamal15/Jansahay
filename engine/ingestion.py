"""Module A: Data Ingestion, Web Scraping, File Uploads, Dataset Importers, and Deduplication."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import requests
from engine.preprocessing import normalize_text, tokenize_words

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "JanSahayStudentProject/2.0 (Civic Intelligence and Academic NLP Research)"

# Mapping HuffPost News categories to JanSahay issue categories
HUFFPOST_TO_JANSAHAY = {
    'ENVIRONMENT': 'environment',
    'GREEN': 'environment',
    'WELLNESS': 'health',
    'HEALTHY LIVING': 'health',
    'CRIME': 'public_safety',
    'WORLD NEWS': 'governance',
    'POLITICS': 'governance',
    'TECH': 'electricity',
    'BUSINESS': 'governance',
    'TRAVEL': 'roads'
}

def calculate_sha256(text: str) -> str:
    """Calculate SHA-256 hash of normalized text for exact deduplication."""
    norm = normalize_text(text)
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()

def check_duplicate(text: str, existing_docs: list[dict], threshold: float = 0.85) -> dict:
    """Check if document is an exact or near duplicate of any existing document."""
    new_hash = calculate_sha256(text)
    new_words = set(tokenize_words(text))
    
    for doc in existing_docs:
        # 1. Exact hash duplicate
        if doc.get('sha256') == new_hash:
            return {
                'is_duplicate': True,
                'duplicate_type': 'exact',
                'matched_doc_id': doc.get('id'),
                'similarity': 1.0,
                'note': f"Exact duplicate of existing document #{doc.get('id')}."
            }
            
        # 2. Near-duplicate via Jaccard token overlap
        if new_words and doc.get('text'):
            existing_words = set(tokenize_words(doc['text']))
            if existing_words:
                intersection = len(new_words & existing_words)
                union = len(new_words | existing_words)
                jaccard = intersection / max(1, union)
                if jaccard >= threshold:
                    return {
                        'is_duplicate': True,
                        'duplicate_type': 'near_duplicate',
                        'matched_doc_id': doc.get('id'),
                        'similarity': round(jaccard, 3),
                        'note': f"Near-duplicate ({round(jaccard*100, 1)}% token overlap) of document #{doc.get('id')}."
                    }
                    
    return {'is_duplicate': False, 'similarity': 0.0}

def parse_csv_content(content_str: str) -> list[dict]:
    """Parse uploaded CSV data into standardized document dictionaries."""
    reader = csv.DictReader(io.StringIO(content_str))
    documents = []
    
    # Auto-detect field names
    for row in reader:
        # Find text column
        text = row.get('text') or row.get('grievance_text') or row.get('body') or row.get('content') or row.get('description') or ''
        text = text.strip()
        if not text:
            continue
            
        title = row.get('title') or row.get('headline') or row.get('subject') or (text[:60] + '...')
        category = row.get('category') or row.get('department') or row.get('topic') or 'other'
        location = row.get('location') or row.get('city') or row.get('locality') or 'unknown'
        lang = row.get('lang') or row.get('language') or 'en'
        source = row.get('source') or 'CSV Upload'
        
        documents.append({
            'title': title.strip(),
            'text': text,
            'category': category.strip().lower(),
            'location': location.strip(),
            'lang': lang.strip().lower(),
            'source': source.strip(),
            'source_type': 'csv_upload',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'sha256': calculate_sha256(text)
        })
    return documents

def parse_txt_content(content_str: str, filename: str = 'uploaded.txt') -> list[dict]:
    """Parse uploaded TXT file. If paragraphs or separators exist, splits into reports."""
    norm = normalize_text(content_str)
    if not norm:
        return []
        
    paragraphs = [p.strip() for p in re.split(r'\n{2,}|\r\n{2,}', norm) if len(p.strip()) > 20]
    
    if not paragraphs:
        paragraphs = [norm]
        
    docs = []
    for idx, p in enumerate(paragraphs):
        first_line = p.splitlines()[0][:60]
        title = f"{filename}: {first_line}..." if len(paragraphs) > 1 else f"{filename} (Imported)"
        docs.append({
            'title': title,
            'text': p,
            'category': 'other',
            'location': 'unknown',
            'lang': 'en',
            'source': filename,
            'source_type': 'txt_upload',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'sha256': calculate_sha256(p)
        })
    return docs

def scrape_web_page(url: str, timeout: int = 15) -> dict:
    """Safely fetch and extract article title and readable body from a permitted public HTTPS URL."""
    u = urlsplit(url)
    if u.scheme != 'https' or not u.hostname:
        raise ValueError("Only public https:// URLs are supported.")
        
    # Check robots.txt
    robots_url = urlunsplit((u.scheme, u.netloc, '/robots.txt', '', ''))
    try:
        r_resp = requests.get(robots_url, headers={'User-Agent': USER_AGENT}, timeout=5)
        if r_resp.status_code == 200:
            rfp = RobotFileParser()
            rfp.parse(r_resp.text.splitlines())
            if not rfp.can_fetch(USER_AGENT, url):
                raise ValueError("robots.txt on target host disallows automated access to this page.")
    except (requests.RequestException, OSError):
        pass  # Proceed if robots.txt unreachable
        
    # Fetch page
    headers = {'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    
    if 'text/html' not in response.headers.get('Content-Type', '').lower():
        raise ValueError("Target URL did not return an HTML document.")
        
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Strip non-content elements
    for tag in soup(['script', 'style', 'noscript', 'nav', 'header', 'footer', 'aside', 'svg']):
        tag.decompose()
        
    title = soup.title.get_text(' ', strip=True) if soup.title else 'Scraped Article'
    
    # Extract main content container
    main_el = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|post', re.I)) or soup.body or soup
    body_text = ' '.join(main_el.stripped_strings)
    
    # Normalize
    body_text = normalize_text(body_text)[:20000]
    if len(body_text) < 40:
        raise ValueError("Insufficient readable body text found on the page (possible client-side JavaScript rendering).")
        
    return {
        'title': title[:160],
        'text': body_text,
        'category': 'other',
        'location': 'unknown',
        'lang': 'en',
        'source': url,
        'source_type': 'web_scrape',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'sha256': calculate_sha256(body_text)
    }

def load_bundled_service_dataset(limit: int = 150) -> list[dict]:
    """Load records from data/service_train.json into standardized document format."""
    path = ROOT / 'data/service_train.json'
    if not path.exists():
        path = ROOT / 'data/training.json'
    if not path.exists():
        return []
        
    raw = json.loads(path.read_text(encoding='utf-8'))
    docs = []
    
    # Take representative slice across categories and languages
    for idx, r in enumerate(raw[:limit]):
        text = r.get('text', '').strip()
        if not text:
            continue
        first_line = text[:60] + '...'
        docs.append({
            'id': f"civic_{idx+1}",
            'title': f"Report #{idx+1}: {first_line}",
            'text': text,
            'category': r.get('category', 'other'),
            'location': r.get('location', 'Maharashtra'),
            'lang': r.get('lang', 'en'),
            'source': r.get('source', 'JanSahay Civic Grievance Dataset'),
            'source_type': 'bundled_dataset',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'sha256': calculate_sha256(text)
        })
    return docs

def load_huffpost_sample() -> list[dict]:
    """Load curated HuffPost News Category sample items mapped to JanSahay categories."""
    huffpost_sample_data = [
        {
            "headline": "Massive Flash Floods Submerge Key Urban Arterial Roads Following Monsoonal Deluge",
            "short_description": "Commuters stranded as severe waterlogging inundated underpasses, leaving vehicles submerged and disrupting public transportation routes across the district.",
            "category": "ENVIRONMENT",
            "date": "2018-05-24"
        },
        {
            "headline": "City Residents Protest Persistent Drinking Water Shortages and Contaminated Pipelines",
            "short_description": "Neighborhood associations reported brown tap water and zero supply for five consecutive days, prompting emergency tanker requests to municipal authorities.",
            "category": "ENVIRONMENT",
            "date": "2017-09-12"
        },
        {
            "headline": "Emergency Response Stalled as Neglected Potholes and Debris Block Primary Ambulance Access",
            "short_description": "Paramedics cited severe delays reaching critical patients after main access roads were obstructed by unpaved excavations and deep road craters.",
            "category": "CRIME",
            "date": "2016-11-04"
        },
        {
            "headline": "Power Grid Failure Causes Widespread Blackout Across Five Sectors for Over 18 Hours",
            "short_description": "Overheating substation transformers triggered sudden electrical outages, leaving streetlights dark and traffic signals inoperative throughout the night.",
            "category": "TECH",
            "date": "2018-02-19"
        },
        {
            "headline": "Overflowing Open Dumps and Uncollected Waste Spark Urgent Dengue and Health Warnings",
            "short_description": "Health inspectors warned of disease outbreaks as municipal sanitation workers failed to collect accumulating waste bins outside residential clusters.",
            "category": "WELLNESS",
            "date": "2017-08-30"
        },
        {
            "headline": "Citizens Demand Public Hearing Over Two-Year Delay in Drainage Canal Construction",
            "short_description": "Administrative records reveal repeated budget allocations for storm-water drainage projects without any physical ground inspection or progress report.",
            "category": "POLITICS",
            "date": "2015-06-18"
        }
    ]
    
    docs = []
    for idx, item in enumerate(huffpost_sample_data):
        full_text = f"{item['headline']}. {item['short_description']}"
        mapped_cat = HUFFPOST_TO_JANSAHAY.get(item['category'], 'other')
        docs.append({
            'id': f"huffpost_{idx+1}",
            'title': item['headline'],
            'text': full_text,
            'category': mapped_cat,
            'location': 'Metro Region',
            'lang': 'en',
            'source': f"HuffPost News ({item['category']})",
            'source_type': 'huffpost_dataset',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'sha256': calculate_sha256(full_text),
            'metadata': {
                'original_category': item['category'],
                'published_date': item['date'],
                'mapping_reason': f"HuffPost '{item['category']}' category mapped to JanSahay '{mapped_cat}' infrastructure domain."
            }
        })
    return docs
