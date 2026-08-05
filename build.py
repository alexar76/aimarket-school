#!/usr/bin/env python3
"""Build AIMarket School static site (EN + RU/ES/FR/ZH).

Default (nested under ecosystem landing):
  python3 school/build.py
  → ecosystem-landing/school/ + ecosystem-landing/{lang}/school/

Dedicated edu portal (edu.modelmarket.dev at site root):
  SEO_BASE_URL=https://edu.modelmarket.dev SCHOOL_MOUNT= SCHOOL_OUT=edu-landing \\
    LEARN_BASE=https://modeldev.modelmarket.dev python3 school/build.py
  → edu-landing/ + edu-landing/{lang}/
"""

from __future__ import annotations

import html
import json
import os
import shutil
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]
SCHOOL = Path(__file__).resolve().parent
NB_OUT = SCHOOL / "notebooks"
BASE = os.environ.get("SEO_BASE_URL", "https://modeldev.modelmarket.dev").rstrip("/")
LEARN_BASE = os.environ.get("LEARN_BASE", "https://modeldev.modelmarket.dev").rstrip("/")
COURSES = "https://alexar76.github.io/aimarket-courses"
GITHUB_NB = "https://colab.research.google.com/github/alexar76/aicom/blob/main/school/notebooks"
LANGS = ("en", "ru", "es", "fr", "zh")
# URL mount segment: "school" (default → /school/…) or "" for site-root edu portal
MOUNT = os.environ.get("SCHOOL_MOUNT", "school").strip().strip("/")
OUT_ROOT = Path(os.environ.get("SCHOOL_OUT", str(ROOT / "ecosystem-landing")))
if not OUT_ROOT.is_absolute():
    OUT_ROOT = ROOT / OUT_ROOT


CSS = r"""
:root {
  --ink: #eef3ff;
  --muted: #8b9bb8;
  --faint: #5a6a86;
  --bg: #03060f;
  --bg2: #070d1c;
  --lime: #b8f23a;
  --lime2: #8fd41a;
  --ice: #7ee7ff;
  --hot: #ff5a36;
  --nebula: #1a3a5c;
  --line: rgba(126, 231, 255, 0.14);
  --head: "Syne", system-ui, sans-serif;
  --body: "IBM Plex Sans", system-ui, sans-serif;
  --max: 1100px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: var(--body); font-size: 17px; line-height: 1.5;
  min-height: 100vh; overflow-x: hidden;
}
a { color: var(--lime); text-decoration: none; }
a:hover { color: #fff; }
.wrap { width: min(var(--max), calc(100% - 32px)); margin: 0 auto; position: relative; z-index: 2; }
nav {
  position: sticky; top: 0; z-index: 30;
  backdrop-filter: blur(14px);
  background: rgba(3, 6, 15, 0.78);
  border-bottom: 1px solid var(--line);
}
nav .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 58px; flex-wrap: wrap; }
.brand { font-family: var(--head); font-weight: 800; letter-spacing: -0.03em; color: var(--ink); font-size: 1.05rem; }
.brand span { color: var(--lime); }
.nav-links { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; font-size: 0.88rem; }
.nav-links a { color: var(--muted); }
.nav-links a:hover, .nav-links a[aria-current] { color: var(--lime); }
.lang-switch { display: flex; gap: 4px; align-items: center; }
.lang-switch a {
  font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--faint); padding: 4px 6px; border: 1px solid transparent; border-radius: 3px;
}
.lang-switch a[aria-current] { color: var(--ice); border-color: var(--line); }
.lang-switch a:hover { color: var(--ink); }

/* —— cosmic portal hero —— */
.hero-cosmic {
  position: relative; isolation: isolate;
  min-height: min(92vh, 760px);
  display: flex; align-items: flex-end;
  padding: 0 0 56px;
  border-bottom: 1px solid var(--line);
  overflow: hidden;
}
.hero-cosmic .sky {
  position: absolute; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 70% 55% at 70% 20%, rgba(26, 58, 92, 0.55), transparent 60%),
    radial-gradient(ellipse 45% 40% at 15% 70%, rgba(184, 242, 58, 0.12), transparent 55%),
    radial-gradient(ellipse 50% 35% at 85% 80%, rgba(255, 90, 54, 0.14), transparent 50%),
    linear-gradient(180deg, #010309 0%, #03060f 55%, #050a16 100%);
}
.hero-cosmic canvas#cosmos {
  position: absolute; inset: 0; width: 100%; height: 100%; z-index: 1; display: block;
}
.hero-cosmic .veil {
  position: absolute; inset: 0; z-index: 1; pointer-events: none;
  background: linear-gradient(180deg, transparent 40%, rgba(3,6,15,0.75) 78%, var(--bg) 100%);
}
.hero-cosmic .wrap { z-index: 2; padding-top: clamp(72px, 14vh, 120px); }
.eyebrow {
  font-size: 0.78rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--ice); font-weight: 600; margin: 0 0 16px;
}
.hero-cosmic .brand-hero {
  font-family: var(--head); font-weight: 800;
  font-size: clamp(2.6rem, 8vw, 4.4rem); line-height: 0.95;
  letter-spacing: -0.045em; margin: 0 0 18px; max-width: 12ch;
  text-shadow: 0 0 40px rgba(184,242,58,0.25);
}
.hero-cosmic .brand-hero span { color: var(--lime); }
.hero-cosmic h1 {
  font-family: var(--head); font-weight: 800;
  font-size: clamp(1.35rem, 3.2vw, 1.85rem); line-height: 1.15;
  letter-spacing: -0.03em; margin: 0 0 12px; max-width: 22ch;
  color: var(--ink);
}
.hero-cosmic .lede { color: var(--muted); max-width: 40ch; margin: 0 0 28px; font-size: 1.05rem; }
.ctas { display: flex; flex-wrap: wrap; gap: 10px; }
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 12px 18px; border-radius: 4px; font-weight: 700; font-size: 0.95rem;
  border: 1px solid transparent; cursor: pointer; font-family: var(--body);
}
.btn-primary { background: var(--lime); color: #081208; }
.btn-primary:hover { background: #d4ff5c; color: #081208; }
.btn-ghost { border-color: var(--line); color: var(--ink); background: rgba(7,13,28,0.55); }
.btn-ghost:hover { border-color: var(--ice); color: var(--ice); }
.btn-hot { background: var(--hot); color: #fff; }
.btn-hot:hover { filter: brightness(1.08); color: #fff; }

.catalog-head {
  padding: 48px 0 8px;
  font-family: var(--head); font-weight: 800; font-size: 1.15rem;
  letter-spacing: -0.02em; color: var(--muted);
}
.grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px; padding: 16px 0 72px;
}
.card {
  display: flex; flex-direction: column; gap: 8px;
  padding: 20px 18px 18px; border: 1px solid var(--line);
  background:
    linear-gradient(155deg, rgba(126,231,255,0.07), transparent 45%),
    linear-gradient(320deg, rgba(184,242,58,0.05), transparent 40%),
    var(--bg2);
  min-height: 188px; transition: border-color .18s, transform .18s, box-shadow .18s;
  position: relative; overflow: hidden;
}
.card::before {
  content: ""; position: absolute; top: -20%; right: -15%; width: 90px; height: 90px;
  background: radial-gradient(circle, rgba(184,242,58,0.18), transparent 70%);
  pointer-events: none;
}
.card:hover {
  border-color: rgba(184,242,58,0.55);
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.35), 0 0 24px rgba(126,231,255,0.08);
}
.card .num {
  font-family: var(--head); font-size: 0.78rem; color: var(--ice); letter-spacing: 0.1em;
}
.card h3 {
  font-family: var(--head); font-size: 1.22rem; letter-spacing: -0.02em;
  margin: 0; line-height: 1.15; color: var(--ink);
}
.card p { margin: 0; color: var(--muted); font-size: 0.92rem; flex: 1; }
.card .meta { font-size: 0.78rem; color: var(--faint); }

.section { padding: 40px 0 64px; }
.lesson-hero h1 {
  font-family: var(--head); font-weight: 800;
  font-size: clamp(1.9rem, 4.5vw, 2.8rem); letter-spacing: -0.03em;
  margin: 0 0 10px; line-height: 1.05; max-width: 16ch;
}
.layout {
  display: grid; grid-template-columns: 1.05fr 1fr; gap: 28px; align-items: start;
}
@media (max-width: 860px) { .layout { grid-template-columns: 1fr; } }
.reel {
  position: relative; aspect-ratio: 9 / 16; max-height: 560px; width: min(100%, 320px);
  margin: 0 auto; border: 1px solid var(--line); background: #02050c; overflow: hidden;
  border-radius: 12px;
  box-shadow: 0 0 48px rgba(126,231,255,0.08), inset 0 0 40px rgba(184,242,58,0.04);
}
.reel canvas { width: 100%; height: 100%; display: block; }
.reel .cap {
  position: absolute; left: 12px; right: 12px; bottom: 16px;
  font-family: var(--head); font-size: 1.15rem; font-weight: 800;
  letter-spacing: -0.02em; text-shadow: 0 2px 12px #000;
  transition: opacity .25s;
}
.reel .progress {
  position: absolute; left: 0; right: 0; top: 0; height: 3px; background: rgba(255,255,255,0.1);
}
.reel .progress > i {
  display: block; height: 100%; width: 0; background: linear-gradient(90deg, var(--lime), var(--ice));
}
.panel {
  border: 1px solid var(--line); padding: 18px; background: var(--bg2);
}
.panel h2 {
  font-family: var(--head); font-size: 1.1rem; margin: 0 0 10px; letter-spacing: -0.02em;
}
.panel pre {
  margin: 0 0 12px; padding: 12px; background: #02050c; border: 1px solid var(--line);
  font-size: 0.78rem; overflow: auto; max-height: 220px; color: #c8e8d8;
  white-space: pre-wrap; word-break: break-word;
}
.steps { margin: 0 0 18px; padding-left: 18px; color: var(--muted); }
.steps li { margin: 6px 0; }
.note { color: var(--faint); font-size: 0.85rem; margin-top: 18px; }
footer {
  border-top: 1px solid var(--line); padding: 28px 0 40px; color: var(--faint); font-size: 0.88rem;
}
footer .row { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
@media (prefers-reduced-motion: reduce) {
  .card:hover { transform: none; }
}
"""


COSMOS_JS = r"""
function playCosmos(canvas) {
  const ctx = canvas.getContext('2d');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let W = 0, H = 0, dpr = 1, t0 = performance.now();
  const stars = [];
  function resize() {
    dpr = Math.min(devicePixelRatio || 1, 2);
    const nw = Math.floor(canvas.clientWidth * dpr);
    const nh = Math.floor(canvas.clientHeight * dpr);
    if (nw === W && nh === H) return;
    W = canvas.width = nw; H = canvas.height = nh;
    stars.length = 0;
    const n = Math.floor((W * H) / (9000 * dpr));
    for (let i = 0; i < n; i++) {
      stars.push({
        x: Math.random() * W, y: Math.random() * H,
        r: (Math.random() * 1.4 + 0.3) * dpr,
        a: Math.random() * 0.7 + 0.2,
        s: Math.random() * 0.25 + 0.05
      });
    }
  }
  resize();
  window.addEventListener('resize', resize, { passive: true });
  const nodes = [[0.18,0.35],[0.42,0.22],[0.62,0.38],[0.48,0.58],[0.78,0.48],[0.70,0.72]];
  function frame(now) {
    if (!W || !H) resize();
    const u = ((now - t0) % 20000) / 20000;
    ctx.clearRect(0, 0, W, H);
    // nebula soft blobs
    const blobs = [
      [0.7, 0.25, 0.35, 'rgba(30,70,120,0.35)'],
      [0.2, 0.65, 0.28, 'rgba(184,242,58,0.08)'],
      [0.85, 0.75, 0.22, 'rgba(255,90,54,0.1)']
    ];
    blobs.forEach(([x,y,r,c], i) => {
      const ox = x + 0.02 * Math.sin(u * Math.PI * 2 + i);
      const oy = y + 0.015 * Math.cos(u * Math.PI * 2 + i);
      const g = ctx.createRadialGradient(ox*W, oy*H, 0, ox*W, oy*H, r*W);
      g.addColorStop(0, c); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(0,0,W,H);
    });
    stars.forEach((s, i) => {
      const tw = s.a * (0.55 + 0.45 * Math.sin(u * Math.PI * 2 * 3 + i));
      ctx.fillStyle = `rgba(230,240,255,${tw})`;
      ctx.beginPath(); ctx.arc(s.x, (s.y + u * s.s * H * 0.15) % H, s.r, 0, Math.PI * 2); ctx.fill();
    });
    // constellation
    ctx.strokeStyle = 'rgba(126,231,255,0.28)';
    ctx.lineWidth = 1.2 * dpr;
    for (let i = 0; i < nodes.length - 1; i++) {
      const a = nodes[i], b = nodes[i+1];
      ctx.beginPath();
      ctx.moveTo(a[0]*W, a[1]*H); ctx.lineTo(b[0]*W, b[1]*H); ctx.stroke();
    }
    const hop = u * (nodes.length - 1);
    const si = Math.min(nodes.length - 2, Math.floor(hop));
    const sf = hop - si;
    const a = nodes[si], b = nodes[si+1];
    const px = (a[0] + (b[0]-a[0])*sf) * W;
    const py = (a[1] + (b[1]-a[1])*sf) * H;
    nodes.forEach((n, i) => {
      const pulse = 0.5 + 0.5 * Math.sin(u * Math.PI * 2 + i);
      ctx.fillStyle = i === Math.floor(u * nodes.length) % nodes.length ? '#ff5a36' : '#b8f23a';
      ctx.beginPath(); ctx.arc(n[0]*W, n[1]*H, (3.5 + pulse * 2.5) * dpr, 0, Math.PI*2); ctx.fill();
    });
    ctx.fillStyle = '#fff';
    ctx.beginPath(); ctx.arc(px, py, 4 * dpr, 0, Math.PI*2); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.35)';
    ctx.beginPath(); ctx.arc(px, py, 10 * dpr, 0, Math.PI*2); ctx.stroke();
    if (!reduce) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
"""


DEMO_JS = r"""
async function schoolDemo(kind, outEl) {
  outEl.textContent = 'Running…';
  const HUB = 'https://modelmarket.dev';
  const FAMILY = 'https://oracles.modelmarket.dev/family';
  try {
    if (kind === 'hub_search') {
      const r = await fetch(`${HUB}/ai-market/v2/search?intent=oracle&limit=5`);
      const d = await r.json();
      outEl.textContent = (d.matches || []).map(m => `${m.capability_id}  $${m.price_per_call_usd}`).join('\n') || JSON.stringify(d).slice(0, 500);
    } else if (kind === 'platon_random') {
      const r = await fetch(`${FAMILY}/ai-market/v2/invoke`, {
        method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({capability_id: 'platon.random@v1', input: {}})
      });
      const d = await r.json();
      outEl.textContent = `random_hex: ${d.output?.random_hex}\nscheme: ${d.output?.proof?.scheme}\nok: ${d.ok}`;
    } else if (kind === 'payment_402') {
      const r = await fetch(`${HUB}/ai-market/v2/invoke`, {
        method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({
          product_id: 'prod-platon', capability_id: 'platon.random@v1',
          source_hub: 'https://oracles.modelmarket.dev/family', input: {}
        })
      });
      const t = await r.text();
      outEl.textContent = `HTTP ${r.status}\n${t.slice(0, 500)}`;
    } else if (kind === 'hub_stats' || kind === 'factory_health') {
      const r = await fetch(`${HUB}/.well-known/ai-market.json`);
      const d = await r.json();
      outEl.textContent = JSON.stringify({
        name: d.name, hub_version: d.hub_version,
        payment_configured: d.payment_configured,
        federated: d.federated_capabilities_count,
        demo_mode: d.plugin_extensions?.['aimarket-channels']?.channels?.demo_mode
      }, null, 2);
    } else if (kind === 'warden_static') {
      outEl.textContent = [
        'WARDEN threat model (clip):',
        '',
        'SAFE   get_weather(city)',
        '       → returns forecast JSON',
        'POISON get_weather(city)',
        '       → also reads ~/.ssh and exfils',
        '',
        'Rule: pin tools. Scan before invoke.',
        'Academy: MCP Security & Agent Safety'
      ].join('\n');
    } else if (kind === 'search_proof' || kind === 'search_physics') {
      const intent = kind === 'search_physics' ? 'murmuration' : 'optimize';
      const r = await fetch(`${HUB}/ai-market/v2/search?intent=${intent}&limit=6`);
      const d = await r.json();
      outEl.textContent = (d.matches || []).map(m => `${m.capability_id}\n  ${m.description || ''}`).join('\n\n') || tSlice(d);
    } else if (kind === 'basescan_escrow') {
      outEl.textContent = 'Opening Basescan escrow…';
      window.open('https://basescan.org/address/0x0606983cbEc6D0C12a0B750f72Ceb6032c72C25D', '_blank', 'noopener');
      outEl.textContent = 'Escrow 0x0606983c…72C25D — Base mainnet.\nExternal depositor proof: onchain-journal §3j.';
    } else if (kind === 'mesh_live') {
      window.open('https://service-mesh.modelmarket.dev/', '_blank', 'noopener');
      outEl.textContent = 'Opened live mesh dashboard.\nLanding: https://alexar76.github.io/ai-service-mesh/';
    } else {
      outEl.textContent = 'Unknown demo: ' + kind;
    }
  } catch (e) {
    outEl.textContent = 'Error: ' + e;
  }
}
function tSlice(d) { return JSON.stringify(d).slice(0, 500); }

function playReel(canvas, beats, capEl, barEl, scene) {
  const ctx = canvas.getContext('2d');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let t0 = performance.now();
  const dur = 10000;
  let W = 0, H = 0, dpr = 1;
  const C = { cyan:'#7ee7ff', lime:'#b8f23a', hot:'#ff5a36', gold:'#f5c542', violet:'#a78bfa', ink:'#02050c' };
  function resize() {
    dpr = Math.min(devicePixelRatio || 1, 2);
    const cw = Math.max(canvas.clientWidth || 320, 160);
    const ch = Math.max(canvas.clientHeight || 480, 240);
    const nw = Math.floor(cw * dpr), nh = Math.floor(ch * dpr);
    if (nw === W && nh === H) return false;
    W = canvas.width = nw; H = canvas.height = nh;
    return true;
  }
  resize();
  window.addEventListener('resize', resize, { passive: true });
  function hexA(hex, a) {
    const n = hex.replace('#','');
    const r = parseInt(n.slice(0,2),16), g = parseInt(n.slice(2,4),16), b = parseInt(n.slice(4,6),16);
    return `rgba(${r},${g},${b},${a})`;
  }
  function nebula(u, palette) {
    ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H);
    palette.forEach(([hx, hy, rr, col, aa], i) => {
      const x = (hx + 0.03 * Math.sin(u * Math.PI * 2 + i)) * W;
      const y = (hy + 0.02 * Math.cos(u * Math.PI * 2 + i * 1.3)) * H;
      const g = ctx.createRadialGradient(x, y, 0, x, y, rr * W);
      g.addColorStop(0, hexA(col, aa)); g.addColorStop(1, hexA(col, 0));
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    });
  }
  function stars(u, n) {
    for (let i = 0; i < n; i++) {
      const sx = ((i * 97) % 100) / 100, sy = ((i * 53) % 100) / 100;
      const tw = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(u * Math.PI * 4 + i));
      ctx.fillStyle = hexA('#ffffff', 0.15 + tw * 0.45);
      ctx.beginPath();
      ctx.arc(sx * W, sy * H, (0.6 + (i % 3) * 0.4) * dpr, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  function beatIndex(u, list) {
    return list.length ? Math.min(list.length - 1, Math.floor(u * list.length)) : 0;
  }
  // —— per-lesson technological fairy-tale scenes ——
  const scenes = {
    hub_search(u, bi) {
      nebula(u, [[0.3,0.3,0.5,C.cyan,0.14],[0.75,0.65,0.4,C.lime,0.1],[0.5,0.8,0.35,C.violet,0.08]]);
      stars(u, 40);
      const agents = [
        [0.18 + 0.04*Math.sin(u*6), 0.35],
        [0.82 - 0.03*Math.cos(u*5), 0.28],
        [0.5, 0.72 - 0.04*Math.sin(u*4)]
      ];
      // seek trails toward center meet
      const meet = [0.5, 0.48];
      const t = Math.min(1, u * 1.4);
      agents.forEach((a, i) => {
        const x = (a[0] + (meet[0]-a[0]) * t) * W;
        const y = (a[1] + (meet[1]-a[1]) * t) * H;
        ctx.strokeStyle = hexA([C.cyan,C.lime,C.hot][i], 0.35);
        ctx.lineWidth = 2*dpr; ctx.setLineDash([6*dpr, 6*dpr]);
        ctx.beginPath(); ctx.moveTo(a[0]*W, a[1]*H); ctx.lineTo(x,y); ctx.stroke();
        ctx.setLineDash([]);
        const g = ctx.createRadialGradient(x,y,0,x,y,18*dpr);
        g.addColorStop(0, hexA([C.cyan,C.lime,C.hot][i], 0.9));
        g.addColorStop(1, hexA([C.cyan,C.lime,C.hot][i], 0));
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x,y,18*dpr,0,Math.PI*2); ctx.fill();
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x,y,5*dpr,0,Math.PI*2); ctx.fill();
      });
      if (bi >= 2) {
        ctx.strokeStyle = hexA(C.gold, 0.7); ctx.lineWidth = 2*dpr;
        ctx.strokeRect(meet[0]*W - 28*dpr, meet[1]*H + 22*dpr, 56*dpr, 18*dpr);
        ctx.fillStyle = hexA(C.gold, 0.85); ctx.font = `${11*dpr}px ui-monospace,monospace`;
        ctx.fillText('receipt', meet[0]*W - 22*dpr, meet[1]*H + 35*dpr);
      }
    },
    platon_random(u, bi) {
      nebula(u, [[0.5,0.45,0.55,C.violet,0.18],[0.2,0.2,0.35,C.cyan,0.1],[0.8,0.75,0.3,C.hot,0.08]]);
      // cave arch
      ctx.strokeStyle = hexA(C.violet, 0.35); ctx.lineWidth = 3*dpr;
      ctx.beginPath(); ctx.ellipse(0.5*W, 0.55*H, 0.38*W, 0.32*H, 0, Math.PI, 0); ctx.stroke();
      // falling hex sparks (chaos)
      for (let i = 0; i < 18; i++) {
        const hx = ((i * 37 + u * 80) % 100) / 100;
        const hy = ((i * 19 + u * 120 + i*7) % 100) / 100;
        ctx.fillStyle = hexA(i%2?C.cyan:C.gold, 0.55);
        ctx.font = `${9*dpr}px ui-monospace,monospace`;
        ctx.fillText((i*17).toString(16).padStart(2,'0'), hx*W, hy*H);
      }
      // VRF seal
      const ang = u * Math.PI * 4;
      const cx = 0.5*W, cy = 0.48*H, R = 36*dpr;
      ctx.strokeStyle = hexA(C.gold, 0.8); ctx.lineWidth = 2.5*dpr;
      ctx.beginPath(); ctx.arc(cx, cy, R, ang, ang + Math.PI * 1.4); ctx.stroke();
      ctx.fillStyle = hexA(C.gold, bi >= 1 ? 0.9 : 0.4);
      ctx.beginPath(); ctx.arc(cx, cy, 10*dpr, 0, Math.PI*2); ctx.fill();
      if (bi >= 2) {
        ctx.strokeStyle = hexA(C.lime, 0.9); ctx.beginPath();
        ctx.moveTo(cx-8*dpr, cy); ctx.lineTo(cx-2*dpr, cy+7*dpr); ctx.lineTo(cx+10*dpr, cy-8*dpr); ctx.stroke();
      }
    },
    warden_static(u, bi) {
      nebula(u, [[0.5,0.4,0.5,C.hot,0.1],[0.3,0.7,0.35,C.lime,0.12]]);
      // shield
      const sx = 0.5*W, sy = 0.42*H;
      ctx.fillStyle = hexA(C.cyan, 0.12); ctx.strokeStyle = hexA(C.cyan, 0.7); ctx.lineWidth = 2.5*dpr;
      ctx.beginPath();
      ctx.moveTo(sx, sy - 55*dpr); ctx.lineTo(sx + 48*dpr, sy - 20*dpr);
      ctx.lineTo(sx + 40*dpr, sy + 35*dpr); ctx.quadraticCurveTo(sx, sy + 70*dpr, sx - 40*dpr, sy + 35*dpr);
      ctx.lineTo(sx - 48*dpr, sy - 20*dpr); ctx.closePath(); ctx.fill(); ctx.stroke();
      // scan beam
      const scanY = sy - 50*dpr + ((u * 1.5) % 1) * 110*dpr;
      ctx.fillStyle = hexA(C.lime, 0.25); ctx.fillRect(sx - 44*dpr, scanY, 88*dpr, 4*dpr);
      // tools: safe vs poison
      const tools = [[0.18,0.78,'SAFE',C.lime],[0.82,0.78,'POISON',C.hot]];
      tools.forEach(([x,y,label,col], i) => {
        const alert = bi >= 1 && i === 1;
        ctx.fillStyle = hexA(col, alert ? 0.9 : 0.45);
        ctx.fillRect(x*W - 28*dpr, y*H - 14*dpr, 56*dpr, 28*dpr);
        ctx.fillStyle = '#02050c'; ctx.font = `bold ${10*dpr}px ui-sans-serif,system-ui`;
        ctx.fillText(label, x*W - 18*dpr, y*H + 4*dpr);
        if (alert) {
          ctx.strokeStyle = hexA(C.hot, 0.8 + 0.2*Math.sin(u*20));
          ctx.strokeRect(x*W - 32*dpr, y*H - 18*dpr, 64*dpr, 36*dpr);
        }
      });
      if (bi >= 2) {
        ctx.fillStyle = hexA(C.lime, 0.85); ctx.font = `${12*dpr}px ui-monospace,monospace`;
        ctx.fillText('WARDEN', sx - 28*dpr, sy + 8*dpr);
      }
    },
    payment_402(u, bi) {
      nebula(u, [[0.5,0.35,0.45,C.gold,0.14],[0.2,0.7,0.35,C.hot,0.1]]);
      // escrow vault
      const vx = 0.5*W, vy = 0.55*H;
      ctx.fillStyle = hexA(C.gold, 0.15); ctx.strokeStyle = hexA(C.gold, 0.7); ctx.lineWidth = 2*dpr;
      ctx.fillRect(vx - 50*dpr, vy - 40*dpr, 100*dpr, 80*dpr); ctx.strokeRect(vx - 50*dpr, vy - 40*dpr, 100*dpr, 80*dpr);
      ctx.fillStyle = hexA(C.gold, 0.8); ctx.font = `${11*dpr}px ui-monospace,monospace`;
      ctx.fillText('ESCROW', vx - 26*dpr, vy + 5*dpr);
      // coin hop into vault
      const t = (u * 2) % 1;
      const cx = (0.15 + t * 0.35) * W, cy = (0.25 + Math.sin(t * Math.PI) * 0.15) * H;
      ctx.fillStyle = hexA(C.lime, 0.9); ctx.beginPath(); ctx.arc(cx, cy, 10*dpr, 0, Math.PI*2); ctx.fill();
      ctx.fillStyle = C.ink; ctx.font = `bold ${10*dpr}px ui-sans-serif`; ctx.fillText('$', cx - 3*dpr, cy + 4*dpr);
      // 402 flash
      if (bi === 0 || (u % 0.2) < 0.08) {
        ctx.fillStyle = hexA(C.hot, 0.85); ctx.font = `bold ${28*dpr}px ui-sans-serif,system-ui`;
        ctx.fillText('402', 0.12*W, 0.18*H);
      }
      if (bi >= 2) {
        ctx.strokeStyle = hexA(C.lime, 0.8); ctx.beginPath();
        ctx.moveTo(vx-20*dpr, vy+50*dpr); ctx.lineTo(vx-5*dpr, vy+62*dpr); ctx.lineTo(vx+22*dpr, vy+42*dpr); ctx.stroke();
      }
    },
    hub_stats(u, bi) {
      nebula(u, [[0.45,0.4,0.5,C.cyan,0.12],[0.7,0.7,0.35,C.violet,0.1]]);
      const nodes = [[0.5,0.22],[0.22,0.45],[0.78,0.42],[0.32,0.72],[0.68,0.75],[0.5,0.5]];
      ctx.strokeStyle = hexA(C.cyan, 0.25); ctx.lineWidth = 1.5*dpr;
      for (let i = 0; i < nodes.length; i++) for (let j = i+1; j < nodes.length; j++) {
        if ((i+j) % 2 === 0) continue;
        ctx.beginPath();
        ctx.moveTo(nodes[i][0]*W, nodes[i][1]*H); ctx.lineTo(nodes[j][0]*W, nodes[j][1]*H); ctx.stroke();
      }
      nodes.forEach((n, i) => {
        const trust = 0.35 + 0.55 * (0.5 + 0.5 * Math.sin(u * Math.PI * 2 + i * 0.9));
        const r = (5 + trust * 14) * dpr;
        const g = ctx.createRadialGradient(n[0]*W, n[1]*H, 0, n[0]*W, n[1]*H, r*2);
        g.addColorStop(0, hexA(C.lime, 0.85)); g.addColorStop(1, hexA(C.lime, 0));
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(n[0]*W, n[1]*H, r*2, 0, Math.PI*2); ctx.fill();
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(n[0]*W, n[1]*H, 3.5*dpr, 0, Math.PI*2); ctx.fill();
      });
      if (bi >= 2) {
        ctx.fillStyle = hexA(C.violet, 0.8); ctx.font = `${11*dpr}px ui-monospace,monospace`;
        ctx.fillText('federated trust', 0.28*W, 0.12*H);
      }
    },
    search_proof(u, bi) {
      nebula(u, [[0.5,0.45,0.5,C.lime,0.12],[0.25,0.25,0.3,C.gold,0.1]]);
      // geometric certificate unfolding
      const cx = 0.5*W, cy = 0.45*H;
      const sides = 3 + bi;
      ctx.strokeStyle = hexA(C.lime, 0.75); ctx.lineWidth = 2*dpr; ctx.beginPath();
      for (let i = 0; i <= sides; i++) {
        const a = -Math.PI/2 + (i/sides) * Math.PI * 2 + u * 0.4;
        const r = (40 + bi * 8) * dpr;
        const x = cx + Math.cos(a)*r, y = cy + Math.sin(a)*r;
        if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
      }
      ctx.stroke();
      // stamp
      const stamp = Math.min(1, Math.max(0, (u - 0.55) * 4));
      if (stamp > 0) {
        ctx.save(); ctx.translate(cx, cy + 70*dpr); ctx.scale(stamp, stamp); ctx.rotate(-0.15);
        ctx.strokeStyle = hexA(C.hot, 0.9); ctx.lineWidth = 3*dpr;
        ctx.strokeRect(-40*dpr, -16*dpr, 80*dpr, 32*dpr);
        ctx.fillStyle = hexA(C.hot, 0.9); ctx.font = `bold ${12*dpr}px ui-sans-serif`;
        ctx.fillText('PROOF', -22*dpr, 5*dpr);
        ctx.restore();
      }
    },
    basescan_escrow(u, bi) {
      nebula(u, [[0.5,0.4,0.5,C.gold,0.14],[0.7,0.7,0.3,C.cyan,0.08]]);
      const cx = 0.5*W, cy = 0.42*H, R = 55*dpr;
      const spin = u * Math.PI * 6;
      ctx.strokeStyle = hexA(C.gold, 0.7); ctx.lineWidth = 3*dpr;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI*2); ctx.stroke();
      for (let i = 0; i < 8; i++) {
        const a = spin + i * Math.PI / 4;
        ctx.strokeStyle = hexA(i%2?C.lime:C.hot, 0.6);
        ctx.beginPath(); ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(a)*R, cy + Math.sin(a)*R); ctx.stroke();
      }
      // VRF seed crystal
      ctx.fillStyle = hexA(C.cyan, 0.85); ctx.beginPath();
      ctx.moveTo(cx, cy - 14*dpr); ctx.lineTo(cx + 10*dpr, cy); ctx.lineTo(cx, cy + 14*dpr); ctx.lineTo(cx - 10*dpr, cy);
      ctx.closePath(); ctx.fill();
      if (bi >= 2) {
        ctx.fillStyle = hexA(C.gold, 0.9); ctx.font = `${12*dpr}px ui-monospace,monospace`;
        ctx.fillText('Base · settle', cx - 40*dpr, cy + R + 28*dpr);
      }
    },
    factory_health(u, bi) {
      nebula(u, [[0.4,0.3,0.4,C.hot,0.1],[0.6,0.7,0.4,C.lime,0.1]]);
      const stages = ['idea','spec','build','QA','ship'];
      const y = 0.45*H;
      stages.forEach((s, i) => {
        const x = (0.1 + i * 0.18) * W;
        const on = Math.floor(u * stages.length) >= i;
        ctx.fillStyle = hexA(on ? C.lime : C.cyan, on ? 0.85 : 0.25);
        ctx.beginPath(); ctx.arc(x, y, 14*dpr, 0, Math.PI*2); ctx.fill();
        if (i < stages.length - 1) {
          ctx.strokeStyle = hexA(C.cyan, on ? 0.6 : 0.2); ctx.lineWidth = 2*dpr;
          ctx.beginPath(); ctx.moveTo(x + 16*dpr, y); ctx.lineTo(x + 0.18*W - 16*dpr, y); ctx.stroke();
        }
        ctx.fillStyle = hexA('#ffffff', 0.7); ctx.font = `${9*dpr}px ui-monospace,monospace`;
        ctx.fillText(s, x - 12*dpr, y + 32*dpr);
      });
      // product card lands on storefront
      if (bi >= 2) {
        const px = 0.5*W, py = 0.72*H;
        ctx.fillStyle = hexA(C.gold, 0.2); ctx.strokeStyle = hexA(C.gold, 0.8); ctx.lineWidth = 2*dpr;
        ctx.fillRect(px - 55*dpr, py - 28*dpr, 110*dpr, 56*dpr); ctx.strokeRect(px - 55*dpr, py - 28*dpr, 110*dpr, 56*dpr);
        ctx.fillStyle = hexA(C.gold, 0.9); ctx.font = `${11*dpr}px ui-sans-serif`;
        ctx.fillText('storefront', px - 32*dpr, py + 5*dpr);
      }
    },
    mesh_live(u, bi) {
      nebula(u, [[0.35,0.35,0.45,C.cyan,0.14],[0.7,0.55,0.4,C.lime,0.12],[0.5,0.8,0.3,C.hot,0.08]]);
      stars(u, 25);
      const nodes = [[0.22,0.28],[0.72,0.22],[0.55,0.55],[0.28,0.72],[0.78,0.70]];
      ctx.strokeStyle = hexA(C.lime, 0.4); ctx.lineWidth = 2*dpr;
      for (let i = 0; i < nodes.length - 1; i++) {
        ctx.beginPath();
        ctx.moveTo(nodes[i][0]*W, nodes[i][1]*H); ctx.lineTo(nodes[i+1][0]*W, nodes[i+1][1]*H); ctx.stroke();
      }
      const seg = u * (nodes.length - 1);
      const si = Math.min(nodes.length - 2, Math.floor(seg));
      const sf = seg - si;
      const a = nodes[si], b = nodes[si+1];
      const px = (a[0] + (b[0]-a[0])*sf)*W, py = (a[1] + (b[1]-a[1])*sf)*H;
      // spend sparkles along hop
      if (bi >= 2) {
        ctx.fillStyle = hexA(C.gold, 0.8); ctx.font = `${10*dpr}px ui-monospace,monospace`;
        ctx.fillText('$' + (0.01 + u*0.04).toFixed(3), px + 8*dpr, py - 8*dpr);
      }
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(px, py, 5*dpr, 0, Math.PI*2); ctx.fill();
      nodes.forEach((n, i) => {
        const pulse = 0.5 + 0.5 * Math.sin(u * Math.PI * 2 + i);
        ctx.fillStyle = i === Math.floor(u * nodes.length) % nodes.length ? C.hot : C.lime;
        ctx.beginPath(); ctx.arc(n[0]*W, n[1]*H, (6 + pulse*4)*dpr, 0, Math.PI*2); ctx.fill();
      });
    },
    search_physics(u, bi) {
      nebula(u, [[0.5,0.4,0.5,C.violet,0.12],[0.3,0.7,0.35,C.hot,0.1],[0.75,0.25,0.3,C.cyan,0.1]]);
      // murmuration flock
      const N = 48;
      for (let i = 0; i < N; i++) {
        const a = u * Math.PI * 2 + i * 0.35;
        const r = 0.12 + 0.08 * Math.sin(u * 6 + i);
        const x = (0.5 + Math.cos(a) * r + 0.05 * Math.sin(u * 3 + i)) * W;
        const y = (0.42 + Math.sin(a * 1.3) * r * 1.4) * H;
        ctx.fillStyle = hexA(i % 3 === 0 ? C.cyan : C.lime, 0.7);
        ctx.beginPath(); ctx.arc(x, y, 2.2*dpr, 0, Math.PI*2); ctx.fill();
      }
      // cascade sand pile
      if (bi >= 1) {
        const baseY = 0.78*H;
        for (let k = 0; k < 12; k++) {
          const fall = ((u * 2 + k * 0.08) % 1);
          ctx.fillStyle = hexA(C.hot, 0.5 + 0.4 * (1-fall));
          ctx.fillRect(0.2*W + k * 8*dpr, baseY - fall * 80*dpr, 6*dpr, 6*dpr);
        }
      }
      if (bi >= 2) {
        ctx.fillStyle = hexA(C.gold, 0.85); ctx.font = `${11*dpr}px ui-monospace,monospace`;
        ctx.fillText('Landauer · audit', 0.28*W, 0.14*H);
      }
    }
  };
  const draw = scenes[scene] || scenes.mesh_live;
  function frame(now) {
    if (!W || !H) resize();
    const u = reduce ? 0.5 : ((now - t0) % dur) / dur;
    const list = Array.isArray(beats) ? beats : [];
    const bi = beatIndex(u, list);
    draw(u, bi);
    if (capEl) capEl.textContent = list[bi] || '';
    if (barEl) barEl.style.width = (u * 100).toFixed(1) + '%';
    if (!reduce) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
"""


def load_lessons() -> dict[str, Any]:
    return yaml.safe_load((SCHOOL / "lessons.yaml").read_text(encoding="utf-8"))


def load_i18n() -> dict[str, Any]:
    return yaml.safe_load((SCHOOL / "i18n.yaml").read_text(encoding="utf-8"))


def lang_prefix(lang: str) -> str:
    return "" if lang == "en" else f"/{lang}"


def mount_prefix() -> str:
    """'' or '/school'."""
    return f"/{MOUNT}" if MOUNT else ""


def school_root(lang: str) -> Path:
    if MOUNT:
        return OUT_ROOT / "school" if lang == "en" else OUT_ROOT / lang / "school"
    return OUT_ROOT if lang == "en" else OUT_ROOT / lang


def canon_path(sub: str) -> str:
    """Canonical path without lang: '/' or '/agents-in-5-min/'."""
    if not sub.startswith("/"):
        sub = "/" + sub
    if not sub.endswith("/"):
        sub += "/"
    m = mount_prefix()
    if sub == "/":
        return f"{m}/" if m else "/"
    return f"{m}{sub}"


def school_href(lang: str, path: str = "/") -> str:
    """path like '/' or '/agents-in-5-min/'."""
    return f"{BASE}{lang_prefix(lang)}{canon_path(path)}"


def css_href(lang: str, *, depth: int = 0) -> str:
    """Shared CSS at {mount}/school.css (EN root of school tree)."""
    if MOUNT:
        if lang == "en":
            return "school.css" if depth == 0 else "../school.css"
        return "../" * (2 + depth) + "school/school.css"
    # site-root mount: CSS at /school.css
    if lang == "en":
        return "school.css" if depth == 0 else "../school.css"
    return "../" * (1 + depth) + "school.css"


def colab_url(lesson_id: str) -> str:
    return f"{GITHUB_NB}/{lesson_id}.ipynb"


def academy_url(folder: str) -> str:
    return f"{COURSES}/{folder}/"


def learn_href(lang: str) -> str:
    return f"{LEARN_BASE}{lang_prefix(lang)}/learn/"


def guides_href(lang: str) -> str:
    return f"{LEARN_BASE}{lang_prefix(lang)}/guides/"


def ui(i18n: dict[str, Any], lang: str) -> dict[str, str]:
    table = i18n.get("ui", {})
    base = dict(table.get("en") or {})
    base.update(table.get(lang) or {})
    return base


def portal_copy(i18n: dict[str, Any], lang: str, fallback: dict[str, Any]) -> dict[str, str]:
    table = i18n.get("portal", {})
    out = {
        "eyebrow": fallback.get("eyebrow", ""),
        "h1": fallback.get("h1", ""),
        "lede": fallback.get("lede", ""),
    }
    out.update(table.get("en") or {})
    out.update(table.get(lang) or {})
    return out


def lesson_copy(lesson: dict[str, Any], i18n: dict[str, Any], lang: str) -> dict[str, Any]:
    lid = lesson["id"]
    block = (i18n.get("lessons") or {}).get(lid) or {}
    en = block.get("en") or {}
    loc = block.get(lang) or {}
    return {
        "title": loc.get("title") or en.get("title") or lesson.get("title", lid),
        "punch": loc.get("punch") or en.get("punch") or lesson.get("punch", ""),
        "academy_label": loc.get("academy_label") or en.get("academy_label") or lesson.get("academy_label", ""),
        "demo_label": loc.get("demo_label") or en.get("demo_label") or lesson.get("demo_label", "Run"),
        "short_beats": loc.get("short_beats") or en.get("short_beats") or lesson.get("short_beats") or [],
    }


def write_notebook(lesson: dict[str, Any]) -> None:
    NB_OUT.mkdir(parents=True, exist_ok=True)
    md = (
        f"# {lesson['title']}\n\n"
        f"{lesson['punch']}\n\n"
        f"**Academy next:** [{lesson['academy_label']}]({academy_url(lesson['academy'])})\n"
    )
    code = "\n".join(lesson["colab_cells"]) + "\n"
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [md]},
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [code],
        },
    ]
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }
    (NB_OUT / f"{lesson['id']}.ipynb").write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")


def lang_switcher(lang: str, path: str) -> str:
    """path is canonical without lang prefix (e.g. /school/ or / or /school/id/)."""
    bits = []
    for L in LANGS:
        cur = ' aria-current="page"' if L == lang else ""
        href = f"{BASE}{lang_prefix(L)}{path}"
        bits.append(f'<a href="{html.escape(href)}"{cur}>{L.upper()}</a>')
    return f'<div class="lang-switch" aria-label="Language">{"".join(bits)}</div>'


def hreflang_tags(path: str) -> str:
    tags = []
    for L in LANGS:
        tags.append(
            f'<link rel="alternate" hreflang="{L}" href="{html.escape(BASE + lang_prefix(L) + path)}" />'
        )
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{html.escape(BASE + path)}" />')
    return "\n".join(tags)


def nav(lang: str, U: dict[str, str], path: str) -> str:
    return f"""<nav><div class="wrap row">
  <a class="brand" href="{html.escape(school_href(lang, '/'))}"><span>AIMarket</span> {html.escape(U['brand_school'])}</a>
  <div class="nav-links">
    <a href="{html.escape(school_href(lang, '/'))}" aria-current="page">{html.escape(U['nav_lessons'])}</a>
    <a href="{html.escape(learn_href(lang))}">{html.escape(U['nav_academy'])}</a>
    <a href="{html.escape(guides_href(lang))}">{html.escape(U['nav_guides'])}</a>
    <a href="https://alexar76.github.io/ai-service-mesh/">{html.escape(U['nav_mesh'])}</a>
    <a href="https://github.com/alexar76/aicom">GitHub</a>
    {lang_switcher(lang, path)}
  </div>
</div></nav>"""


def foot(lang: str, U: dict[str, str]) -> str:
    return f"""<footer><div class="wrap row">
  <span>{html.escape(U['footer'])}</span>
  <span>
    <a href="{html.escape(learn_href(lang))}">{html.escape(U['nav_academy'])}</a> ·
    <a href="{html.escape(COURSES)}/">Course portal</a> ·
    <a href="https://oracles.modelmarket.dev/">Oracles</a>
  </span>
</div></footer>"""


def head(title: str, desc: str, path: str, lang: str, *, depth: int = 0) -> str:
    url = f"{BASE}{lang_prefix(lang)}{path}"
    return f"""<!DOCTYPE html>
<html lang="{html.escape(lang)}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}" />
<link rel="canonical" href="{html.escape(url)}" />
{hreflang_tags(path)}
<meta property="og:title" content="{html.escape(title)}" />
<meta property="og:description" content="{html.escape(desc)}" />
<meta property="og:url" content="{html.escape(url)}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="{html.escape(css_href(lang, depth=depth))}" />
</head>
<body>
"""


def lesson_page(
    lesson: dict[str, Any],
    lessons: list[dict[str, Any]],
    copies: dict[str, dict[str, Any]],
    lang: str,
    U: dict[str, str],
) -> str:
    copy = copies[lesson["id"]]
    beats = copy["short_beats"]
    beats_json = json.dumps(beats, ensure_ascii=False)
    idx = next(i for i, L in enumerate(lessons) if L["id"] == lesson["id"])
    prev_l = lessons[idx - 1] if idx > 0 else None
    next_l = lessons[idx + 1] if idx + 1 < len(lessons) else None
    nav_lessons = ""
    if prev_l:
        nav_lessons += (
            f'<a class="btn btn-ghost" href="../{html.escape(prev_l["id"])}/">'
            f'← {html.escape(copies[prev_l["id"]]["title"])}</a>'
        )
    if next_l:
        nav_lessons += (
            f'<a class="btn btn-primary" href="../{html.escape(next_l["id"])}/">'
            f'{html.escape(copies[next_l["id"]]["title"])} →</a>'
        )
    path = canon_path(f"/{lesson['id']}/")
    meta = U["lesson_meta"].format(order=f"{lesson['order']:02d}", minutes=lesson["minutes"])
    academy_btn = U["academy_btn"].format(label=copy["academy_label"])
    return (
        head(f"{copy['title']} — AIMarket School", copy["punch"], path, lang, depth=1)
        + nav(lang, U, path)
        + f"""
<div class="wrap section lesson-hero">
  <p class="eyebrow">{html.escape(meta)}</p>
  <h1>{html.escape(copy['title'])}</h1>
  <p class="lede" style="color:var(--muted);max-width:46ch">{html.escape(copy['punch'])}</p>
  <div class="layout">
    <div>
      <div class="reel" id="reel">
        <div class="progress"><i id="reel-bar"></i></div>
        <canvas id="reel-c"></canvas>
        <div class="cap" id="reel-cap"></div>
      </div>
      <p class="note" style="text-align:center">{html.escape(U['short_note'])}</p>
    </div>
    <div>
      <div class="panel" style="margin-bottom:14px">
        <h2>{html.escape(U['watch'])}</h2>
        <ol class="steps">
          {''.join(f'<li>{html.escape(b)}</li>' for b in beats)}
        </ol>
      </div>
      <div class="panel" style="margin-bottom:14px">
        <h2>{html.escape(U['try_live'])}</h2>
        <p style="color:var(--muted);margin:0 0 10px;font-size:0.92rem">{html.escape(copy['demo_label'])}</p>
        <button class="btn btn-hot" type="button" id="run-demo">{html.escape(copy['demo_label'])}</button>
        <pre id="demo-out">{html.escape(U['output_placeholder'])}</pre>
      </div>
      <div class="panel">
        <h2>{html.escape(U['go_deeper'])}</h2>
        <div class="ctas">
          <a class="btn btn-primary" href="{html.escape(colab_url(lesson['id']))}" target="_blank" rel="noopener">{html.escape(U['colab'])}</a>
          <a class="btn btn-ghost" href="{html.escape(academy_url(lesson['academy']))}" target="_blank" rel="noopener">{html.escape(academy_btn)}</a>
        </div>
        <p class="note">{html.escape(U['colab_note'])}</p>
      </div>
    </div>
  </div>
  <div class="ctas" style="margin-top:28px">{nav_lessons}<a class="btn btn-ghost" href="../">{html.escape(U['all_lessons'])}</a></div>
</div>
{foot(lang, U)}
<script>
{DEMO_JS}
(() => {{
  const beats = {beats_json};
  const scene = {json.dumps(lesson.get("demo") or lesson["id"])};
  const canvas = document.getElementById('reel-c');
  playReel(canvas, beats, document.getElementById('reel-cap'), document.getElementById('reel-bar'), scene);
  document.getElementById('run-demo').addEventListener('click', () => {{
    schoolDemo({json.dumps(lesson.get('demo'))}, document.getElementById('demo-out'));
  }});
}})();
</script>
</body></html>
"""
    )


def portal_page(
    lessons: list[dict[str, Any]],
    copies: dict[str, dict[str, Any]],
    portal: dict[str, str],
    lang: str,
    U: dict[str, str],
) -> str:
    cards = []
    for L in lessons:
        c = copies[L["id"]]
        cards.append(
            f"""<a class="card" href="{html.escape(L['id'])}/">
  <div class="num">LESSON {L['order']:02d} · ~{L['minutes']} MIN</div>
  <h3>{html.escape(c['title'])}</h3>
  <p>{html.escape(c['punch'])}</p>
  <div class="meta">→ {html.escape(c['academy_label'])}</div>
</a>"""
        )
    path = canon_path("/")
    return (
        head(U["portal_title"], portal["lede"], path, lang)
        + nav(lang, U, path)
        + f"""
<header class="hero-cosmic">
  <div class="sky" aria-hidden="true"></div>
  <canvas id="cosmos" aria-hidden="true"></canvas>
  <div class="veil" aria-hidden="true"></div>
  <div class="wrap">
    <p class="eyebrow">{html.escape(portal['eyebrow'])}</p>
    <p class="brand-hero"><span>AIMarket</span> {html.escape(U['brand_school'])}</p>
    <h1>{html.escape(portal['h1'])}</h1>
    <p class="lede">{html.escape(portal['lede'])}</p>
    <div class="ctas">
      <a class="btn btn-primary" href="{html.escape(lessons[0]['id'])}/">{html.escape(U['cta_start'])}</a>
      <a class="btn btn-ghost" href="{html.escape(learn_href(lang))}">{html.escape(U['cta_academy'])}</a>
    </div>
  </div>
</header>
<main class="wrap">
  <p class="catalog-head">{html.escape(U['section_catalog'])}</p>
  <div class="grid">
{''.join(cards)}
  </div>
</main>
{foot(lang, U)}
<script>
{COSMOS_JS}
playCosmos(document.getElementById('cosmos'));
</script>
</body></html>
"""
    )


def build_lang(
    lang: str,
    lessons: list[dict[str, Any]],
    data: dict[str, Any],
    i18n: dict[str, Any],
) -> None:
    U = ui(i18n, lang)
    portal = portal_copy(i18n, lang, data.get("portal") or {})
    copies = {L["id"]: lesson_copy(L, i18n, lang) for L in lessons}
    out = school_root(lang)
    lesson_ids = {L["id"] for L in lessons}

    if not MOUNT and lang == "en":
        out.mkdir(parents=True, exist_ok=True)
        for p in list(out.iterdir()):
            if p.name in LANGS:
                continue
            if p.is_dir():
                shutil.rmtree(p)
            elif p.suffix in (".html", ".css") or p.name == "school.css":
                p.unlink(missing_ok=True)
    else:
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)

    (out / "index.html").write_text(portal_page(lessons, copies, portal, lang, U), encoding="utf-8")
    for L in lessons:
        if L["id"] not in lesson_ids:
            continue
        d = out / L["id"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(lesson_page(L, lessons, copies, lang, U), encoding="utf-8")


def main() -> int:
    data = load_lessons()
    i18n = load_i18n()
    lessons = sorted(data["lessons"], key=lambda L: L["order"])

    for L in lessons:
        merged = dict(L)
        merged.update(lesson_copy(L, i18n, "en"))
        write_notebook(merged)

    if not MOUNT:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)

    for lang in LANGS:
        build_lang(lang, lessons, data, i18n)
        if lang == "en":
            (school_root("en") / "school.css").write_text(CSS, encoding="utf-8")
            nb_site = school_root("en") / "notebooks"
            if nb_site.exists():
                shutil.rmtree(nb_site)
            shutil.copytree(NB_OUT, nb_site)

    where = f"{OUT_ROOT}" + (f" (mount {mount_prefix() or '/'})" )
    print(f"OK school → {where} langs={LANGS} lessons={len(lessons)} base={BASE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
