#include "ReShade.fxh"
namespace AberrationFX {

uniform float Amount < ui_type = "drag";
ui_min = 0.0;
ui_max = 100.0;
ui_step = 1.0;
ui_label = "Aberration Amount";
ui_tooltip = "Aberration Amount";
> = 12.0;

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float amt = Amount / length(ReShade::ScreenSize);
  float2 d = (uv - (.5)) * amt;
  float3 color = float3(tex2D(ReShade::BackBuffer, uv - 0.0 * d).r,
                        tex2D(ReShade::BackBuffer, uv - 1.0 * d).g,
                        tex2D(ReShade::BackBuffer, uv - 2.0 * d).b);

  return float4(color, 1);
}

technique Aberration {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}

}  // namespace AberrationFX