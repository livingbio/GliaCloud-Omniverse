#include "ReShade.fxh"

namespace OcularFX
{
uniform float timer < source = "timer";
> ;

uniform float Size < ui_type = "drag";
ui_min = 0.0;
ui_max = 50.0;
ui_step = 1.0;
ui_label = "Ocular Size";
ui_tooltip = "Ocular Size";
> = 20.0;

uniform float Softness < ui_type = "drag";
ui_min = 0.0;
ui_max = 100.0;
ui_step = 1.0;
ui_label = "Ocular Softness";
ui_tooltip = "Ocular Edge Mask Softness";
> = 10.0;

uniform float Binocular < ui_type = "drag";
ui_min = 0.0;
ui_max = 100.0;
ui_step = 1.0;
ui_label = "Binocular";
ui_tooltip = "Monocular/Binocular Shape";
> = 20.0;

uniform float3 Color < ui_type = "color";
ui_label = "Ocular Mask Color";
> = float3(0.0, 0.0, 0.0);

uniform int NightVisionMode < ui_type = "list";
ui_label = "Color Mode";
ui_items = "Normal; Night Vision";
> = 0;

uniform float3 NightVisionTint < ui_type = "list";
ui_label = "Night Vision Color Tint";
> = float3(0.4, 0.9, 0.4);

uniform float Noise < ui_type = "drag";
ui_min = 0.0;
ui_max = 100.0;
ui_step = 1.0;
ui_label = "Night Vision Noise";
ui_tooltip = "Noise";
> = 0.0;

float hash12(float2 p)
{
    float3 p3 = frac((p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return frac((p3.x + p3.y) * p3.z);
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target
{

    float2 circle[2];

    float bino = lerp(0.0, 0.5, 1. - Binocular * 0.01);
    circle[0] = float2(float(ReShade::ScreenSize.x) * bino, ReShade::ScreenSize.y * 0.5);
    circle[1] = float2(float(ReShade::ScreenSize.x) * (1.0 - bino), ReShade::ScreenSize.y * 0.5);

    float circle_size[4];
    float abs_res = length(ReShade::ScreenSize);
    circle_size[0] = abs_res * Size;
    circle_size[1] = abs_res * Size;

    float dist[2];
    float t1, t2;

    t1 = vpos.x - circle[0].x;
    t2 = vpos.y - circle[0].y;
    dist[0] = sqrt(t1 * t1 + t2 * t2);
    dist[0] = circle_size[0] / (dist[0] * dist[0]);

    t1 = vpos.x - circle[1].x;
    t2 = vpos.y - circle[1].y;
    dist[1] = sqrt(t1 * t1 + t2 * t2);
    dist[1] = circle_size[1] / (dist[1] * dist[1]);

    float t3 = dist[0] + dist[1];

    t3 = smoothstep(0.5, .5001 + Softness * 0.01, t3);

    float4 c0 = tex2D(ReShade::BackBuffer, uv);
    float4 c1 = 1.0;
    c1.rgb = Color.rgb;
    float4 c = 1.0;
    c.rgb = lerp(c0.rgb, c1.rgb, 1. - t3);

    float fnoise = 1.0 - hash12(round(vpos.xy / 4.) * 4. + timer) * Noise * 0.01;
    if (Noise > 0.0)
    {
        c.rgb *= fnoise;
    }
    if (NightVisionMode > 0)
    {
        c.rgb = (c.r + c.g + c.b) / 3.;
        c.rgb *= NightVisionTint;
    }
    return c;
}

technique Ocular
{
    pass
    {
        VertexShader = PostProcessVS;
        PixelShader = PS;
    }
}

} // namespace OcularFX