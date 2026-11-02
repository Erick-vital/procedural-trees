import copy
import json
from pathlib import Path
import unittest
from treegen.season_transition import validate_profile, blend_rgb, decode_srgb, encode_srgb
ROOT=Path(__file__).resolve().parents[1]

class TransitionTests(unittest.TestCase):
    def test_profile_resources_and_no_mutation(self):
        p=json.loads((ROOT/'configs/seasons/roble-mezcla-v1.json').read_text());before=copy.deepcopy(p)
        self.assertEqual(validate_profile(p),p);self.assertEqual(before,p)
        for mutation in ['extra','species','path','hash']:
            bad=copy.deepcopy(p)
            if mutation=='extra':bad['unknown']=1
            if mutation=='species':bad['species']='pino@1.0.0'
            if mutation=='path':bad['resources']['summer']['path']='../secret.png'
            if mutation=='hash':bad['resources']['autumn']['sha256']='0'*64
            with self.assertRaises(ValueError):validate_profile(bad)

    def test_linear_midpoint_and_roundtrip(self):
        mid=blend_rgb([0,0,0],[1,1,1],.5,mode='uniform')
        self.assertAlmostEqual(mid[0],.735356983,places=8)
        for c in [0,.003,.04045,.3,.9,1]:self.assertAlmostEqual(encode_srgb(decode_srgb(c)),c,places=7)

    def test_extremes_direct_jump_reverse_and_common_group(self):
        a,b=[.1,.6,.2],[.9,.3,.05]
        values=[blend_rgb(a,b,p/120,.25,.2) for p in range(121)]
        for x,y in zip(values[0],a):self.assertAlmostEqual(x,y)
        for x,y in zip(values[-1],b):self.assertAlmostEqual(x,y)
        self.assertEqual(list(reversed(values)),[blend_rgb(a,b,p/120,.25,.2) for p in range(120,-1,-1)])
        blend_rgb(a,b,.9,.25,.2)
        self.assertEqual(blend_rgb(a,b,.2,.25,.2),values[24])
        for mode in ('summer','autumn'):
            self.assertEqual(blend_rgb(a,b,0,mode=mode),blend_rgb(a,b,1,mode=mode))

    def test_bad_phase_rgb_and_mode(self):
        for p in [-.1,1.1,float('nan'),float('inf'),True]:
            with self.assertRaises(ValueError):blend_rgb([0,0,0],[1,1,1],p)
        with self.assertRaises(ValueError):blend_rgb([0,0],[1,1,1],.5)
        with self.assertRaises(ValueError):blend_rgb([0,0,0],[1,1,1],.5,mode='winter')
