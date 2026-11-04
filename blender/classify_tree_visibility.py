"""R4: clasificador histórico más ángulos de inspección del árbol completo.

Solo añade protección. El clasificador y sus consumidores históricos se conservan.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'blender')]
import classify_branch_visibility as classifier
from treegen.branch_tree_guards import visibility_guard_directions

if __name__=='__main__':
    original=classifier.directions
    classifier.directions=lambda offset=0.:original(offset)+(visibility_guard_directions() if offset else [])
    classifier.main(sys.argv[sys.argv.index('--')+1])
