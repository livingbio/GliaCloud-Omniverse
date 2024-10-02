# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.ext
import omni.kit.ui
from .reshade_window import ReshadeWindow

MENU_PATH = "Window/ReShade Editor"

class ReshadeWindowExtension(omni.ext.IExt):
    def on_startup(self):
        self._window = None

        try:
            self._menu = omni.kit.ui.get_editor_menu().add_item(
                MENU_PATH, lambda m, v: self.show_window(v), toggle=True, value=False
            )
        except:
            pass

    def on_shutdown(self):
        self._menu = None

    def show_window(self, value):
        if value:
            def on_visibility_changed(visible):
                omni.kit.ui.get_editor_menu().set_value(MENU_PATH, visible)

            self._window = ReshadeWindow(on_visibility_changed if self._menu else None)
        else:
            if self._window:
                self._window.destroy()
                self._window = None
