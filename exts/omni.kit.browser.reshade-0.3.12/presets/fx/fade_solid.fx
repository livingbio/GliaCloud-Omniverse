#include "ReShade.fxh"

namespace FadeSolidFX {

uniform float timer < source = "timer";
> ;
uniform int framecount < source = "framecount";
> ;
uniform float frametime < source = "frametime";
> ;
uniform float2 pingpong < source = "pingpong";
min = 0;
max = 360;
step = 0.01;
smoothing = 0.0;
> ;

uniform float3 FadeToColor < ui_type = "color";
ui_label = "Fade Color";
> = float3(0.0, 0.0, 0.0);

#define reso float2(BUFFER_SCREEN_SIZE / 1)

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

float4 PS_Final(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = tex2D(ReShade::BackBuffer, uv);
  c.rgb = lerp(FadeToColor, c.rgb, fade());
  return c;
}

technique FadeSolid {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Final;
  }
}
}  // namespace