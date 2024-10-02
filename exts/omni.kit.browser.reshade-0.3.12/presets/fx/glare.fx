#include "ReShade.fxh"

namespace GlareFX {

uniform float3 GlareTint < ui_type = "color";
ui_label = "Glare Tint";
> = float3(1, 1, 1);

uniform float3 SourceTint < ui_type = "color";
ui_label = "Source Tint";
> = float3(1, 1, 1);

// uniform int RandomSeed = 6;
uniform float GlareExposure < ui_type = "drag";
ui_min = 0;
ui_max = 10.0;
> = 1.0;
uniform float GlareIntensity < ui_type = "drag";
> = 0.322;

uniform int BladeCount < ui_type = "drag";
> = 3;
uniform float BladeAngle < ui_type = "drag";
> = 0;

uniform float BladeDistance < ui_type = "drag";
> = 1.0;

uniform int BladeSteps < ui_type = "drag";
> = 12;
uniform float SourceIntensity < ui_type = "drag";
> = 1.0;

uniform float HighlightFactor < ui_type = "drag";
> = 0.0;
uniform float BurnHighlights < ui_type = "drag";
> = 0.0;
uniform float Hue < ui_type = "drag";
> = 0.50500;
uniform float HueSpread < ui_type = "drag";
> = .8;
uniform float HueShape < ui_type = "drag";
> = .6;
uniform float Saturation < ui_type = "drag";
> = 0.59598;
uniform float Gamma < ui_type = "drag";
> = 1.005;
uniform float BlendFactor < ui_type = "drag";
> = 1.0;
uniform float timer < source = "timer";
> ;
// uniform int framecount < source = "framecount"; >;
// int2 GridSize=int2(12,12);
#define ZOOMFIX 1.17

// #define BladeAngle (timer*exp2(-15))
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
  float h = (r != 0) ? frac(((v == c.x) ? ((c.y - c.z) / r)
                                        : (v == c.y) ? (2 + (c.z - c.x) / r)
                                                     : (4 + (c.x - c.y) / r)) /
                            6)
                     : 0;
  float s = (v != 0) ? (1 - m / v) : 0;
  return float3(h, s, v);
}

float3 Untonemap(float3 c) {
  return c / (1.0 + exp2(-6 - HighlightFactor) - saturate(c));
}
float3 Tonemap(float3 c) { return c / (1.0 + c); }

texture2D GlareTexMip0 {
  Width = BUFFER_WIDTH;
  Height = BUFFER_HEIGHT;
  Format = RGBA16F;
};
sampler SamplerMip0 { Texture = GlareTexMip0; };
texture2D GlareTexMip1 {
  Width = BUFFER_WIDTH * 4;
  Height = BUFFER_HEIGHT;
  Format = RGBA16F;
};
sampler SamplerMip1 { Texture = GlareTexMip1; };
texture2D GlareTexMip2 {
  Width = BUFFER_WIDTH * 4;
  Height = BUFFER_HEIGHT;
  Format = RGBA16F;
};
sampler SamplerMip2 { Texture = GlareTexMip2; };

#define reso float2(BUFFER_SCREEN_SIZE / 1)
float4 readtex(sampler s, int2 xy) {
  if (any(xy < 0) || any(xy > int2(reso) - 1)) return 0;
  return tex2D(s, (float2(xy) + .5) / reso);
}

float4 PS_Pass0(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = tex2D(ReShade::BackBuffer, uv);
  c.rgb = Untonemap(c.rgb);
  c.rgb /= 1.0 + BurnHighlights;

  c.rgb = pow(c.rgb, Gamma);
  float z0 = ReShade::GetLinearizedDepth(uv).x;
  c.a = z0;
  return c;
}

// float4 PS_Pass1(float4 vpos : SV_Position, float2 uv: TexCoord) : SV_Target
// {
//     float4 c=tex2D(SamplerMip0,uv);
//     c=0;
//     float3 wsum=exp2(-20);

//     float2 uvd=frac(uv*float2(BladeCount,1));

//     float ang=.5*floor(uv.x*BladeCount)/BladeCount+BladeAngle;
//     float2 bdir=r2d(float2(1,0),ang);
//     int wd=30;
//     for(int i=-wd;i<=wd;i++){
//         float3 w=1.0;
//         w=exp2(-4*abs(float(i)/float(wd)));
//         w=exp2(-pow(float3(7,5,3)*abs(float(i)/float(wd)),2));
//         //
//         w=exp2(-pow(4*abs(float(i)/float(wd)),2))*hsv2rgb(float3(.0+ang*0+.5*abs(float(i))/float(wd),1,1));
//         //
//         w=exp2(-pow(3*abs(float(i)/float(wd)),2))*hsv2rgb(float3(Hue+.23*log2(abs(float(i))+1),.9,1));
//         w=exp2(-pow(42*hsv2rgb(float3(Hue+.3+HueSpread*log2(abs(float(i))+1),Saturation*(1-exp2(-pow(4*abs(float(i)/wd),2))),1))*abs(float(i)/float(wd)),1))/(1+abs(i)/float(wd));
//         // w/=hsv2rgb(float3(.33+.13*log2(1),.9,1));
//         //
//         w*=.1+.9*exp2(-22.1/pow(.1+float3(11,15,17)*abs(float(i)/float(wd)),1));
//         wsum+=w;
//         float2 uvc=r2d(uvd-.5,ang)*ZOOMFIX+.5-bdir*(float(i)*60/reso.x);
//         uvc.y=(uvc.y-.5)*reso.x/reso.y+.5;
//         if(any(abs(uvc-.5)>.5))continue;
//         c.rgb+=w*tex2D(SamplerMip0,uvc).rgb;//
//         *(.25+abs(i/float(BladeCount)));

//     }
//     c.rgb/=wsum;
//     // c.rgb/=sqrt(hsv2rgb(float3(Hue+.23*log2(2),.9,1)));

//     return c;
// }
// float4 PS_Pass2(float4 vpos : SV_Position, float2 uv: TexCoord) : SV_Target
// {
//     float4 c=0;
//     float3 wsum=exp2(-20);
//     int wd=12;
//     for(int i=-wd;i<=wd;i++){
//         float3 w=exp2(-pow(2*abs(float(i)/float(wd)),2));
//         wsum+=w;
//         float2 uvc=uv+float2(i,0)/reso;
//         if(any(abs(uvc-.5)>.5))continue;
//         c.rgb+=w*tex2D(SamplerMip1,uvc).rgb;

//     }
//     c.rgb/=wsum;

//     return c;
// }

float4 PS_Pass1(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = tex2D(SamplerMip0, uv);
  c = 0;
  float3 wsum = exp2(-20);

  float2 uvd = frac(uv * float2(BladeCount, 1));

  float ang = .5 * floor(uv.x * BladeCount) / BladeCount + BladeAngle;
  float2 bdir = r2d(float2(1, 0), ang);
  int wd = BladeSteps;
  for (int i = -wd; i <= wd; i++) {
    float3 w = 1.0;
    // w=exp2(-4*abs(float(i)/float(wd)));
    // w=exp2(-pow(float3(7,5,3)*abs(float(i)/float(wd)),2));
    // w=exp2(-pow(4*abs(float(i)/float(wd)),2))*hsv2rgb(float3(.0+ang*0+.5*abs(float(i))/float(wd),1,1));
    // w=exp2(-pow(3*abs(float(i)/float(wd)),2))*hsv2rgb(float3(Hue+.23*log2(abs(float(i))+1),.9,1));
    // w=exp2(-pow(42*hsv2rgb(float3(Hue+.3+HueSpread*log2(abs(float(i))+1),Saturation*(1-exp2(-pow(4*abs(float(i)/wd),2))),1))*abs(float(i)/float(wd)),1))/(1+abs(i)/float(wd));
    w = exp2(-pow(2 * abs(float(i + 1)) / float(wd + 1), 2.5));
    // w/=hsv2rgb(float3(.33+.13*log2(1),.9,1));
    // w*=.1+.9*exp2(-22.1/pow(.1+float3(11,15,17)*abs(float(i)/float(wd)),1));
    wsum += w;
    float2 uvc = r2d(uvd - .5, ang) * ZOOMFIX + .5 -
                 bdir * (float(i) * 3 / reso.x) * BladeDistance;
    uvc.y = (uvc.y - .5) * reso.x / reso.y + .5;
    if (any(abs(uvc - .5) > .5)) continue;
    c.rgb +=
        w * tex2D(SamplerMip0, uvc).rgb;  // *(.25+abs(i/float(BladeCount)));
  }
  c.rgb /= wsum;
  // c.rgb/=sqrt(hsv2rgb(float3(Hue+.23*log2(2),.9,1)));

  return c;
}
float4 PS_Pass2(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;
  float3 wsum = exp2(-20);
  int wd = BladeSteps * 2;
  for (int i = -wd; i <= wd; i++) {
    float3 w = exp2(-pow(2 * abs(float(i) / float(wd)), 2));
    // float hx=log2(abs(float(i+1)))/log2(float(wd+1));
    float hx = .5 * pow(2 * abs(float(i)) / float(wd), HueShape);
    float3 col = hsv2rgb(float3(
        Hue + .3 + HueSpread * hx,
        Saturation + 0 * (1 - exp2(-pow(14 * abs(float(i) / wd), 2))), 1));
    w = exp2(-pow(15 * col * abs(float(i) / float(wd)), 1)) /
        (1 + abs(i) / float(wd));

    w /= float(wd);
    wsum += w;
    float2 uvc = uv + float2(i, 0) * 6 * BladeDistance / reso;
    if (any(abs(uvc - .5) > .5)) continue;
    c.rgb += w * tex2D(SamplerMip1, uvc).rgb /
             (.05 + .2 * (col + 1) * abs(i / float(BladeCount)));
  }
  // c.rgb/=wsum;

  return c;
}

float4 PS_Final(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float4 c = 0;

  float3 cg = 0;
  float2 ac = float2(1, reso.y / reso.x);
  float ang = BladeAngle;
  for (int i = 0; i < BladeCount; i++) {
    float2 uvs =
        (r2d((uv - .5) * ac / ZOOMFIX, -float(i) * 0.5 / BladeCount - ang) +
         .5 + float2(i, 0)) /
        float2(BladeCount, 1);

    cg.rgb += tex2D(SamplerMip2, uvs).rgb * GlareIntensity *
              exp2(GlareExposure) * GlareTint / float(BladeCount);
  }
  float4 c0 = tex2D(SamplerMip0, uv);
  c.rgb += c0.rgb * SourceIntensity * SourceTint;
  // c.rgb+=cg/sqrt(1+c.rgb);
  c.rgb += cg;
  c.rgb = pow(c.rgb, 1. / Gamma);
  // c=tex2D(SamplerMip2,uv);
  c.rgb = Tonemap(c.rgb) * (1 + BurnHighlights);
  c.rgb = lerp(pow(tex2D(SamplerMip0, uv).rgb, 1. / Gamma), c.rgb, BlendFactor);
  // c.rgb=int(vpos.x)%2;
  c.a = 1;
  return c;
}

technique Glare {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Pass0;
    RenderTarget = GlareTexMip0;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Pass1;
    RenderTarget = GlareTexMip1;
  }
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Pass2;
    RenderTarget = GlareTexMip2;
  }

  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS_Final;
  }
}

}  // namespace GlareFX
