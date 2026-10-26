"""Evitar resultados de benchmark con límites o métricas mal interpretadas."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pine_benchmark',ROOT/'scripts/benchmark_painted_pine.py')
benchmark=importlib.util.module_from_spec(spec);spec.loader.exec_module(benchmark)

class PerformanceTests(unittest.TestCase):
    def report(self):
        return {'renderer':'gl_compatibility','gpu':'test GPU','actual_vsync':0,'actual_max_fps':0,'actual_lod_threshold':0,
                'actual_resolution':[1920,1080],'settings':{'resolution':[1920,1080],'shadows':True},'actual_msaa':2,'actual_shadows':True,
                'columns':['frame_ms','render_cpu_ms','render_gpu_ms','render_setup_cpu_ms','draw_calls','primitives','objects'],
                'trials':[{'trial':i,'version':v,'mesh_instances':1,'samples':[[ms,1,0,.1,2,10,1] for _ in range(10)]}
                          for i,(v,ms) in enumerate([('baseline',10),('candidate',8),('candidate',12),('baseline',10)])]}

    def test_independent_pairs_fps_and_missing_gpu(self):
        r=benchmark.summarize(self.report())
        self.assertAlmostEqual(r['paired_frame_time_reduction_percent'][0],20)
        self.assertAlmostEqual(r['paired_frame_time_reduction_percent'][1],-20)
        self.assertAlmostEqual(r['median_paired_frame_time_reduction_percent'],0)
        self.assertAlmostEqual(r['aggregate']['baseline']['fps'],100)
        self.assertIsNone(r['aggregate']['candidate']['render_gpu_ms'])
        self.assertAlmostEqual(benchmark.percentile([1,2,3,4],.5),2.5)

    def test_reject_cap_lod_software_and_resolution_mismatch(self):
        for key,value in [('actual_vsync',1),('actual_max_fps',60),('actual_lod_threshold',1),('gpu','llvmpipe'),('actual_resolution',[1280,720])]:
            r=self.report();r[key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):benchmark.summarize(r)

    def test_reject_empty_or_nonpositive_timings(self):
        for samples in ([],[[0,0,0,0,0,0,0]]*10):
            r=self.report();r['trials'][0]['samples']=samples
            with self.assertRaises(AssertionError):benchmark.summarize(r)

if __name__=='__main__':unittest.main()
