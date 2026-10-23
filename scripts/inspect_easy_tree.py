"""Inspección local del grafo Easy Tree; ejecutar con Blender, sin instalarlo."""
import hashlib
import json
from pathlib import Path
import sys
import bpy

source, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
with bpy.data.libraries.load(str(source / 'assets/assets.blend'), link=False) as (available, loaded):
    loaded.node_groups = ['Simple Tree Generator']
group = bpy.data.node_groups['Simple Tree Generator']
inputs = [{'name': s.name, 'identifier': s.identifier, 'type': s.socket_type}
          for s in group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT']
report = {'blender': bpy.app.version_string,
          'asset_sha256': hashlib.sha256((source / 'assets/assets.blend').read_bytes()).hexdigest(),
          'groups': {g.name: len(g.nodes) for g in bpy.data.node_groups}, 'inputs': inputs,
          'loaded': True, 'full_generation_tested': False,
          'legacy_modifier_assignment_supported': False}
try:
    modifier = bpy.context.object.modifiers.new('EasyTreeProbe', 'NODES')
    modifier.node_group = group
    modifier['Socket_16'] = 17
    report['legacy_modifier_assignment_supported'] = True
except TypeError as exc:
    report['legacy_error'] = str(exc)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
