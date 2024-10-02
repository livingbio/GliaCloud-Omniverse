#include "ReShade.fxh"

namespace FadeHolodeckFX {

uniform float EdgeWidth = 1.0;
uniform float EdgeConstanMul = 0.50;
uniform float EdgeConstantAmt = .25;
uniform float EdgeWaveAmt = 0.5;
uniform float EdgeWaveFreq = 1.0;
uniform float EdgeWaveSpeed = 1.0;
uniform float4 EdgeWaveDir = float4(0, 0, 0.2, 1);
uniform float3 EdgeColor = float3(.463, .725, 0.01);
uniform float EdgeIntensity = 1;
uniform float DepthEdgeIntensity = 10.0;
uniform float DepthEdgeThreshold = 0.000125;

uniform float timer < source = "timer";
> ;

uniform bool DebugBar = false;
uniform float2 pingpong < source = "pingpong";
min = 0;
max = 360;
step = 0.05;
smoothing = 0.0;
> ;
// uniform float2 pingpong < source = "pingpong"; min = 0; max = .5; step = 0.1;
// smoothing = 0.0; >;

uniform bool ReverseZ = true;

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

float bayer2(float2 v) {
  v = floor(v);
  return frac(v.y * v.y * .75 + v.x * .5);
}
float bayer4(float2 v) { return bayer2(.5 * v) * .25 + bayer2(v); }
float bayer8(float2 v) { return bayer4(.5 * v) * .25 + bayer2(v); }
float bayer16(float2 v) { return bayer8(.5 * v) * .25 + bayer2(v); }
float bayer32(float2 v) { return bayer16(.5 * v) * .25 + bayer2(v); }

float2 noise2d(int2 xy, int seed) {
  int3 c = int3(xy + (xy >= 0), seed);
  int r = int(0xf6a47f78 * c.x * c.x + c.y) *
          int(0x82f88c81 * c.y * c.y + c.x) *
          int(0x964cb8a1 * c.z * c.z + c.y) * int(0xafc35eb8 * c.y * c.x + c.z);
  int2 r2 = int2(0xebfd9f9a, 0x93b7c155) * r;
  return (r2 % 358934592) * .5 / 358934592. + 0.5;
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

float3 Untonemap(float3 c) { return c / (1.0 + exp2(-6) - saturate(c)); }
float3 Tonemap(float3 c) { return c / (1.0 + c); }
float3 SampleViewPos(float2 uv) {
  float2 asp = float2(1.0, float(BUFFER_HEIGHT) / float(BUFFER_WIDTH));
  float z = ReShade::GetLinearizedDepth(uv).x;
  float2 sp = (uv * 2 - 1) * asp;
  z = min(z, .99);
  float d = .1 / (1.0 - 1.0 / z);

  float4 p = float4(sp * d, d, 1);
  return p.xyz;
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  float f = fade();
  int2 ip = int2(vpos.xy - .25);
  // float4 c=tex2D(ReShade::BackBuffer, uv);
  float3 c0 = tex2D(ReShade::BackBuffer, uv).rgb;
  float2 e = float2(EdgeWidth, 0.0);
  float2 reso = BUFFER_SCREEN_SIZE;
  float2 ipq = ip;
  // int q=int(floor(lerp(1,32,(1-f)*exp2(-(f)*4))));
  // int q = 1;
  // ipq = (ip / q);
  float q = 1.0;
  float2 uvq = (float2(ipq * q) + .5) / reso;
  float z0 = ReShade::GetLinearizedDepth(uvq).x;
  float z1 = ReShade::GetLinearizedDepth(uvq - e.xy / reso).x;
  float z2 = ReShade::GetLinearizedDepth(uvq + e.xy / reso).x;
  float z3 = ReShade::GetLinearizedDepth(uvq - e.yx / reso).x;
  float z4 = ReShade::GetLinearizedDepth(uvq + e.yx / reso).x;
  float3 vpc = SampleViewPos(float2(0.5, 0.5));
  float3 vp0 = SampleViewPos(uv);
  // float3 vp1=SampleViewPos(uv-e.xy/reso);
  // float3 vp2=SampleViewPos(uv+e.xy/reso);
  // float3 vp3=SampleViewPos(uv-e.yx/reso);
  // float3 vp4=SampleViewPos(uv+e.yx/reso);

  float zedge =
      length(z0 * 2 - float2(z1 + z2, z3 + z4)) * 333 / z0 / EdgeWidth;
  // float
  // zedge=length(vp0.z*2-float2(vp1.z+vp2.z,vp3.z+vp4.z))*333/vp0.z/EdgeWidth;
  // zedge=length(vp0.zz*2-float2(vp1.z+vp2.z,vp3.z+vp4.z));
  float zedge0 = zedge;
  // zedge=max(0,(zedge-DepthEdgeThreshold)*DepthEdgeIntensity/(1.0-DepthEdgeThreshold));
  zedge = max(0, (zedge - DepthEdgeThreshold) * DepthEdgeIntensity);
  zedge = zedge * DepthEdgeIntensity *
          smoothstep(DepthEdgeThreshold * .05, DepthEdgeThreshold, zedge);
  zedge = log2(1 + zedge);
  zedge = zedge * 0.1 / z0;

  // c.rgb=c.rgb/(1.001-c.rgb);
  // c.rgb=Untonemap(c.rgb);

  // c.rgb+=zedge*1.102*EdgeColor*(.3+exp2(4*sin(timer*exp2(-8)+uv.y*3+(z0-1.0)*33))+exp2(4*sin(timer*exp2(-11)+uv.y*.3+(z0-1.0)*2)));
  // c.rgb+=zedge*3*(EdgeColor*EdgeConstantAmt+EdgeWaveAmt*exp2(4*sin(timer*EdgeWaveSpeed*exp2(-9.9)+uv.x*3-(z0-1.0)*17))*lerp(EdgeColor,11,.001*exp2(4*sin(timer*exp2(-8)+uv.y*3+(z0-1.0)*33))+.001*exp2(4*sin(timer*EdgeWaveSpeed*exp2(-11)+uv.y*.3+(z0-1.0)*2))));
  // float
  // wave=exp2(12*(-.9+sin(timer*EdgeWaveSpeed*exp2(-9.9)-EdgeWaveFreq*(uv.x*3-(z0-1.0)*17))));
  // float
  // wave2=exp2(4*(-.9+sin(timer*EdgeWaveSpeed*exp2(-9.9)-EdgeWaveFreq*2*(uv.y*1+uv.x*2+(z0-1.0)*31))));

  // float
  // wave=exp2(12*(-.9+sin(timer*EdgeWaveSpeed*exp2(-9.9)-EdgeWaveFreq*log2(.01+length(vp0-vpc)))));
  float wave = exp2(
      12 *
      (-.9 + sin(timer * EdgeWaveSpeed * exp2(-9.9) -
                 EdgeWaveFreq *
                     dot(EdgeWaveDir, float4(uv.x - .5, uv.y - .5, -vp0.z,
                                             log2(.01 + length(vp0 - vpc)))))));

  // c0=c.rgb*.01/(1.0+c.rgb*.01);
  float v = max(c0.x, max(c0.y, c0.z));
  v = lerp(v, dot(c0.rgb, float3(.333, .59, .11)), .15);
  // c.rgb=hsv2rgb(float3(.66-.66*v,1,pow(v,.5)));

  // c.rgb+=EdgeColor*zedge*EdgeConstantAmt;
  // c.rgb*=lerp(exp2(-zedge*2),1,EdgeConstanMul);

  float zz = ReShade::GetLinearizedDepth(uvq).x;
  zz = pow(zz, 2);
  // zz=lerp(zz,uv.x,.2);
  zz = lerp(zz, uv.y, .12);

  float dth = bayer8(ipq % 8);
  zz = lerp(zz, dth, .01 + .3 * (1 - f) * exp(-(f)*4));
  // if((pingpong.y<0)^ReverseZ)zz=1.0-zz;
  if (ReverseZ) zz = 1.0 - zz;
  float f_a = saturate(f * 2 - 0);
  float f_b = saturate(f * 2 - 1);
  f_a = smoothstep(0, 1, f_a);
  f_b = smoothstep(0, 1, f_b);

  // f=f_a;
  // float fsmooth=smoothstep(0,1,f);
  float f2 = pow((1 - f) * 2 * f, 1);

  // float zd=zz*.99-f;
  float zda = zz * .995 - f_a;
  float zdb = zz * .995 - f_b;

  float3 col_src = Untonemap(c0.rgb);
  float3 col_edge = Untonemap(EdgeColor) *
                    (.02 / (.0001 + abs(zda)) + .02 / (.0001 + abs(zdb))) * f;

  float3 col_grid = Untonemap(EdgeColor) * zedge * EdgeIntensity *
                    (EdgeConstantAmt + wave * EdgeWaveAmt);
  float3 c = 0;
  c += col_src * (zdb < 0);

  c += col_edge * f2;
  c += col_grid * (zda < 0) * (1.0 - f_b) *
       (.5 + .1 / (.001 + abs(zda)) + .1 / (.001 + abs(zdb)));

  // c.rgb+=f2*col_grid;
  // c.rgb+=zedge*EdgeIntensity*(EdgeConstantAmt);
  // c.rgb+=EdgeColor*EdgeWaveAmt*smoothstep(1.0,1.25,zedge0*wave2*8)*23*wave2*(.1+wave);
  // c.rgb=c.rgb/(1.000+c.rgb);
  // c.rgb*=f;
  c.rgb = Tonemap(c.rgb);

  // c.r+=fade()>uv.x;
  if (ip.y == 0 && DebugBar)
    c.rgb = f > uv.x ? float3(1, 0, 0) : float3(0, 1, 0);
  // float f=frac(timer*exp(-7)+1*log2(vp0.z*2+1));
  // c.rgb=float3(1,1,1)*step(f,.5);
  // c.rgb=float3(1,1,1)*.2/abs(f*2-1);
  // c.a=1;
  return float4(c.rgb, 1);
}

technique FadeHolodeck {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace