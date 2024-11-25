#include "ReShade.fxh"

namespace NoirFX
{
uniform float3 TargetColor <
ui_type="color";
ui_label = "Target Color 1";
> = float3(1.0, 0.0, 0.0);

uniform float3 TargetColor2 <
ui_type="color";
ui_label = "Target Color 2";
> = float3(0.1, 0.0, 0.0);

uniform float EdgeWidth < ui_type = "drag";
> = 1.;

uniform float Threshold < ui_type = "drag";
> = .50;

uniform float ThresholdSmooth < ui_type = "drag";
> = .15;

uniform float SaturationA < ui_type = "drag";
> = 0.0;

uniform float SaturationB < ui_type = "drag";
> = 2.0;

uniform float GammaA < ui_type = "drag";
> = 4.0;

uniform float GammaB < ui_type = "drag";
> = -1.0;

uniform float Ambient < ui_type = "drag";
> = 0.1;

uniform float AmbientEdgeFade < ui_type = "drag";
> = 1.5;

uniform float ChromaSensitivity < ui_type = "drag";
> = 1.0;

uniform float ValueSensitivity < ui_type = "drag";
> = 0.1;

uniform float Sharpness < ui_type = "drag";
> = 0.1;

uniform float timer < source = "timer";
> ;

float3 HUEtoRGB(in float H) {
  H = frac(H);
  float R = abs(H * 6 - 3) - 1;
  float G = 2 - abs(H * 6 - 2);
  float B = 2 - abs(H * 6 - 4);
  return saturate(float3(R, G, B));
}
float3 HSVtoRGB(in float3 HSV) {
  float3 RGB = HUEtoRGB(HSV.x);
  return ((RGB - 1) * HSV.y + 1) * HSV.z;
}
float3 RGBtoHSV(in float3 RGB) {
  float3 HSV = 0;
  HSV.z = max(RGB.r, max(RGB.g, RGB.b));
  float M = min(RGB.r, min(RGB.g, RGB.b));
  float C = HSV.z - M;
  if (C != 0) {
    float4 RGB0 = float4(RGB, 0);
    float4 Delta = (HSV.z - RGB0) / C;
    Delta.rgb -= Delta.brg;
    Delta.rgb += float3(2, 4, 6);
    Delta.brg = step(HSV.z, RGB) * Delta.brg;
    HSV.x = max(Delta.r, max(Delta.g, Delta.b));
    HSV.x = frac(HSV.x / 6);
    HSV.y = 1 / Delta.w;
  }
  return HSV;
}
float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}

#define linstep(a, b, x) saturate((x - a) / (b - a))

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = tex2D(ReShade::BackBuffer, uv);

  float2 e = float2(EdgeWidth, 0.0);
  float2 reso = BUFFER_SCREEN_SIZE;

  // float2 e2=e;
  // float3 c0=tex2D(ReShade::BackBuffer,uv).rgb;
  float3 c1 = tex2D(ReShade::BackBuffer, uv - e.xy / reso).rgb;
  float3 c2 = tex2D(ReShade::BackBuffer, uv + e.xy / reso).rgb;
  float3 c3 = tex2D(ReShade::BackBuffer, uv - e.yx / reso).rgb;
  float3 c4 = tex2D(ReShade::BackBuffer, uv + e.yx / reso).rgb;
  // float3 c0l=c0/(1.005-c0);
  // float3 c1l=c1/(1.005-c1);
  // float3 c2l=c2/(1.005-c2);
  // float3 c3l=c3/(1.005-c3);
  // float3 c4l=c4/(1.005-c4);

  // float cedge=length(float3(
  //     length(c0.x*2-float2(c1.x+c2.x,c3.x+c4.x))/(.02+c0.x),
  //     length(c0.y*2-float2(c1.y+c2.y,c3.y+c4.y))/(.02+c0.y),
  //     length(c0.z*2-float2(c1.z+c2.z,c3.z+c4.z))/(.02+c0.z)
  //     ))*2/EdgeWidth;
  // cedge=max(0,(cedge-ColorEdgeThreshold)*ColorEdgeIntensity/(1.0-ColorEdgeThreshold));
  // cedge=cedge/(1+cedge);
  float3 c0 = tex2D(ReShade::BackBuffer, uv).rgb;
  float3 hsv0 = RGBtoHSV(c0);
  float3 hsv1 = RGBtoHSV(TargetColor);
  float3 hsv2 = RGBtoHSV(TargetColor2);

  float3 xyv0 = float3(r2d(float2(hsv0.y, 0), hsv0.x), hsv0.z);
  float3 xyv1 = float3(r2d(float2(hsv1.y, 0), hsv1.x), hsv1.z);
  float3 xyv2 = float3(r2d(float2(hsv2.y, 0), hsv2.x), hsv2.z);

  float cd1 =
      length((xyv0 - xyv1) *
             float3(ChromaSensitivity, ChromaSensitivity, ValueSensitivity));
  float cd2 =
      length((xyv0 - xyv2) *
             float3(ChromaSensitivity, ChromaSensitivity, ValueSensitivity));
  float cd = min(cd1, cd2);

  float cm = smoothstep(1.0, 0.99 - ThresholdSmooth, cd / Threshold);
  c.rgb = c0;
  c.rgb +=
      ((c0 - c1) + (c0 - c2) + (c0 - c3) + (c0 - c4)) * Sharpness / EdgeWidth;
  c = max(float4(0.0, 0.0, 0.0, 0.0), c);
  float3 h = RGBtoHSV(c.rgb);
  h.y = h.y / (1.0001 - h.y);
  // h.y*=cm*2;
  h.y *= lerp(SaturationA, SaturationB, cm);
  h.y = h.y / (1.0 + h.y);

  // h.z=h.z/(1.01-min(1.0,h.z));
  // h.z*=exp2(lerp(ExposureA,ExposureB,cm));
  // h.z=h.z/(1.0+h.z);
  float pillow =
      exp2(-AmbientEdgeFade * (pow(abs(uv.x * 2 - 1), 2) +
                               pow(abs(uv.y * 2 - 1) * reso.y / reso.x, 2)));
  h.z = (pow(h.z * 1.1, exp2(lerp(GammaA, GammaB, cm))) / 1.1 +
         log2(1.0 + 5 * h.z / (1.01 - saturate(h.z))) * pillow * Ambient * 0.3 *
             (1.0 - cm));
  c.rgb = HSVtoRGB(h);
  // c.rgb=cm;
  // c.rgb=cd;
  // c.rgb=yuv0.y;
  // c.rgb=c.rgb/(1.001-c.rgb);
  // float3 h=RGBtoHSV(c.rgb);
  // h.y=pow(smoothstep(0,1,h.y),.25);
  // h.z=pow(smoothstep(0,1,h.z),.25);
  // float fcol=0.94;
  // float fsat=Colorize;
  // float fval=Colorize;
  // h.y=pow(lerp(h.y,smoothstep(0,1,h.y),fsat),exp2(1-fsat*2));
  // h.z=pow(lerp(h.z,smoothstep(0,1,h.z),fval),exp2(-fval*2));
  // h.y+=(1-h.y)*(.75*pow(smoothstep(0,1,h.y),.5));
  // h.z=pow(h.z,.5);
  // c.rgb=HSVtoRGB(h);

  // c.rgb+=((c0-c1)+(c0-c2)+(c0-c3)+(c0-c4))*Sharpness/EdgeWidth;
  // c.rgb+=((c0-c1)+(c0-c2)+(c0-c3)+(c0-c4))*Sharpness;

  // if(length(c0l.rgb)>22.92)c.rgb+=((c0l-c1l)+(c0l-c2l)+(c0l-c3l)+(c0l-c4l))*Sharpness/EdgeWidth;

  c = max(float4(0.0, 0.0, 0.0, 0.0), c);

  // c.rgb=c.rgb/(1.0+c.rgb);
  // c.rgb=lerp(c.rgb,0,saturate(max(cedge,zedge)*1)*float(z0<.99));
  // c.rgb*=exp2(-2*saturate(max(cedge,zedge)*1)*float(z0<DepthThreshold));
  // c.rgb+=c.rgb/(1.0+c.rgb);
  c.a = 1;
  return c;
}

technique Noir {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}//namespace