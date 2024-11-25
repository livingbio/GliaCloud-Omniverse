#include "ReShade.fxh"

namespace LutPackFX 
{
// #define LUTSIZE 7
// #define LUTTEXWIDTH 49
// #define LUTTEXHEIGHT 231
#define LUTSIZE 32
#define LUTTEXWIDTH 1024
#define LUTTEXHEIGHT 2048

uniform int LutIndex < ui_type = "list";
ui_label = "LUTs";
ui_items =
  "Amber;B&W Delta;B&W Yellow Filter;B&W Blue Filter;B&W Green Filter;B&W "
  "Infrared;B&W ND;B&W Red HC Filter;Bleach Bypass;Bleak;Cooler;Cooler "
  "Bright;Cooler Dark;Desaturate Hicon;Film Eterna;Film F125;Film Reala;Full "
  "Color;Horror Blue;Horror Green;Mono Blue;Mono Blue Ligher;Night;Scifi "
  "Movie;Sunset;Teal Orange 1;Teal Orange 2;Teal Orange 3;Teal Orange 4;"
  "Teal Orange 5;Warmer Bright;Warmer Dark;Warmer";
> = 0;

texture texImage < source = "lut_pack.png";
>
{
  Width = LUTTEXWIDTH;
  Height = LUTTEXHEIGHT;
  Format = RGBA8;
};

sampler SamplerImage
{
  AddressU = CLAMP;
  AddressV = CLAMP;
  MagFilter = POINT;
  MinFilter = POINT;
  MipFilter = POINT;
  Texture = texImage;
};

// uniform float Exposure = 0.0;
uniform float Gamma = 1.0;
uniform float Factor = 1.0;
// uniform float ShiftWhitePoint = 1.0;
uniform int framecount < source = "framecount";
> ;

#define reso float2(BUFFER_SCREEN_SIZE / 1)
float4
readtex(sampler s, int2 xy, int2 texsize)
{
  // if(any(xy<0)||any(xy>int2(texsize)-1))return 0;
  xy = clamp(xy, 0, texsize - 1);
  return tex2Dlod(s, float4((float2(xy) + .5) / float2(texsize), 0, 0));
}
float3
readlut(int3 ci)
{
  // int ts = LUTSIZE;
  int2 tres = int2(LUTTEXWIDTH, LUTTEXHEIGHT);
  int3 lpi = clamp(ci, 0, LUTSIZE - 1);
  int2 lt = int2(0, LutIndex);
  int2 xy = (lpi.xy % LUTSIZE) +
            int2(lpi.z % (tres.x / LUTSIZE), lpi.z / (tres.x / LUTSIZE)) * LUTSIZE +
            lt * int2(0, LUTSIZE);
  // int2
  // xy=(lpi.xz%ts)+int2(lpi.y%(tres.x/ts),lpi.y/(tres.x/ts))*ts+lt*int2(0,LUTSIZE);
  return readtex(SamplerImage, xy, tres).rgb;
}

float3
lerplut(float3 c)
{
  // int ts = LUTSIZE;

  float3 ret = readlut(c.rgb * (LUTSIZE - 1));
  float3 lp = c.rgb * (LUTSIZE);

  int3 lpi = clamp(int3(floor(lp)), 0, LUTSIZE - 1);

  ret = lerp(

    lerp(
      lerp(
        readlut(lpi + int3(0, 0, 0)), readlut(lpi + int3(1, 0, 0)), frac(lp.x)),
      lerp(
        readlut(lpi + int3(0, 1, 0)), readlut(lpi + int3(1, 1, 0)), frac(lp.x)),
      frac(lp.y)),

    lerp(
      lerp(
        readlut(lpi + int3(0, 0, 1)), readlut(lpi + int3(1, 0, 1)), frac(lp.x)),
      lerp(
        readlut(lpi + int3(0, 1, 1)), readlut(lpi + int3(1, 1, 1)), frac(lp.x)),
      frac(lp.y)),

    frac(lp.z));
  return ret;
}

float4
PS(float4 vpos
   : SV_Position, float2 uv
   : TexCoord)
  : SV_Target
{
  float4 c = 0;
  float4 c0 = tex2D(ReShade::BackBuffer, uv);
  c = c0;
  c.rgb = pow(c.rgb, Gamma);
  float3 ct = lerplut(c.rgb);
  // ct/=pow(max(.00001,readlut(int3(1,1,1)*LUTSIZE-1)),ShiftWhitePoint);
  c.rgb = lerp(c0.rgb, ct.rgb, Factor);
  c.a = 1;
  return c;
}

technique LutTexPack
{
  pass
  {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}

}//namespace