#include "ReShade.fxh"
namespace CamerashakeFX {

uniform float Speed < ui_type = "drag";
ui_min = 0.0;
ui_max = 24.0;
ui_step = 0.1;
ui_label = "Speed";
ui_tooltip = "Speed of movement";
> = 1.0;

uniform float Amplitude < ui_type = "drag";
ui_min = 0.0;
ui_max = 24.0;
ui_step = 0.1;
ui_label = "Amplitude";
ui_tooltip = "Amplitude of movement";
> = 0.5;

uniform float ExposureWobble < ui_type = "drag";
ui_min = 0.0;
ui_max = 24.0;
ui_step = 0.1;
ui_label = "Random exposure";
ui_tooltip = "Additional random exposure over time";
> = 0.5;

uniform int NoiseOctaves <
    // ui_type = "slider";
    ui_type = "drag";
ui_min = 1;
ui_max = 7;
ui_label = "Noise octaves";
ui_tooltip = "Amount of noise octaves. Affects the character of noise signal";
> = 5;

uniform int MotionBlurSamples < ui_type = "drag";
ui_min = 1;
ui_max = 32;
ui_label = "Motion blur samples";
ui_tooltip = "Motion blur samples";
> = 8;

uniform float MotionBlurAmount < ui_type = "drag";
ui_min = 0.0;
ui_max = 12.0;
ui_label = "Motion blur amount";
ui_tooltip = "Motion blur amount";
> = 1.0;

uniform float timer < source = "timer";
> ;

float3 Untonemap(float3 c) { return c / (1.0 + exp2(-6) - saturate(c)); }
float3 Tonemap(float3 c) { return c / (1.0 + c); }
float3 hsv2rgb(float3 hsv) {
  return lerp(1,
              saturate(abs(frac((hsv.x - float3(0, 2, 4) / 6)) - .5) * 6 - 1),
              hsv.y) *
         hsv.z;
}
float3 rgb2hsv(float3 c) {
  float v = max(c.x, max(c.y, c.z));
  float m = min(c.x, min(c.y, c.z));
  float r = v - m;
  float h = (r != 0) ? frac(((v == c.x) ? ((c.y - c.z) / r)
                                        : (v == c.y) ? (2 + (c.z - c.x) / r)
                                                     : (4 + (c.x - c.y) / r)) /
                            6)
                     : 0;
  float s = (v != 0) ? (1 - m / v) : 0;
  return float3(h, s, v);
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = tex2D(ReShade::BackBuffer, uv);
  float2 reso = BUFFER_SCREEN_SIZE;

  // float2 offset=sin(tt*sqrt(float2(3,5)));

  c.rgb = 0;
  for (int j = 0; j < MotionBlurSamples; j++) {
    float ft = float(j) / max(1.0, float(MotionBlurSamples - 1));
    float tt =
        (timer * exp2(-11.0) + (ft - .5) * exp2(-5) * MotionBlurAmount) * Speed;
    tt += sin(tt * 1.1) * .8 * exp2(-2 * (1 + sin(tt * .07)));
    float2 offset = 0;
    for (int i = 0; i < NoiseOctaves; i++) {
      float2 fq = exp2(float(i) * float2(1.02, 1.05) * 0.7 + float2(.3, .5));
      offset += sin(tt * fq) / fq;
    }
    offset = tanh(offset) * .5;
    float maxoffset = 30 * Amplitude;
    float4 tc = tex2Dlod(ReShade::BackBuffer,
                         float4((uv - .5) * (reso.x - maxoffset) / reso.x +
                                    maxoffset * offset / reso.x + .5,
                                0, 0));
    tc.rgb = Untonemap(tc.rgb);
    tc.rgb *= exp2(ExposureWobble * 0.5 * sin(offset.x * 8));
    // tc.rgb*=hsv2rgb(float3(ft,.9,1));
    c.rgb += tc.rgb / float(MotionBlurSamples);
  }
  c.rgb = Tonemap(c.rgb);

  // c.a=1;
  return c;
}

technique CameraShake {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace