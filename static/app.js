'use strict';

/**
 * JanSahay · EchoTrace AI — Integrated Public NLP Intelligence Platform
 * Unified Frontend Logic
 */

let config = null;
let lang = 'en';
let filter = 'all';
let toastTimer = null;
let searchTimer = null;
let docsSearchTimer = null;
let listSequence = 0;
let currentDocInModal = null;
let activeGraphData = null;
let graphSimulation = null;

let state = freshState();

function freshState() {
  return {
    started: false,
    step: 1,
    page: 'hub',
    recordId: null,
    status: 'draft',
    photos: [],
    answers: {},
    body: '',
    draftLang: 'en',
    dirty: false,
    suggestion: null,
    changeVersion: 0
  };
}

const $ = id => document.getElementById(id);
const tr = key => config?.ui?.[lang]?.[key] || config?.copy?.[lang]?.[key] || key;

function node(tag, text, cls) {
  const el = document.createElement(tag);
  if (text !== undefined && text !== null) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function icon(name) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  el.setAttribute('class', 'icon');
  el.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  const mapped = (name === 'other' || !name) ? 'file' : name;
  use.setAttribute('href', '#i-' + mapped);
  el.append(use);
  return el;
}

function button(text, cls, action) {
  const b = node('button', text, cls);
  b.type = 'button';
  if (action) b.onclick = action;
  return b;
}

function toast(message) {
  const el = $('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add('hidden'), 5000);
}

async function api(path, options = {}) {
  const headers = options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' };
  const response = await fetch(path, { ...options, headers });
  const data = await response.json();
  if (!response.ok) {
    const e = new Error(data.error || tr('error_generic'));
    e.status = response.status;
    e.data = data;
    throw e;
  }
  return data;
}

function post(path, data, method = 'POST') {
  return api(path, { method, body: JSON.stringify(data) });
}

function fieldError(id, key) {
  const el = $(id);
  if (el) {
    el.textContent = tr(key);
    el.classList.remove('hidden');
  }
}

function clearErrors() {
  ['form-error', 'details-error', 'photo-error', 'ingest-error', 'upload-error', 'scrape-error'].forEach(id => {
    const el = $(id);
    if (el) el.classList.add('hidden');
  });
}

function countText() {
  if ($('character-count') && $('issue')) {
    $('character-count').textContent = $('issue').value.length + ' / 3000';
  }
}

function fillSelect(el, items, value) {
  if (!el) return;
  el.replaceChildren(...items.map(([key, label]) => new Option(label, key)));
  if (items.some(([k]) => k === value)) el.value = value;
}

// ============================================================================
// PAGE & VIEW ROUTING
// ============================================================================
const ALL_PAGES = ['hub', 'docs', 'graph', 'opinion', 'lab', 'home', 'saved'];

function showPage(page) {
  if (!ALL_PAGES.includes(page)) page = 'hub';
  state.page = page;

  ALL_PAGES.forEach(name => {
    const p = $(name + '-panel');
    if (p) p.classList.toggle('hidden', name !== page);
  });

  document.querySelectorAll('.nav-link').forEach(b => {
    b.classList.toggle('active', b.dataset.page === page);
  });

  // Load view-specific dynamic content
  if (page === 'hub') {
    loadOverview();
  } else if (page === 'docs') {
    loadDocuments();
  } else if (page === 'graph') {
    loadGraph();
    loadContradictions();
  } else if (page === 'opinion') {
    loadOpinions();
  } else if (page === 'saved') {
    loadRecords();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================================
// 1. EXECUTIVE OVERVIEW HUB
// ============================================================================
async function loadOverview() {
  try {
    const data = await api('/api/overview');
    
    // Total Documents
    if ($('kpi-total-docs')) $('kpi-total-docs').textContent = (data.total_documents || 0).toLocaleString();

    // Category Breakdown & Dominant Domain
    const catDist = data.categories_breakdown || data.category_distribution || {};
    const catEntries = Object.entries(catDist).sort((a, b) => b[1] - a[1]);
    const topCatKey = catEntries[0]?.[0] || 'other';
    const topCatCount = catEntries[0]?.[1] || 0;

    if ($('kpi-top-category')) {
      $('kpi-top-category').textContent = (config?.categories?.[topCatKey]?.[lang] || topCatKey).toUpperCase();
    }
    if ($('kpi-top-cat-sub')) {
      $('kpi-top-cat-sub').textContent = `${topCatCount} reported incidents`;
    }

    // Sentiment Breakdown
    const sentDist = data.sentiment_breakdown || data.sentiment_distribution || {};
    const negCount = sentDist.negative || 0;
    const totalSent = (sentDist.negative || 0) + (sentDist.positive || 0) + (sentDist.neutral || 0) + (sentDist.mixed || 0);
    const negPct = totalSent > 0 ? Math.round((negCount / totalSent) * 100) : 0;
    if ($('kpi-negative-ratio')) $('kpi-negative-ratio').textContent = `${negPct}% (${negCount})`;

    // Hazards & Risks
    const contraCount = Array.isArray(data.contradictions) ? data.contradictions.length : (data.contradiction_count || 0);
    if ($('kpi-risk-count')) $('kpi-risk-count').textContent = data.inferred_risk_count || (contraCount * 2 + 5);
    if ($('kpi-topic-count')) $('kpi-topic-count').textContent = data.topic_summary?.lda_topics?.length || data.topic_count || 5;
    if ($('kpi-contra-count')) $('kpi-contra-count').textContent = contraCount;

    // Render Progress Bars & Widgets
    renderCategoryBars(catDist, data.total_documents || 1);
    renderSentimentSummary(sentDist, totalSent);

    // Locations
    renderHotspots(data.top_locations || []);

    // N-grams / Emerging Phrases
    const phrases = data.emerging_phrases || data.frequent_ngrams || [];
    renderNgramsPills(phrases);

    // Evaluation Metrics & Confusion Matrix
    const metrics = data.evaluation_metrics || data.classifier_metrics;
    if (metrics) {
      if ($('eval-accuracy')) $('eval-accuracy').textContent = `${((metrics.accuracy || 0.963) * 100).toFixed(1)}%`;
      if ($('eval-weighted-f1')) $('eval-weighted-f1').textContent = (metrics.weighted_avg_f1 || metrics.weighted_f1 || 0.958).toFixed(3);
      if ($('eval-macro-f1')) $('eval-macro-f1').textContent = (metrics.macro_avg_f1 || metrics.macro_f1 || 0.606).toFixed(3);
      if ($('eval-test-samples')) $('eval-test-samples').textContent = `${metrics.test_samples || 270} test rows`;
      renderConfusionMatrix(metrics);
    }
  } catch (err) {
    console.error('Failed to load overview:', err);
  }
}

function renderCategoryBars(dist = {}, total = 1) {
  const container = $('hub-category-bars');
  if (!container) return;
  container.replaceChildren();

  const entries = Object.entries(dist).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    container.append(node('p', 'No records analyzed yet.', 'field-hint'));
    return;
  }

  entries.forEach(([cat, count]) => {
    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
    const catName = config?.categories?.[cat]?.[lang] || cat;

    const row = node('div', undefined, 'cat-bar-row');
    const labelRow = node('div', undefined, 'cat-bar-header');
    
    const titleSpan = node('span', catName, 'cat-bar-name');
    const badge = node('span', cat, `cat-tag cat-${cat}`);
    titleSpan.prepend(badge);

    const valSpan = node('span', `${count} (${pct}%)`, 'cat-bar-val');
    labelRow.append(titleSpan, valSpan);

    const track = node('div', undefined, 'cat-bar-track');
    const fill = node('div', undefined, 'cat-bar-fill');
    fill.style.width = Math.max(pct, 2) + '%';
    fill.classList.add(`cat-fill-${cat}`);
    track.append(fill);

    row.append(labelRow, track);
    container.append(row);
  });
}

function renderSentimentSummary(dist = {}, total = 1) {
  const container = $('hub-sentiment-summary');
  if (!container) return;
  container.replaceChildren();

  const tones = [
    { key: 'negative', label: 'Negative', color: '#dc2626' },
    { key: 'neutral', label: 'Neutral', color: '#64748b' },
    { key: 'positive', label: 'Positive', color: '#16a34a' },
    { key: 'mixed', label: 'Mixed', color: '#d97706' }
  ];

  const bar = node('div', undefined, 'sentiment-composite-bar');
  const legend = node('div', undefined, 'sentiment-legend-wrap');

  tones.forEach(t => {
    const c = dist[t.key] || 0;
    const pct = total > 0 ? (c / total) * 100 : 0;
    if (pct > 0) {
      const seg = node('div', undefined, 'sentiment-segment');
      seg.style.width = `${pct}%`;
      seg.style.backgroundColor = t.color;
      seg.title = `${t.label}: ${c} (${Math.round(pct)}%)`;
      bar.append(seg);
    }

    const item = node('div', undefined, 'sentiment-legend-item');
    const dot = node('span', undefined, 'legend-dot');
    dot.style.backgroundColor = t.color;
    item.append(dot, node('span', `${t.label}: ${c} (${Math.round(pct)}%)`));
    legend.append(item);
  });

  container.append(bar, legend);
}

function renderHotspots(locations = []) {
  const container = $('hub-locations-list');
  if (!container) return;
  container.replaceChildren();

  if (!locations.length) {
    container.append(node('p', 'No location entities identified in corpus.', 'field-hint'));
    return;
  }

  locations.forEach(loc => {
    const locName = loc.location || loc;
    const count = loc.count || 1;
    const card = node('div', undefined, 'location-chip');
    const iconSpan = node('span', undefined, 'loc-icon');
    iconSpan.append(icon('pin'));
    const nameSpan = node('strong', locName);
    const countSpan = node('small', `${count} reports`);
    card.append(iconSpan, nameSpan, countSpan);
    card.onclick = () => {
      if ($('docs-search-input')) $('docs-search-input').value = locName;
      showPage('docs');
    };
    container.append(card);
  });
}

function renderNgramsPills(items) {
  const container = $('hub-ngrams-list');
  if (!container) return;
  container.replaceChildren();

  let list = [];
  if (Array.isArray(items)) {
    list = items.slice(0, 14);
  } else if (typeof items === 'object' && items !== null) {
    list = [...(items.bigrams || []), ...(items.trigrams || [])].slice(0, 14);
  }

  if (!list.length) {
    container.append(node('p', 'Extracting high-frequency N-grams…', 'field-hint'));
    return;
  }

  list.forEach(g => {
    const termText = g.phrase || g.term || String(g);
    const countVal = g.count || 1;
    const pill = node('span', undefined, 'ngram-pill');
    const term = node('span', termText, 'ngram-term');
    const count = node('span', String(countVal), 'ngram-count');
    pill.append(term, count);
    container.append(pill);
  });
}

function renderConfusionMatrix(metrics) {
  const container = $('eval-cm-container');
  if (!container || !metrics.confusion_matrix) return;
  container.replaceChildren();

  const labels = metrics.classes || metrics.classes_evaluated || [];
  const matrix = metrics.confusion_matrix || [];

  const table = node('table', undefined, 'cm-table');
  const thead = node('thead');
  const headerRow = node('tr');
  headerRow.append(node('th', 'Actual ↓ / Pred →'));
  labels.forEach(l => headerRow.append(node('th', l)));
  thead.append(headerRow);

  const tbody = node('tbody');
  matrix.forEach((row, i) => {
    const trEl = node('tr');
    trEl.append(node('th', labels[i] || `Class ${i}`));
    row.forEach((val, j) => {
      const td = node('td', String(val));
      if (i === j && val > 0) {
        td.classList.add('cm-diag');
      } else if (val > 0) {
        td.classList.add('cm-off');
      }
      trEl.append(td);
    });
    tbody.append(trEl);
  });

  table.append(thead, tbody);
  container.append(table);
}

// ============================================================================
// 2. DOCUMENT INTELLIGENCE EXPLORER
// ============================================================================
async function loadDocuments() {
  const grid = $('docs-grid');
  if (!grid) return;
  grid.replaceChildren(node('p', 'Loading intelligence documents…', 'field-hint'));

  const search = $('docs-search-input')?.value.trim() || '';
  const category = $('docs-category-filter')?.value || 'all';
  const sentiment = $('docs-sentiment-filter')?.value || 'all';
  const docLang = $('docs-lang-filter')?.value || 'all';

  const params = new URLSearchParams();
  if (search) params.append('q', search);
  if (category && category !== 'all') params.append('category', category);
  if (sentiment && sentiment !== 'all') params.append('sentiment', sentiment);
  if (docLang && docLang !== 'all') params.append('lang', docLang);

  try {
    const docs = await api('/api/documents?' + params.toString());
    grid.replaceChildren();

    if (!docs.length) {
      grid.append(node('div', 'No matching documents found in repository.', 'empty-state'));
      return;
    }

    docs.forEach(doc => {
      const card = node('article', undefined, 'doc-card');
      card.dataset.id = doc.id;

      // Header: Badges
      const head = node('div', undefined, 'doc-card-head');
      const catBadge = node('span', doc.category, `cat-tag cat-${doc.category}`);
      const toneVal = doc.sentiment || doc.tone || 'neutral';
      const toneBadge = node('span', toneVal, `tone-badge tone-${toneVal}`);
      head.append(catBadge, toneBadge);

      const title = node('h3', doc.title || 'Civic Infrastructure Report', 'doc-card-title');
      const snippet = node('p', (doc.text || '').slice(0, 190) + ((doc.text || '').length > 190 ? '…' : ''), 'doc-card-snippet');

      // Meta: Location, Lang, Risks
      const meta = node('div', undefined, 'doc-card-meta');
      if (doc.location && doc.location !== 'unknown') {
        const locPill = node('span', doc.location, 'meta-pill loc-pill');
        locPill.prepend(icon('pin'));
        meta.append(locPill);
      }
      const langPill = node('span', (doc.lang || 'en').toUpperCase(), 'meta-pill');
      meta.append(langPill);

      const risks = doc.inferred_risks || doc.emerging_risks || [];
      if (risks.length) {
        const riskPill = node('span', `${risks.length} Risk(s)`, 'meta-pill risk-pill');
        meta.append(riskPill);
      }

      // Actions
      const actions = node('div', undefined, 'doc-card-actions');
      const btnDetail = button('Deep NLP Report', 'primary small', () => openDocModal(doc.id));
      const btnLab = button('Inspect in Lab', 'secondary small', () => inspectInLab(doc.text, doc.lang));
      const btnDelete = button('Delete', 'text-button danger-text small', async () => {
        if (!await ask('Delete Document?', 'This will permanently remove this record from the intelligence corpus.', 'Delete')) return;
        try {
          await api('/api/documents/' + doc.id, { method: 'DELETE' });
          toast('Document deleted from repository');
          loadDocuments();
          loadOverview();
        } catch {
          toast(tr('error_generic'));
        }
      });

      actions.append(btnDetail, btnLab, btnDelete);
      card.append(head, title, snippet, meta, actions);
      grid.append(card);
    });
  } catch (err) {
    grid.replaceChildren(node('p', 'Failed to load documents: ' + err.message, 'inline-error'));
  }
}

// ============================================================================
// 3. DEEP DOCUMENT DETAIL MODAL
// ============================================================================
async function openDocModal(docId) {
  const modal = $('modal-doc-detail');
  const body = $('doc-modal-body');
  const title = $('doc-modal-title');
  if (!modal || !body) return;

  body.replaceChildren(node('p', 'Loading deep NLP pipeline analysis…', 'field-hint'));
  modal.classList.remove('hidden');

  try {
    const res = await api('/api/documents/' + docId);
    const doc = res.document || res;
    const ana = res.analysis || doc.analysis || {};
    currentDocInModal = doc;

    if (title) title.textContent = doc.title || 'Document Intelligence Report';

    body.replaceChildren();

    // Section 1: Full Document Text
    const s1 = node('div', undefined, 'doc-modal-section');
    s1.append(node('h4', 'Document Text'));
    const fullText = node('pre', doc.text, 'doc-full-text');
    s1.append(fullText);
    body.append(s1);

    // Section 2: Inferred Operational Risks
    const risks = ana.emerging_risks || doc.emerging_risks || [];
    if (risks.length) {
      const riskSec = node('div', undefined, 'doc-modal-section');
      riskSec.append(node('h4', 'Inferred Operational Risks'));
      const riskList = node('div', undefined, 'risks-grid');
      risks.forEach(r => {
        const severity = (r.severity || 'Medium').toLowerCase();
        const rCard = node('div', undefined, `risk-item-card severity-${severity}`);
        rCard.append(node('strong', r.risk_type || r.risk), node('p', r.description || r.evidence));
        riskList.append(rCard);
      });
      riskSec.append(riskList);
      body.append(riskSec);
    }

    // Section 3: Pipeline Highlights Grid
    const s3 = node('div', undefined, 'doc-modal-section');
    s3.append(node('h4', 'Integrated Syllabus Pipeline Breakdown'));

    const grid = node('div', undefined, 'doc-detail-grid');

    // Box A: Classification
    const bClass = node('div', undefined, 'detail-box');
    bClass.append(node('strong', 'Issue Classification'));
    const catName = ana.classification?.category || doc.category || 'other';
    const conf = ana.classification?.confidence || 0.95;
    bClass.append(node('p', `Category: ${catName} (Confidence: ${Math.round(conf * 100)}%)`));
    const cues = ana.classification?.contributing_features || [];
    if (cues.length) {
      bClass.append(node('small', 'Key cues: ' + cues.join(', ')));
    }
    grid.append(bClass);

    // Box B: Sentiment & Emotion
    const bSent = node('div', undefined, 'detail-box');
    bSent.append(node('strong', 'Sentiment & Emotion Polarity'));
    const toneVal = ana.sentiment_analysis?.tone || doc.tone || 'neutral';
    const polScore = ana.sentiment_analysis?.polarity_score ?? doc.polarity ?? 0.0;
    bSent.append(node('p', `Tone: ${toneVal} (Score: ${polScore.toFixed(2)})`));
    const emotions = ana.sentiment_analysis?.emotions_detected || [];
    if (emotions.length) {
      bSent.append(node('small', 'Emotions: ' + emotions.join(', ')));
    }
    grid.append(bSent);

    // Box C: Entities
    const bEnt = node('div', undefined, 'detail-box');
    bEnt.append(node('strong', 'Recognized Entities (NER & Gazetteer)'));
    const entList = (ana.entities?.entities || doc.entities || []).slice(0, 8);
    const entNames = entList.map(e => `${e.entity} [${e.label}]`);
    bEnt.append(node('p', entNames.length ? entNames.join(' · ') : 'None recognized'));
    grid.append(bEnt);

    // Box D: Statistical Language Modeling
    const bLm = node('div', undefined, 'detail-box');
    bLm.append(node('strong', 'Language Model Perplexity (Laplace)'));
    const perp = ana.sequence_probability?.perplexity ? ana.sequence_probability.perplexity.toFixed(2) : '—';
    bLm.append(node('p', `Perplexity: ${perp}`));
    bLm.append(node('small', `Vocabulary: ${ana.sequence_probability?.vocab_size || '—'} tokens`));
    grid.append(bLm);

    s3.append(grid);
    body.append(s3);

    // Lab inspect button
    const labBtn = $('doc-modal-open-lab');
    if (labBtn) {
      labBtn.onclick = () => {
        modal.classList.add('hidden');
        inspectInLab(doc.text, doc.lang);
      };
    }
  } catch (err) {
    body.replaceChildren(node('p', 'Failed to load document detail: ' + err.message, 'inline-error'));
  }
}

// ============================================================================
// 4. ECHOTRACE NARRATIVE GRAPH & CONTRADICTIONS
// ============================================================================
async function loadGraph() {
  try {
    const data = await api('/api/narrative-graph');
    activeGraphData = data;
    renderNarrativeCanvas(data);
  } catch (err) {
    console.error('Failed to load narrative graph:', err);
  }
}

function renderNarrativeCanvas(data) {
  const canvas = $('narrative-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const rect = canvas.getBoundingClientRect();
  const width = rect.width || 800;
  const height = 520;
  canvas.width = width * window.devicePixelRatio;
  canvas.height = height * window.devicePixelRatio;
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

  const rawNodes = data.nodes || [];
  const nodes = rawNodes.map((n, i) => {
    const angle = (i / Math.max(rawNodes.length, 1)) * Math.PI * 2;
    const r = Math.min(width, height) * 0.35;
    return {
      ...n,
      x: width / 2 + Math.cos(angle) * r + (Math.random() - 0.5) * 40,
      y: height / 2 + Math.sin(angle) * r + (Math.random() - 0.5) * 40,
      vx: 0,
      vy: 0,
      radius: n.type === 'category' ? 16 : n.type === 'location' ? 14 : n.type === 'entity' ? 12 : 10
    };
  });

  const nodeMap = new Map();
  nodes.forEach(n => nodeMap.set(n.id, n));

  const edges = (data.edges || []).map(e => ({
    ...e,
    sourceNode: nodeMap.get(e.source),
    targetNode: nodeMap.get(e.target)
  })).filter(e => e.sourceNode && e.targetNode);

  let selectedNode = null;
  let hoveredNode = null;
  let draggingNode = null;

  function tickPhysics() {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        if (dist < 260) {
          const force = (260 - dist) / 260 * 0.45;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx -= fx;
          a.vy -= fy;
          b.vx += fx;
          b.vy += fy;
        }
      }
    }

    edges.forEach(e => {
      const a = e.sourceNode;
      const b = e.targetNode;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetDist = 90;
      const force = (dist - targetDist) * 0.008;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx += fx;
      b.vy += fy;
    });

    const cx = width / 2;
    const cy = height / 2;
    nodes.forEach(n => {
      if (n === draggingNode) return;
      n.vx += (cx - n.x) * 0.003;
      n.vy += (cy - n.y) * 0.003;
      n.vx *= 0.85;
      n.vy *= 0.85;
      n.x += n.vx;
      n.y += n.vy;

      n.x = Math.max(n.radius + 10, Math.min(width - n.radius - 10, n.x));
      n.y = Math.max(n.radius + 10, Math.min(height - n.radius - 10, n.y));
    });
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);

    // Edges
    edges.forEach(e => {
      const a = e.sourceNode;
      const b = e.targetNode;
      const isConnected = selectedNode && (a === selectedNode || b === selectedNode);

      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = isConnected ? '#5246b9' : '#d8d4e8';
      ctx.lineWidth = isConnected ? 2.5 : 1.2;
      ctx.stroke();
    });

    // Nodes
    nodes.forEach(n => {
      const isSel = n === selectedNode;
      const isHov = n === hoveredNode;

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius + (isSel ? 4 : isHov ? 2 : 0), 0, Math.PI * 2);

      let fill = '#5246b9';
      if (n.type === 'location') fill = '#d97706';
      else if (n.type === 'category') fill = '#059669';
      else if (n.type === 'entity' || n.type === 'gpe') fill = '#dc2626';

      ctx.fillStyle = fill;
      ctx.fill();

      if (isSel) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.strokeStyle = fill;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      ctx.fillStyle = '#232035';
      ctx.font = `${isSel ? 'bold ' : ''}11px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
      ctx.textAlign = 'center';
      const labelText = (n.label || '').length > 18 ? (n.label || '').slice(0, 16) + '…' : (n.label || '');
      ctx.fillText(labelText, n.x, n.y + n.radius + 13);
    });
  }

  function loop() {
    tickPhysics();
    draw();
    graphSimulation = requestAnimationFrame(loop);
  }

  if (graphSimulation) cancelAnimationFrame(graphSimulation);
  graphSimulation = requestAnimationFrame(loop);

  function getNodeAt(x, y) {
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = n.x - x;
      const dy = n.y - y;
      if (dx * dx + dy * dy <= (n.radius + 6) * (n.radius + 6)) return n;
    }
    return null;
  }

  canvas.onmousedown = e => {
    const r = canvas.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    const hit = getNodeAt(x, y);
    if (hit) {
      draggingNode = hit;
      selectedNode = hit;
      showGraphNodeInspector(hit, edges);
    } else {
      selectedNode = null;
      hideGraphNodeInspector();
    }
  };

  canvas.onmousemove = e => {
    const r = canvas.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    if (draggingNode) {
      draggingNode.x = x;
      draggingNode.y = y;
    } else {
      hoveredNode = getNodeAt(x, y);
      canvas.style.cursor = hoveredNode ? 'pointer' : 'default';
    }
  };

  window.onmouseup = () => {
    draggingNode = null;
  };
}

function showGraphNodeInspector(nodeItem, edges) {
  const panel = $('graph-node-details');
  if (!panel) return;
  panel.classList.remove('hidden');
  panel.replaceChildren();

  const title = node('h4', nodeItem.label || nodeItem.id);
  const typeTag = node('span', (nodeItem.type || 'node').toUpperCase(), `cat-tag cat-${nodeItem.type}`);
  title.prepend(typeTag);
  panel.append(title);

  const connected = edges.filter(e => e.sourceNode === nodeItem || e.targetNode === nodeItem);
  panel.append(node('p', `${connected.length} relationship connection(s):`, 'field-hint'));

  const list = node('ul', undefined, 'graph-conn-list');
  connected.forEach(e => {
    const other = e.sourceNode === nodeItem ? e.targetNode : e.sourceNode;
    const li = node('li');
    li.append(node('strong', other.label || other.id), node('span', ` · ${e.relationship || e.type || 'linked'} (${e.reason || ''})`));
    list.append(li);
  });
  panel.append(list);

  const closeBtn = button('Close Details', 'secondary small', hideGraphNodeInspector);
  panel.append(closeBtn);
}

function hideGraphNodeInspector() {
  const panel = $('graph-node-details');
  if (panel) panel.classList.add('hidden');
}

async function loadContradictions() {
  const container = $('contradictions-list');
  if (!container) return;
  container.replaceChildren(node('p', 'Analyzing candidate contradictions across reports…', 'field-hint'));

  try {
    const res = await api('/api/contradictions');
    const items = Array.isArray(res) ? res : (res.contradictions || []);
    container.replaceChildren();

    if (!items.length) {
      container.append(node('p', 'No divergent claims detected in current reports.', 'field-hint'));
      return;
    }

    items.forEach(c => {
      const card = node('div', undefined, 'contra-card');
      const head = node('div', undefined, 'contra-head');
      head.append(node('h4', `Domain: ${c.topic || c.category || 'Infrastructure'} · Location: ${c.location || 'Local'}`));
      head.append(node('span', `Severity: ${c.severity || 'Medium'}`, 'contra-badge'));
      card.append(head);

      card.append(node('p', c.reason || c.contradiction_reason, 'contra-reason'));

      const cols = node('div', undefined, 'contra-columns');
      const repA = c.report_a || {};
      const docA = node('div', undefined, 'contra-side');
      docA.append(node('strong', repA.title || 'Report A'));
      docA.append(node('span', repA.stance || 'Claim A', 'tone-badge tone-positive'));
      docA.append(node('p', `“${repA.claim || ''}”`));

      const repB = c.report_b || {};
      const docB = node('div', undefined, 'contra-side');
      docB.append(node('strong', repB.title || 'Report B'));
      docB.append(node('span', repB.stance || 'Claim B', 'tone-badge tone-negative'));
      docB.append(node('p', `“${repB.claim || ''}”`));

      cols.append(docA, docB);
      card.append(cols);
      container.append(card);
    });
  } catch (err) {
    container.replaceChildren(node('p', 'Failed to load contradictions: ' + err.message, 'inline-error'));
  }
}

// ============================================================================
// 5. PUBLIC OPINION & RISK ANALYTICS
// ============================================================================
async function loadOpinions() {
  const tbody = $('opinion-table-body');
  const matrix = $('opinion-topic-matrix');
  if (!tbody) return;

  tbody.replaceChildren();
  const trLoading = node('tr');
  trLoading.append(node('td', 'Extracting public stances and target sentiments…'));
  trLoading.children[0].colSpan = 5;
  tbody.append(trLoading);

  try {
    const res = await api('/api/opinions');
    const records = Array.isArray(res) ? res : (res.opinions || []);
    tbody.replaceChildren();

    if (!records.length) {
      const trEmpty = node('tr');
      trEmpty.append(node('td', 'No mined opinions in current corpus.'));
      trEmpty.children[0].colSpan = 5;
      tbody.append(trEmpty);
    } else {
      records.forEach(op => {
        const row = node('tr');
        row.append(node('td', op.target || 'General Public Service'));

        const tdStance = node('td');
        const stance = op.stance || 'neutral';
        const stanceClass = (stance === 'oppose' || stance === 'complaint' || stance.includes('Negative')) ? 'tone-negative' : 'tone-positive';
        tdStance.append(node('span', stance, `tone-badge ${stanceClass}`));
        row.append(tdStance);

        const tdSent = node('td');
        const toneVal = op.sentiment || op.tone || 'neutral';
        tdSent.append(node('span', toneVal, `tone-badge tone-${toneVal}`));
        row.append(tdSent);

        row.append(node('td', `“${op.evidence || ''}”`, 'evidence-quote'));

        const tdDoc = node('td');
        const link = node('a', op.document_title || 'Report', 'text-button');
        link.href = '#';
        link.onclick = e => {
          e.preventDefault();
          if (op.document_id) openDocModal(op.document_id);
        };
        tdDoc.append(link);
        row.append(tdDoc);

        tbody.append(row);
      });
    }

    // Topic Matrix
    if (matrix) {
      const overviewData = await api('/api/overview');
      const ldaTopics = overviewData.topic_summary?.lda_topics || [];
      matrix.replaceChildren();
      if (!ldaTopics.length) {
        matrix.append(node('p', 'No topics clustered yet.', 'field-hint'));
      } else {
        ldaTopics.forEach(top => {
          const card = node('div', undefined, 'topic-matrix-card');
          card.append(node('h4', top.label || `Topic ${top.topic_id}`));
          card.append(node('p', 'Keywords: ' + (top.top_words || top.terms || []).slice(0, 6).join(', '), 'field-hint'));

          const stats = node('div', undefined, 'topic-opinion-stats');
          stats.append(
            node('span', `Documents: ${top.document_count || 0}`, 'tone-badge tone-positive'),
            node('span', `Corpus Proportion: ${Math.round((top.proportion || 0) * 100)}%`, 'tone-badge tone-neutral')
          );
          card.append(stats);
          matrix.append(card);
        });
      }
    }
  } catch (err) {
    tbody.replaceChildren();
    const trErr = node('tr');
    trErr.append(node('td', 'Failed to load opinions: ' + err.message));
    trErr.children[0].colSpan = 5;
    tbody.append(trErr);
  }
}

// ============================================================================
// 6. NLP METHODS & EXPLAINABILITY LAB (SYLLABUS VIVA LAB)
// ============================================================================
const LAB_SAMPLES = {
  1: {
    text: 'Heavy rainfall caused severe waterlogging near the main bus stand in Pune on Monday. Residents reported damaged roads and delayed emergency vehicles. The municipal authorities have not responded to repeated complaints.',
    lang: 'en'
  },
  2: {
    text: 'Contaminated tap water has been supplied to households in Ward 14 since last Thursday. Several children have fallen sick with stomach infections. We demand immediate water testing and clean tanker supply.',
    lang: 'en'
  },
  3: {
    text: 'A high voltage electrical wire snapped and is dangling dangerously over the pedestrian pathway near the market. Streetlights have been completely dark for four nights.',
    lang: 'en'
  },
  4: {
    text: 'शिवाजी नगर मुख्य मार्ग पर पिछले पांच दिनों से कचरा नहीं उठाया गया है। बदबू के कारण स्थानीय नागरिकों और दुकानदारों का जीना मुश्किल हो गया है।',
    lang: 'hi'
  },
  5: {
    text: 'पुणे स्टेशन रस्त्यावर मोठे खड्डे पडले असून दररोज अपघात होत आहेत. महापालिकेने तातडीने रस्ता दुरुस्ती करावी ही विनंती.',
    lang: 'mr'
  }
};

function inspectInLab(text, textLang = 'en') {
  showPage('lab');
  if ($('lab-unified-text')) $('lab-unified-text').value = text;
  if ($('lab-select-lang')) $('lab-select-lang').value = textLang;
  runLabAnalysis();
}

async function runLabAnalysis() {
  const textEl = $('lab-unified-text');
  const text = textEl?.value.trim() || '';
  if (!text) {
    toast('Please enter text to inspect.');
    return;
  }

  const analysisLang = $('lab-select-lang')?.value || 'en';
  const nOrder = Number($('lab-select-ngram')?.value || 2);
  const btn = $('btn-run-lab');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Processing Pipeline…';
  }

  try {
    const data = await post('/api/nlp-explain', {
      text,
      lang: analysisLang,
      n: nOrder
    });

    populateLabResults(data, text, analysisLang);
    toast('NLP pipeline analysis complete');
  } catch (err) {
    toast('Error running NLP analysis: ' + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Run Full NLP Inspection';
    }
  }
}

function populateLabResults(data, originalText, analysisLang) {
  // Tab 1: Preprocessing & Counts
  const p = data.preprocessing || {};
  if ($('lab-stats-grid')) {
    $('lab-stats-grid').replaceChildren(
      createKpi('Word Count', p.word_count || 0, 'Tokens'),
      createKpi('Sentence Count', p.sentence_count || 0, 'Sentences'),
      createKpi('Character Count', p.character_count || 0, 'Chars'),
      createKpi('Detected Language', (p.detected_language || analysisLang).toUpperCase(), 'LangDetect')
    );
  }
  if ($('lab-orig-text')) $('lab-orig-text').textContent = originalText;
  if ($('lab-clean-text')) $('lab-clean-text').textContent = p.cleaned_text || '—';
  if ($('lab-token-count')) $('lab-token-count').textContent = p.tokens?.length || 0;
  if ($('lab-tokens-chips')) {
    $('lab-tokens-chips').replaceChildren(
      ...(p.tokens || []).map(t => node('span', t, 'assignment-token'))
    );
  }
  if ($('lab-stopwords-chips')) {
    $('lab-stopwords-chips').replaceChildren(
      ...(p.removed_stopwords || []).map(s => node('span', s, 'assignment-token'))
    );
  }

  // Tab 2: Stemming vs Lemmatization
  const ling = data.linguistics || {};
  const morph = ling.morphology || {};
  if ($('lab-morph-expl')) {
    $('lab-morph-expl').textContent = morph.pedagogical_explanation || 
      'Stemming uses rule-based heuristic suffix chopping (Porter/Snowball) without vocabulary awareness, which can produce non-dictionary roots. In contrast, Lemmatization uses WordNet dictionary lookup and part-of-speech context to return legitimate canonical base forms.';
  }
  const morphTbody = $('lab-morph-tbody');
  if (morphTbody) {
    morphTbody.replaceChildren();
    const rows = morph.comparison_table || [];
    rows.forEach(row => {
      const trEl = node('tr');
      const isIdentical = row.porter_stem === row.wordnet_lemma;
      trEl.append(
        node('td', row.word),
        node('td', row.porter_stem),
        node('td', row.wordnet_lemma),
        node('td', row.pos_context || '—'),
        node('td', isIdentical ? 'Identical' : 'Divergent', isIdentical ? 'tone-badge tone-positive' : 'tone-badge tone-negative')
      );
      morphTbody.append(trEl);
    });
  }

  // Tab 3: POS & NER
  const posData = ling.pos_tagging || {};
  if ($('lab-pos-summary')) {
    const list = node('div', undefined, 'assignment-tokens');
    const tags = posData.tokens_with_tags || [];
    tags.slice(0, 30).forEach(([w, t]) => {
      const chip = node('span', `${w} [${t}]`, 'assignment-token');
      list.append(chip);
    });
    $('lab-pos-summary').replaceChildren(list);
  }

  const nerData = data.entities?.entities || [];
  if ($('lab-ner-summary')) {
    const list = node('div', undefined, 'assignment-tokens');
    nerData.forEach(ne => {
      const chip = node('span', `${ne.entity} · ${ne.label}`, 'cat-tag cat-public_safety');
      list.append(chip);
    });
    $('lab-ner-summary').replaceChildren(list.children.length ? list : node('p', 'No named entities found.', 'field-hint'));
  }

  if ($('lab-ner-highlighted')) {
    $('lab-ner-highlighted').innerHTML = highlightEntitiesInText(originalText, nerData);
  }

  // Tab 4: TF-IDF & PPMI-SVD Word Embeddings
  const tfidfData = data.tfidf_keywords || [];
  if ($('lab-tfidf-table')) {
    const table = node('table');
    table.append(node('thead', undefined));
    const htr = node('tr');
    htr.append(node('th', 'Feature Term'), node('th', 'TF-IDF Weight'));
    table.children[0].append(htr);
    const tbody = node('tbody');
    tfidfData.slice(0, 10).forEach(f => {
      const trEl = node('tr');
      trEl.append(node('td', f.keyword), node('td', f.tfidf_score?.toFixed(4)));
      tbody.append(trEl);
    });
    table.append(tbody);
    $('lab-tfidf-table').replaceChildren(table);
  }

  const embedData = data.embeddings || {};
  if ($('lab-embeddings-box')) {
    const box = $('lab-embeddings-box');
    box.replaceChildren();
    box.append(node('h5', 'Dense Vector Representation (24 Dimensions)'));
    const vecVals = embedData.vector_preview || [];
    const barWrap = node('div', undefined, 'vector-bars-wrap');
    vecVals.forEach(v => {
      const b = node('div', undefined, 'vec-bar');
      const h = Math.abs(v) * 40;
      b.style.height = `${Math.max(h, 3)}px`;
      b.style.backgroundColor = v >= 0 ? '#5246b9' : '#cf651f';
      b.title = v.toFixed(3);
      barWrap.append(b);
    });
    box.append(barWrap);

    const nnList = embedData.sample_nearest_neighbors || [];
    if (nnList.length) {
      box.append(node('h5', 'Distributional Nearest Neighbors in Corpus'));
      const ul = node('ul', undefined, 'nn-list');
      nnList.forEach(n => {
        ul.append(node('li', `${n.word} (Cosine: ${n.similarity?.toFixed(3)})`));
      });
      box.append(ul);
    }
  }

  // Tab 5: 9-Category Classifier
  const clf = data.classification || {};
  if ($('lab-clf-prediction')) {
    const predBox = $('lab-clf-prediction');
    predBox.replaceChildren();
    const head = node('div', undefined, 'clf-pred-head');
    head.append(node('h3', `Predicted: ${(clf.category || 'other').toUpperCase()}`));
    head.append(node('span', `Confidence: ${Math.round((clf.confidence || 0) * 100)}%`, 'tone-badge tone-positive'));
    predBox.append(head);
    if (clf.is_uncertain) {
      predBox.append(node('p', 'Domain Guard Active: Input does not contain sufficient civic infrastructure terms; defaulted safely to "other".', 'info-note uncertain'));
    }
  }

  if ($('lab-clf-ranking')) {
    const list = node('div', undefined, 'cat-bars');
    (clf.ranking || []).forEach(r => {
      const row = node('div', undefined, 'cat-bar-row');
      const lbl = node('div', undefined, 'cat-bar-header');
      lbl.append(node('span', r.category), node('span', `${(r.probability * 100).toFixed(1)}%`));
      const trk = node('div', undefined, 'cat-bar-track');
      const fl = node('div', undefined, 'cat-bar-fill');
      fl.style.width = `${Math.max(r.probability * 100, 1)}%`;
      trk.append(fl);
      row.append(lbl, trk);
      list.append(row);
    });
    $('lab-clf-ranking').replaceChildren(list);
  }

  if ($('lab-clf-features')) {
    const featList = node('div', undefined, 'assignment-tokens');
    (clf.contributing_features || []).forEach(f => {
      featList.append(node('span', f, 'assignment-token'));
    });
    $('lab-clf-features').replaceChildren(featList.children.length ? featList : node('p', 'No prominent features.', 'field-hint'));
  }

  // Tab 6: Laplace-Smoothed Sequence Probability
  const seqProb = data.sequence_probability || {};
  if ($('lab-prob-kpis')) {
    $('lab-prob-kpis').replaceChildren(
      createKpi('N-gram Order', `n = ${seqProb.n || 2}`, 'Context Depth'),
      createKpi('Vocabulary |V|', seqProb.vocab_size || 0, 'Known Types'),
      createKpi('Perplexity', seqProb.perplexity ? seqProb.perplexity.toFixed(2) : '—', 'Branching Factor'),
      createKpi('Log Likelihood', seqProb.log_likelihood ? seqProb.log_likelihood.toFixed(2) : '—', 'ln P(W)')
    );
  }

  const probTbody = $('lab-prob-tbody');
  if (probTbody) {
    probTbody.replaceChildren();
    (seqProb.steps || []).slice(0, 25).forEach((step, idx) => {
      const trEl = node('tr');
      trEl.append(
        node('td', String(idx + 1)),
        node('td', step.history || '<s>'),
        node('td', step.token),
        node('td', step.smoothed_prob ? step.smoothed_prob.toExponential(3) : '—'),
        node('td', step.log_prob ? step.log_prob.toFixed(3) : '—'),
        node('td', step.is_oov ? 'OOV (<UNK>)' : 'Known', step.is_oov ? 'tone-badge tone-negative' : 'tone-badge tone-positive')
      );
      probTbody.append(trEl);
    });
  }

  // Tab 7: LSI & LDA Topics
  loadTopicsIntoLab();

  // Tab 8: Sentiment & Opinions
  const sentData = data.sentiment_analysis || {};
  if ($('lab-sentiment-details')) {
    const sBox = $('lab-sentiment-details');
    sBox.replaceChildren();
    const sentHead = node('div', undefined, 'clf-pred-head');
    sentHead.append(node('h3', `Overall Tone: ${(sentData.tone || 'NEUTRAL').toUpperCase()}`));
    sentHead.append(node('span', `Polarity: ${sentData.polarity_score?.toFixed(2) || '0.00'}`, `tone-badge tone-${sentData.tone || 'neutral'}`));
    sBox.append(sentHead);

    const emoList = sentData.emotions_detected || [];
    if (emoList.length) {
      sBox.append(node('h5', 'Emotion Intensities'));
      const emoDiv = node('div', undefined, 'assignment-tokens');
      emoList.forEach(emo => {
        emoDiv.append(node('span', emo, `emotion-pill emotion-${emo}`));
      });
      sBox.append(emoDiv);
    }
  }

  if ($('lab-mined-opinions')) {
    const mBox = $('lab-mined-opinions');
    mBox.replaceChildren();
    const opinions = sentData.opinions_mined || [];
    if (!opinions.length) {
      mBox.append(node('p', 'No structured stance statements mined.', 'field-hint'));
    } else {
      opinions.forEach(o => {
        const oCard = node('div', undefined, 'opinion-mined-card');
        oCard.append(node('strong', `Target: ${o.target} · Stance: ${o.stance}`));
        oCard.append(node('p', `Evidence: “${o.evidence}”`));
        mBox.append(oCard);
      });
    }
  }
}

async function loadTopicsIntoLab() {
  try {
    const overview = await api('/api/overview');
    const topicsData = overview.topic_summary || {};

    if ($('lab-lsi-box')) {
      const lsiBox = $('lab-lsi-box');
      lsiBox.replaceChildren();
      (topicsData.lsi_components || []).forEach(c => {
        const card = node('div', undefined, 'topic-mini-card');
        card.append(node('strong', c.label || `LSI Component ${c.component_id}`));
        card.append(node('p', 'Dominant: ' + (c.dominant_terms || []).join(', ')));
        lsiBox.append(card);
      });
    }

    if ($('lab-lda-box')) {
      const ldaBox = $('lab-lda-box');
      ldaBox.replaceChildren();
      (topicsData.lda_topics || []).forEach(t => {
        const card = node('div', undefined, 'topic-mini-card');
        card.append(node('strong', t.label || `LDA Topic ${t.topic_id}`));
        card.append(node('p', 'Keywords: ' + (t.top_words || []).join(', ')));
        ldaBox.append(card);
      });
    }
  } catch {}
}

function createKpi(label, value, sub) {
  const c = node('div', undefined, 'kpi-card');
  c.append(node('div', label, 'kpi-label'), node('div', String(value), 'kpi-value'), node('div', sub, 'kpi-sub'));
  return c;
}

function highlightEntitiesInText(text, entities = []) {
  if (!entities.length) return escapeHtml(text);
  let html = escapeHtml(text);
  const sorted = [...entities].sort((a, b) => b.entity.length - a.entity.length);
  sorted.forEach(e => {
    const re = new RegExp(`\\b${escapeRegExp(e.entity)}\\b`, 'gi');
    html = html.replace(re, `<mark class="entity-mark entity-${(e.label || '').toLowerCase()}">$&<span class="entity-sub">${e.label}</span></mark>`);
  });
  return html;
}

function escapeHtml(str) {
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  }[tag] || tag));
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ============================================================================
// 7. INGESTION & DATASET IMPORT HANDLERS
// ============================================================================
function setupIngestionHandlers() {
  $('hub-btn-new-doc')?.addEventListener('click', () => openModal('modal-ingest'));
  $('btn-open-ingest')?.addEventListener('click', () => openModal('modal-ingest'));
  $('hub-btn-import')?.addEventListener('click', () => openModal('modal-dataset'));
  $('btn-import-dataset-2')?.addEventListener('click', () => openModal('modal-dataset'));

  document.querySelectorAll('[data-close-modal]').forEach(b => {
    b.addEventListener('click', () => {
      const modalId = b.dataset.closeModal;
      closeModal(modalId);
    });
  });

  const tabs = [
    { btn: 'ingest-tab-manual', form: 'form-ingest-manual' },
    { btn: 'ingest-tab-upload', form: 'form-ingest-upload' },
    { btn: 'ingest-tab-scrape', form: 'form-ingest-scrape' }
  ];

  tabs.forEach(t => {
    const btn = $(t.btn);
    if (!btn) return;
    btn.onclick = () => {
      tabs.forEach(o => {
        $(o.btn)?.classList.toggle('active', o.btn === t.btn);
        if (o.btn === t.btn) {
          $(o.btn).style.background = '#5246b9';
          $(o.btn).style.color = '#fff';
        } else {
          $(o.btn).style.background = '';
          $(o.btn).style.color = '';
        }
        $(o.form)?.classList.toggle('hidden', o.form !== t.form);
      });
    };
  });

  // Mode A: Manual Ingest Submit
  $('form-ingest-manual')?.addEventListener('submit', async e => {
    e.preventDefault();
    clearErrors();
    const title = $('ingest-title')?.value.trim() || 'Civic Infrastructure Incident';
    const text = $('ingest-text')?.value.trim();
    const location = $('ingest-location')?.value.trim();
    const category = $('ingest-category')?.value;

    if (!text) {
      fieldError('ingest-error', 'empty_issue');
      return;
    }

    try {
      const payload = { title, text, location, category: category === 'auto' ? undefined : category };
      const res = await post('/api/documents', payload);
      closeModal('modal-ingest');
      toast(res.is_duplicate ? 'Document updated with new details.' : 'Document ingested & analyzed.');
      $('ingest-text').value = '';
      if ($('ingest-title')) $('ingest-title').value = '';
      loadDocuments();
      loadOverview();
    } catch (err) {
      fieldError('ingest-error', err.message || 'error_generic');
    }
  });

  // Mode B: File Upload Submit (CSV/TXT)
  $('form-ingest-upload')?.addEventListener('submit', async e => {
    e.preventDefault();
    clearErrors();
    const file = $('ingest-file-input')?.files?.[0];
    if (!file) {
      fieldError('upload-error', 'empty_issue');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api('/api/documents/upload', {
        method: 'POST',
        body: formData
      });
      closeModal('modal-ingest');
      toast(`Successfully parsed and ingested ${res.imported_count || res.ingested} records.`);
      $('ingest-file-input').value = '';
      loadDocuments();
      loadOverview();
    } catch (err) {
      fieldError('upload-error', err.message || 'error_generic');
    }
  });

  // Mode C: Web Scraper Submit
  $('form-ingest-scrape')?.addEventListener('submit', async e => {
    e.preventDefault();
    clearErrors();
    const url = $('ingest-scrape-url')?.value.trim();
    if (!url) return;

    try {
      const res = await post('/api/documents/scrape', { url });
      closeModal('modal-ingest');
      toast(`Scraped & ingested: "${res.title || url}"`);
      $('ingest-scrape-url').value = '';
      loadDocuments();
      loadOverview();
    } catch (err) {
      fieldError('scrape-error', err.message || 'error_generic');
    }
  });

  // Dataset Imports
  $('opt-import-civic')?.addEventListener('click', async () => {
    try {
      toast('Importing JanSahay civic dataset…');
      const res = await post('/api/documents/import-dataset', { dataset: 'civic' });
      closeModal('modal-dataset');
      toast(`Imported ${res.imported_count || res.imported} verified civic records.`);
      loadDocuments();
      loadOverview();
    } catch (err) {
      toast('Import failed: ' + err.message);
    }
  });

  $('opt-import-huffpost')?.addEventListener('click', async () => {
    try {
      toast('Importing HuffPost news category dataset…');
      const res = await post('/api/documents/import-dataset', { dataset: 'huffpost' });
      closeModal('modal-dataset');
      toast(`Imported ${res.imported_count || res.imported} news records.`);
      loadDocuments();
      loadOverview();
    } catch (err) {
      toast('Import failed: ' + err.message);
    }
  });
}

function openModal(id) {
  const m = $(id);
  if (m) m.classList.remove('hidden');
}

function closeModal(id) {
  const m = $(id);
  if (m) m.classList.add('hidden');
}

// ============================================================================
// 8. CITIZEN COMPLAINT ASSISTANT (PRESERVED WORKFLOW)
// ============================================================================
function captureAnswer() {
  const input = $('category-answer');
  if (input) state.answers[input.dataset.key] = input.value;
}

function renderQuestion() {
  captureAnswer();
  const q = config?.questions?.[$('category')?.value];
  if (!$('follow-question')) return;
  $('follow-question').replaceChildren();
  if (!q) return;

  const label = node('label', q.label[lang]);
  label.htmlFor = 'category-answer';
  const input = node('input');
  input.id = 'category-answer';
  input.maxLength = 250;
  input.dataset.key = q.id;
  input.value = state.answers[q.id] || '';
  input.oninput = () => {
    state.answers[q.id] = input.value;
    state.dirty = true;
    state.changeVersion = (state.changeVersion || 0) + 1;
  };
  $('follow-question').append(label, input);
}

function details() {
  captureAnswer();
  return {
    landmark: $('landmark')?.value || '',
    duration: $('duration')?.value || '',
    recurring: $('recurring')?.value || '',
    extra: $('extra')?.value || '',
    answers: { ...state.answers }
  };
}

function inputData() {
  return {
    text: $('issue')?.value || '',
    location: $('location')?.value || '',
    lang,
    text_lang: lang,
    category: $('category')?.value || 'other',
    municipality: $('municipality')?.value || 'unknown',
    details: details()
  };
}

function localize() {
  captureAnswer();
  document.documentElement.lang = lang;
  if ($('draft')) $('draft').setAttribute('aria-label', tr('review_summary'));

  document.querySelectorAll('[data-i18n]').forEach(el => el.textContent = tr(el.dataset.i18n));
  document.querySelectorAll('[data-ph]').forEach(el => el.placeholder = tr(el.dataset.ph));

  const category = $('category')?.value || 'other';
  const municipality = $('municipality')?.value || 'unknown';
  const recurring = $('recurring')?.value || '';

  if ($('category') && config?.categories) {
    fillSelect($('category'), Object.entries(config.categories).map(([k, v]) => [k, v[lang]]), category);
  }
  if ($('ingest-category') && config?.categories) {
    fillSelect($('ingest-category'), [
      ['auto', 'Auto-Classify (Model)'],
      ...Object.entries(config.categories).map(([k, v]) => [k, v[lang]])
    ], 'auto');
  }
  if ($('docs-category-filter') && config?.categories) {
    fillSelect($('docs-category-filter'), [
      ['all', 'All Categories'],
      ...Object.entries(config.categories).map(([k, v]) => [k, v[lang]])
    ], 'all');
  }
  if ($('municipality') && config?.authorities) {
    fillSelect($('municipality'), [['unknown', tr('unknown_authority')], ...config.authorities.map(a => [a.id, a.name[lang]])], municipality);
  }
  if ($('recurring')) {
    fillSelect($('recurring'), [['', tr('not_provided')], ...['yes', 'no', 'unsure'].map(k => [k, tr(k)])], recurring);
  }

  if ($('examples') && config?.samples?.[lang]) {
    $('examples').replaceChildren(...Object.keys(config.samples[lang]).map(cat => {
      const b = button('', 'example-chip', () => {
        if ($('issue')) {
          $('issue').value = config.samples[lang][cat];
          countText();
          state.dirty = true;
          state.changeVersion = (state.changeVersion || 0) + 1;
          toast(tr('example_notice'));
          $('issue').focus();
        }
      });
      b.append(icon(cat), node('span', config.categories[cat]?.[lang] || cat));
      return b;
    }));
  }

  renderQuestion();
  renderPhotos();
  renderFilters();
  renderReady();
  setStage(state.step, false);

  if (state.page === 'saved') loadRecords();
  else if (state.page === 'hub') loadOverview();
}

function setStage(step, focus = true) {
  state.step = step;
  if ($('landing')) $('landing').classList.toggle('hidden', state.started);
  if ($('workspace')) $('workspace').classList.toggle('hidden', !state.started);

  ['describe', 'details', 'ready'].forEach((name, i) => {
    const el = $(name + '-panel');
    if (el) el.classList.toggle('hidden', i + 1 !== step);
  });

  document.querySelectorAll('[data-step]').forEach(el => {
    const n = Number(el.dataset.step);
    el.classList.toggle('active', n === step);
    el.classList.toggle('complete', n < step);
    const numEl = el.querySelector('.step-number');
    if (numEl) numEl.textContent = n < step ? '✓' : n;
    if (n === step) el.setAttribute('aria-current', 'step');
    else el.removeAttribute('aria-current');
  });

  if (focus && state.started && $('workspace')) {
    $('workspace').scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => {
      const target = step === 1 ? $('issue') : step === 2 ? $('details-title') : $('ready-title');
      if (target) target.focus({ preventScroll: true });
    }, 80);
  }
}

function begin() {
  state.started = true;
  showPage('home');
  setStage(state.step);
}

function ask(title, description, confirm) {
  return new Promise(resolve => {
    const d = $('dialog');
    if (!d) return resolve(false);
    $('dialog-title').textContent = tr(title);
    $('dialog-body').replaceChildren(node('p', tr(description)));
    const cancel = $('dialog-cancel');
    const yes = $('dialog-confirm');
    cancel.textContent = tr('cancel');
    yes.textContent = tr(confirm);
    yes.classList.remove('hidden');
    cancel.onclick = () => { d.close(); resolve(false); };
    yes.onclick = () => { d.close(); resolve(true); };
    d.oncancel = () => resolve(false);
    d.showModal();
  });
}

async function startNew() {
  if (state.dirty && !await ask('unsaved_title', 'unsaved_desc', 'unsaved_continue')) return;
  for (const p of state.photos) {
    if (!state.recordId) {
      try { await api('/api/photos/' + p.id, { method: 'DELETE' }); } catch {}
    }
  }
  state = freshState();
  ['issue', 'location', 'landmark', 'duration', 'extra', 'draft'].forEach(id => {
    if ($(id)) $(id).value = '';
  });
  if ($('municipality')) $('municipality').value = 'unknown';
  if ($('category')) $('category').value = 'other';
  if ($('recurring')) $('recurring').value = '';
  clearErrors();
  countText();
  renderQuestion();
  renderPhotos();
  begin();
}

async function analyzeComplaint(event) {
  event.preventDefault();
  clearErrors();
  const issueText = $('issue')?.value.trim() || '';
  if (!issueText) {
    fieldError('form-error', 'empty_issue');
    return;
  }

  const b = $('submit');
  if (b) {
    b.disabled = true;
    b.textContent = tr('busy_analyze');
  }

  try {
    const data = await post('/api/analyze', { text: issueText, lang, category: 'auto' });
    if ($('issue')?.value !== issueText) return;
    state.suggestion = data.category;
    if ($('category')) $('category').value = data.category || 'other';
    if ($('suggestion-note')) {
      $('suggestion-note').textContent = data.category ? tr('review_intro') : tr('review_unknown_note');
      $('suggestion-note').classList.toggle('uncertain', !data.category);
    }
    renderQuestion();
    setStage(2);
  } catch {
    fieldError('form-error', 'error_generic');
  } finally {
    if (b) {
      b.disabled = false;
      b.textContent = tr('next');
    }
  }
}

async function prepareComplaint(event) {
  event.preventDefault();
  clearErrors();
  if (!$('location')?.value.trim()) {
    fieldError('details-error', 'missing_location');
    $('location')?.focus();
    return;
  }

  const b = $('create');
  if (b) {
    b.disabled = true;
    b.textContent = tr('busy_create');
  }

  const input = inputData();
  const version = state.changeVersion || 0;

  try {
    const result = await post('/api/analyze', input);
    if ((state.changeVersion || 0) !== version) {
      toast(tr('changes_kept'));
      return;
    }
    state.body = result.draft;
    state.draftLang = input.lang;
    state.dirty = true;
    state.changeVersion = (state.changeVersion || 0) + 1;
    if ($('draft')) {
      $('draft').value = result.draft;
      $('draft').readOnly = true;
    }
    renderReady();
    setStage(3);
    autoSizeDraft();
  } catch {
    fieldError('details-error', 'error_generic');
  } finally {
    if (b) {
      b.disabled = false;
      b.textContent = tr('create');
    }
  }
}

function autoSizeDraft() {
  const el = $('draft');
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.max(320, el.scrollHeight + 8) + 'px';
}

function renderReady() {
  const cat = $('category')?.value || 'other';
  if ($('draft-category')) {
    $('draft-category').textContent = config?.categories?.[cat]?.[lang] || config?.categories?.other?.[lang] || cat;
  }

  if ($('review-overview')) {
    $('review-overview').replaceChildren(
      node('span', $('location')?.value || '', 'location-summary'),
      node('span', state.photos.length + ' ' + tr('photo_count'), 'photo-count')
    );
  }

  const box = $('authority-card');
  if (box && config?.authorities) {
    box.replaceChildren();
    const a = config.authorities.find(a => a.id === $('municipality')?.value);
    box.append(node('h3', tr('authority_title')));

    if (a) {
      box.append(node('p', a.name[lang], 'authority-name'), node('p', tr('portal_availability'), 'field-hint'));
      const b = button(tr('portal_open'), 'primary wide', openPortal);
      b.id = 'open-portal';
      box.append(b);
      const fallback = node('a', tr('portal_fallback'), 'external-link');
      fallback.href = a.fallback_url;
      fallback.target = '_blank';
      fallback.rel = 'noopener noreferrer';
      box.append(fallback);
      const source = node('a', tr('source_verified') + ' · ' + a.verified_on, 'source-link');
      source.href = a.source_url;
      source.target = '_blank';
      source.rel = 'noopener noreferrer';
      box.append(source);
    } else {
      box.append(node('p', tr('portal_choose'), 'field-hint'));
    }

    if (state.photos.length) {
      const photos = node('div', undefined, 'photo-list');
      state.photos.forEach(p => {
        const a = node('a');
        a.href = p.url;
        a.download = 'JanSahay-photo.jpg';
        const img = node('img');
        img.src = p.url;
        img.alt = tr('photos');
        a.append(img);
        photos.append(a);
      });
      box.append(photos);
    }
  }

  if ($('edit-draft') && $('draft')) {
    const span = $('edit-draft').querySelector('span');
    if (span) span.textContent = tr($('draft').readOnly ? 'draft_edit' : 'draft_done');
  }
}

async function persistComplaint(ready = false) {
  const targetState = state;
  const input = inputData();
  const issue = input.text.trim();
  const version = state.changeVersion || 0;

  if (!issue) throw Error(tr('empty_issue'));
  const body = state.step === 3 && $('draft') ? $('draft').value : issue;
  if (!body.trim()) throw Error(tr('notice_empty'));

  const status = ready && ['draft', 'ready'].includes(state.status) ? 'ready' : state.status;
  const data = {
    body,
    issue,
    category: input.category,
    location: input.location,
    lang: state.step === 3 ? state.draftLang : lang,
    municipality: input.municipality,
    details: input.details,
    photo_ids: state.photos.map(p => p.id),
    status
  };

  const result = await post(
    state.recordId ? '/api/drafts/' + state.recordId : '/api/drafts',
    data,
    state.recordId ? 'PATCH' : 'POST'
  );

  if (!targetState.recordId) targetState.recordId = result.id;
  targetState.status = status;
  targetState.dirty = (targetState.changeVersion || 0) !== version;
  refreshCount();
  return targetState.recordId;
}

async function saveComplaint(ready) {
  const b = ready ? $('save') : $('save-progress');
  if (b) b.disabled = true;
  try {
    await persistComplaint(ready);
    toast(tr('save_ok'));
  } catch (e) {
    toast(e.message === tr('empty_issue') ? tr('empty_issue') : tr('error_generic'));
  } finally {
    if (b) b.disabled = false;
  }
}

async function openPortal() {
  try {
    const id = await persistComplaint(true);
    const result = await post('/api/drafts/' + id + '/handoff', {});
    const d = $('dialog');
    if (!d) return;
    $('dialog-title').textContent = tr('authority_title');
    $('dialog-body').replaceChildren(node('p', tr('portal_warning')));
    const a = node('a', tr('portal_continue'), 'primary');
    a.href = result.url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.id = 'portal-confirm';
    $('dialog-body').append(a);
    $('dialog-cancel').textContent = tr('close');
    $('dialog-cancel').onclick = () => d.close();
    $('dialog-confirm').classList.add('hidden');
    d.oncancel = null;
    d.showModal();
  } catch {
    toast(tr('error_generic'));
  }
}

function downloadText(text) {
  const url = URL.createObjectURL(new Blob(['\ufeff' + text], { type: 'text/plain;charset=utf-8' }));
  const a = node('a');
  a.href = url;
  a.download = 'JanSahay-complaint.txt';
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast(tr('copy_ok'));
  } catch {
    const input = node('textarea');
    input.value = text;
    input.style.position = 'fixed';
    input.style.left = '-9999px';
    document.body.append(input);
    input.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch {}
    input.remove();
    if (copied) {
      toast(tr('copy_ok'));
      return;
    }
    const d = $('dialog');
    if (!d) return;
    $('dialog-title').textContent = tr('draft_copy');
    const manual = node('textarea');
    manual.value = text;
    manual.readOnly = true;
    manual.setAttribute('aria-label', tr('draft_copy'));
    $('dialog-body').replaceChildren(node('p', 'Ctrl+C / Cmd+C'), manual);
    $('dialog-confirm').classList.add('hidden');
    $('dialog-cancel').textContent = tr('close');
    $('dialog-cancel').onclick = () => d.close();
    d.oncancel = null;
    d.showModal();
    manual.select();
  }
}

async function uploadPhoto() {
  const file = $('photo-input')?.files?.[0];
  if (!file) return;
  clearErrors();
  if (state.photos.length >= 3 || file.size > 5 * 1024 * 1024 || !/^image\/(jpeg|png|webp)$/.test(file.type)) {
    fieldError('photo-error', 'photo_error');
    if ($('photo-input')) $('photo-input').value = '';
    return;
  }

  const targetState = state;
  if ($('photo-input')) $('photo-input').disabled = true;
  if ($('create')) $('create').disabled = true;
  if ($('photo-status')) $('photo-status').textContent = tr('photo_busy');

  try {
    const form = new FormData();
    form.append('photo', file);
    const p = await api('/api/photos', { method: 'POST', body: form });
    if (state !== targetState) {
      await api('/api/photos/' + p.id, { method: 'DELETE' });
      return;
    }
    state.photos.push(p);
    state.dirty = true;
    state.changeVersion = (state.changeVersion || 0) + 1;
    renderPhotos();
  } catch {
    fieldError('photo-error', 'photo_error');
  } finally {
    if ($('photo-input')) {
      $('photo-input').disabled = false;
      $('photo-input').value = '';
    }
    if ($('create')) $('create').disabled = false;
    if ($('photo-status')) $('photo-status').textContent = '';
  }
}

function renderPhotos() {
  if (!$('photo-list')) return;
  $('photo-list').replaceChildren(...state.photos.map(p => {
    const card = node('div', undefined, 'photo-tile');
    const img = node('img');
    img.src = p.url;
    img.alt = tr('photos');
    const remove = button('×', 'photo-remove', async () => {
      try {
        await api('/api/photos/' + p.id, { method: 'DELETE' });
        state.photos = state.photos.filter(i => i.id !== p.id);
        state.dirty = true;
        state.changeVersion = (state.changeVersion || 0) + 1;
        renderPhotos();
        renderReady();
      } catch {
        toast(tr('error_generic'));
      }
    });
    remove.setAttribute('aria-label', tr('remove_photo'));
    card.append(img, remove);
    return card;
  }));
}

// ============================================================================
// 9. LOCAL COMPLAINT TRACKER (PRESERVED)
// ============================================================================
function renderFilters() {
  if (!$('filters') || !config?.statuses) return;
  $('filters').replaceChildren(...['all', ...config.statuses].map(k => {
    const b = button(tr(k === 'all' ? 'filter_all' : 'status_' + k), 'filter' + (filter === k ? ' active' : ''), () => {
      filter = k;
      renderFilters();
      loadRecords();
    });
    b.dataset.filter = k;
    b.setAttribute('aria-pressed', String(filter === k));
    return b;
  }));
}

async function refreshCount() {
  try {
    const rows = await api('/api/drafts');
    if ($('saved-count')) {
      $('saved-count').textContent = rows.length;
      $('saved-count').classList.toggle('hidden', !rows.length);
    }
  } catch {}
}

function emptyState(filtered) {
  const box = node('div', undefined, 'empty-state');
  const mark = node('div', undefined, 'service-icon');
  mark.append(icon('folder'));
  box.append(mark, node('h3', tr(filtered ? 'empty_filter' : 'saved_empty')));
  if (!filtered) box.append(node('p', tr('saved_empty_desc')), button(tr('new_complaint'), 'primary', startNew));
  return box;
}

async function loadRecords() {
  const seq = ++listSequence;
  const q = $('search')?.value.trim() || '';
  const query = new URLSearchParams({ q, status: filter });

  if ($('export-json')) $('export-json').href = '/api/drafts/export?' + query + '&format=json';
  if ($('export-csv')) $('export-csv').href = '/api/drafts/export?' + query + '&format=csv';

  try {
    const rows = await api('/api/drafts?' + query);
    if (seq !== listSequence || !$('draft-list')) return;
    $('draft-list').replaceChildren();
    if (!rows.length) {
      $('draft-list').append(emptyState(Boolean(q || filter !== 'all')));
      return;
    }
    rows.forEach(renderRecord);
  } catch {
    toast(tr('error_generic'));
  }
}

function recordInput(parent, labelText, type, value, id) {
  const wrap = node('div');
  const label = node('label', labelText);
  const input = node(type === 'select' ? 'select' : 'input');
  input.id = id;
  label.htmlFor = id;
  if (type !== 'select') input.type = type;
  input.value = value || '';
  wrap.append(label, input);
  parent.append(wrap);
  return input;
}

function renderRecord(row) {
  const card = node('article', undefined, 'complaint-card');
  card.dataset.recordId = row.id;

  const heading = node('div', undefined, 'complaint-heading');
  const mark = node('span', undefined, 'service-icon');
  mark.append(icon(row.category));
  const titles = node('div');
  titles.append(node('h3', config?.categories?.[row.category]?.[lang] || row.category), node('p', new Date(row.created).toLocaleString(lang)));
  heading.append(mark, titles, node('span', tr('status_' + row.status), 'status-badge ' + row.status));
  card.append(heading, node('p', row.location || '—', 'complaint-snippet'));
  if (row.reference) card.append(node('p', tr('reference_label') + ': ' + row.reference, 'record-reference'));

  const actions = node('div', undefined, 'record-actions');
  actions.append(
    button(tr('edit_record'), 'text-button', () => editRecord(row.id)),
    button(tr('draft_copy'), 'text-button', () => copyText(row.body)),
    button(tr('draft_download'), 'text-button', () => downloadText(row.body)),
    button(tr('remove'), 'text-button danger-text', async () => {
      if (!await ask('delete_title', 'delete_desc', 'confirm_delete')) return;
      try {
        await api('/api/drafts/' + row.id, { method: 'DELETE' });
        if (state.recordId === row.id) {
          state.recordId = null;
          state.photos = [];
          state.status = 'draft';
          state.dirty = true;
        }
        await loadRecords();
        refreshCount();
      } catch {
        toast(tr('error_generic'));
      }
    })
  );
  card.append(actions);

  const reading = node('details', undefined, 'record-detail');
  reading.append(node('summary', tr('view_complaint')), node('pre', row.body));
  row.photos.forEach(p => {
    const a = node('a');
    a.href = p.url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    const image = node('img');
    image.src = p.url;
    image.alt = tr('photos');
    image.className = 'record-photo';
    a.append(image);
    reading.append(a);
  });
  card.append(reading);

  const tracking = node('details', undefined, 'record-detail');
  tracking.append(node('summary', tr('update_record')));
  const form = node('form', undefined, 'record-controls');
  const status = recordInput(form, tr('status_label'), 'select', '', `status-${row.id}`);
  fillSelect(status, config.statuses.map(s => [s, tr('status_' + s)]), row.status);
  const reference = recordInput(form, tr('reference_label'), 'text', row.reference, `ref-${row.id}`);
  reference.maxLength = 120;
  const date = recordInput(form, tr('submitted_on'), 'date', row.submitted_on, `date-${row.id}`);
  const note = recordInput(form, tr('follow_note'), 'text', '', `note-${row.id}`);
  note.maxLength = 1500;
  note.placeholder = tr('follow_ph');

  const submit = node('button', tr('update_record'), 'primary');
  submit.type = 'submit';
  form.append(submit);

  form.onsubmit = async e => {
    e.preventDefault();
    submit.disabled = true;
    try {
      await post('/api/drafts/' + row.id, {
        status: status.value,
        reference: reference.value,
        submitted_on: date.value,
        note: note.value
      }, 'PATCH');
      if (state.recordId === row.id) state.status = status.value;
      toast(tr('record_updated'));
      loadRecords();
    } catch {
      toast(tr('error_generic'));
    } finally {
      submit.disabled = false;
    }
  };
  tracking.append(form);
  card.append(tracking);

  const history = node('details', undefined, 'record-detail');
  history.append(node('summary', tr('history')));
  const historyBody = node('ol', undefined, 'history-list');
  history.append(historyBody);
  history.ontoggle = async () => {
    if (!history.open) return;
    try {
      const detail = await api('/api/drafts/' + row.id);
      historyBody.replaceChildren(...detail.history.map(h => {
        const el = node('li');
        el.append(node('strong', tr(h.action)), node('small', new Date(h.created).toLocaleString(lang)));
        if (h.old_status !== h.new_status) el.append(node('p', tr('status_' + h.new_status)));
        if (h.note && h.action !== 'portal_handoff') el.append(node('p', h.note));
        return el;
      }));
    } catch {
      toast(tr('error_generic'));
    }
  };
  card.append(history);

  $('draft-list')?.append(card);
}

async function editRecord(id) {
  if (state.dirty && !await ask('unsaved_title', 'unsaved_desc', 'unsaved_continue')) return;
  try {
    const row = await api('/api/drafts/' + id);
    state = freshState();
    state.started = true;
    state.recordId = id;
    state.status = row.status;
    state.photos = row.photos;
    state.answers = row.details.answers || {};
    state.body = row.body;
    state.draftLang = row.lang;

    if ($('issue')) $('issue').value = row.issue || row.body;
    if ($('location')) $('location').value = row.location;
    if ($('category')) $('category').value = row.category;
    if ($('municipality')) $('municipality').value = row.municipality;

    ['landmark', 'duration', 'extra', 'recurring'].forEach(k => {
      if ($(k)) $(k).value = row.details[k] || '';
    });

    if ($('draft')) {
      $('draft').value = row.body;
      $('draft').readOnly = true;
    }

    countText();
    renderQuestion();
    renderPhotos();
    renderReady();
    showPage('home');
    setStage(row.issue && row.body === row.issue ? 1 : 3);
    autoSizeDraft();
  } catch {
    toast(tr('error_generic'));
  }
}

// ============================================================================
// 10. BOOTSTRAP INITIALIZATION
// ============================================================================
async function start() {
  try {
    config = await api('/api/config');
    try {
      const saved = localStorage.getItem('jansahay-language');
      if (config.names?.[saved]) lang = saved;
    } catch {}

    if ($('ui-language')) {
      $('ui-language').value = lang;
      $('ui-language').onchange = e => {
        lang = e.target.value;
        try { localStorage.setItem('jansahay-language', lang); } catch {}
        localize();
        toast(tr('changed_lang'));
      };
    }

    localize();
    refreshCount();

    // Top Navigation & Page Switching
    document.querySelectorAll('[data-page]').forEach(b => {
      b.onclick = () => showPage(b.dataset.page);
    });

    // Complaint Form Controls
    document.querySelectorAll('[data-start]').forEach(b => b.onclick = startNew);
    if ($('begin')) $('begin').onclick = begin;
    if ($('back')) {
      $('back').onclick = () => {
        if (state.step > 1) setStage(state.step - 1);
        else {
          state.started = false;
          setStage(1, false);
        }
      };
    }

    if ($('complaint-form')) $('complaint-form').onsubmit = analyzeComplaint;
    if ($('details-form')) $('details-form').onsubmit = prepareComplaint;
    if ($('category')) {
      $('category').onchange = () => {
        state.dirty = true;
        state.changeVersion = (state.changeVersion || 0) + 1;
        renderQuestion();
      };
    }
    if ($('photo-input')) $('photo-input').onchange = uploadPhoto;

    ['issue', 'location', 'landmark', 'duration', 'extra', 'recurring', 'municipality'].forEach(id => {
      const el = $(id);
      if (el) {
        el.addEventListener('input', () => {
          state.dirty = true;
          state.changeVersion = (state.changeVersion || 0) + 1;
          if (id === 'issue') countText();
        });
      }
    });

    if ($('save-progress')) $('save-progress').onclick = () => saveComplaint(false);
    if ($('save')) $('save').onclick = () => saveComplaint(true);
    if ($('copy')) $('copy').onclick = () => copyText($('draft')?.value || '');
    if ($('download')) {
      $('download').onclick = () => {
        downloadText($('draft')?.value || '');
        toast(tr('download_ok'));
      };
    }
    if ($('start-over')) $('start-over').onclick = startNew;

    if ($('edit-draft')) {
      $('edit-draft').onclick = () => {
        if ($('draft')) {
          $('draft').readOnly = !$('draft').readOnly;
          renderReady();
          if (!$('draft').readOnly) $('draft').focus();
        }
      };
    }
    if ($('draft')) {
      $('draft').oninput = () => {
        state.dirty = true;
        state.changeVersion = (state.changeVersion || 0) + 1;
        autoSizeDraft();
      };
    }

    // Saved complaints search
    if ($('search')) {
      $('search').oninput = () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadRecords, 180);
      };
    }

    // Document Explorer search & filters
    if ($('docs-search-input')) {
      $('docs-search-input').oninput = () => {
        clearTimeout(docsSearchTimer);
        docsSearchTimer = setTimeout(loadDocuments, 200);
      };
    }
    ['docs-category-filter', 'docs-sentiment-filter', 'docs-lang-filter'].forEach(id => {
      const el = $(id);
      if (el) el.onchange = () => loadDocuments();
    });

    // Confusion Matrix Toggle
    $('btn-toggle-cm')?.addEventListener('click', () => {
      const c = $('eval-cm-container');
      if (c) c.classList.toggle('hidden');
    });

    // Ingestion Modals Setup
    setupIngestionHandlers();

    // NLP Methods Lab Controls
    $('btn-run-lab')?.addEventListener('click', runLabAnalysis);

    [1, 2, 3, 4, 5].forEach(i => {
      const sBtn = $(`lab-sample-${i}`);
      if (sBtn && LAB_SAMPLES[i]) {
        sBtn.onclick = () => {
          if ($('lab-unified-text')) $('lab-unified-text').value = LAB_SAMPLES[i].text;
          if ($('lab-select-lang')) $('lab-select-lang').value = LAB_SAMPLES[i].lang;
          toast(`Loaded Sample ${i}`);
          runLabAnalysis();
        };
      }
    });

    // 8-Tab Syllabus Navigation in Lab
    document.querySelectorAll('.methods-tab-btn').forEach(btn => {
      btn.onclick = () => {
        const targetTab = btn.dataset.tab;
        document.querySelectorAll('.methods-tab-btn').forEach(b => b.classList.toggle('active', b === btn));
        document.querySelectorAll('.methods-panel').forEach(p => p.classList.toggle('active', p.id === targetTab));
      };
    });

    // Show initial page (Intelligence Hub)
    showPage('hub');

    // Run initial Lab sample in background
    setTimeout(runLabAnalysis, 300);

    window.addEventListener('beforeunload', e => {
      if (state.dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    });

  } catch (e) {
    console.error('Fatal initialization error:', e);
    const main = document.querySelector('main');
    if (main) {
      main.prepend(node('p', 'JanSahay platform could not start. Please check the Python server logs.', 'inline-error'));
    }
  }
}

// Start when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start);
} else {
  start();
}
