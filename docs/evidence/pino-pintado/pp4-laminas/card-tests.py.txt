"""Separar reducción de soporte transparente y ajuste explícito de copa."""
import copy
import math
import unittest
from pathlib import Path
from PIL import Image
from treegen.blueprints import load_blueprint,load_instance,resolve_blueprint
from treegen.pine_painted import build,check_parameters
from treegen.pine_painted_cards import OUTLINE
from treegen.pine_painted_sample import ROW_CENTERS,canonical_hash

ROOT=Path(__file__).resolve().parents[1]

class CardTests(unittest.TestCase):
    def resolve(self,n,version):
        folder='pino-pintado-laminas' if version=='2.3.0' else 'pino-pintado-madera'
        return resolve_blueprint(load_blueprint(f'blueprints/pino_conico/{version}.json'),load_instance(f'presets/blueprints/{folder}/{n}.json'))

    def test_four_cases_common_tuning_and_affine_planes(self):
        for n in ('pilot','control-01','control-02','control-03'):
            old=build(self.resolve(n,'2.2.0'));new=build(self.resolve(n,'2.3.0'))
            self.assertEqual(old[:2],new[:2]);self.assertEqual(len(new[2]),435)
            for a,b in zip(old[2],new[2]):
                self.assertEqual(b['card_optimization']['before_sha256'],canonical_hash(a))
                self.assertEqual(b['origin_m'],a['origin_m']);self.assertEqual(b['group_id'],a['group_id'])
                self.assertEqual(len(b['polygons']),6)
                self.assertAlmostEqual(b['crown_reduction']['width_scale']**2,.9)
                for offset,new_offset in ((0,0),(8,5)):
                    v0,v1,v2=[a['vertices'][offset+i] for i in (0,1,2)]
                    width=[(v1[k]-v0[k])/.09 for k in range(3)]
                    longitudinal=[(v2[k]-v0[k]+.11*width[k])/.18 for k in range(3)]
                    axis=[x/math.sqrt(sum(y*y for y in longitudinal)) for x in longitudinal]
                    for i,(u,v) in enumerate(OUTLINE):
                        p=[v0[k]+(u-.05)*longitudinal[k]+(v+.045)*width[k] for k in range(3)]
                        delta=[p[k]-a['origin_m'][k] for k in range(3)];along=sum(x*y for x,y in zip(delta,axis))
                        expected=[a['origin_m'][k]+along*axis[k]+math.sqrt(.9)*(delta[k]-along*axis[k]) for k in range(3)]
                        for x,y in zip(expected,b['vertices'][new_offset+i]):self.assertAlmostEqual(x,y,places=12)
                        self.assertEqual(b['uv'][new_offset+i],[u,ROW_CENTERS[a['atlas_variant']]+v])

    def test_extended_support_is_transparent_in_frozen_atlas(self):
        im=Image.open(ROOT/'assets/pino-pintado/v0.1.0/foliage.png');pixels=im.load();n=im.width
        for center in ROW_CENTERS:
            checked=0
            for y in range(n):
                v=1-(y+.5)/n-center
                if abs(v)>.155:continue
                for x in range(math.ceil(.05*n),int(.97*n)):
                    u=(x+.5)/n
                    top=.155 if u<=.65 else .155-(u-.65)/.32*.035
                    if v>top:continue
                    half=.045+(u-.05)/.18*.11 if u<.23 else .155 if u<.65 else top
                    if abs(v)>half:
                        self.assertLess(pixels[x,y][3],128);checked+=1
            self.assertGreater(checked,1000)

    def test_budget_and_repeat(self):
        r=self.resolve('pilot','2.3.0');self.assertEqual(build(r),build(r))
        self.assertEqual(r['budget_upper_bound']['added_triangles_max'],2610)
        with self.assertRaises(ValueError):
            check_parameters(r['parameters'],{'triangles':4909,'materials':2},representation='pine-painted-crossed@0.4.0')

if __name__=='__main__':unittest.main()
