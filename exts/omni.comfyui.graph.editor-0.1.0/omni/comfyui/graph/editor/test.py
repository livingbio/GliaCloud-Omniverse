import asyncio
import carb
from omni.services.client import AsyncClient
from omni.services.core import main
from omni.comfyui.graph.editor.services.viewport_capture import ViewportCaptureRequestModel

def get_current_viewport():
    async def wrapper():

        async def call_endpoint():
            # call viewport-capture endpoint
            client = AsyncClient(uri="local://", app=main.get_app())
            request = ViewportCaptureRequestModel(
                usd_stage_path="omniverse://nucleus.githubhero.com/Projects/Assets/coffee_table_1.usd"
            )
            response = await client.capture.post(request.dict())
            return response

        try:
            value = await call_endpoint()
            carb.log_warn(value)
        except Exception as e:
            carb.log_warn(f'Error Message: {e}')

    asyncio.run(wrapper())
