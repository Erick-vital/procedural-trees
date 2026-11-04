"""Ángulos adicionales conservadores para R3 al integrarse en un árbol."""
import math
VERSION='branch-tree-guard-angles-0.1.0'

def visibility_guard_directions():
    vectors=[(0,-1,.1),(1,0,.1),(1,-1,.45),(0,0,1),(1,-1,-.5),(-1,1,.3)]
    vectors += [(math.cos(math.radians(7.5+45*i)),math.sin(math.radians(7.5+45*i)),-.25) for i in range(8)]
    return [tuple(v/math.sqrt(sum(x*x for x in d)) for v in d) for d in vectors]
