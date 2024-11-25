#include "ReShade.fxh"
namespace TritoneFX
{
uniform float3 ShadowColor < ui_type = "color";
ui_label = "Shadows Color";
> = float3(0.05, 0.1, 0.1);

uniform float3 MidtoneColor < ui_type = "color";
ui_label = "Midtones Color";
> = float3(0.5, 0.5, 0.5);

uniform float3 HighlightColor < ui_type = "color";
ui_label = "Highlights Color";
> = float3(0.95, 0.85, 0.9);


uniform float BlendOriginalAmount < ui_type = "drag";
ui_min = 0.0;
ui_max = 100.0;
ui_label = "Blend With Original";

> = 5.0;

uniform float timer < source = "timer";
> ;


float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}


float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {


  float4 c = tex2D(ReShade::BackBuffer, uv);
  float4 outc=c;
  float bri = (c.r + c.g + c.b / 3.0);

  outc.rgb=lerp(ShadowColor,HighlightColor,bri);
  float u = 1.0-abs(bri*2.0-1.0);
    outc.rgb=lerp(outc.rgb,MidtoneColor,u);

  outc.a=1.0;
  outc=lerp(outc,c,BlendOriginalAmount*0.01);
  return outc;
}

technique Tritone {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}//namespace