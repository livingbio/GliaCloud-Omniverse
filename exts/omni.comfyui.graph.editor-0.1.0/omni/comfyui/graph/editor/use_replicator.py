import omni.replicator.core as replicator
from omni.kit.viewport.utility import get_active_viewport

import os
import carb

from .ext_utils import get_extension_data_path

def setup():
    _viewport = get_active_viewport()
    if not _viewport or _viewport.frame_info.get("viewport_handle", None) is None:
        return
    active_camera_path = _viewport.camera_path

    _ext_data_path = get_extension_data_path()
    replicator_data_path = os.path.join(_ext_data_path, "replicator").replace(os.sep, "/")
    carb.log_warn(replicator_data_path)

    with replicator.new_layer():
        render_product = replicator.create.render_product(active_camera_path, (2048, 1024))

        with replicator.trigger.on_frame(max_execs=1):
            pass
        
        # Initialize and attach writer
        writer = replicator.WriterRegistry.get("BasicWriter")
        writer.initialize(
            output_dir=replicator_data_path,
            rgb=True,
            bounding_box_2d_tight=True,
            bounding_box_2d_loose=True,
            semantic_segmentation=True,
            instance_segmentation=True,
            distance_to_camera=True,
            distance_to_image_plane=True,
            bounding_box_3d=True,
            occlusion=True,
            normals=True,
        )

        writer.attach([render_product])

        replicator.orchestrator.run()
