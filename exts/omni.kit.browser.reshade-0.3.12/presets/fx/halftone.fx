#include "ReShade.fxh"

namespace HalftoneFX {

uniform float PatternScale < ui_type = "drag";
ui_min = 0.0;
ui_max = 12.0;
> = 4;
uniform float HalftoneAmt < ui_type = "slider";
ui_min = 0;
ui_max = 100.0;
ui_step = 1;
> = 50.0;
// uniform float timer < source = "timer"; >;

float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}

// float4 rgb2cmyki(float3 c)
// {
//     float k = max(max(c.r, c.g), c.b);
//     return min(vec4(c.rgb / k, k), 1.0);
// }

// float3 cmyki2rgb(float4 c)
// {
//     return c.rgb * c.a;
// }
float4 rgb2cmyki(float3 c) {
  float w = max(max(c.r, c.g), c.b);  // w is 1-k
  return float4((w - c.rgb) / w, 1. - w);
}

float3 cmyki2rgb(float4 c) { return (1. - c.rgb) * (1. - c.a); }
float hexd(float2 uv, float scale, float angle) {
  float2 kv = float2(1, .8164);
  float2 gp = r2d(uv, angle) * scale / kv;
  float d = length((frac(gp - .5 * float2(floor(gp.y) % 2, 0)) - 0.5) * kv);
  return d;
}
float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;
  float2 e = float2(.5, 0.0);
  float2 reso = BUFFER_SCREEN_SIZE;

  float4 c0 = tex2D(ReShade::BackBuffer, uv);

  // float d=hexd(uv*reso,.072,.16);

  float sz = exp2(-2.0 - PatternScale);

  float hf_sz = exp2(lerp(-4.0, 4.0, pow(HalftoneAmt / 100.0, 0.5)));

  float4 d4 = float4(hexd(uv * reso, sz * exp2(-0.01), .06),
                     hexd(uv * reso, sz * exp2(-0.02), .093),
                     hexd(uv * reso, sz * exp2(-0.03), .013),
                     hexd(uv * reso, sz * exp2(-0.04), .34));

  float4 cmyk = rgb2cmyki(c0.rgb);
  c.rgb = cmyki2rgb(1.0 - step(cmyk, d4 / .82));
  float dx = 50.0 * hf_sz / reso.x;
  dx = sqrt(dx);
  c.rgb = cmyki2rgb(1.0 - smoothstep(dx, -dx, cmyk - d4 / .82));
  c.a = 1;
  return c;
}

float4 PSmono(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;

  float2 e = float2(.5, 0.0);
  float2 reso = BUFFER_SCREEN_SIZE;

  float4 c0 = tex2D(ReShade::BackBuffer, uv);

  float d = hexd(uv * reso, PatternScale, 0.035);

  float v = max(c0.x, max(c0.y, c0.z));
  v = lerp(v, dot(c0.rgb, float3(.333, .59, .11)), .15);
  c.rgb = float3(1, 1, 1) * (1.0 - step(v, d / .82));
  c.a = 1;
  return c;
}

technique Halftone {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace