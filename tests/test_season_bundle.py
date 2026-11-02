import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from treegen.season_bundle import validate_profile,validate_portable,VERSION
ROOT=Path(__file__).resolve().parents[1]

class SeasonBundleTests(unittest.TestCase):
    def test_profile_explicit_and_selected_approval(self):
        p=json.loads((ROOT/'configs/seasons/roble-integracion-v1.json').read_text())
        self.assertEqual(validate_profile(p),p)
        for key,value in [('normal_strength',.65),('normal_strength',True),('normal_strength',float('nan')),('blueprint','latest'),('max_materials',True),('unknown',1)]:
            bad=copy.deepcopy(p);bad[key]=value
            with self.assertRaises(ValueError):validate_profile(bad,resources=False)

    def portable_fixture(self,root):
        (root/'tree.glb').write_bytes(b'resource')
        m={'version':VERSION,'files_sha256':{'tree.glb':hashlib.sha256(b'resource').hexdigest()},'cases':[{'id':i,'triangles':6812,'groups':264,'materials':2,'exports':{k:'tree.glb' for k in ['summer-selected','autumn-selected','summer-original','autumn-original']}} for i in ['pilot','joven-07','adulto-00','viejo-00']]}
        (root/'manifest.json').write_text(json.dumps(m));return m

    def test_portable_hashes_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);m=self.portable_fixture(root)
            self.assertEqual(validate_portable(root),m)
            (root/'tree.glb').write_bytes(b'changed')
            with self.assertRaises(ValueError):validate_portable(root)

    def test_portable_rejects_escape_budget_or_missing_export_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);m=self.portable_fixture(root)
            for change in ('escape','budget','missing','duplicate'):
                bad=copy.deepcopy(m)
                if change=='escape':bad['files_sha256']['../outside']='0'*64
                if change=='budget':bad['cases'][0]['triangles']=7000
                if change=='missing':bad['cases'][0]['exports']['summer-selected']='missing.glb'
                if change=='duplicate':bad['cases'][0]['id']='joven-07'
                (root/'manifest.json').write_text(json.dumps(bad))
                with self.assertRaises(ValueError):validate_portable(root)
