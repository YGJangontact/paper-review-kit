import copy
import json
import tempfile
import unittest
from pathlib import Path
import reviewkit as k

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.data=k.read(k.ROOT/'examples/lora/evidence.json')
    def test_valid(self):self.assertEqual(k.validate(self.data),[])
    def test_missing_locator(self):
        del self.data['claims'][0]['locator'];self.assertTrue(k.validate(self.data))
    def test_unknown_source(self):
        self.data['claims'][0]['source']='Missing';self.assertTrue(k.validate(self.data))
    def test_abstract_scope(self):
        self.data['sources'][0]['access']='abstract';self.assertTrue(k.validate(self.data))
    def test_duplicate_ids(self):
        self.data['sources'].append(copy.deepcopy(self.data['sources'][0]));self.assertTrue(k.validate(self.data))
    def test_script_url(self):
        self.data['sources'][0]['url']='javascript:alert(1)';self.assertTrue(k.validate(self.data))
    def test_unknown_hypothesis(self):
        self.data['hypotheses'][0]['basis']='Missing';self.assertTrue(k.validate(self.data))
    def test_false_claim_not_detected(self):
        self.data['claims'][0]['text']='LoRA always improves all models by 999 percent.'
        self.assertEqual(k.validate(self.data),[], 'Structural validation cannot determine truth')
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'a';k.write(p,'original')
            with self.assertRaises(ValueError):k.write(p,'replacement')
            self.assertEqual(p.read_text(),'original')
    def test_resume_invalidation(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t);k.write(f/'review.md','v1');k.mark(f,'review',['review.md'])
            self.assertEqual(k.state(f)['stages']['review']['state'],'done')
            k.write(f/'review.md','v2',True)
            self.assertEqual(k.state(f)['stages']['review']['state'],'stale')
    def test_evidence_outside_folder(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):k.mark(Path(t),'review',['../missing.md'])
    def test_doi_versions_not_merged(self):
        s=copy.deepcopy(self.data['sources'][0]);s['id']='Other';s['doi']='https://doi.org/'+s['doi'].upper();s['version']='v1'
        self.data['sources'].append(s)
        self.assertEqual(len(k.duplicates(self.data)[0]),2)
    def test_render_escapes_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t);self.data['claims'][0]['text']='<script>alert(1)</script>'
            k.dump(f/'evidence.json',self.data);k.write(f/'review.md',' '.join('[claim:'+c['id']+']' for c in self.data['claims']))
            k.export(f)
            output=(f/'exports/review.html').read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;',output);self.assertNotIn('<script>alert(1)',output)
    def test_unknown_prose_claim(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t);k.dump(f/'evidence.json',self.data);k.write(f/'review.md','[claim:Missing]')
            self.assertTrue(k.check(f))

if __name__=='__main__':unittest.main()
