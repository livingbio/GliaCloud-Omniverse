#include "ReShade.fxh"
namespace GlowFX 
{
uniform float3 GlowTint < ui_type = "color";
ui_label = "Glow Tint";
> = float3(1.0, 1.0, 1.0);

uniform float3 FlareTint < ui_type = "color";
ui_label = "Flare Tint";
> = float3(1.0, 1.0, 1.0);

uniform float GlowExposure < ui_type = "drag";
> = 0.0;
uniform float GlowIntensity < ui_type = "drag";
> = .10;

uniform float GlowShape < ui_type = "drag";
> = 3.0;
uniform float FlareIntensity < ui_type = "drag";
> = 1.0;
uniform int FlareCount < ui_type = "drag";
> = 14;
uniform float BoostHighlights < ui_type = "drag";
> = .050;
uniform float BlendSource < ui_type = "drag";
> = 1.0;
// uniform float BlendPass0 < ui_type="drag";> = 1.0;
uniform float DirtFactor < ui_type = "drag";
> = .5;
uniform float DirtScale < ui_type = "drag";
> = 0.80;
uniform int RandomSeed < ui_type = "drag";
> = 6;

uniform float RandomizeSpeed < ui_type = "drag";
> = .0;

uniform int RandomSeedDirt < ui_type = "drag";
> = 0;

uniform float timer < source = "timer";
> ;
#define BICUBIC true

float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}

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
  float h = (r != 0) ? frac(((v == c.x)   ? ((c.y - c.z) / r)
                             : (v == c.y) ? (2 + (c.z - c.x) / r)
                                          : (4 + (c.x - c.y) / r)) /
                            6)
                     : 0;
  float s = (v != 0) ? (1 - m / v) : 0;
  return float3(h, s, v);
}

float3 Untonemap(float3 c) { return c / (1.0 + exp2(-6) - saturate(c)); }
float3 Tonemap(float3 c) { return c / (1.0 + c); }

float4 tex_sample(sampler tex, float2 uv, float2 texsize, bool bicubic) {
  if (!bicubic)
    return tex2D(tex, uv);
  float2 p = uv * texsize + 0.5;
  float2 ts = 1. / texsize;
  int2 ip = floor(p);
  float2 x = frac(p);
  float2 w0 = (x * (x * (-x + 3) - 3) + 1) / 6;
  float2 w1 = (x * x * (3 * x - 6) + 4) / 6;
  float2 w2 = (x * (x * (-3 * x + 3) + 3) + 1) / 6;
  float2 w3 = (x * x * x) / 6;
  float2 g0 = w0 + w1;
  float2 g1 = w2 + w3;
  float2 h0 = w1 / (w0 + w1) - 1;
  float2 h1 = w3 / (w2 + w3) + 1;
  float2 p0 = (ip + float2(h0.x, h0.y) - 0.5) * ts;
  float2 p1 = (ip + float2(h1.x, h0.y) - 0.5) * ts;
  float2 p2 = (ip + float2(h0.x, h1.y) - 0.5) * ts;
  float2 p3 = (ip + float2(h1.x, h1.y) - 0.5) * ts;
  float4 c0 = tex2D(tex, p0);
  float4 c1 = tex2D(tex, p1);
  float4 c2 = tex2D(tex, p2);
  float4 c3 = tex2D(tex, p3);
  return g0.y * (g0.x * c0 + g1.x * c1) + g1.y * (g0.x * c2 + g1.x * c3);
}

#define BUFFERHEIGHT0 BUFFER_HEIGHT
#define BUFFERWIDTH0 BUFFER_WIDTH
#define BUFFERHEIGHT1 BUFFER_HEIGHT / 2
#define BUFFERWIDTH1 BUFFER_WIDTH / 2
#define BUFFERHEIGHT2 BUFFER_HEIGHT / 4
#define BUFFERWIDTH2 BUFFER_WIDTH / 4
#define BUFFERHEIGHT3 BUFFER_HEIGHT / 8
#define BUFFERWIDTH3 BUFFER_WIDTH / 8
#define BUFFERHEIGHT4 BUFFER_HEIGHT / 16
#define BUFFERWIDTH4 BUFFER_WIDTH / 16
#define BUFFERHEIGHT5 BUFFER_HEIGHT / 32
#define BUFFERWIDTH5 BUFFER_WIDTH / 32
#define BUFFERHEIGHT6 BUFFER_HEIGHT / 64
#define BUFFERWIDTH6 BUFFER_WIDTH / 64
#define BUFFERHEIGHT7 BUFFER_HEIGHT / 128
#define BUFFERWIDTH7 BUFFER_WIDTH / 128

texture2D TexMip0 {
  Width = BUFFERWIDTH0;
  Height = BUFFERHEIGHT0;
  Format = RGBA16F;
};
sampler SamplerMip0 { Texture = TexMip0; };
texture2D TexMip1 {
  Width = BUFFERWIDTH1;
  Height = BUFFERHEIGHT1;
  Format = RGBA16F;
};
sampler SamplerMip1 { Texture = TexMip1; };
texture2D TexMip2 {
  Width = BUFFERWIDTH2;
  Height = BUFFERHEIGHT2;
  Format = RGBA16F;
};
sampler SamplerMip2 { Texture = TexMip2; };
texture2D TexMip3 {
  Width = BUFFERWIDTH3;
  Height = BUFFERHEIGHT3;
  Format = RGBA16F;
};
sampler SamplerMip3 { Texture = TexMip3; };
texture2D TexMip4 {
  Width = BUFFERWIDTH4;
  Height = BUFFERHEIGHT4;
  Format = RGBA16F;
};
sampler SamplerMip4 { Texture = TexMip4; };
texture2D TexMip5 {
  Width = BUFFERWIDTH5;
  Height = BUFFERHEIGHT5;
  Format = RGBA16F;
};
sampler SamplerMip5 { Texture = TexMip5; };
texture2D TexMip6 {
  Width = BUFFERWIDTH6;
  Height = BUFFERHEIGHT6;
  Format = RGBA16F;
};
sampler SamplerMip6 { Texture = TexMip6; };
texture2D TexMip7 {
  Width = BUFFERWIDTH7;
  Height = BUFFERHEIGHT7;
  Format = RGBA16F;
};
sampler SamplerMip7 { Texture = TexMip7; };

texture2D TexNoise {
  Width = 512;
  Height = 512;
};

sampler SamplerNoise {
  Texture = TexNoise;
  AddressU = MIRROR;
  AddressV = MIRROR;
};

float4 PS_Prepass(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c0 = tex2D(ReShade::BackBuffer, uv);
  float4 c = 0;
  c.rgb = Untonemap(c0.rgb);
  c.rgb *= 1 + pow(length(c.rgb) * BoostHighlights, 2);
  c.a = 1;
  return c;
}
float3 blur(sampler tex, float2 uv, float2 texsize, int rad) {
  float4 c = 0;
  // int rad=3;
  float2 sz = 1. / float2(floor(texsize));
  // sz*=1+rad*0.125;
  for (int i = -rad; i <= rad; i++) {
    for (int j = -rad; j <= rad; j++) {
      float4 nc = tex2D(tex, uv + float2(i, j) * sz);
      float a = 0.1;
      float w = exp2(-a * pow(length(float2(i, j)) * 2 / float(1), 1));
      w = 1;
      w *= exp2(-a * pow(abs(float(i)) * 2 / float(1), 2));
      w *= exp2(-a * pow(abs(float(j)) * 2 / float(1), 2));

      c += float4(nc.rgb, 1) * w;
    }
  }
  c.rgb /= c.a;
  return c.rgb;
}
float4 PS_Blur1(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  return float4(
      blur(SamplerMip0, uv, floor(float2(BUFFERWIDTH1, BUFFERHEIGHT1)), 2).rgb,
      1);
}
float4 PS_Blur2(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  return float4(
      blur(SamplerMip1, uv, floor(float2(BUFFERWIDTH2, BUFFERHEIGHT2)), 2).rgb,
      1);
}
float4 PS_Blur3(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  return float4(
      blur(SamplerMip2, uv, floor(float2(BUFFERWIDTH3, BUFFERHEIGHT3)), 3).rgb,
      1);
}
float4 PS_Blur4(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  return float4(
      blur(SamplerMip3, uv, floor(float2(BUFFERWIDTH4, BUFFERHEIGHT4)), 3).rgb,
      1);
}
float4 PS_Blur5(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  return float4(
      blur(SamplerMip4, uv, floor(float2(BUFFERWIDTH5, BUFFERHEIGHT5)), 3).rgb,
      1);
}
float4 PS_Blur6(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  return float4(
      blur(SamplerMip5, uv, floor(float2(BUFFERWIDTH6, BUFFERHEIGHT6)), 4).rgb,
      1);
}
float4 PS_Blur7(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  return float4(
      blur(SamplerMip6, uv, floor(float2(BUFFERWIDTH7, BUFFERHEIGHT7)), 4).rgb,
      1);
}

float2 noise2d(int2 xy, int seed) {
  int3 c = int3(xy + (xy >= 0), seed);
  int r = int(0xf6a47f78 * c.x * c.x + c.y) *
          int(0x82f88c81 * c.y * c.y + c.x) *
          int(0x964cb8a1 * c.z * c.z + c.y) * int(0xafc35eb8 * c.y * c.x + c.z);
  int2 r2 = int2(0xebfd9f9a, 0x93b7c155) * r;
  return (r2 % 358934592) * .5 / 358934592. + 0.5;
}

#define reso float2(BUFFER_SCREEN_SIZE)

float4 SampleLevel(float2 uv, int lod, bool bicubic) {
  int x = clamp(lod, 0, 7);
  float4 c = 0;
  switch (x) {
    // switch(int(uv.x*6)){
  case 0: {
    c = tex_sample(SamplerMip0, uv, int2(BUFFERWIDTH0, BUFFERHEIGHT0), bicubic);
    break;
  }
  case 1: {
    c = tex_sample(SamplerMip1, uv, int2(BUFFERWIDTH1, BUFFERHEIGHT1), bicubic);
    break;
  }
  case 2: {
    c = tex_sample(SamplerMip2, uv, int2(BUFFERWIDTH2, BUFFERHEIGHT2), bicubic);
    break;
  }
  case 3: {
    c = tex_sample(SamplerMip3, uv, int2(BUFFERWIDTH3, BUFFERHEIGHT3), bicubic);
    break;
  }
  case 4: {
    c = tex_sample(SamplerMip4, uv, int2(BUFFERWIDTH4, BUFFERHEIGHT4), bicubic);
    break;
  }
  case 5: {
    c = tex_sample(SamplerMip5, uv, int2(BUFFERWIDTH5, BUFFERHEIGHT5), bicubic);
    break;
  }
  case 6: {
    c = tex_sample(SamplerMip6, uv, int2(BUFFERWIDTH6, BUFFERHEIGHT6), bicubic);
    break;
  }
  case 7: {
    c = tex_sample(SamplerMip7, uv, int2(BUFFERWIDTH7, BUFFERHEIGHT7), bicubic);
    break;
  }
  default: {
    // c.rgb=c0.rgb;
    break;
  }
  }
  c.a = 1;
  return c;
}
float4 rndz(int3 p, int s) {
  int4 c = int4(p.xyz, s);
  int r =
      (int(0x3504f333 * c.x * c.x + c.y) * int(0xf1bbcdcb * c.y * c.y + c.x) *
       int(0xbf5c3da7 * c.z * c.z + c.y) * int(0x2eb164b3 * c.w * c.w + c.z));
  int4 r4 = int4(0xbf5c3da7, 0xa4f8e125, 0x9284afeb, 0xe4f5ae21) * r;
  return (r4 % 858934592) * .5 / 858934592. + 0.5;
}

float4 PS_Final(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;
  float4 lensdirt = tex2D(SamplerNoise, uv);
  float4 c0 = tex2D(SamplerMip0, uv);
  float4 c00 = tex2D(ReShade::BackBuffer, uv);
  float2 asp = float2(1.0, float(BUFFER_HEIGHT) / float(BUFFER_WIDTH));
  c.a = 1;
  c = 0.0;
  float4 glow = 0;
  glow = 0;
  for (int i = 0; i <= 7; i++) {
    float lf = float(i) / 7.;
    float2 v1 = noise2d(int2(1, 2), i);
    float2 v2 = noise2d(int2(3, 4), i);
    float2 v3 = noise2d(int2(5, 6), i);
    float4 dirt =
        tex2D(SamplerNoise,
              ((.5 + r2d((uv - .5) * asp, v3.x) / asp * .3 * (1.0 + lf) - 0.5) *
                   (1 - 2 * 2. / reso.y) +
               0.5 + normalize(v1 - .5) * 2.0 / reso));
    float4 nc = SampleLevel(uv, i, BICUBIC);
    nc.rgb *= pow(dirt.rgb, DirtFactor * exp2(lerp(-1, -3, lf)));
    // nc.rgb*=exp2(1*sin(timer*exp2(-8.2)-lf*lf*5));
    // glow+=nc*levelweight(i);
    glow += nc * (0.25 + exp2((float(i) / 6. - .5) * GlowShape));
  }
  glow.rgb /= glow.w;

  int2 sr = RandomSeed;
  sr += int(timer * RandomizeSpeed * exp2(-10)) % 1000;
  int2 ip = int2(round(uv * reso - .5));

  float4 flare = 0;
  if (FlareIntensity > 0) {
    for (int i = 0; i < FlareCount; i++) {
      float2 uvc = (uv - .5) * (i - 6) * .3 * asp;
      float2 v1 = noise2d(int2(2, 7) + sr, i + FlareCount);
      float2 v2 = noise2d(int2(3, 2) + sr, i + FlareCount * 2);
      float2 v3 = noise2d(int2(4, 1) + sr, i + FlareCount * 3);
      float2 v4 = noise2d(int2(1, 3) + sr, i + FlareCount * 4);
      float2 v5 = noise2d(int2(2, 8) + sr, i + FlareCount * 5);

      float zm = (v1.x - .5) * 2 * (.02 + v3.y);
      zm = -exp2(v1.x * 4 - .05 / (.012 + v3.y));
      zm = -v1.x / (1.08 - v1.x) * 4;
      zm = -exp2(lerp(-5, 5, pow(v1.x, .5)));
      // if(zm>-5551.393&&v4.y>.5)zm=-zm*.5;
      if (v4.y > .6)
        zm = -zm * .75;
      uvc = (uv - .5) * zm * asp;

      float lvl = pow(1.0 - v1.x, exp2((v1.y - .5) * 2));
      lvl = saturate(log2(abs(zm)) * -.1 + abs(.5 * log2(abs(zm))));
      lvl = pow(lvl, exp2((v1.y - .5) * 3));
      // float4 nc=SampleLevel(uvc/asp+0.5,round(lvl*7),BICUBIC);
      float4 nc = SampleLevel(uvc / asp + 0.5, round(lvl * 7),
                              BICUBIC && abs(zm) < 1 * exp2(lvl * 7));

      nc *= exp2(lvl * .0);
      nc *= pow(1. / (.1 + abs(zm)), .035);
      nc *= lerp(1, pow(length((uv - 0.5) * asp) * 2, 2),
                 pow(smoothstep(.5, 0, abs(zm)), 2.5));
      float rd = length((uv - 0.5) * asp);
      rd = length(uvc);
      float4 rdp = pow(rd * 2, float4(1, 2, 4, 8));
      nc *= 2 * exp2(dot(rdp, float4(1, 3, -2, -18)));
      // nc*=2*exp2(rd*3-4*pow(rd*2,3));

      // nc*=length((uv-0.5)*asp)*2*exp2(-4*pow(length((uv-0.5)*asp)*2,2));
      nc *= zm < 0 ? 1.0 : .5;
      // nc*=abs(zm)+1;
      // nc*=pow(saturate(dot(lensdirt.rgb,hsv2rgb(float3(v5.x,1,1)))),2);
      // float4 dirt=tex2D(SamplerNoise,frac(uv*pow(abs(zm),.25)+v5.xy));
      // float4 dirt=tex2D(SamplerNoise,uv+normalize(v5-.5)*28.0/reso).r;
      // dirt.g=tex2D(SamplerNoise,uv+normalize(v5-.5)*28.0/reso).g;
      // dirt.b=tex2D(SamplerNoise,uv+normalize(v5-.5)*28.0/reso).b;
      float4 dirt =
          tex2D(SamplerNoise,
                (.5 + r2d((uv - 0.5) * asp, v5.y * 3) / asp * pow(abs(zm), .5) +
                 v5.xy));
      nc *= pow(dirt, DirtFactor * exp2(lerp(-1, -3, lvl)));
      // nc*=pow(dirt,exp2(lerp(1,-2,lvl)));
      // nc*=pow(dirt*2,2*exp2(-.1/(.01+abs(zm))));
      nc.rgb *=
          hsv2rgb(float3(.7 - pow(v2.x, 4) + rd * 4.3 * 0 + rd * rd * rd * 5 -
                             pow(length((uv - .5) * asp) * 2, 2) * .1,
                         pow(lvl, .5) * 0.9, 1));
      // nc*=pow(length(uvc)*2,2);
      nc *= smoothstep(.5, 0, length(uvc)) *
            pow(smoothstep(.5, 0.0, abs(uvc.x / asp.x)) *
                    smoothstep(.5, 0.0, abs(uvc.y / asp.y)),
                .5);
      flare +=
          nc * exp2(-8 + lvl * 5 - length((uv - 0.5) * asp) * 6 - abs(zm) * .3);
    }
  }
  c = glow * (float)(GlowIntensity * GlowTint * exp2(GlowExposure)); // *exp2(-pow(length((uv-.5)*asp)*2,2));

  c += flare * (float)(FlareIntensity * FlareTint * exp2(GlowExposure));
  // c+=c0*BlendPass0;
  c.rgb += Untonemap(c00.rgb) * BlendSource;

  c.rgb = Tonemap(c.rgb);
  // c=tex2D(SamplerNoise,uv);

  // int2 np=floor((uv.xy-0.5)*asp*244);
  // c=0;
  // for(int i=0;i<31;i++){
  //     c+=noise2d(np,i)/31.0;
  // }
  c.a = 1;
  return c;
}
float4 PS_Dirt(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;

  c.rgb = uv.xyy;
  c = 0;
  float2 asp = float2(1.0, float(BUFFER_HEIGHT) / float(BUFFER_WIDTH));
  float2 p = (uv.xy - 0.5) * asp * DirtScale;
  int iter = 8;
  for (int i = 0; i < iter; i++) {
    int4 rs = RandomSeedDirt;
    float2 v0 = noise2d(int2(3, 7), i);
    float2 gp = r2d(p * pow(float(i + 1), .1) * 18 * exp2(v0.x * 1), v0.y);
    float2 v1 = noise2d(int2(floor(gp)), rs.w + i + iter);
    float2 v2 = noise2d(int2(floor(gp)), rs.w + i + iter * 2);
    float2 v3 = noise2d(int2(floor(gp).yx), rs.w + i + iter * 3);
    float2 v4 = noise2d(int2(floor(gp).yx), rs.w + i + iter * 4);

    float sr = exp2(-v1.x * v1.x * 4 - .1 / v1.y);
    // sr=(.0+v1.x);
    sr = lerp(.2, .4, v1.x);
    sr = lerp(sr, .9, pow(v1.y, 4));
    sr = lerp(.3, .9, exp2(-8 * v1.x));
    float2 offset = 1 * (1 - sr);
    offset *= (v2 * 2 - 1);
    // float d=length(frac(gp)*2-1);
    float d = length(frac(gp) * 2 - 1 - offset);
    float d0 = d;
    d /= sr;

    // c+=smoothstep(1,.9,d/sr)*.2*exp2((v1.y-.5)*3);
    if (d < 1) {
      float3 f = smoothstep(1, .9 * exp2(-v3.x * v3.x * v3.x * 8), d) * .2 *
                 exp2((v1.y - .95) * 6);
      // f/=d;
      // float3
      // xd=(1-d)*.62*exp2(float3(1,0,-1)*v4.y*v4.y*.5+(v4.x-.5)*3+log2(sr)+4);
      // f=exp(-xd-.1/(.01+xd))*xd;
      // f*=1-exp(-4*(1-d));
      // f*=pow(sr,.275);
      // f+=smoothstep(1,0,d0)*.011/sr*saturate(1-f)*exp2(-3*v1.y);
      f *= .5 / (.02 + v4.x);
      // f*=hsv2rgb(float3(v4.x,pow(v4.y,.1),1));
      c.rgb += f;
    }
  }
  c *= .4;
  c += .05;
  c = c / (1 + c);
  c.a = 1;
  return c;
}

technique Glow {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Prepass;
    RenderTarget = TexMip0;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Blur1;
    RenderTarget = TexMip1;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Blur2;
    RenderTarget = TexMip2;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Blur3;
    RenderTarget = TexMip3;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Blur4;
    RenderTarget = TexMip4;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Blur5;
    RenderTarget = TexMip5;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Blur6;
    RenderTarget = TexMip6;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Blur7;
    RenderTarget = TexMip7;
  }

  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Dirt;
    RenderTarget = TexNoise;
  }

  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Final;
  }
}

} // namespace GlowFX
