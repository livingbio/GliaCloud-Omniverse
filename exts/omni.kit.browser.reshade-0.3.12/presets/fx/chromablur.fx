#include "ReShade.fxh"

namespace ChromaBlurFX {

uniform float Distortion < ui_type = "drag";
ui_min = 0.0;
ui_max = 50.0;
ui_step = 1.0;
ui_label = "Distortion Amount";
ui_tooltip = "Distortion Amount";
> = 5.0;

float2 remap(float2 t, float2 a, float2 b) {
  return clamp((t - a) / (b - a), 0.0, 1.0);
}

float2 distort(float2 uv, float t, float2 d) {
  float2 dist = lerp(d * 0.5, d, t);
  float2 cc = uv - 0.5;
  return uv + 6.0 * (uv - 0.5) * 2.0 * dist;
}

float hash12(float2 p) {
  float3 p3 = frac((p.xyx) * .1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return frac((p3.x + p3.y) * p3.z);
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float2 in_distort = Distortion / ReShade::ScreenSize.xy;

  float2 oversize = distort((1.0), 1.0, in_distort);
  uv = remap(uv, 1.0 - oversize, oversize);

  const int ITERS = 5;
  const float stepsize = 1.0 / (float(ITERS) - 1.0);

  float rnd = hash12(vpos.xy);
  float t = stepsize * rnd;

  float3 sumcol = (0.0);
  float3 sumw = (0.0);
  for (int i = 0; i < ITERS; ++i) {
    float3 w =
        clamp(float3(-3.0 * t + 1.5, 1.0 - abs(3.0 * t - 1.5), 3.0 * t - 1.5),
              0.0, 1.0);

    sumw += w;
    float2 uvd = distort(uv, t, in_distort);  // TODO: move out of loop
    sumcol += w * tex2D(ReShade::BackBuffer, uvd).rgb;
    t += stepsize;
  }
  sumcol.rgb /= sumw;

  float3 outcol = sumcol.rgb;
  outcol += rnd / 255.0;

  return float4(outcol, 1.0);
}

technique ChromaBlur {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}

}  // namespace ChromaBlurFX