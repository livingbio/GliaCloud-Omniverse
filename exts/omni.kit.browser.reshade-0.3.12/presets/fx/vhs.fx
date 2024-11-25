#include "ReShade.fxh"

namespace VhsFX {

// uniform float ANIM_SPEED = 0.14f; // Animation speed
uniform float POWER = 0.01;

uniform float2 uFXRes = float2(320, 240);

uniform float uLFWaveFreq = .20;
uniform float uLFWaveAmt = 0.05;
uniform float uLFWaveSpeed = 1.0;

uniform float uHFWaveFreq = 10.0;
uniform float uHFWaveAmt = .006010111;
uniform float uHFWaveSpeed = 10.0;

uniform float uTCStripeCount = 33;
uniform float uTCStripeScrollSpeed = 1.;

uniform float uTapeSpeed = 1.0;
uniform float uTapeNoisePow = 71;
uniform float uTapeDisplaceAmt = 2;
uniform float uBottomSwitchDisplace = .001;
uniform float uBottomSwitchHeight = 0.01;
uniform float uHueRotateAmt = 2.2;

uniform float uStripeNoiseThreshold = 0.6;

uniform float uHeadFuzz = 3.1;

uniform float uColorNoiseScale = 0.255;
uniform float uColorNoiseAmt = 0.03;

uniform float timer < source = "timer";
> ;

// keep these define

#ifndef __RESHADE__
// for vvvv (comment out before reshade): ->
#define tex2D(a, b) tex0.Sample(s0, b)
#define ReShade ::BackBuffer tex0
float2 R : TARGETSIZE;
#define tex2D(a, b) tex0.Sample(s0, b)
#define BUFFER_WIDTH R.x
#define BUFFER_HEIGHT Ry
Texture2D tex0 : PREVIOUS;

SamplerState s0 {
  Filter = MIN_MAG_MIP_LINEAR;
  AddressU = MIRROR;
  AddressV = MIRROR;
};
uniform float timer;  //< source = "timer"; >;

//<-for vvvv (comment out before reshade):
#else
uniform float timer_reshade < source = "timer";
> ;
#define timer float(timer_reshade) * 0.01f * 0.1f

#endif

#define modf(x, y) (x - y * floor(x / y))

#define V float2(0., 1.)
#define PI 3.14159265

#define SAMPLES 15

float random2(float2 n) {
  return frac(sin(dot(n.xy, float2(12.9898, 78.233))) * 43758.5453);
}

float2 mod(float2 x, float2 y) { return (x - y * floor(x / y)); }

float mod(float x, float y) { return (x - y * floor(x / y)); }

float2x2 rotate2D(float t) { return float2x2(cos(t), -sin(t), sin(t), cos(t)); }

///////////////////////////////
// IQ's noises

float3 hash_sine33(float3 p)  // replace this by something better
{
  p = float3(dot(p, float3(127.1, 311.7, 74.7)),
             dot(p, float3(269.5, 183.3, 246.1)),
             dot(p, float3(113.5, 271.9, 124.6)));

  return -1.0 + 2.0 * frac(sin(p) * 43758.5453123);
}

float2 hash(float2 p)  // replace this by something better
{
  p = float2(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)));
  return -1.0 + 2.0 * frac(sin(p) * 43758.5453123);
}

float3 hash(float3 p) {
  return hash_sine33(p).xyz;
  // return hash_without_sine33(p).x;
}

float noise(float3 p) { return 1.0; }

float noise(float2 p) {
  const float K1 = 0.366025404;  // (sqrt(3)-1)/2;
  const float K2 = 0.211324865;  // (3-sqrt(3))/6;

  float2 i = floor(p + (p.x + p.y) * K1);
  float2 a = p - i + (i.x + i.y) * K2;
  float m = step(a.y, a.x);
  float2 o = float2(m, 1.0 - m);
  float2 b = a - o + K2;
  float2 c = a - 1.0 + 2.0 * K2;
  float3 h = max(0.5 - float3(dot(a, a), dot(b, b), dot(c, c)), 0.0);
  float3 n = h * h * h * h * float3(dot(a, hash(i + 0.0)), dot(b, hash(i + o)),
                                    dot(c, hash(i + 1.0)));
  return dot(n, 70.0);
}

float fnoise(float2 p) {
  float2 f = 0.0;
  const float2x2 m = float2x2(1.6, -1.2, 1.2, 1.6);

  float2 q = 1.0 * p;
  //    f  = 0.5000*noise( q ); q = mul(m,q)*2.01;
  //    f += 0.2500*noise( q ); q = mul(m,q)*2.02;
  //    f += 0.1250*noise( q ); q = mul(m,q)*2.03;
  //    f += 0.0625*noise( q ); q = mul(m,q)*2.01;
  f = 0.5000 * noise(q);
  q = mul(m, q);
  f += 0.2500 * noise(q);
  q = mul(m, q);
  f += 0.1250 * noise(q);
  q = mul(m, q);
  f += 0.0625 * noise(q);
  q = mul(m, q);
  // f = 0.5 + 0.5*f;
  return f.x;
}

// rgb to ntsc
float3 rgb2yiq(float3 rgb) {
  return float3((0.299 * rgb.x + 0.596 * rgb.y + 0.211 * rgb.z),
                (0.587 * rgb.x - 0.274 * rgb.y - 0.523 * rgb.z),
                (0.114 * rgb.x - 0.322 * rgb.y + 0.311 * rgb.z));
};
// ntsc to rgb
float3 yiq2rgb(float3 yiq) {
  return float3((1.0 * yiq.x + 1.0 * yiq.y + 1.0 * yiq.z),
                (0.956 * yiq.x - 0.272 * yiq.y - 1.106 * yiq.z),
                (0.621 * yiq.x - 0.647 * yiq.y + 1.705 * yiq.z)

                    );
};

// rgb to pal
float3 rgb2yuv(float3 rgb) {
  return float3(rgb.r * 0.299 + rgb.g * 0.587 + rgb.b * 0.114,
                rgb.r * -0.169 + rgb.g * -0.331 + rgb.b * 0.5 + 0.5,
                rgb.r * 0.5 + rgb.g * -0.419 + rgb.b * -0.081 + 0.5);
};
// pal to rgb
float3 yuv2rgb(float3 yuv) {
  yuv.y = yuv.y - 0.5;
  yuv.z -= 0.5;
  return float3(yuv.x * 1.0 + yuv.y * 0.0 + yuv.z * 1.4,
                yuv.x * 1.0 + yuv.y * -0.343 + yuv.z * -0.711,
                yuv.x * 1.0 + yuv.y * 1.765 + yuv.z * 0.0);
}

float3 rgb2ydbdr(float3 rgb) {
  return float3(0.299 * rgb.x + 0.587 * rgb.y + 0.114 * rgb.z,
                -0.450 * rgb.x - 0.883 * rgb.y + 1.333 * rgb.z,
                -1.333 * rgb.x + 1.116 * rgb.y + 0.217 * rgb.z);
}

float3 ydbdr2rgb(float3 ydbdr) {
  return float3(
      ydbdr.x + 0.000092303716148 * ydbdr.y - 0.525912630661865 * ydbdr.z,
      ydbdr.x - 0.129132898890509 * ydbdr.y + 0.525912630661865 * ydbdr.z,
      ydbdr.x + 0.664679059978955 * ydbdr.y - 0.000079202543533 * ydbdr.z);
}

///////////////////////////////////
float ramp(float y, float start, float end) {
  float inside = step(start, y) - step(end, y);
  float fact = (y - start) / (end - start) * inside;
  return (1. - fact) * inside;
}

float stripes(float2 uv, float time) {
  float noise = random2(uv * float2(0.5, 1.) + float2(1., 3.));
  return ramp(modf(uv.y * 4. + time / 2. + sin(time + sin(time * 0.6)), 1.),
              0.5, 0.6) *
         noise;
  // return 0.1;
}

////////////////////////////////////

float wiggle(float signal, float freq, float amt, float speed) {
  float time = timer;
  float result = (noise(float2(signal * freq, time * speed))) * amt;
  return result;
}

float3 texHead(float2 uv, float absFuzz, float hueRot) {
  int ITERS = 15;
  float3 yiq = 0;
  for (int i = 0; i < ITERS; i++) {
    yiq += (rgb2yiq(tex2D(ReShade::BackBuffer,
                          uv - float2(float(i), 0.0) / uFXRes / absFuzz)
                        .xyz) *
            float2(float(ITERS - 1 - i), float(i)).xxy / float(ITERS - 1));
  }
  yiq /= 0.7 * float(ITERS);
  yiq.yz = mul(rotate2D(hueRot), yiq.yz);

  return yiq2rgb(yiq);
}

float4 calcImage(float2 uv) {
  float time = timer;

  float2 uvDist = uv;
  float3 color = float3(1.0, 0.0, 0.0);

  // tape wave (sin distort)
  uvDist.x += wiggle(uvDist.y, uLFWaveFreq, uLFWaveAmt, uLFWaveSpeed);
  uvDist.x += wiggle(uvDist.y, uHFWaveFreq, uHFWaveAmt, uHFWaveSpeed);

  // tape crease noise
  float tapeCreasePhase =
      smoothstep(0.9, 0.96, sin(uvDist.y * uTCStripeCount -
                                (time + 1. * noise(time * float2(0.67, 0.59))) *
                                    PI * (uTCStripeScrollSpeed)));
  float tapeCreaseNoise =
      smoothstep(0.0, .990, noise(float2(uvDist.y * 4.77, time)));
  float tapeCrease = tapeCreasePhase * tapeCreaseNoise;

  uvDist.x = uvDist.x - tapeCrease * uTapeDisplaceAmt / uFXRes.x;

  // Head switching noise / bottom shift
  // http://www.avartifactatlas.com/artifacts/head_switching_noise.html
  float headSwitchPhase = smoothstep(uBottomSwitchHeight, 0.0, 1. - uvDist.y);
  // uvDist.y += headSwitchPhase * 0.2;
  // uvDist.x += 0.1 * headSwitchPhase + (0.1 * (noise(float2(uv.y, time *
  // 0.1))));
  // uvDist.x -= 0.03;

  // multisample in yiq space:
  color = texHead(uvDist, uHeadFuzz,
                  uHueRotateAmt * (tapeCreasePhase * 0.02 +
                                   headSwitchPhase * uBottomSwitchDisplace));
  // color = texHead( uv,uHeadFuzz, uHueRotateAmt*(tapeCreasePhase * 0.02 +
  // headSwitchPhase * uBottomSwitchDisplace) );

  // Stripes over crease noise:

  if (uStripeNoiseThreshold < (tapeCreaseNoise * 0.9 + 0.1 * tapeCreasePhase)) {
    // return abs(noise( float2( uFXRes.y*uvDist.y, time*10 ))).xxxx;
    float2 uvNoise =
        (uvDist +
         float2(1, 0) * (noise(float2(uFXRes.y * uvDist.y, time * 10)))) *
        float2(5, 1);

    float noiseBase = (noise(uvNoise));

    float noiseShifted = (noise(uvNoise + float2(10.1, 0) / uFXRes.y));

    if (noiseShifted < noiseBase) {
      color = lerp(color, uTapeNoisePow, pow(abs(noiseBase), 10.0));
    }
  }

  // Noise in yiq signal
  color = rgb2yiq(color);
  float time_fps = round(time * 30.) / 30.;

  // color.g = color.g*0.9 + 0.1 * (fnoise(uv * uFXRes * 0.1 + time * 120));
  color.r = color.r * (1.0 - uColorNoiseAmt) +
            uColorNoiseAmt * noise(uColorNoiseScale * uv * uFXRes +
                                   100. * noise(float2(time_fps * 11, 1.0)));
  color.g = color.g * (1.0 - uColorNoiseAmt) +
            uColorNoiseAmt * fnoise(uColorNoiseScale * uv * uFXRes +
                                    100. * noise(float2(time_fps * 12., 1.0)));
  color.b = color.b * (1.0 - uColorNoiseAmt) +
            uColorNoiseAmt * fnoise(uColorNoiseScale * uv * uFXRes +
                                    100 * noise(float2(time_fps * 13., 1.0)));

  color = float3(0.15, -0.15, 0.0) + float3(0.85, 1.15, 1.5) * color;

  color = yiq2rgb(color);

  return float4(color, 1.0);
  // return 1;
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 color = calcImage(uv);
  color.a = 1.0;
  return color;
}

technique Vhs {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}