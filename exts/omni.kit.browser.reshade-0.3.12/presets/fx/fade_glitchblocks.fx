#include "ReShade.fxh"

namespace FadeGlitchBlocksFX {

// uniform float GlitchIntensity = 3.25;
// uniform float GlitchScale =.80;
uniform float GlitchSpeed = 1.0;
uniform float GlitchWave = .50;
uniform float GlitchWaveSpeed = 1.40;
uniform float EdgeWidth = .30;

uniform float timer < source = "timer";
> ;

uniform int DebugBarSize = -1;
uniform float2 pingpong < source = "pingpong";
min = 0;
max = 360;
step = 0.05;
smoothing = 0.0;
> ;

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

float FADER_LERP(float a, float b, float offset) {
  float f = fade();
  // return exp(lerp(log(a),log(b),f));
  return lerp(a, b, f);
}
float FADER_EXPLERP(float a, float b, float offset) {
  float f = fade();
  // float f=1-abs(frac(x)*2-1);
  // f=saturate((f-.5)*2+.5);
  return exp(lerp(log(a), log(b), f));
  // return lerp(a,b,f);
}
float FADER_SMOOTHLERP(float a, float b, float offset) {
  float f = fade();
  f = smoothstep(0, 1, f);
  return lerp(a, b, f);
}
float FADER_STEP(float a, float b, float offset) {
  float f = fade();
  return exp(floor(lerp(log(a), log(b), f)));
  // return lerp(a,b,f);
}

#define GlitchScale (FADER_STEP(1.81, .2, 0))
// #define GlitchIntensity (1.01)
#define GlitchIntensity (FADER_EXPLERP(.001, 333.1, 0))

float2 r2d(float2 x, float a) {
  a *= acos(-1) * 2;
  return float2(cos(a) * x.x + sin(a) * x.y, cos(a) * x.y - sin(a) * x.x);
}

float2 noise2d(int2 xy, int seed) {
  int3 c = int3(xy + (xy >= 0), seed);
  int r = int(0xf6a47f78 * c.x * c.x + c.y) *
          int(0x82f88c81 * c.y * c.y + c.x) *
          int(0x964cb8a1 * c.z * c.z + c.y) * int(0xafc35eb8 * c.y * c.x + c.z);
  int2 r2 = int2(0xebfd9f9a, 0x93b7c155) * r;
  return (r2 % 358934592) * .5 / 358934592. + 0.5;
}
float4 readtex(float2 uv) { return tex2D(ReShade::BackBuffer, uv); }

#define glichtime (timer * exp2(-3.70) * GlitchSpeed)
#define reso float2(BUFFER_SCREEN_SIZE)
#define asp float2(1.0, float(BUFFER_HEIGHT) / float(BUFFER_WIDTH))
float bayer2(float2 v) {
  v = floor(v);
  return frac(v.y * v.y * .75 + v.x * .5);
}
float bayer4(float2 v) { return bayer2(.5 * v) * .25 + bayer2(v); }
float bayer8(float2 v) { return bayer4(.5 * v) * .25 + bayer2(v); }
float bayer16(float2 v) { return bayer8(.5 * v) * .25 + bayer2(v); }
float bayer32(float2 v) { return bayer16(.5 * v) * .25 + bayer2(v); }
float4 glicthlayer(float2 uv, float time_offset, float Displace, float2 scale) {
  float4 c = tex2D(ReShade::BackBuffer, uv);

  // float2 reso=BUFFER_SCREEN_SIZE;
  // float2 asp=float2(1.0,float(BUFFER_HEIGHT)/float(BUFFER_WIDTH));
  float dth = bayer16(int2(round(uv * reso - 0.5)) % 16);
  float tt0 = glichtime * exp2(-5.3) + time_offset;
  float tf0 = frac(tt0);
  int ti0 = floor(tt0);
  float2 gd = uv - .5;
  gd.y *= 1;
  gd *= scale;

  //  gd=r2d(gd*asp,.125)/asp;
  gd += (noise2d(floor(gd * .01 * asp + .7), 1 + ti0) - .5) * 1.5;
  gd *= exp2((noise2d(floor(gd * 2 * asp), 7 + ti0) - .5) * 3.15);

  //  gd.xy*=exp2((tf0-.5)*.06*exp2((noise2d(floor(gd*2*asp),7+ti0)-.5)*3).x);
  gd += (noise2d(floor(gd * 2 * asp + .3), 5 + ti0) - .5) * 0.15;
  gd *= exp2((noise2d(floor(gd * 4 * asp), 2 + ti0) - .5) * 3.15);
  gd += (noise2d(floor(gd * 7 * asp + .8), 8 + ti0) - .5) * 0.205;

  gd += (noise2d(floor(gd * 5 * asp + .1), 9 + ti0) - .5) * 0.05;

  //  gd-=(uv-.5)*1.2*exp2((noise2d(floor(gd*5*asp),16+ti0)-.5)*0.05);
  gd -= uv - .5;
  gd.x += floor(gd.y * 16.13) * 1.61;
  //  gd*=0;
  uv += gd;
  int2 ip = round(uv * reso - 0.5);

  //  int2 gs=8;
  //  float div=8;
  float2 gp = uv * 2 * asp;
  float tt = glichtime * exp2(-4) + frac(gd.y * 3.1340) * .3 + time_offset;
  //  tt=3;
  int ti = floor(tt);
  float tf = frac(tt);

  float2 v = noise2d(gp * 1, 6 + ti);
  float2 v2 = noise2d(gp * 2, 16 + ti);
  float2 v3 = noise2d(gp * 3, 13 + ti);
  float2 v4 = noise2d(gp * 4, 11 + ti);
  float2 v5 = noise2d(gp * 5, 17 + ti);
  float2 v6 = noise2d(gp * 1.5, 19 + ti);
  float2 vd = noise2d(gp.yx * 4, 2 + ti);
  // uv+=(vd-0.5)*0.1*Displace;
  uv += r2d(float2(vd.x * exp2((vd.x - 1) * 6), 0), vd.y) * 0.5 * Displace;
  float2 v7 = noise2d(gp.yx * 1.5, 3 + ti);
  float2 v8 = noise2d(gp.yx * 1.35, 2 + ti);
  float2 v9 = noise2d(gp.yx * 1.85 + 3, 10 + ti);
  //  c=c.x;
  float2 offset = ((v - .5) + (v2 - .5) * .1) * Displace * asp;
  //  offset*=(saturate(tf0*2)>v3.x)*(saturate(2-tf0*2)>v3.y);
  //  offset/=tf0;
  float2 xr = exp2((v5.x - .5) * .4);
  float2 xb = exp2((v5.y - .5) * .4);
  float2 xg = exp2((v5.y - .5) * .4);
  float rgbt =
      tf0 * 2 - (v4.x - .5) +
      .71 * (frac(length(sin(floor(gp * 3 * exp2(7 * (v4.y - .5)))))) - .5);
  rgbt += (frac(dth + .3) - .5) * 33;
  xr = saturate(rgbt * 2 - .2);
  xg = saturate(rgbt * 2 - .5);
  xb = saturate(rgbt * 2 - .8);
  float3 xv = .5 +
              .5 * sin((tt0 * exp2((v8.x - .5) * 5) +
                        12.1 * exp2(-v8.y) * float3(-1, 0, 1) / 3) *
                       acos(-1) * 2);
  xv *= xv > v7.x;
  xr = xv.x;
  xg = xv.y;
  xb = xv.z;
  //  xr=xg=xb=1;
  offset *= exp2((v6.yx - .65) * 2);  // *.2+1.21*Displace;
                                      //  offset*=length(uv0.xy-.5)*2;
  c = readtex(uv - gd + offset * xg);
  c.r = readtex(uv - gd + offset * xr).r;
  c.b = readtex(uv - gd + offset * xb).b;

  float2 e = float2(11 * exp2((v8.x - .5) * 2), 0);
  float4 c0 = readtex(uv - gd + offset * xg);
  float z0 = ReShade::GetLinearizedDepth(uv - gd + offset * xg).x;

  float4 cx1 = readtex(uv - gd + offset * xg + e.xy / reso);
  float4 cx2 = readtex(uv - gd + offset * xg - e.xy / reso);

  float4 cy1 = readtex(uv - gd + offset * xg + e.yx / reso);
  float4 cy2 = readtex(uv - gd + offset * xg - e.yx / reso);
  //  c+=(c10-c00)*4;

  c += ((c0 - cx1) + (c0 - cx2) + (c0 - cy1) + (c0 - cy2)) *
       exp2((v8.y - .5) * 6) * 2.40 / pow(e.x + .2, 1.) *
       sqrt(length(offset) * 3);
  c = pow(max(0, c * 1.), exp2((v9.x - .5) * .3 * sqrt(length(offset * xg)) *
                               38 * dot(frac(gp.xy * 3) - .5, v8.yx)));
  float4 cedge = max(abs(c0 - cx1), abs(c0 - cy2));
  //  c.rgb=frac(v4.y*8)<.29?c.rgb:(cedge.rgb*13/(1+cedge*13))*(length((frac((uv-gd)*188*asp)-.5))<.4);
  float pd = length((frac((uv - gd) * 188 * asp * exp2((v3.x - .5) * 2)) - .5));
  float3 pc = (c.rgb > .5) * .35 / (.000302 + pd);
  pc = pc / (1 + pc);

  c.a = z0;
  c.a = .1 / (1.01 - 1.0 / z0);

  // c.a*=exp2((dth-0.5)*0.1);

  return c;
}

float3 GetViewPos(float2 sp, float z) {
  float d = .1 / (1.0 - 1.0 / z);
  float4 p = float4(sp * d, d, 1);
  return p.xyz;
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  int2 ip = round(uv * reso - 0.5);
  float4 c = tex2D(ReShade::BackBuffer, uv);

  float2 uvc = float2(0.5, 0.5);

  float sz = .5;
  float z0 = ReShade::GetLinearizedDepth(uv).x;
  float zc = ReShade::GetLinearizedDepth(uvc).x;

  float3 vp = GetViewPos((uv * 2 - 1) * asp * sz, z0);
  float3 vpc = GetViewPos((uvc * 2 - 1) * asp * sz, zc);
  // if(z0>.99){vp=-normalize(vp)*0.003;z0=.003;}
  // if(zc>.99){vpc=-normalize(vpc)*0.003;zc=.003;}
  float2 e = float2(1, 0);
  float z1 = ReShade::GetLinearizedDepth(uv - e.xy / reso).x;
  float z2 = ReShade::GetLinearizedDepth(uv + e.xy / reso).x;
  float z3 = ReShade::GetLinearizedDepth(uv - e.yx / reso).x;
  float z4 = ReShade::GetLinearizedDepth(uv + e.yx / reso).x;
  float3 vp1 = GetViewPos(((uv - e.xy / reso) * 2 - 1) * asp * sz, z1);
  float3 vp2 = GetViewPos(((uv + e.xy / reso) * 2 - 1) * asp * sz, z2);
  float3 vp3 = GetViewPos(((uv - e.yx / reso) * 2 - 1) * asp * sz, z3);
  float3 vp4 = GetViewPos(((uv + e.yx / reso) * 2 - 1) * asp * sz, z4);
  float3 vn = normalize(cross(vp - vp1, vp - vp3));
  // if(z0>.99){vn=-normalize(vp);vp=-vn*0.003;z0=.003;}
  if (max(max(z3, z4), max(z1, z2)) > .99) {
    vp = -normalize(vp) * 0.003;
    z0 = .003;
    vn = 1;
  }

  if (zc > .99) {
    vpc = -normalize(vpc) * 0.003;
    zc = .003;
    vn = 1;
  }

  // vn=1;
  // vp=1;
  // float disp=Displace*exp2(-2.1/length((uv.xy*2-1)*asp))*8;
  // float fd=length(vp-vpc);
  // fd=clamp(1,10,fd);
  float fd = length(vp - vpc);
  fd = max(0.01, fd);
  float focus = exp2(-.006 / fd);
  focus = 1 - focus;
  focus = smoothstep(.002, .03, fd);
  float disp = GlitchIntensity;
  disp *= exp2(GlitchWave *
               (cos(timer * GlitchWaveSpeed * exp2(-9.39) - fd * 18 * 0 -
                    r2d(vn.xy, 1 * timer * GlitchWaveSpeed * exp2(-11.5)).x +
                    r2d(uv - .5, timer * GlitchWaveSpeed * exp2(-13.4)).y * 3) -
                1) *
               3);
  // disp*=exp2((cos(glichtime*exp2(-6.9)-log2(fd+.01)*.6)-1)*3);
  // disp*=exp2((cos(floor(glichtime*exp2(-2.9))*.618*acos(-1)*2+uv.x*4+log2(fd+.001)*.23)-.135)*1);
  // disp*=1-exp2((-fd*5-fd*fd*50)*.1);
  // disp=disp*(.01+focus);
  // disp*=exp2((frac(8*length(cos(floor(vp*43+.3))))-.5)*16);

  float dth = bayer16(int2(round(uv * reso - 0.5)) % 16);
  float time_offset = .15 * (dth - .5) * 5;
  float gscale = GlitchScale * exp2(.2 * floor(log2(fd * 110) * .5) / .5);
  float4 c0 = glicthlayer(uv, time_offset * .12 + 0.0, disp * 1,
                          gscale * 4 * float2(.37, 3));
  float4 c1 = glicthlayer(uv, time_offset * .3 + 5.678, disp * 1,
                          gscale * 1 * float2(1, 1));

  // float4 c2=glicthlayer(uv,7.678,disp,4*float2(1,1));
  c = c0;
  c = c1.a < c.a ? c1 : c;
  float f = fade();
  // c.rgb*=frac(.1/(.001+z0)+.03)>f*f;
  c = pow(max(0, c) * exp2(-pow(f, 12) * 32) * (1 - pow(f, 4)),
          exp2(pow(f, 8) * 4));

  c.a = 1;

  return c;
}

technique FadeGlitchBlocks {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace