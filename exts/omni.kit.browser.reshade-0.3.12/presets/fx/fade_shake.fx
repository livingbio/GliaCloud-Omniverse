#include "ReShade.fxh"

namespace FadeShakeFX {

uniform float Speed = 3.0;
uniform float Amplitude = 0.50;
uniform float ExposureWobble = 1.0;
uniform int NoiseOctaves = 6;
uniform float OctaveTilt = 0.4;
uniform int MotionBlurSamples = 20;
uniform float MotionBlurAmount = 1.0;

uniform float Zoom = .210;

uniform float timer < source = "timer";
> ;

uniform int DebugBarSize = -1;
uniform float2 pingpong < source = "pingpong";
min = 0;
max = 360;
step = 0.05;
smoothing = 0.0;
> ;

uniform float FadeTime = 2;

uniform int FadeType < ui_type = "list";
ui_label = "Fade type";
ui_items = "Demo mode; Slider mode";
> = 0;

uniform float Fade < ui_type = "slider";
ui_label = "Fade";
ui_min = 0;
ui_max = 100;
ui_step = 1.0;
> = 0;

float fade() {
  float f2 = (pingpong.x * 10 / FadeTime);
  float f = saturate(f2 * 2 - 1) * 0;
  switch (FadeType) {
    case 0:
      f = saturate((abs(frac(f2) * 2 - 1) - .5) * 1.25 + .5);
      break;
    case 1:
      f = Fade * 0.01;
      break;
  }
  return f;
}

float FADER_LERP(float a, float b, float offset) {
  float f = fade();
  // return exp(lerp(log(a),log(b),f));
  return lerp(a, b, f);
}
float FADER_EXPLERP(float a, float b, float offset) {
  float f = fade();
  // float f=1-abs(frac(x)*2-1);
  // f=saturate((f-.5)*2+.5);
  return exp(lerp(log(a), log(b), f));
  // return lerp(a,b,f);
}
float FADER_SMOOTHLERP(float a, float b, float offset) {
  float f = fade();
  f = smoothstep(0, 1, f);
  return lerp(a, b, f);
}
// #define Speed (3.01)
// #define Amplitude (FADER_LERP(.0,3.1,ot))

float bayer2(float2 v) {
  v = floor(v);
  return frac(v.y * v.y * .75 + v.x * .5);
}
float bayer4(float2 v) { return bayer2(.5 * v) * .25 + bayer2(v); }
float bayer8(float2 v) { return bayer4(.5 * v) * .25 + bayer2(v); }
float bayer16(float2 v) { return bayer8(.5 * v) * .25 + bayer2(v); }
float bayer32(float2 v) { return bayer16(.5 * v) * .25 + bayer2(v); }

float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}

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
  int2 ip = int2(vpos.xy - .25);
  float dth = bayer8(ip.xy % 8);
  // float2 offset=sin(tt*sqrt(float2(3,5)));
  float2 asp = float2(reso.x / float(reso.y), 1);
  c.rgb = 0;
  for (int j = 0; j < MotionBlurSamples; j++) {
    float ft = float(j) / max(1.0, float(MotionBlurSamples - 1));
    float tt =
        (timer * exp2(-11.0) + (ft - .5) * exp2(-5) * MotionBlurAmount) * Speed;
    float ot = (ft - 0.5 + (dth - .5) * .3) * .01;
    float f = FADER_LERP(0, 1, ot);
    // f=smoothstep(0,1,f);
    tt += sin(tt * 1.1) * .8 * exp2(-2 * (1 + sin(tt * .07)));
    float2 offset = 0;
    for (int i = 0; i < NoiseOctaves; i++) {
      float2 fq = exp2(float(i) * float2(1.02, 1.015) * 0.77 + float2(.3, .5));
      offset += sin(tt * fq) * exp2(float(i) * OctaveTilt) / fq;
    }
    offset = tanh(offset) * .5;
    offset = lerp(offset, normalize(offset.yx) * float2(1, -1) * .5 * 1,
                  pow(saturate(f * 2 - 1), 12));
    float maxoffset = Amplitude * 230 * f * exp((f * f * f - 1) * 3);
    float maxoffset2 = f * FADER_EXPLERP(.001, 33.1, ot);
    float4 tc = tex2Dlod(
        ReShade::BackBuffer,
        float4(r2d((uv - .5) * asp,
                   tanh(offset.x * 3) * -.046 * pow(saturate(f * 3 - 2), 8)) /
                       asp * (reso.x - maxoffset * Zoom * f * f) / reso.x +
                   (maxoffset + maxoffset2) * offset / reso.x + .5,
               0, 0));
    tc.rgb = Untonemap(tc.rgb);
    tc.rgb *= exp2(f * ExposureWobble * 0.5 * sin(offset.x * 8));
    // tc.rgb*=hsv2rgb(float3(ft,.9,1));
    c.rgb += tc.rgb / float(MotionBlurSamples);
  }
  float f = FADER_LERP(0, 1, 0);
  c.rgb *= smoothstep(0.0, 1, 1 - pow(f, 8));
  c.rgb = Tonemap(c.rgb);
  if (ip.y < DebugBarSize) c.rgb = f > uv.x ? float3(1, 0, 0) : float3(0, 1, 0);
  // c.a=1;
  return c;
}

technique FadeShake {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace