"""Optional read-only hook adapter; never installs itself or performs network I/O.

Invoke with the review directory and 'resume' (session start) or 'check' (after save).
Wire manually using the host's documented hook configuration. Plain stdout only;
host-specific JSON envelopes are intentionally not presumed.
"""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewkit
p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('action',choices=['resume','check']);a=p.parse_args()
try:
    result=reviewkit.state(a.folder) if a.action=='resume' else {'errors':reviewkit.check(a.folder),'semantic_truth_checked':False}
    print(json.dumps(result,ensure_ascii=False))
except (ValueError,OSError) as e:
    print(json.dumps({'error':str(e)},ensure_ascii=False));sys.exit(1)
