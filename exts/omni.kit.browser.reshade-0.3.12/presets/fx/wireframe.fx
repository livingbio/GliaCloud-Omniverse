#include "ReShade.fxh"

namespace WireframeFX {
    
uniform float EdgeWidth = 1.0;
uniform float EdgeConstanMul = 0.50;
uniform float EdgeConstantAmt = .25;
uniform float EdgeWaveAmt = 0.5;
uniform float EdgeWaveFreq = 1.0;
uniform float EdgeWaveSpeed = 1.0;
uniform float4 EdgeWaveDir = float4(0, 0, 0.2, 1);
uniform float3 EdgeColor = float3(.463, .725, 0.0);
uniform float EdgeIntensity = 1;
uniform float DepthEdgeIntensity = 10.0;
uniform float DepthEdgeThreshold = 0.000125;

uniform float timer < source = "timer";
> ;

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
  float4 c = tex2D(ReShade::BackBuffer, uv);
  float3 c0 = tex2D(ReShade::BackBuffer, uv).rgb;
  float2 e = float2(EdgeWidth, 0.0);
  float2 reso = BUFFER_SCREEN_SIZE;
  float z0 = ReShade::GetLinearizedDepth(uv).x;
  float z1 = ReShade::GetLinearizedDepth(uv - e.xy / reso).x;
  float z2 = ReShade::GetLinearizedDepth(uv + e.xy / reso).x;
  float z3 = ReShade::GetLinearizedDepth(uv - e.yx / reso).x;
  float z4 = ReShade::GetLinearizedDepth(uv + e.yx / reso).x;
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
  c.rgb = Untonemap(c.rgb);
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
  c.rgb *= lerp(exp2(-zedge * 2), 1, EdgeConstanMul);

  c.rgb += Untonemap(EdgeColor) * zedge * EdgeIntensity *
           (EdgeConstantAmt + wave * EdgeWaveAmt);
  // c.rgb+=zedge*EdgeIntensity*(EdgeConstantAmt);
  // c.rgb+=EdgeColor*EdgeWaveAmt*smoothstep(1.0,1.25,zedge0*wave2*8)*23*wave2*(.1+wave);
  // c.rgb=c.rgb/(1.000+c.rgb);

  c.rgb = Tonemap(c.rgb);
  // float f=frac(timer*exp(-7)+1*log2(vp0.z*2+1));
  // c.rgb=float3(1,1,1)*step(f,.5);
  // c.rgb=float3(1,1,1)*.2/abs(f*2-1);
  c.a = 1;
  return c;
}

technique Wireframe {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace