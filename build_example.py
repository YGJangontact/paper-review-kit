"""Build the authored public LoRA walkthrough. No LLM/API calls."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def save(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
def obj(properties,required=None):
    return {'type':'object','properties':properties,'required':required or list(properties),'additionalProperties':False}
S={'type':'string','minLength':1}
ID={'type':'string','pattern':'^[A-Za-z][A-Za-z0-9_-]*$'}
def array(item):return {'type':'array','items':item}
source=obj(dict(id=ID,title=S,url=S,doi={'type':'string'},version=S,access={'enum':['full','abstract','metadata']},checked=S))
claim=obj(dict(id=ID,text=S,source=ID,locator=S,conditions=S,kind={'enum':['reported','interpretation','hypothesis','unverified']}))
relation=obj({'from':ID,'to':ID,'kind':S,'basis':S,'verified':{'type':'boolean'}})
hypothesis=obj(dict(id=ID,basis=ID,proposal=S,conditions=S,experiment=S,falsification=S))
schema=obj(dict(schema_version={'const':1},title=S,question=S,sources=array(source),claims=array(claim),relations=array(relation),hypotheses=array(hypothesis)))
schema['$schema']='https://json-schema.org/draft/2020-12/schema'
save(Path('schema.json'),json.dumps(schema,indent=2))

data={
 'schema_version':1,'title':'LoRA를 읽고, 근거와 계산을 남기는 논문 리뷰',
 'question':'전체 가중치를 학습하지 않고도 작업에 적응시키는 방법은 무엇이며, 이번 리뷰에서 직접 확인할 수 있는 범위는 어디까지인가?',
 'sources':[
  {'id':'LoRA','title':'LoRA: Low-Rank Adaptation of Large Language Models','url':'https://arxiv.org/abs/2106.09685v2','doi':'10.48550/arXiv.2106.09685','version':'v2 (2021-10-16)','access':'full','checked':'2026-10-22'},
  {'id':'QLoRA','title':'QLoRA: Efficient Finetuning of Quantized LLMs','url':'https://arxiv.org/abs/2305.14314v1','doi':'10.48550/arXiv.2305.14314','version':'v1 (2023-05-23)','access':'abstract','checked':'2026-10-22'}],
 'claims':[
  {'id':'C1','text':'LoRA는 원래 가중치를 고정하고 두 행렬의 곱으로 업데이트를 표현한다.','source':'LoRA','locator':'Section 4.1, Eq. (3), PDF p.4','conditions':'W0: d×k, B: d×r, A: r×k. 본문은 업데이트에 alpha/r 스케일도 적용한다.','kind':'reported'},
  {'id':'C2','text':'행렬을 미리 병합하면 추론 때 추가 분기를 계산하지 않아도 된다.','source':'LoRA','locator':'Section 4.1, PDF p.4','conditions':'고정된 어댑터를 W0에 합산하는 선형 연산. 실제 장치의 지연시간은 이번에 측정하지 않았다.','kind':'reported'},
  {'id':'C3','text':'일부 가중치만 학습하는 것과 기반 모델을 메모리에 보관하지 않는 것은 다르다.','source':'LoRA','locator':'Section 4.2, PDF p.5, footnote 4','conditions':'학습할 매개변수, optimizer 상태, 기반 가중치 저장을 구분한다.','kind':'interpretation'},
  {'id':'C4','text':'alpha는 항상 2r이어야 한다는 규칙은 이 논문의 일반 결론이 아니다.','source':'LoRA','locator':'Section 4.1, PDF p.4','conditions':'논문은 첫 시도 rank에 alpha를 맞추고 별도 조정하지 않았다고 설명한다.','kind':'interpretation'},
  {'id':'C5','text':'QLoRA는 고정된 4비트 기반 모델을 통과해 LoRA 매개변수로 gradient를 전달하는 후속 접근이다.','source':'QLoRA','locator':'Abstract','conditions':'초록 기반 관계 확인. 세부 구현과 실험은 정독·재현하지 않았다.','kind':'reported'}],
 'relations':[{'from':'LoRA','to':'QLoRA','kind':'보완·후속 적용','basis':'QLoRA Abstract explicitly describes low-rank adapters with frozen 4-bit pretrained weights.','verified':True}],
 'hypotheses':[{'id':'H1','basis':'C1','proposal':'rank를 키울 때 표현 가능한 변화가 늘어도 일반화 성능이 계속 좋아지는지는 별도 질문이다.','conditions':'동일 모델·데이터 분할·적용 층·학습 예산; rank와 alpha 설정을 함께 기록','experiment':'작은 공개 데이터에서 rank별 검증 손실과 학습 시간·메모리를 여러 seed로 비교한다. 이번 패키지에서는 미실행.','falsification':'높은 rank에서 검증 성능 개선이 반복되지 않으면 단조 개선 가설을 지지하지 않는다.'}]
}
save(Path('examples/lora/evidence.json'),json.dumps(data,ensure_ascii=False,indent=2))
save(Path('examples/lora/review.md'),'''# LoRA를 읽고, 근거와 계산을 남기기

> 이 예제는 **논문 리뷰 절차의 실행 검증**입니다. 대규모 언어모델의 학습 성능을 재현한 실험이 아닙니다. 원문은 LoRA v2, 후속 QLoRA는 초록까지 확인했습니다.

[TOC]

## 1. 왜 작은 업데이트를 따로 학습할까

학습된 모델을 새로운 작업에 맞출 때 모든 숫자를 바꾸는 대신, 바뀔 부분을 작은 행렬 두 개로 표현하는 접근입니다. 원본 가중치 W0는 고정하고 A와 B를 학습합니다. [claim:C1]

행렬은 숫자를 직사각형으로 놓은 표입니다. 입력 벡터 x에 행렬을 곱하면 새 벡터가 나옵니다. rank r은 여기서 중간 통로의 폭입니다. 작은 통로로 표현한 업데이트에는 표현력 제약이 있지만, 저장하고 학습할 숫자도 줄어듭니다.

## 2. 기호보다 계산 순서를 먼저 보기

```text
입력 x ── W0 (고정) ──────────┐
      └── A → B → alpha/r ───┴─ 합산 → 출력 h
             (학습)
```

W0가 d×k, A가 r×k, B가 d×r이면 BA는 d×k입니다. 따라서 같은 입력 x에 대한 두 출력은 더할 수 있습니다. 논문 식 (3)에 본문의 스케일 설명을 함께 쓰면 다음과 같습니다.

```text
h = W0 x + (alpha / r) B A x
학습할 숫자: d*k → r*(d+k)  (이 한 층의 가중치만 비교)
```

이 숫자 비율을 전체 GPU 메모리 절약률로 읽으면 안 됩니다. 기반 가중치와 활성값 등 다른 항목이 남습니다. [claim:C3]

## 3. 손으로 따라갈 수 있는 예제

아래 숫자는 설명을 위해 만든 값입니다. 실제 학습한 가중치가 아닙니다.

```text
W0 = [[1, 0], [0, 1]], x = [2, 3]
A = [[1, -1]], B = [[2], [1]], r = 1
Ax = [-1], BAx = [-2, -1]
alpha = 0 → h = [2, 3]
alpha = 1 → h = [0, 2]
alpha = 2 → h = [-2, 1]
```

같은 입력에 대해 분기 계산과 병합한 행렬 계산이 일치하는지 Python으로 검사합니다. 이 작은 예제는 2×2여서 매개변수 절약 사례는 아닙니다. 절약 비율은 아래 상호작용에서 별도로 보여줍니다. [claim:C2]

## 4. 원문과 내 해석을 구분하기

| 질문 | 판단 | 확인 범위 |
|---|---|---|
| A와 B만 학습하는가? | 원문 방법 설명 | 4.1절 |
| 병합하면 선형 출력이 같은가? | 원문 설명 + 작은 수치 검증 | 실제 GPU 속도는 미측정 |
| alpha=2r가 고정 공식인가? | 일반화 불가 | 원문 설정과 구분 |
| 다른 작업에서도 항상 성능이 유지되는가? | 이번 검증으로 판단 불가 | 모델 학습 미실행 |

alpha를 항상 rank의 두 배로 고정해야 한다는 규칙을 만들지 않습니다. [claim:C4]

주요 방법과 조건은 PDF 4–5쪽을 시각적으로 대조합니다. 나머지 페이지의 텍스트 추출 성공은 모든 표·실험을 정독했다는 뜻이 아닙니다. 이번 설명 범위는 저랭크 업데이트, 병합, 저장 구분입니다.

## 5. 다른 논문과 연결하기

QLoRA 초록은 4비트 기반 모델과 LoRA를 연결합니다. 이는 ‘학습할 숫자를 줄이는 방법’에 ‘기반 가중치 표현을 줄이는 방법’을 결합하는 관계로 읽을 수 있습니다. [claim:C5]

이번 탐색은 공개 arXiv의 LoRA v2 전문과 QLoRA v1 초록을 사용한 한 단계 연결입니다. Google Scholar와 Deep Research를 실행하지 않았고, 최신 연구 전체를 조사하지 않았습니다. 독립적인 성능 비교도 아닙니다.

## 6. 의문점과 다음 실험

rank가 커지면 검증 성능도 계속 좋아질까요? 표현할 수 있는 변화가 늘어나는 것과 일반화가 좋아지는 것은 같은 말이 아닙니다.

가설 H1은 동일한 공개 모델·데이터 분할·학습 예산으로 rank별 검증 손실과 메모리를 비교하는 것입니다. 적용 층과 alpha도 기록하고 여러 seed로 흔들림을 확인해야 합니다. 높은 rank의 개선이 반복되지 않으면 단조 개선 가설을 버립니다. **이 후속 학습 실험은 실행하지 않았습니다.**

## 7. 재사용 방법과 원본 그림

evidence.json에는 주장과 출처를, review.md에는 설명을 둡니다. check는 ID·필수 필드·접근 범위·본문 연결을 검사합니다. 그럴듯하지만 틀린 문장도 형식이 맞으면 통과하므로 원문 검토가 필요합니다.

원본 Figure 1은 [LoRA PDF 1쪽](https://arxiv.org/pdf/2106.09685v2#page=1)에서 확인할 수 있습니다. 원문 PDF·그림은 공개 저장소에 재배포하지 않았습니다. 위 흐름도와 상호작용은 별도로 제작한 설명 자료입니다. 본문의 모든 그림을 재현하는 범위는 아닙니다.
''')
save(Path('examples/lora/demo.html'),'''<section id="demo"><h2>수식 실험: 업데이트 강도 바꾸기</h2><p>설명용 고정 A·B·x. alpha를 바꾸면 출력이 어떻게 달라질까요?</p><label for="alpha">alpha: <output id="av">1</output></label><br><input id="alpha" type="range" min="0" max="2" step="0.1" value="1"><p id="result" aria-live="polite"></p><svg viewBox="0 0 600 220" role="img" aria-label="입력과 출력의 각 성분을 비교하는 막대. 가로축 원점 300, 값 하나당 60픽셀"><line x1="300" y1="10" x2="300" y2="200" stroke="#999"/><text x="15" y="60">h[0]</text><text x="15" y="140">h[1]</text><rect id="b0" y="35" height="40" fill="#285e89"/><rect id="b1" y="115" height="40" fill="#9c632d"/><text x="290" y="215">0</text></svg><p><small>막대: 출력 성분, 값 단위 없음. 성능 곡선이나 학습 과정이 아닙니다.</small></p><label for="rank">1024×1024 한 층의 rank: <output id="rv">4</output></label><br><input id="rank" type="range" min="1" max="64" value="4"><p id="params" aria-live="polite"></p><p>기반 가중치·활성값·optimizer를 포함한 전체 메모리 계산은 아닙니다.</p></section><script>
function update(){let a=+document.querySelector('#alpha').value;document.querySelector('#av').textContent=a;let h=[2-2*a,3-a];document.querySelector('#result').textContent='h = ['+h.map(x=>x.toFixed(1)).join(', ')+']';h.forEach((v,i)=>{let e=document.querySelector('#b'+i);e.setAttribute('x',Math.min(300,300+v*60));e.setAttribute('width',Math.abs(v*60))});let r=+document.querySelector('#rank').value;document.querySelector('#rv').textContent=r;document.querySelector('#params').textContent='학습할 숫자 '+(2048*r).toLocaleString()+' / 1,048,576 ('+(r/512*100).toFixed(2)+'%)';}document.querySelector('#alpha').addEventListener('input',update);document.querySelector('#rank').addEventListener('input',update);update();</script>''')
print('Authored schema and example written')
