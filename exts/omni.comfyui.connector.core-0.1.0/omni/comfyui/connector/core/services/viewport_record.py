from omni.services.core import routers

import carb
from fastapi import Response

from ..use_replicator import run
from ..models.viewport_models import ViewportRecordRequestModel, ViewportRecordResponseModel

router = routers.ServiceAPIRouter()

# Using the `@router` annotation, we'll tag our `capture` function handler to document the responses and path of the
# API, once again using the OpenAPI specification format.
@router.get(
    path="/viewport-record",
    summary="Record a given USD stage",
    description="Record a given USD stage and output data in json format.",
    response_model=ViewportRecordResponseModel,
    tags=["Viewport"],
    responses={200: {"model": ViewportRecordResponseModel}, 400: {"model": ViewportRecordResponseModel}},
)
async def viewport_record(request: ViewportRecordRequestModel, response: Response) -> ViewportRecordResponseModel:
    carb.log_warn("Received a request to record viewport.")
    response_model: ViewportRecordResponseModel = await run(request)

    if response_model.success:
        response.status_code = 200
    else:
        response.status_code = 400

    return response_model
