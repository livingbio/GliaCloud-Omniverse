#include "ReShade.fxh"

namespace DepthBlocksFX {

uniform float ANIM_SPEED < ui_type = "drag";
ui_label = "Animation Speed";
> = 1.0;

uniform float CYCLE < ui_type = "drag";
ui_label = "Rotation cycle";
> = .75;

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
float2x2 lookat2d(float2 v) {
  v = normalize(v);
  float2 e = float2(dot(v, float2(1, 0)), dot(v, float2(0, 1)));
  return float2x2(e.x, e.y, -e.y, e.x);
}

float2 hash22(float2 p) {
  p = float2(dot(p, float2(127.1, 311.7)), dot(p, float2(269.5, 183.3)));

  return normalize(-1.0 + 2.0 * frac(sin(p) * 43758.5453123));
}
float2 hash22si(int2 ip, int seed) {
  float2 p = float2(ip) + float(seed) * float2(1.618, .618);
  return hash22(p);
  // p = float2( dot(p,float2(127.1,311.7)),
  //           dot(p,float2(269.5,183.3)));

  // return normalize(-1.0 + 2.0 * frac(sin(p)*43758.5453123));
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  // float4 c =0;

  float2 asp = float2(1.0, float(BUFFER_HEIGHT) / float(BUFFER_WIDTH));
  float a = (floor(timer * .01 * .1 * exp2(.4 * sin(floor(uv.y * 5))))) / 8.;
  a = -.125 / 2.;
  a = timer * 0.0250 * 0.02 * 0.01;
  a = CYCLE;
  // a=timer*.02*0.02*0.1;
  float4 c = tex2Dlod(ReShade::BackBuffer, float4(uv.xy, 0.0, 0.0));
  float d = ReShade::GetLinearizedDepth(uv);
  if (d >= exp2(-0.1 * 0.041)) d = 4.0;
  // if(d>0.99)d=.199;
  // for(int i=0;i<10;i++){
  //     float fq=exp2(float(i));
  //     float2 gs=asp*2*fq;
  //     float a=0.037*timer;
  //     a=0*30.30/exp2(float(i));;
  //     // a=frac(hash22(float2(.1,.3)).x*float(timer)*0.003);
  //     float2 gp=r2d((uv-0.5)*gs,a);
  //     float2 gt=r2d(((floor(gp)+0.5)/gs)*asp,-a)/asp+0.5;
  //     float4 gc=tex2Dlod(ReShade::BackBuffer,float4(gt.xy,0.0,0.0));
  //     float gd=ReShade::GetLinearizedDepth(gt);
  //     float cd=length(frac(gp)-0.5);
  //     if( (gd<d+.02) && (cd<0.4995) && (cd>fq*.0001)){
  //         c=gc*exp2(-pow(cd*2,2)/fq);
  //         //
  //         c=lerp(c,gc,length(frac(gp)-0.5)<0.5*(exp2(-.12*float(i)*dot(gc,.33))));
  //         d=gd+length(frac(gp)-0.5)*0.0/fq;
  //     }
  // }
  float2 uvd = r2d(uv * asp, a);
  int iter = 25;
  int seed = int(floor(0.02 * timer * ANIM_SPEED * .015));
  float2 gs = float2(16, 9) * 4;
  if (hash22si(int2(2, floor(uvd * gs).y), seed + 4).x < .0) gs *= 3;
  if (hash22si(int2(3, floor(uvd * gs).y), seed + 5).x < .0) gs *= 3;
  if (hash22si(int2(4, floor(uvd * gs).y), seed + 6).x < .0) gs *= 3;
  if (hash22si(int2(5, floor(uvd * gs * 2.26).y), seed + 7).x < .0) gs *= 2;
  float tt = timer * .015 * ANIM_SPEED;
  float2 hv0 = hash22si(int2(5, floor(uvd * gs).y), seed);

  for (int i = 0; i < iter; i++) {
    float lf = float(i) / float(iter);
    float ld = lf * exp2((lf - 1.0) * 5.0);
    float ft = frac(tt * pow(gs.y * 0.006, 0.75) * .15 * exp2(hv0.y));
    float fd =
        exp2(hv0.x * .5 + sin(uvd.y * 1883.0) * 0.0 + (ft * 2.0 - 1.0) * 5.0);
    float2 gt =
        uvd - ld * float2(1.0, 0.0) * fd * 1.25 * pow(gs.y * 0.02, -0.975);
    // gt=r2d(gt,a);
    if (frac(hv0.x * 15.0) < 0.92) gt = (floor(gt * gs) + 0.5) / gs;
    float2 gtt = r2d(gt.xy, -a) / asp;
    if (abs(gtt.x - 0.5) > 0.5 || abs(gtt.x - 0.5) > 0.5) break;
    float4 gc = tex2Dlod(ReShade::BackBuffer, float4(gtt.xy, 0.0, 0.0));
    float gd = ReShade::GetLinearizedDepth(gtt);
    if (gd >= exp2(-0.1 * 0.041))
      gd = 2.0 -
           0.31 *
               exp2(-(hash22si(int2(floor(gt * gs)), seed + 55).x * 0.5 + 0.5));
    // float2 hv=hash22(floor(gt*gs)+0.0*float(i)*float2(1.618,.618));
    // float2 hv2=hash22(floor(gt*gs)+0.0*(0.5+float(i))*float2(.618,1.618));
    float2 hv = hash22si(int2(floor(gt * gs)), seed);
    float2 hv2 = hash22si(int2(floor(gt * gs)), seed + 55);
    float2 hv3 = hash22si(int2(floor(gt * gs)), seed + 88);

    float3 col = HSVtoRGB(float3(hv.y, lf * 0.2, 1.0));
    float3 h = RGBtoHSV(gc.rgb);
    h.y = h.y / (1.001 - h.y);
    h.y *= exp2(hv.x * 3.0 * ld * exp2((ld - 1.0) * 2.0));
    h.x += .3 * hv.y * ld * exp2((ld - 1.0) * 2.0);
    h.z *= exp2(hv3.x * ld * .6 * fd);
    h.y = h.y / (1.001 + h.y);

    float3 col2 = HSVtoRGB(h);

    // if( gd<d && hv.x<1.0-2.0*lf){
    // && hv.x*.5+.5>1.0-lf
    if (gd + .025 * exp2((ld - 1.0) * 8.0 * exp2(hv2.x)) * ld <
        d + 0 * ld * exp2(-3.0 + (ld - 1.0) * 29 - 1.0 * frac(hv0.y * 33.0))) {
      // c=gc*float4(col.rgb,1.0);
      // c=lerp(c,float4(col2.rgb,1.0),1.0-ft*ft);
      c = lerp(c, float4(col2.rgb, 1.0),
               (1.0 - pow(ft, 6.0)) * exp2(-pow(ft, 6.0) * 161 * ld * ld));

      // c=float4(col2.rgb,1.0);
      d = gd;
    }
  }
  d = ReShade::GetLinearizedDepth(uv);
  // c.rgb=float3(1,1,0)*float(d<.99);
  // c.rgb=float3(1,1,0)*frac(log2(d)*28);
  // c.rgb=float3(1,1,0)*(d>=exp2(-0.1*0.041));
  float4 co = tex2Dlod(ReShade::BackBuffer, float4(uv.xy, 0.0, 0.0));
  c.a = 1;
  // c=lerp(c,co,c.a);
  return c;
}

technique DepthBlocks {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace