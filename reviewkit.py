"""Local evidence bookkeeping, not a scientific truth detector. Python 3.10+."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
STAGES = ('extract', 'review', 'check', 'export')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, value, force=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise ValueError(f'Already exists: {path}; use --force explicitly')
    # Exclusive creation prevents accidental replacement; replacement is atomic.
    if not force:
        with path.open('x', encoding='utf-8') as f:
            f.write(value)
    else:
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(value, encoding='utf-8')
        tmp.replace(path)

def dump(path, value, force=False):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n', force)

def safe_url(value):
    p = urlsplit(value)
    return p.scheme in ('https', 'http') and bool(p.netloc) and not p.username

def validate(data):
    from jsonschema import Draft202012Validator
    errors = [f'{"/".join(map(str,e.path))}: {e.message}' for e in Draft202012Validator(read(ROOT/'schema.json')).iter_errors(data)]
    if errors:
        return errors
    sources = {s['id']: s for s in data['sources']}
    claims = {c['id']: c for c in data['claims']}
    for kind in ('sources', 'claims'):
        ids = [x['id'] for x in data[kind]]
        if len(ids) != len(set(ids)):
            errors.append(f'Duplicate {kind} ID')
    for s in data['sources']:
        if not safe_url(s['url']):
            errors.append(f"Unsafe URL: {s['id']}")
    for c in data['claims']:
        if c['source'] not in sources:
            errors.append(f"Unknown source: {c['id']}")
        elif c['kind'] == 'reported' and sources[c['source']]['access'] != 'full' and c['locator'] != 'Abstract':
            errors.append(f"Access mismatch: {c['id']}")
    for r in data['relations']:
        if r['from'] not in sources or r['to'] not in sources:
            errors.append('Unknown relation endpoint')
    for h in data['hypotheses']:
        if h['basis'] not in claims:
            errors.append('Unknown hypothesis basis')
    return errors

def fingerprint(folder):
    files = [p for p in Path(folder).rglob('*') if p.is_file() and p.name != 'status.json' and 'exports' not in p.parts and p.suffix in ('.md','.json','.pdf','.py')]
    h = hashlib.sha256()
    for p in sorted(files):
        h.update(p.relative_to(folder).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()

def state(folder):
    folder = Path(folder)
    path = folder/'status.json'
    old = read(path) if path.exists() else {'stages': {s: {'state':'pending','evidence':[]} for s in STAGES}}
    changed = old.get('fingerprint') != fingerprint(folder)
    if changed:
        for item in old['stages'].values():
            if item['state'] == 'done':
                item['state'] = 'stale'
    old['fingerprint'] = fingerprint(folder)
    return old

def mark(folder, stage, evidence):
    folder = Path(folder).resolve()
    for name in evidence:
        p = (folder/name).resolve()
        if not p.is_relative_to(folder) or not p.is_file():
            raise ValueError('Completion evidence must be an existing file inside review folder')
    result = state(folder)
    result['stages'][stage] = {'state':'done','evidence':evidence}
    dump(folder/'status.json', result, True)
    return result

def check(folder):
    folder = Path(folder)
    data = read(folder/'evidence.json')
    errors = validate(data)
    if errors:
        return errors
    md = (folder/'review.md').read_text(encoding='utf-8')
    ids = {c['id'] for c in data['claims']}
    for cid in re.findall(r'\[claim:([\w-]+)\]', md):
        if cid not in ids:
            errors.append(f'Unknown prose claim: {cid}')
    for cid in ids:
        if f'[claim:{cid}]' not in md:
            errors.append(f'Unreferenced claim: {cid}')
    return errors

def normalize_doi(value):
    return re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', value.strip(), flags=re.I).lower()

def duplicates(data):
    groups = {}
    for s in data['sources']:
        key = normalize_doi(s.get('doi','')) or re.sub(r'\W+', '', s['title'].lower())
        groups.setdefault(key, []).append({'id':s['id'], 'version':s['version']})
    return [g for g in groups.values() if len(g)>1]

CSS = '''body{margin:0;background:#f4f6f8;color:#172334;font:18px/1.85 system-ui,sans-serif}main{max-width:880px;margin:auto;padding:55px 24px}h1{font-size:clamp(30px,5vw,48px);line-height:1.35}h2{margin-top:65px;border-top:2px solid #c9d3df;padding-top:25px}a{color:#205991;overflow-wrap:anywhere}table{border-collapse:collapse;display:block;overflow:auto}td,th{border:1px solid #cbd4df;padding:12px}th{background:#e4ebf2}pre{background:#182535;color:white;padding:20px;overflow:auto}blockquote,.card{background:white;border-left:4px solid #3b6f91;padding:18px 24px;margin:24px 0}img,svg{max-width:100%;height:auto}input{width:min(100%,400px)}:focus-visible{outline:3px solid #df852c}nav{padding:12px;background:#e4ebf2}button{font:inherit;padding:8px 16px}section[hidden]{display:none}small{color:#536478}'''

def export(folder, force=False, formats=('html','obsidian','graph')):
    import markdown
    folder = Path(folder)
    errors = check(folder)
    if errors:
        raise ValueError('\n'.join(errors))
    data = read(folder/'evidence.json')
    md = (folder/'review.md').read_text(encoding='utf-8')
    # Markdown source is trusted local author content; evidence fields are escaped.
    for c in data['claims']:
        md = md.replace(f"[claim:{c['id']}]", f"[근거 {c['id']}](#claim-{c['id']})")
    body = markdown.markdown(md, extensions=['tables','fenced_code','toc'])
    ledger = '<h2 id="evidence">주장별 근거</h2>'
    for c in data['claims']:
        s = next(s for s in data['sources'] if s['id']==c['source'])
        ledger += f'<article class="card" id="claim-{c["id"]}"><b>{html.escape(c["id"])} · {html.escape(c["kind"])}</b><p>{html.escape(c["text"])}</p><a href="{html.escape(s["url"],quote=True)}">{html.escape(s["title"])}</a><p>{html.escape(c["locator"])} · {html.escape(c["conditions"])}</p></article>'
    demo = (folder/'demo.html').read_text(encoding='utf-8') if (folder/'demo.html').exists() else ''
    head = f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(data["title"])}</title><style>{CSS}</style><main>'
    content = head + '<nav><a href="#demo">수식 실험</a> · <a href="#evidence">근거 기록</a></nav>' + body + demo + ledger + '</main></html>'
    outputs=[]
    if 'html' in formats:
        write(folder/'exports/review.html', content, force);outputs.append('review.html')
    relations = ['flowchart LR']
    for s in data['sources']:
        relations.append(f'  {s["id"]}["{html.escape(s["title"],quote=True)}"]')
    for r in data['relations']:
        relations.append(f'  {r["from"]} -->|{html.escape(r["kind"])}| {r["to"]}')
    if 'graph' in formats:
        write(folder/'exports/relations.mmd', '\n'.join(relations), force);outputs.append('relations.mmd')
    if 'obsidian' in formats:
        appendix='\n\n## 근거 기록\n'+ '\n'.join(f"- {c['id']}: {c['text']} — {c['source']}, {c['locator']}. {c['conditions']}" for c in data['claims'])
        appendix+='\n\n'+ '\n'.join(f"- {s['id']}: {s['url']} ({s['version']}, {s['access']})" for s in data['sources'])
        write(folder/'exports/obsidian.md', (folder/'review.md').read_text(encoding='utf-8')+'\n\n```mermaid\n'+'\n'.join(relations)+'\n```\n'+appendix, force);outputs.append('obsidian.md')
    dump(folder/'exports/manifest.json', {'input_sha256':fingerprint(folder),'outputs':outputs}, force)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('check','resume','bibliography','export'):
        q = sub.add_parser(command); q.add_argument('folder',type=Path)
        if command=='export':
            q.add_argument('--force',action='store_true')
            q.add_argument('--format',choices=['html','obsidian','graph'],nargs='+',default=['html'])
    q = sub.add_parser('mark'); q.add_argument('folder',type=Path);q.add_argument('stage',choices=STAGES);q.add_argument('evidence',nargs='+')
    q = sub.add_parser('extract');q.add_argument('pdf',type=Path);q.add_argument('output',type=Path);q.add_argument('--force',action='store_true')
    a = p.parse_args()
    if a.command=='extract':
        from pypdf import PdfReader
        pages = [{'page':i+1,'text':page.extract_text() or ''} for i,page in enumerate(PdfReader(a.pdf).pages)]
        for page in pages: page['low_text']=len(page['text'].strip())<80
        dump(a.output,{'sha256':hashlib.sha256(a.pdf.read_bytes()).hexdigest(),'pages':pages},a.force)
        print(f'{len(pages)} pages extracted; figures/equations need visual inspection')
    elif a.command=='check':
        errors=check(a.folder); print(json.dumps({'errors':errors,'semantic_truth_checked':False},ensure_ascii=False));raise SystemExit(bool(errors))
    elif a.command=='resume': print(json.dumps(state(a.folder),ensure_ascii=False,indent=2))
    elif a.command=='mark': print(json.dumps(mark(a.folder,a.stage,a.evidence),ensure_ascii=False))
    elif a.command=='bibliography': print(json.dumps(duplicates(read(a.folder/'evidence.json')),ensure_ascii=False))
    elif a.command=='export': export(a.folder,a.force,a.format);print('Exported: '+', '.join(a.format))

if __name__=='__main__':
    main()
