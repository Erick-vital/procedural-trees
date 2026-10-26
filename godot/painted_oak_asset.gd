@tool
extends Node3D
## Material RGBA del roble: sombras dobles y filtrado fijados para Godot.
func _ready() -> void:
    configure(self)

func configure(node: Node) -> void:
    if node is MeshInstance3D:
        node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
        for index in range(node.mesh.get_surface_count()):
            var source=node.mesh.surface_get_material(index)
            if source.resource_name!='Oak_Painted_Leaf':continue
            var mat=source.duplicate()
            mat.cull_mode=BaseMaterial3D.CULL_DISABLED
            mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
            mat.alpha_scissor_threshold=.5
            mat.alpha_antialiasing_mode=BaseMaterial3D.ALPHA_ANTIALIASING_OFF
            mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
            node.set_surface_override_material(index,mat)
    for child in node.get_children():configure(child)
