"""Synthetic arithmetic only. Does not reproduce model training."""
import json
from pathlib import Path
def matmul(a,b):
    if not a or not b or len(a[0])!=len(b): raise ValueError('shape mismatch')
    return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
def verify():
    w=[[1.,0.],[0.,1.]];a=[[1.,-1.]];b=[[2.],[1.]];x=[[2.],[3.]]
    delta=matmul(b,a);base=matmul(w,x);branch=matmul(b,matmul(a,x))
    cases=[]
    for alpha in (0.,0.5,1.,2.):
        merged=[[w[i][j]+alpha*delta[i][j] for j in range(2)] for i in range(2)]
        left=matmul(merged,x);right=[[base[i][0]+alpha*branch[i][0]] for i in range(2)]
        error=max(abs(left[i][0]-right[i][0]) for i in range(2))
        assert error<1e-12
        cases.append({'alpha':alpha,'output':left,'max_abs_error':error})
    assert cases[2]['output']==[[0.],[2.]]
    return {'scope':'synthetic linear arithmetic; no model training','cases':cases,'parameter_count':{'d':1024,'k':1024,'r':4,'full':1048576,'lora':8192}}
if __name__=='__main__':
    result=verify();Path(__file__).with_name('math-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
