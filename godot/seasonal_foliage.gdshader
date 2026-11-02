shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

// Transformación de color: geometría, UV y alfa originales conservados.
uniform sampler2D foliage_texture : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 palette_dark : source_color;
uniform vec4 palette_copper : source_color;
uniform vec4 palette_gold : source_color;
uniform float season_amount : hint_range(0.0, 1.0) = 1.0;
uniform float green_retention = 0.10;
uniform float patch_scale_m = 1.7;
uniform float season_seed = 1101.0;
uniform bool mask_mode = false;
varying vec3 tree_position;

void vertex() {
    tree_position = VERTEX;
}

float patch(vec3 p) {
    // Campo continuo en espacio local: no cambia al mover el árbol ni la cámara.
    float offset = mod(season_seed, 8191.0) * 0.137;
    return clamp(0.5 + 0.24 * sin(p.x * 1.8 + p.y * 0.9 + offset)
        + 0.18 * sin(p.z * 2.3 - p.y * 1.4 - offset * 1.7), 0.0, 1.0);
}

void fragment() {
    vec4 paint = texture(foliage_texture, UV);
    float region = patch(tree_position / patch_scale_m);
    vec3 warm = mix(palette_dark.rgb, palette_copper.rgb, smoothstep(0.05, 0.5, region));
    warm = mix(warm, palette_gold.rgb, smoothstep(0.48, 0.85, region));
    float luminance = dot(paint.rgb, vec3(0.2126, 0.7152, 0.0722));
    warm *= clamp(luminance / 0.22, 0.28, 1.25);
    // Proteger trazos pardos de ramilla; transformar pigmentos verdes de hojas.
    float leaf_pigment = smoothstep(-0.015, 0.045, paint.g - paint.r);
    float retained = green_retention > 0.0 ? smoothstep(1.0-green_retention-0.06, 1.0-green_retention, region) : 0.0;
    ALBEDO = mask_mode ? vec3(0.0) : mix(paint.rgb, warm, season_amount * leaf_pigment * (1.0-retained));
    ALPHA = paint.a;
    ALPHA_SCISSOR_THRESHOLD = 0.5;
    ROUGHNESS = 0.88;
    SPECULAR = 0.5;
}
