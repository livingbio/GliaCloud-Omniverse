from omni.services.core import routers

from typing import Optional
import carb
from pydantic import BaseModel, Field
from fastapi import Response, status

from .. import ext_utils

router = routers.ServiceAPIRouter()


# We will also define a model to handle the delivery of responses back to clients.
#
# Just like the model used to handle incoming requests, the model to deliver responses will not only help define
# default values of response parameters, but also in documenting the values clients can expect using the OpenAPI
# specification format.
class ViewportCaptureResponseModel(BaseModel):
    """Model describing the response to the request to capture a viewport as an image."""

    success: bool = Field(
        default=False,
        title="Capture status",
        description="Status of the capture of the given USD stage.",
    )
    output_url_path: Optional[str] = Field(
        default=None,
        title="Output URL Path",
        description="The URL path where the captured image will be served from",
    )
    details_message: Optional[str] = Field(
        default=None,
        title="Details Message",
        description="Optional message with details about about the operation.",
    )


# Using the `@router` annotation, we'll tag our `capture` function handler to document the responses and path of the
# API, once again using the OpenAPI specification format.
@router.get(
    path="/simple-capture",
    summary="Capture a given USD stage",
    description="Capture a given USD stage as an image.",
    response_model=ViewportCaptureResponseModel,
    tags=["Viewport"],
    responses={200: {"model": ViewportCaptureResponseModel}, 400: {"model": ViewportCaptureResponseModel}},
)
async def simple_capture(response: Response) -> ViewportCaptureResponseModel:
    # For now, let's just print incoming request to the log to confirm all components of our extension are properly
    # wired together:
    carb.log_warn("Received a request to capture viewport screenshot")
    _success, _output_url_path, _details_message = await ext_utils.capture_viewport(response)

    return ViewportCaptureResponseModel(
        success=_success, output_url_path=_output_url_path, details_message=_details_message
    )
