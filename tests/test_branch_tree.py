"""Contrato público de integración: entradas estrictas y presupuesto previo."""
import copy
import tempfile
import unittest
from pathlib import Path
from treegen.branch_tree import read_strict,resolve_tree,validate_definition,ROOT,PROFILES

class BranchTreeTests(unittest.TestCase):
    def setUp(self):
        self.definition=read_strict(ROOT/'configs/branch-tree/0.1.0.json')
        self.request={'profile':'joven','seeds':{'base':1003,'canopy':17,'paint':2718}}

    def test_supported_profiles_have_prebudget_below_limit(self):
        for profile in PROFILES:
            resolved=resolve_tree(self.definition,{**self.request,'profile':profile})
            self.assertLessEqual(resolved['triangle_upper_bound'],6999)
            self.assertEqual(resolved['source_resolved']['parameters']['canopy']['group_count'],264)

    def test_no_implicit_seeds_or_unknown_controls(self):
        for value in (True,-1,2147483647,1.5,'17',None):
            request=copy.deepcopy(self.request);request['seeds']['base']=value
            with self.assertRaises(ValueError):resolve_tree(self.definition,request)
        for request in ({'profile':'joven'}, {**self.request,'profile':'inventado'}, {**self.request,'height':5}):
            with self.assertRaises(ValueError):resolve_tree(self.definition,request)

    def test_definition_cannot_raise_limits_or_enable_other_recipes(self):
        for key,value in [('triangle_limit',7000),('generation_seconds',True),('source_blueprint','otro.json'),('collapse_rounds',4)]:
            with self.assertRaises(ValueError):validate_definition({**self.definition,key:value})

    def test_duplicate_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'input.json'
            for text in ('{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}'):
                path.write_text(text)
                with self.assertRaises(ValueError):read_strict(path)

    def test_whole_tree_guards_are_bounded_unit_directions(self):
        from treegen.branch_tree_guards import visibility_guard_directions
        import math
        guards=visibility_guard_directions()
        self.assertEqual(len(guards),14)
        for direction in guards:self.assertAlmostEqual(math.sqrt(sum(v*v for v in direction)),1.)

    def test_resolve_does_not_mutate_inputs_or_historical_recipe(self):
        definition=copy.deepcopy(self.definition);request=copy.deepcopy(self.request)
        source=(ROOT/definition['source_blueprint']).read_bytes()
        result=resolve_tree(definition,request);result['request']['seeds']['base']=9
        self.assertEqual(request,self.request);self.assertEqual(definition,self.definition)
        self.assertEqual(source,(ROOT/definition['source_blueprint']).read_bytes())

if __name__=='__main__':unittest.main()
