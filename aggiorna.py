#!/usr/bin/env python3
"""
aggiorna.py — MIMMOCLST portfolio updater
Esegui dalla cartella portfolio/ con: python3 aggiorna.py
"""

import os, re, shutil, json, subprocess, sys

# ── PATH SETUP ────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
MIMMOCLST    = os.path.join(SCRIPT_DIR, '..')          # cartella mimmoclst/
MIMMOCLST    = os.path.normpath(MIMMOCLST)
DST_ARCHIVE  = os.path.join(SCRIPT_DIR, 'img', 'archive')
DST_MADE     = os.path.join(SCRIPT_DIR, 'img', 'made')
HTML_FILE    = os.path.join(SCRIPT_DIR, 'index.html')

os.makedirs(DST_ARCHIVE, exist_ok=True)
os.makedirs(DST_MADE,    exist_ok=True)

# ── 1. SCARICA NUOVI POST DA INSTAGRAM ───────────────────────────────────────
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  MIMMOCLST — aggiornamento portfolio")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()
print("→ Scarico nuovi post da Instagram...")

try:
    result = subprocess.run(
        ['instaloader', 'mimmoclst', '--no-videos', '--no-metadata-json',
         '--fast-update'],
        cwd=os.path.dirname(MIMMOCLST),
        capture_output=False,
        text=True,
    )
    if result.returncode == 0:
        print("✓ Instagram sincronizzato\n")
    else:
        print("⚠ Instaloader ha restituito un errore — continuo con i file locali\n")
except FileNotFoundError:
    print("⚠ instaloader non trovato — continuo con i file locali\n")

# ── 2. LEGGI E CATEGORIZZA I POST ────────────────────────────────────────────
print("→ Elaborazione post...")

txt_files = sorted(
    [f for f in os.listdir(MIMMOCLST)
     if f.endswith('.txt') and 'profile' not in f],
    reverse=True   # più recenti prima
)

def clean_title(raw):
    t = re.sub(r'^SOLD[^\s]*\s*', '', raw).strip()
    t = re.sub(r'#\S+', '', t).strip()
    t = re.sub(r'\s+', ' ', t).strip()
    # Remove "made by @..." suffixes
    t = re.sub(r'\s*[-–—]\s*made by @\S+.*$', '', t, flags=re.I).strip()
    t = re.sub(r'\s+made by @\S+.*$', '', t, flags=re.I).strip()
    # Capitalise first letter of each word for homemade pieces
    return t

def clean_desc(caption_lines):
    parts = [l.strip() for l in caption_lines[1:4]
             if l.strip() and not l.startswith('#')
             and l.strip() not in ('NFS','Available','available')]
    desc = ' — '.join(parts)
    desc = re.sub(r'@\S+', '', desc)
    desc = re.sub(r'#\S+', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip(' —').strip()
    return desc

items = []
new_count = 0

for txt in txt_files:
    ts      = txt.replace('.txt', '')
    caption = open(os.path.join(MIMMOCLST, txt), encoding='utf-8').read().strip()

    # All images for this post, sorted, max 2 (front + back)
    all_imgs = sorted([
        f for f in os.listdir(MIMMOCLST)
        if f.startswith(ts) and f.endswith('.jpg') and 'profile' not in f
    ])[:2]

    if not all_imgs:
        continue

    is_made = '@alessandrotrevisann' in caption.lower()
    section = 'made' if is_made else 'archive'
    sold    = caption.strip().startswith('SOLD')
    nfs     = 'NFS' in caption
    status  = 'SOLD' if sold else ('NFS' if nfs else '')

    lines   = [l for l in caption.split('\n') if l.strip()]
    title   = clean_title(lines[0])
    desc    = clean_desc(lines)

    dst_dir  = DST_MADE if is_made else DST_ARCHIVE
    rel_pre  = f'img/{"made" if is_made else "archive"}/'
    copied   = []

    for i, img in enumerate(all_imgs, 1):
        slug   = f'{ts}_{i}.jpg'
        src    = os.path.join(MIMMOCLST, img)
        dst    = os.path.join(dst_dir, slug)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            new_count += 1
            print(f"  + {slug}")
        copied.append(rel_pre + slug)

    items.append({
        'section': section,
        'title':   title,
        'desc':    desc,
        'status':  status,
        'cover':   copied[0],
        'images':  copied,
    })

print(f"\n✓ {len(items)} post totali — {new_count} nuove immagini aggiunte")

# ── 3. AGGIORNA index.html ────────────────────────────────────────────────────
print("\n→ Aggiorno index.html...")

html = open(HTML_FILE, encoding='utf-8').read()

items_json = 'const ITEMS = ' + json.dumps(items, ensure_ascii=False, indent=2) + ';'

# Replace the ITEMS block
html_new = re.sub(
    r'const ITEMS = \[[\s\S]*?\];',
    items_json,
    html,
    count=1
)

if html_new == html:
    print("⚠ Nessuna modifica applicata a index.html — controlla il formato del file")
else:
    open(HTML_FILE, 'w', encoding='utf-8').write(html_new)
    print("✓ index.html aggiornato")

print()
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  Fatto! Apri index.html per vedere il sito.")
print("  Per pubblicare: git add . && git commit -m 'update' && git push")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
