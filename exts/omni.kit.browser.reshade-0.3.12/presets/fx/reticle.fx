#include "ReShade.fxh"

namespace ReticleFX {

uniform int ReticleIndex < ui_type = "list";
ui_label = "Reticle";
ui_items = "PSO-1 (Dragunov); MOA Reticle; M3 Binoculars; MIL Reticle";
> = 1;

uniform float ReticleOpacity < ui_type = "drag";
ui_min = 0.0;
ui_max = 100.0;
ui_step = 0.01;
ui_label = "Reticle Opacity";
ui_tooltip = "Reticle Overlay Opacity";
> = 60.0;

texture tex0 < source = "reticle_pso.png";
> { Format = RGBA8; };
texture tex1 < source = "reticle_moa.png";
> { Format = RGBA8; };
texture tex2 < source = "reticle_m3.png";
> { Format = RGBA8; };
texture tex3 < source = "reticle_mil.png";
> { Format = RGBA8; };
// texture tex4 < source = "reticle_vortex.png"; > {Width = LUTTEXWIDTH;Height =
// LUTTEXHEIGHT;Format = RGBA8;};

sampler S0 {
  AddressU = CLAMP;
  AddressV = CLAMP;
  MagFilter = LINEAR;
  MinFilter = LINEAR;
  MipFilter = LINEAR;
  Texture = tex0;
};
sampler S1 {
  AddressU = CLAMP;
  AddressV = CLAMP;
  MagFilter = LINEAR;
  MinFilter = LINEAR;
  MipFilter = LINEAR;
  Texture = tex1;
};
sampler S2 {
  AddressU = CLAMP;
  AddressV = CLAMP;
  MagFilter = LINEAR;
  MinFilter = LINEAR;
  MipFilter = LINEAR;
  Texture = tex2;
};
sampler S3 {
  AddressU = CLAMP;
  AddressV = CLAMP;
  MagFilter = LINEAR;
  MinFilter = LINEAR;
  MipFilter = LINEAR;
  Texture = tex3;
};

// // uniform float Exposure = 0.0;
// uniform float Gamma = 1.0;
// uniform float Factor = 1.0;
// // uniform float ShiftWhitePoint = 1.0;
// uniform int framecount < source = "framecount"; >;

// #define reso float2(BUFFER_SCREEN_SIZE/1)
// float4 readtex(sampler s,int2 xy,int2 texsize){
//     // if(any(xy<0)||any(xy>int2(texsize)-1))return 0;
//     xy=clamp(xy,0,texsize-1);
//     return tex2Dlod(s,float4((float2(xy)+.5)/float2(texsize),0,0));
// }
// float3 readlut(int3 ci){
//     int ts=LUTSIZE;
//     int2 tres=int2(LUTTEXWIDTH,LUTTEXHEIGHT);
//     int3 lpi=clamp(ci,0,ts-1);
//     int2 lt=int2(0,LutIndex);
//     int2
//     xy=(lpi.xy%ts)+int2(lpi.z%(tres.x/ts),lpi.z/(tres.x/ts))*ts+lt*int2(0,LUTSIZE);
//     // int2
//     xy=(lpi.xz%ts)+int2(lpi.y%(tres.x/ts),lpi.y/(tres.x/ts))*ts+lt*int2(0,LUTSIZE);
//     return readtex(SamplerImage,xy,tres).rgb;
// }

// float3 lerplut(float3 c){
//     int ts=LUTSIZE;

//     float3 ret=readlut(c.rgb*(ts-1));
//     float3 lp=c.rgb*(ts);

//     int3 lpi=clamp(int3(floor(lp)),0,ts-1);

//     ret=lerp(

//             lerp(
//             lerp(readlut(lpi+int3(0,0,0)),readlut(lpi+int3(1,0,0)),frac(lp.x)),
//             lerp(readlut(lpi+int3(0,1,0)),readlut(lpi+int3(1,1,0)),frac(lp.x)),
//             frac(lp.y)),

//             lerp(
//             lerp(readlut(lpi+int3(0,0,1)),readlut(lpi+int3(1,0,1)),frac(lp.x)),
//             lerp(readlut(lpi+int3(0,1,1)),readlut(lpi+int3(1,1,1)),frac(lp.x)),
//             frac(lp.y)),

//             frac(lp.z)
//         );
//     return ret;
// }

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;
  float4 c0 = tex2D(ReShade::BackBuffer, uv);

  float texAspect = 1.0;  // assume square reticles only for now
  float screenAspect = ReShade::AspectRatio;
  float tsRatio = texAspect / screenAspect;

  float uscale = 1, vscale = 1;
  if (screenAspect < 1)
    vscale = tsRatio;
  else
    uscale = 1.f / tsRatio;

  float2 textureScale = float2(uscale, vscale);
  float2 uvc = textureScale * (uv - 0.5) + 0.5;

  float4 c1 = float4(0.0, 0.0, 0.0, 1.0);
  switch (ReticleIndex) {
    case 0:
      c1 = tex2D(S0, uvc);
      break;
    case 1:
      c1 = tex2D(S1, uvc);
      break;
    case 2:
      c1 = tex2D(S2, uvc);
      break;
    case 3:
      c1 = tex2D(S3, uvc);
      break;

    default:
      c1 = tex2D(S0, uvc);
      break;
  }

  if (any(abs(uvc - 0.5) > 0.5)) c1 = 0.0;

  c = c0;
  c1.rgb *= c1.a;
  c.rgb = lerp(c0.rgb, c1.rgb, 0.01 * ReticleOpacity * c1.a);
  // if(c1.a>0.0) c.rgb*=c1.a;
  c.a = 1;
  return c;
}

technique Reticle {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}

}  // namespace