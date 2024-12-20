import omni.replicator.core as rep
from omni.replicator.core.scripts.writers_default.tools import colorize_normals
from omni.kit.viewport.utility import get_active_viewport

import os
import carb
import asyncio
import numpy as np
import torch

from .ext_utils import get_extension_data_path

async def run():

    _viewport = get_active_viewport()
    if not _viewport or _viewport.frame_info.get("viewport_handle", None) is None:
        return

    rep.settings.set_render_rtx_realtime()

    active_camera_path = _viewport.camera_path

    _ext_data_path = get_extension_data_path()
    replicator_data_path = os.path.join(_ext_data_path, "replicator3").replace(os.sep, "/")
    carb.log_warn(replicator_data_path)

    render_product = rep.create.render_product(active_camera_path, (1920, 1080))

    annotators = {"rgb": None, "distance_to_camera": None, "normals": None}

    backend = rep.BackendDispatch({"paths": {"out_dir": replicator_data_path}})

    for name in annotators.keys():
        anno = rep.AnnotatorRegistry.get_annotator(name)
        anno.attach(render_product)
        annotators[name] = anno

    rgb_data_list = []
    normals_data_list = []

    for frame_id in range(60):
        await rep.orchestrator.step_async()

        rgb_data = annotators["rgb"].get_data()
        rgb_data_list.append(rgb_data)

        backend.write_image("rgb_" + str(frame_id) + ".png", rgb_data)

        normals_data = annotators["normals"].get_data()
        colorized_normals_data = colorize_normals(normals_data)
        normals_data_list.append(colorized_normals_data)

        # backend.write_image("normals_" + str(frame_id) + ".png", colorized_normals_data)

        backend.wait_until_done()

    rep.orchestrator.stop()

    rgb_data_stack = np.stack(rgb_data_list, axis=0)

    rgb_tensor = torch.tensor(rgb_data_stack)

    carb.log_warn(rgb_tensor.shape)
    carb.log_warn(rgb_tensor.dtype)

def setup():
    asyncio.ensure_future(run())
