"""Generate a small evidence-linked deck from the shared ledger and math results."""
import html
from pathlib import Path
from reviewkit import read, write, check
ROOT=Path(__file__).resolve().parent
folder=ROOT/'examples/lora'
assert not check(folder)
data=read(folder/'evidence.json');math=read(folder/'math-results.json')
template=(ROOT/'assets/deck-template.html').read_text(encoding='utf-8')
def slide(id,title,body,notes):
    return f'<section class="slide" id="{id}"><p class="kicker">PAPER REVIEW · 공개 논문으로 검증하기</p><h2>{title}</h2>{body}<aside class="notes">{notes}</aside></section>'
slides=slide('cover','요약에서 근거가 남는 리뷰로','<p class="lead">LoRA 공개 논문으로 확인한 작은 실행 흐름</p><p>논문 읽기 → 주장 연결 → 수식 계산 → 웹·슬라이드 출력</p><p>대규모 모델 학습 재현이 아닌 리뷰 도구 검증입니다.</p>','논문 v2를 기준으로 핵심 방법을 대조했다. 모든 부록 실험을 재현하지 않았다.')
slides+=slide('workflow','판단과 반복 작업을 나누기','<ul class="points"><li>스킬: 읽는 순서·근거 구분·다음 질문</li><li>Python: 누락·연결·형식·변경 상태 검사</li><li>사람과 AI: 문장이 원문을 정확히 설명하는지 검토</li></ul>','형식이 맞는 거짓 주장은 검사기를 통과한다. 이 한계를 테스트에 포함했다.')
c=data['claims'][0]
slides+=slide('method','원본은 고정하고 작은 변화를 학습하기',f'<p>{html.escape(c["text"])}</p><div class="card"><p>h = W0 x + (alpha/r) B A x</p><p>W0: d×k · A: r×k · B: d×r</p></div><p class="small">{html.escape(c["locator"])} · C1</p>','식 3과 본문의 alpha/r 스케일을 합친 표기. 원문 Figure 1은 공개 PDF에서 확인한다.')
slides+=slide('experiment','alpha를 바꾸면 출력은 어떻게 바뀔까?','''<div class="demo" id="loraDemo"><div class="demo-stage"><div style="padding:35px"><p>설명용: W0=I, x=[2,3], r=1</p><p>A=[1,-1], B=[2,1]ᵀ</p><p>BAx=[-2,-1]</p><p data-out="result" style="font-size:58px"></p></div></div><div class="demo-controls"><label>alpha <output data-out="alpha">1</output><input type="range" name="alpha" min="0" max="2" step="0.1" value="1"></label><p>실제 학습 결과가 아닌 계산 예제</p></div></div>''','alpha 0,1,2를 비교한다. Python 결과는 0에서 [2,3], 1에서 [0,2], 2에서 [-2,1].')
rows=''.join(f'<tr><td>{x["alpha"]}</td><td>{html.escape(str(x["output"]))}</td><td>{x["max_abs_error"]}</td></tr>' for x in math['cases'])
slides+=slide('results','병합 전후의 출력이 일치했습니다',f'<table><thead><tr><th>alpha</th><th>출력</th><th>최대 절대 오차</th></tr></thead><tbody>{rows}</tbody></table><p>이 예제의 선형 계산만 검증했습니다. 속도·학습 성능 측정은 아닙니다.</p>','math-results.json에서 직접 읽은 결과다.')
slides+=slide('sources','출처와 미확인 사항까지 함께 저장하기','<p>LoRA → QLoRA: 저랭크 적응과 양자화를 연결하는 후속 접근</p><p>QLoRA는 초록만 확인했습니다. 성능 비교는 하지 않았습니다.</p><p><a href="https://arxiv.org/abs/2106.09685v2">LoRA v2 원문</a> · <a href="https://arxiv.org/abs/2305.14314v1">QLoRA v1 초록</a></p><p><a href="review.html#evidence">주장별 근거와 전체 리뷰</a></p>','다음 질문: 동일 조건에서 rank를 늘리면 검증 성능도 좋아지는가? 후속 실험은 아직 미실행이다.')
start='<!-- ================= SLIDES START ================= -->';end='<!-- ================= SLIDES END ================= -->'
template=template.split(start)[0]+start+'\n'+slides+'\n'+end+template.split(end)[1]
a=template.index("window.addEventListener('DOMContentLoaded', () => {");b=template.index('</script>',a)
template=template[:a]+'''window.addEventListener('DOMContentLoaded',()=>{Deck.demo('#loraDemo',{mount(el,api){api.bindRange('alpha',v=>{el.querySelector('[data-out="result"]').textContent='h = ['+(2-2*v).toFixed(1)+', '+(3-v).toFixed(1)+']';},v=>v.toFixed(1));}});});
'''+template[b:]
template=template.replace('<title>Deck Title</title>','<title>LoRA 논문 리뷰 검증</title>')
template=template.replace('style="font-size:58px"></p>', 'style="font-size:58px">h = [0.0, 2.0]</p>')
# No external math or font dependencies are required by this elementary arithmetic deck.
import re
template=re.sub(r'<script defer src="https://cdn.jsdelivr.net[^>]+></script>','',template)
template=re.sub(r'<link[^>]+href="https://fonts[^>]+>','',template)
write(folder/'exports/slides.html',template,True)
print('6-slide deck built from shared evidence and math output')
