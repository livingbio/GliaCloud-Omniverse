uniform float3 fill_color <
	ui_type = "color";
	ui_label = "Fill Color";
> = float3(1.0, 0.0, 0.0);

void PostProcessVS(in uint id : SV_VertexID, out float4 position : SV_Position)
{
	float2 texcoord;
	texcoord.x = (id == 2) ? 2.0 : 0.0;
	texcoord.y = (id == 1) ? 2.0 : 0.0;
	position = float4(texcoord * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
}

float4 FillPass(float4 vpos : SV_Position) : SV_Target
{
	return float4(fill_color, 1.0);
}

technique simple
{
	pass
	{
		VertexShader = PostProcessVS;
		PixelShader = FillPass;
	}
}
