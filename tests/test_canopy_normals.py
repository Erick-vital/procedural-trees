import copy
import math
import struct
import unittest
from treegen.canopy_normals import build_fields,normal,dot
from treegen.canopy_normals_glb import replace_normals,audit_normals,rows
from treegen.season_calendar_glb import attach_calendar,audit_transport,pack
from treegen.seasonal_paint import unpack
from test_season_calendar import volumes
from test_season_calendar_glb import fixture


class CanopyNormalsTests(unittest.TestCase):
    def setup_data(self):
        raw,cards,calendar=fixture();derived=attach_calendar(raw,cards,calendar)
        binding=audit_transport(raw,derived,cards,calendar)['binding']
        return derived,binding,build_fields(volumes()[:2],calendar),calendar

    def test_fields_deterministic_under_input_order(self):
        raw,binding,fields,data=self.setup_data()
        self.assertEqual(fields,build_fields(list(reversed(volumes()[:2])),data))
        alt=copy.deepcopy(data);alt['groups'][0]['neighbors']=[]
        self.assertNotEqual(fields,build_fields(volumes()[:2],alt))
        bad=copy.deepcopy(data);bad['groups_sha256']='0'*64
        with self.assertRaises(ValueError):build_fields(volumes()[:2],bad)

    def test_angle_bound_unit_hemisphere_center_and_reverses(self):
        field={'center':[0,0,0],'inverse_covariance':[[1,0,0],[0,1,0],[0,0,1]]}
        for original in ([0,0,1],[0,0,-1]):
            for strength in (0,.35,.65,.75):
                n=normal([1,0,.001],original,field,strength)
                self.assertAlmostEqual(dot(n,n),1)
                self.assertGreaterEqual(dot(n,original),math.cos(math.radians(60*strength))-1e-10)
            self.assertEqual(normal([0,0,0],original,field,.65),original)
        n=normal([1,0,.2],[0,0,1],field,.65)
        reverse=normal([1,0,.2],[0,0,-1],field,.65)
        self.assertTrue(all(abs(a+b)<1e-12 for a,b in zip(n,reverse)))

    def test_bad_normals_parameters_and_groups(self):
        f={'center':[0,0,0],'inverse_covariance':[[1,0,0],[0,1,0],[0,0,1]]}
        for s in (-.1,.8,True,float('nan')):
            with self.assertRaises(ValueError):normal([1,0,0],[0,0,1],f,s)
        with self.assertRaises(ValueError):normal([1,0,0],[0,0,0],f,.35)
        with self.assertRaises(ValueError):normal([float('nan'),0,0],[0,0,1],f,.35)
        with self.assertRaises(ValueError):build_fields(volumes()*200,{})

    def test_glb_only_normals_exact_repeat_zero_and_binding_order(self):
        raw,binding,fields,_=self.setup_data()
        result,report=replace_normals(raw,binding,fields,.65)
        self.assertTrue(report['only_foliage_normals_changed']);self.assertGreater(report['changed_normal_vertices'],0)
        self.assertEqual(result,replace_normals(raw,list(reversed(binding)),fields,.65)[0])
        self.assertEqual(raw,replace_normals(raw,binding,fields,0)[0])
        self.assertTrue(all(abs(dot(r['normal'],r['normal'])-1)<2e-6 for r in rows(result)))
        with self.assertRaises(ValueError):replace_normals(raw,binding[:-1],fields,.65)

    def test_rejects_overlapping_normal_storage(self):
        raw,binding,fields,_=self.setup_data();doc,binary=unpack(raw)
        attrs=doc['meshes'][0]['primitives'][1]['attributes']
        normal=doc['accessors'][attrs['NORMAL']]['bufferView']
        position=doc['accessors'][attrs['POSITION']]['bufferView']
        doc['bufferViews'][position]['byteOffset']=doc['bufferViews'][normal]['byteOffset']
        with self.assertRaises(ValueError):replace_normals(pack(doc,binary),binding,fields,.65)

    def test_audit_rejects_geometry_material_and_normal_corruption(self):
        raw,binding,fields,_=self.setup_data();result,_=replace_normals(raw,binding,fields,.65)
        for kind in ('geometry','material','normal'):
            doc,binary=unpack(result)
            if kind=='material':doc['materials'][0]['name']='Changed'
            else:
                p=doc['meshes'][0]['primitives'][1]
                a=doc['accessors'][p['attributes']['NORMAL' if kind=='normal' else 'POSITION']]
                offset=doc['bufferViews'][a['bufferView']]['byteOffset']
                binary=binary[:offset]+struct.pack('<f',50)+binary[offset+4:]
            with self.subTest(kind=kind),self.assertRaises(ValueError):audit_normals(raw,pack(doc,binary))
