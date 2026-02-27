// Простой, но эффектный шейдер для фона "Квантовый разлом"
// Создает пульсирующую сетку/энергетический фон
#version 330 core

uniform float time;
uniform vec2 resolution;

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;

    float pixel_size = 90.0;
    uv = floor(uv * pixel_size) / pixel_size;

    uv = uv * 2.0 - 1.0;
    uv.x *= resolution.x / resolution.y;

    float d = length(uv);
    vec3 color = vec3(0.0);

    float grid1 = sin(uv.x * 10.0 + time) * sin(uv.y * 10.0 + time);
    float grid2 = sin(uv.x * 20.0 - time * 0.5) * sin(uv.y * 20.0 - time * 0.5);

    color += vec3(0.05, 0.1, 0.2) * (grid1 + 1.5);
    color += vec3(0.0, 0.8, 1.0) * (grid2 * 0.2);

    color *= 1.0 - d * 0.5;

    fragColor = vec4(color, 1.0);
}