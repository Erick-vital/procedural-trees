"""Rechazar benchmarks de roble incompletos o con condiciones distintas."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('oak_benchmark', ROOT/'scripts/benchmark_painted_oak.py')
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class OakPerformanceTests(unittest.TestCase):
    def report(self):
        mats = [dict(name=name, textured=True, mipmaps=True, cull_mode=2, shadow_casting=2,
                     filter=5, roughness=.95, transparency=2 if name=='Painted_Foliage' else 0,
                     alpha_cutoff=.5, alpha_aa=0) for name in ('Painted_Bark', 'Painted_Foliage')]
        return {'settings': {'renderer':'gl_compatibility', 'resolution':[1920,1080],
                'shadow_distance_m':1500, 'camera_far_m':2000, 'count':1, 'repetitions':4,
                'measurement_seconds':.1, 'spacing_m':18},
                'renderer':'gl_compatibility', 'gpu':'test GPU', 'actual_vsync':0, 'actual_max_fps':0,
                'actual_lod_threshold':0, 'actual_resolution':[1920,1080], 'actual_msaa':2,
                'actual_shadows':True, 'shadow_distance_m':1500,
                'camera': {'projection':1, 'far':2000}, 'layout':[{'case':0,'position':[0,0,0],'rotation_y':0}],
                'materials':{'oak':[copy.deepcopy(mats) for _ in range(5)]},
                'columns':['frame_ms','render_cpu_ms','render_gpu_ms','render_setup_cpu_ms','draw_calls','primitives','objects'],
                'trials':[{'trial':i,'version':'oak','mesh_instances':1,
                           'samples':[[ms,1,0,.1,5,100,2]]*10} for i, ms in enumerate((10,20,10,20))]}

    def test_godot_integer_json_numbers_and_fractional_rejection(self):
        r = self.report(); r['settings']['count'] = 1.0
        benchmark.summarize(r)
        r['settings']['count'] = 1.5
        with self.assertRaises(AssertionError): benchmark.summarize(r)

    def test_repetitions_aggregate_and_missing_gpu(self):
        result = benchmark.summarize(self.report())
        self.assertEqual(len(result['trials']), 4)
        self.assertEqual(result['aggregate']['frame_mean_ms'], 15)
        self.assertEqual(result['aggregate']['fps'], 75)
        self.assertIsNone(result['aggregate']['render_gpu_ms'])
        self.assertEqual(result['aggregate']['run_frame_mean_range_ms'], [10,20])

    def test_reject_changed_conditions_and_software(self):
        for key, value in [('actual_vsync',1),('actual_max_fps',60),('actual_lod_threshold',1),
                           ('actual_resolution',[1280,720]),('actual_msaa',0),('actual_shadows',False),
                           ('shadow_distance_m',500),('gpu','llvmpipe'),('gpu','softpipe')]:
            r = self.report(); r[key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): benchmark.summarize(r)

    def test_reject_invalid_or_short_samples(self):
        for samples in ([], [[0,1,1,.1,5,100,2]]*10, [[float('nan'),1,1,.1,5,100,2]]*10,
                        [[1,1,1,.1,5,100,2]]*10, [[10,1,1]]*10):
            r = self.report(); r['trials'][0]['samples'] = samples
            with self.assertRaises(AssertionError): benchmark.summarize(r)

    def test_reject_lost_instances_variants_or_materials(self):
        mutations = [lambda r:r['trials'].pop(),
                     lambda r:r['trials'][0].update(mesh_instances=2),
                     lambda r:r['layout'][0].update(case=4),
                     lambda r:r['layout'][0].update(position=[1,0,0]),
                     lambda r:r['materials']['oak'].pop(),
                     lambda r:r['materials']['oak'][0][1].update(transparency=0),
                     lambda r:r['materials']['oak'][0][1].update(alpha_cutoff=.1),
                     lambda r:r['materials']['oak'][0][1].update(filter=3)]
        for mutate in mutations:
            r=self.report(); mutate(r)
            with self.assertRaises(AssertionError): benchmark.summarize(r)


if __name__ == '__main__': unittest.main()
