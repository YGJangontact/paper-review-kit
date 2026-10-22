from pathlib import Path
r=Path(__file__).resolve().parent
deck=(r/'examples/lora/exports/slides.html').read_text(encoding='utf-8')
checker=(r/'assets/check_deck.js').read_text(encoding='utf-8')
qa="<script>window.addEventListener('load',async()=>{const report=await "+checker+";const pre=document.createElement('pre');pre.id='qa-report';pre.style='position:fixed;inset:0;background:white;color:black;overflow:auto;z-index:99999;padding:20px';pre.textContent=JSON.stringify(report,null,2);document.body.append(pre);});</script>"
(r/'examples/lora/exports/qa.html').write_text(deck.replace('</body>',qa+'</body>'),encoding='utf-8')
(r/'docs/mobile-preview.html').write_text('<!doctype html><meta charset="utf-8"><title>390px 검토</title><iframe title="390px 모바일 너비 검토" style="width:390px;height:840px;border:1px solid" src="../examples/lora/exports/review.html#demo"></iframe>',encoding='utf-8')
