#!/usr/bin/env python3
"""O3: comparar O2/O3, cinco maduros y cinco centenarios, mismas cámaras."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from treegen.oak_growth_runner import execute_growth
from verify_oak_crown import review
from verify_oak_growth import review_ages

CASES=[(stage,seed) for stage in ('maduro','centenario') for seed in range(3100,3105)]+[('joven',3100)]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stage',choices=('generate','review','ages'),default='generate');p.add_argument('--case');a=p.parse_args();study=a.output.resolve()
    if a.stage=='ages':review_ages(study);return
    for stage,seed in CASES:
        case=f'{stage}-{seed}'
        if a.case and case!=a.case:continue
        if a.stage=='review':review(study,case);continue
        for version,out in [('0.2.0',study/'before'/case),('0.3.0',study/case)]:
            print(execute_growth(ROOT/f'presets/oak-growth/{version}/{stage}.json',seed,out),flush=True)

if __name__=='__main__':main()
