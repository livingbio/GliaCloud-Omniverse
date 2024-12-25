import omni.replicator.core as rep
from omni.replicator.core.scripts.writers_default.tools import colorize_normals
from omni.kit.viewport.utility import get_active_viewport

import os
import carb
import asyncio
import numpy as np
import torch
import json
import io
import base64

from .ext_utils import get_extension_data_path, get_local_resource_directory, get_full_resource_path, join_with_replace

async def run():

    _viewport = get_active_viewport()
    if not _viewport or _viewport.frame_info.get("viewport_handle", None) is None:
        return

    rep.settings.set_render_pathtraced(samples_per_pixel=64)

    active_camera_path = _viewport.camera_path

    _ext_data_path = get_extension_data_path()
    replicator_data_path = join_with_replace(_ext_data_path, "replicator")

    render_product = rep.create.render_product(active_camera_path, (1920, 1080))

    annotators = {"rgb": None, "distance_to_camera": None, "normals": None}

    backend = rep.BackendDispatch({"paths": {"out_dir": replicator_data_path}})

    for name in annotators.keys():
        anno = rep.AnnotatorRegistry.get_annotator(name)
        anno.attach(render_product)
        annotators[name] = anno

    all_rgb_data = []
    normals_data_list = []

    for frame_id in range(10):
        await rep.orchestrator.step_async()

        rgba_data = annotators["rgb"].get_data()

        backend.write_image("rgb_" + str(frame_id) + ".png", rgba_data)
        rgb_data = rgba_data[:, :, :3]
        rgb_data = rgb_data / 255.0

        all_rgb_data.append(rgb_data)

        normals_data = annotators["normals"].get_data()
        colorized_normals_data = colorize_normals(normals_data)
        normals_data_list.append(colorized_normals_data)

        # backend.write_image("normals_" + str(frame_id) + ".png", colorized_normals_data)

    rep.orchestrator.stop()

    rgb_data_stack = np.stack(all_rgb_data, axis=0)
    carb.log_warn(f'numpy array shape: {rgb_data_stack.shape}, numpy array datatype: {rgb_data_stack.dtype}')
    rgb_data_path = join_with_replace(_ext_data_path, "replicator/rgb.npy")
    carb.log_warn(f'rgb data path: {rgb_data_path}')
    np.save(rgb_data_path, arr=rgb_data_stack, allow_pickle=False)

    carb.log_warn(f"rgb output: {rgb_data_path}")

    return {"rgb": rgb_data_path}
