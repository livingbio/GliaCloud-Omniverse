#include "ReShade.fxh"
namespace ScifiBlocksFX
{
uniform float ANIM_SPEED < ui_type = "drag";
ui_label = "Rotation Speed";
ui_min = -1;
ui_max = 1;
> = 0.0f; // Animation speed

uniform float ROTATION < ui_type = "drag";
ui_label = "Pattern Rotation";
ui_min = 0;
ui_max = 360;

> = 45;

uniform float timer < source = "timer";
> ;

float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}

float2 hash22(float2 p) {
  p = float2(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)));

  return normalize(-1.0 + 2.0 * frac(sin(p) * 43758.5453123));
  // return rndz(p.xyy*44+33,3).xy*2-1;
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;

  c = tex2D(ReShade::BackBuffer, uv);

  float2 asp = float2(1.0, float(BUFFER_HEIGHT) / float(BUFFER_WIDTH));
  for (int i = 0; i < 8; i++) {
    float2 gs = asp * 2 * exp2(float(i) * 0.99986);

    float a = ROTATION / 360 + timer * ANIM_SPEED * 0.001;

    // a=frac(hash22(float2(.1,.3)).x*float(timer)*0.003);
    float2 gp = r2d((uv - 0.5) * gs, a);
    float2 gt = r2d(((floor(gp) + 0.5) / gs) * asp, -a) / asp + 0.5;
    float4 gc = tex2D(ReShade::BackBuffer, gt);
    c = lerp(c, gc,
             length(frac(gp) - 0.5) <
                 0.5 * (exp2(-.12 * float(i) * dot(gc, .33))));
  }
  // c+=length((uv-0.5)*asp)<0.5;
  return c;
}

// float4 FillPass2(float4 vpos : SV_Position, float2 uv: TexCoord) : SV_Target
// {
//     float4 c=0;
//     c.rgb=tex2D(ReShade::BackBuffer,uv*2).xyz;
//     c.a=1;
//     return c;
// }

technique SciFiBlocks {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}//namespace