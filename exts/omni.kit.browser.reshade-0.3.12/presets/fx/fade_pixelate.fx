#include "ReShade.fxh"

namespace FadePixelateFX {

uniform float3 GridColor = float3(0.0, 0.0, 0.0);
// uniform float Speed = 1.0;

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

float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}

float2 noise2d(int2 xy, int seed) {
  int3 c = int3(xy + (xy >= 0), seed);
  int r = int(0xf6a47f78 * c.x * c.x + c.y) *
          int(0x82f88c81 * c.y * c.y + c.x) *
          int(0x964cb8a1 * c.z * c.z + c.y) * int(0xafc35eb8 * c.y * c.x + c.z);
  int2 r2 = int2(0xebfd9f9a, 0x93b7c155) * r;
  return (r2 % 358934592) * .5 / 358934592. + 0.5;
}

float4 readtex(sampler s, int2 xy, int2 reso) {
  // if(any(xy<0)||any(xy>int2(reso)-1))return 0;
  xy = clamp(xy, 0, reso - 1);
  return tex2D(s, (float2(xy) + .5) / float2(reso));
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
float bayer2(float2 v) {
  v = floor(v);
  return frac(v.y * v.y * .75 + v.x * .5);
}
float bayer4(float2 v) { return bayer2(.5 * v) * .25 + bayer2(v); }
float bayer8(float2 v) { return bayer4(.5 * v) * .25 + bayer2(v); }
float bayer16(float2 v) { return bayer8(.5 * v) * .25 + bayer2(v); }
float bayer32(float2 v) { return bayer16(.5 * v) * .25 + bayer2(v); }

float4 readtex_level(float2 uv, int lod) {
  int2 reso = BUFFER_SCREEN_SIZE;
  int2 ip = uv * reso;
  int2 pxsize = pow(2, floor(lod));
  // ip-=reso/2;
  int2 qp = (ip / pxsize) * pxsize;
  float2 n1 = noise2d(ip / pxsize + int2(pxsize.x * 7, 3), floor(lod));
  // n1.xy=r2d(n1.xy-.5,timer*exp2(-7-floor(lod)))+.5;
  // qp+=(reso/pxsize)*pxsize/2;
  qp += pxsize / 2;
  qp += (n1.xy - .5) * pxsize * 5;
  float4 c1 = readtex(ReShade::BackBuffer, qp, BUFFER_SCREEN_SIZE);
  // c1.w=bayer8((ip/(pxsize))%8);
  // c1.w=n1.x;

  c1 += GridColor * (float)(
        any((ip % pxsize == 0 || ip % pxsize == (pxsize - 1)) && pxsize >= 2) *
        2 * exp2(-.95 * (9 - floor(lod))) * (1 - c1));
  return c1;
}
float4 readtex_lod(float2 uv, float lod) {
  float4 c1 = readtex_level(uv, floor(lod) + 0);
  float4 c2 = readtex_level(uv, floor(lod) + 1);

  float4 ret = lerp(float4(Untonemap(c1.rgb), c1.w),
                    float4(Untonemap(c2.rgb), c2.w), frac(lod));
  return float4(Tonemap(ret.rgb), ret.w);
  // return lerp(c1,c2,frac(lod));
}
float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  int2 ip = int2(vpos.xy - .25);
  float4 c = tex2D(ReShade::BackBuffer, uv);
  int2 reso = BUFFER_SCREEN_SIZE;
  int2 pxsize = 13;
  int2 qp = (ip / pxsize) * pxsize;
  c = readtex(ReShade::BackBuffer, qp, BUFFER_SCREEN_SIZE);

  float f = FADER_LERP(0, 1, 0);
  f = pow(f, 1);
  c = readtex_lod(uv, f * (log2(max(reso.x, reso.y)) + 3) - 2 +
                          length((uv - .5) * 18 / reso));
  // c=readtex_lod(uv,3);
  c.rgb = Untonemap(c.rgb);

  // c.rgb=pow(c.rgb*2,FADER_EXPLERP(1,4))/2;
  c.rgb = normalize(c.rgb) * pow(length(c.rgb) * .5, exp2(f * f * 2)) / .5;
  c.rgb *= exp2(-.01 * (exp2(f * 6 + f * f * 11) - 1));
  // c.rgb=normalize(c.rgb)*pow(length(c.rgb)*.1,FADER_EXPLERP(1,4))/.1;
  c.rgb = Tonemap(c.rgb);

  c.a = 1;
  return c;
}

technique FadePixelate {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace