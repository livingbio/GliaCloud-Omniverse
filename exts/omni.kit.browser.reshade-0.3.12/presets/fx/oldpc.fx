#include "ReShade.fxh"

namespace OldPcFX
{
uniform float BRIGHTNESS < ui_type = "drag";
ui_label = "Brightness";
ui_min = 0;
ui_max = 1;
> = 1.0;
uniform int PALETTE < ui_type = "list";
ui_label = "Color Palette";
ui_items = "PC CGA;B/W Mono;Commodore C64;ZX Spectrum";
> = 1;
uniform int PixelSize < ui_type = "drag";
ui_label = "Downsample Factor";
ui_min = 2;
ui_max = 10;
> = 4;
uniform float DitherFactor < ui_type = "drag";
ui_label = "Dither Factor";
ui_min = 0;
ui_max = 4;
> = .35;
uniform float timer < source = "timer";
> ;

#define modf(x, y) (x - y * floor(x / y))

float bayer2(float2 v)
{
    v = floor(v);
    return frac(v.y * v.y * .75 + v.x * .5);
}
float bayer4(float2 v)
{
    return bayer2(.5 * v) * .25 + bayer2(v);
}
float bayer8(float2 v)
{
    return bayer4(.5 * v) * .25 + bayer2(v);
}
float bayer16(float2 v)
{
    return bayer8(.5 * v) * .25 + bayer2(v);
}
float bayer32(float2 v)
{
    return bayer16(.5 * v) * .25 + bayer2(v);
}
float bayer64(float2 v)
{
    return bayer32(.5 * v) * .25 + bayer2(v);
}
float bayer128(float2 v)
{
    return bayer64(.5 * v) * .25 + bayer2(v);
}

float3 recolor4(float3 color, float3 palette[4])
{
    float3 closestColor = palette[0];
    float closestDistance = distance(color, palette[0]);
    for (int i = 0; i < 4; i++)
    {
        float currentDistance = distance(color, palette[i]);
        if (currentDistance < closestDistance)
        {
            closestDistance = currentDistance;
            closestColor = palette[i];
        }
    }
    return closestColor;
}

float3 recolor8(float3 color, float3 palette[8])
{
    float3 closestColor = palette[0];
    float closestDistance = distance(color, palette[0]);
    for (int i = 0; i < 8; i++)
    {
        float currentDistance = distance(color, palette[i]);
        if (currentDistance < closestDistance)
        {
            closestDistance = currentDistance;
            closestColor = palette[i];
        }
    }
    return closestColor;
}

float3 recolor16(float3 color, float3 palette[16])
{
    float3 closestColor = palette[0];
    float closestDistance = distance(color, palette[0]);

    for (int i = 0; i < 16; i++)
    {
        float currentDistance = distance(color, palette[i]);
        if (currentDistance < closestDistance)
        {
            closestDistance = currentDistance;
            closestColor = palette[i];
        }
    }
    return closestColor;
}

float3 dither(float3 color, float2 fragpos)
{
    color *= BRIGHTNESS;
    // color += (1.05-BRIGHTNESS)*bayer128(float2(modf (fragpos.x, 8.0), modf
    //  (fragpos.y, 8.0))) ;
    color += (bayer128(float2(modf(fragpos.x, 8.0), modf(fragpos.y, 8.0))) - .5) * DitherFactor * pow(color, .2);
    return color;
}

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target
{
    const float3 cga[4] = {float3(1., 1., 1.), float3(0., 1., 1.), float3(1., 0., 1.), float3(0., 0., 0.)};

    const float3 mono[4] = {float3(1., 1., 1.), float3(1., 1., 1.), float3(0., 0., 0.), float3(0., 0., 0.)};

    const float3 zx[8] = {float3(1., 1., 1.), float3(0., 0., 0.), float3(1., 0., 0.),
                          float3(0., 1., 0.), float3(0., 0., 1.), float3(1., 1., 0.),
                          float3(0., 1., 1.), float3(1., 0., 1.)

    };

    const float3 c64[16] = {
        float3(0, 0, 0),          float3(1, 1, 1),          float3(0.41, 0.22, 0.17), float3(0.44, 0.64, 0.70),
        float3(0.44, 0.24, 0.53), float3(0.35, 0.55, 0.26), float3(0.21, 0.16, 0.47), float3(0.72, 0.78, 0.44),
        float3(0.44, 0.31, 0.15), float3(0.26, 0.22, 0),    float3(0.60, 0.40, 0.35), float3(0.27, 0.27, 0.27),
        float3(0.42, 0.42, 0.42), float3(0.60, 0.82, 0.52), float3(0.42, 0.37, 0.71), float3(0.58, 0.58, 0.58)};

    float4 c = tex2D(ReShade::BackBuffer, uv);
    float2 reso = BUFFER_SCREEN_SIZE;
    int2 ip = int2(uv * reso);
    int2 px = PixelSize; //*int2(2,1);
    c = tex2D(ReShade::BackBuffer, ((ip / px) * px + 0.5) / reso);
    // c.rgb=dither(c.rgb,uv*reso);
    c.rgb = dither(c.rgb, ip / px);
    switch (PALETTE)
    {
    case 0:
        c.rgb = recolor4(c.rgb, cga);
        break;
    case 1:
        c.rgb = recolor4(c.rgb, mono);
        break;
    case 2:
        c.rgb = recolor16(c.rgb, c64);
        break;
    case 3:
        c.rgb = recolor8(c.rgb, zx);
        break;

    default:
        c.rgb = recolor4(c.rgb, cga);
        break;
    }

    return c;
}

technique OldPC
{
    pass
    {
        VertexShader = PostProcessVS;
        PixelShader = PS;
    }
}
}//namespace