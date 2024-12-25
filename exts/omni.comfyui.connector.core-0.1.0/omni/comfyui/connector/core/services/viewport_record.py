from omni.services.core import routers

from typing import Optional, Dict
import carb
from pydantic import BaseModel, Field
from fastapi import Response, status

from .. import ext_utils, use_replicator

router = routers.ServiceAPIRouter()


# We will also define a model to handle the delivery of responses back to clients.
#
# Just like the model used to handle incoming requests, the model to deliver responses will not only help define
# default values of response parameters, but also in documenting the values clients can expect using the OpenAPI
# specification format.
class ViewportRecordResponseModel(BaseModel):
    """Model describing the response to the request to capture a viewport as an image."""

    success: bool = Field(
        default=False,
        title="Capture status",
        description="Status of the capture of the given USD stage.",
    )
    output_paths: Optional[Dict[str, str]] = Field(
        default=None,
        title="Output Data",
        description="Path to Viewport recording data on server.",
    )
    details_message: Optional[str] = Field(
        default=None,
        title="Details Message",
        description="Optional message with details about about the operation.",
    )


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
async def viewport_record(response: Response) -> ViewportRecordResponseModel:
    # For now, let's just print incoming request to the log to confirm all components of our extension are properly
    # wired together:
    carb.log_warn("Received a request to record viewport.")
    _output_paths = await use_replicator.run()

    return ViewportRecordResponseModel(success=True, output_paths=_output_paths, details_message="Should be success")
