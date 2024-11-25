

#include "ReShade.fxh"

#include ".\MartysMods\mmx_camera.fxh"
#include "DisplayDepth.fx"
// #include "MartysMods_MXAO.fx"


namespace ShadowFX {


// src: https://github.com/daniel-ilett/shaders-sketched/blob/main/Assets/Textures/SketchPattern.png
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

/*

float3 getTextureValue(float2 coords) {

    float depth = ReShade::GetLinearizedDepth(uv);

		coords.x *= float(BUFFER_WIDTH)/BUFFER_HEIGHT;
		if(useDepth) {
			coords *= pow(2.0,depth);
		}
		
		float4 tex = tex2D(shadow_pattern,coords);

	}
  */



float4 PS(float4 vpos : SV_Position, float2 uv : TexCoord) : SV_Target {
  /*
    This pixel shader will use screen space normals and world space/screen space vertex positions
    to imitate object space shadow textures.
  */

  // TODO: parameters
  float2 tile_amount = (1.0, 1.0);
  float3 normal = GetScreenSpaceNormal(uv); // defined this in depth shader
  float3 position = float3(uv - 0.5, 1) * ReShade::GetLinearizedDepth(uv);
  float3 proj = float3(uv, Camera::depth_to_z(ReShade::GetLinearizedDepth(uv)));
  float2x2 rotation = float2x2(1, 0, 0, 1);
  float blend = 10.0;

  // map uv's onto the XY, YZ, XZ planes, respectively
  float2 uvX = mul(rotation, proj.zy * tile_amount);
  float2 uvY = mul(rotation, proj.xz * tile_amount);
  float2 uvZ = mul(rotation, proj.xy * tile_amount);

  // change sign based off direction of normal vector
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

  /* TODO: attempt to use the Triplanar Sampling Function to interpolate between the three colors sampled from the texture.
  (ref: https://catlikecoding.com/unity/tutorials/advanced-rendering/triplanar-mapping/) */
  
  // sample texture 3 times
  float4 colX = tex2D(pattern_sampler, uvX);
	float4 colY = tex2D(pattern_sampler, uvY);
	float4 colZ = tex2D(pattern_sampler, uvZ);

  // calculate the blend factor using the dot product of normal vector
	float3 blending = pow(abs(normal), blend);
	blending /= dot(blending, 1.0f);

  // interpolate colors
  float4 new_texture = saturate(colX * blending.x + colY * blending.y + colZ * blending.z);

  // add w component
  return new_texture;


}

technique Shadow {
  pass {
    VertexShader = PostProcessVS;
    PixelShader = PS;
  }
}
}  // namespace