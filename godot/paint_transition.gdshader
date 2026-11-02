shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform sampler2D summer_texture : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D autumn_texture : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
instance uniform float season_phase : instance_index(0) = 0.0;
// 0 calendario; 1 uniforme; 2 verano; 3 otoño.
instance uniform int season_mode : instance_index(1) = 0;
instance uniform bool mask_mode : instance_index(2) = false;
varying vec2 group_calendar;

vec3 decode_srgb(vec3 color) {
    return mix(pow((color + vec3(0.055)) / 1.055, vec3(2.4)), color / 12.92, lessThanEqual(color, vec3(0.04045)));
}
vec3 encode_srgb(vec3 color) {
    return mix(1.055 * pow(max(color, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055, color * 12.92, lessThanEqual(color, vec3(0.0031308)));
}
void vertex() {
    group_calendar = UV2;
}
void fragment() {
    vec4 summer = texture(summer_texture, UV);
    vec3 autumn = texture(autumn_texture, UV).rgb;
    // Compatibility entrega muestras sRGB; Forward+/Mobile decodifican source_color.
    vec3 a = OUTPUT_IS_SRGB ? decode_srgb(summer.rgb) : summer.rgb;
    vec3 b = OUTPUT_IS_SRGB ? decode_srgb(autumn) : autumn;
    float p = clamp(season_phase, 0.0, 1.0);
    float w = smoothstep(group_calendar.x, group_calendar.x + group_calendar.y, p);
    if (season_mode == 1) { w = p; }
    if (season_mode == 2) { w = 0.0; }
    if (season_mode == 3) { w = 1.0; }
    vec3 blended = mix(a, b, w);
    vec3 painted = OUTPUT_IS_SRGB ? encode_srgb(blended) : blended;
    if (w <= 0.0) { painted = summer.rgb; }
    if (w >= 1.0) { painted = autumn; }
    ALBEDO = mask_mode ? vec3(0.0) : painted;
    ALPHA = summer.a;
    ALPHA_SCISSOR_THRESHOLD = 0.5;
    ROUGHNESS = 0.95;
    SPECULAR = 0.5;
    // cull_disabled activa la convención de reversos del motor; no duplicarla.
}
