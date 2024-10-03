#include "ReShade.fxh"

#include ".\MartysMods\mmx_camera.fxh"
#include "DisplayDepth.fx"


namespace ShadowFX {

texture2D pattern_texture < source = "shadow_pattern.png";
> 
{
  Width = BUFFER_WIDTH; 
  Height = BUFFER_HEIGHT; 
  Format = RGBA8; 
};

sampler2D pattern_sampler
{
  Texture = pattern_texture;
};

float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {

  float2 tile_amount = (1.0, 1.0);

  float3 normal = GetScreenSpaceNormal(uv);

  float3 proj = Camera::uv_to_proj(uv);

  float2x2 rotation = float2x2(1, 0, 0, 1);

  float blend = 10.0;

  float2 uvX = mul(rotation, proj.zy * tile_amount);
  float2 uvY = mul(rotation, proj.xz * tile_amount);
  float2 uvZ = mul(rotation, proj.xy * tile_amount);

  if (normal.x < 0)
  {
    uvX.x = -uvX.x;
  }

  if (normal.y < 0)
  {
    uvY.x = -uvY.x;
  }

  if (normal.z >= 0)
  {
    uvZ.x = -uvZ.x;
  }

  float4 colX = tex2D(pattern_sampler, uvX);
	float4 colY = tex2D(pattern_sampler, uvY);
	float4 colZ = tex2D(pattern_sampler, uvZ);

	float3 blending = pow(abs(normal), blend);
	blending /= dot(blending, 1.0f);

  float4 new_texture = saturate(colX * blending.x + colY * blending.y + colZ * blending.z);

  new_texture *= float4(0, 0, 0, 1);

  return new_texture;
}

technique Shadow {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace