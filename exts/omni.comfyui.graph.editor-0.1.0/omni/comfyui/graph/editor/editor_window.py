# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
__all__ = ["GraphWindow"]

from .graph_widget import GraphWidget
import omni.ui as ui
import omni.kit.app
import asyncio

class GraphWindow(ui.Window):
    """The Graph window"""
    title = "ComfyUI Graph Editor"

    def __init__(self, **kwargs):
        flags = kwargs.pop("flags", 0) | ui.WINDOW_FLAGS_NO_SCROLLBAR
        if hasattr(ui, "WINDOW_FLAGS_NO_SCROLL_WITH_MOUSE"):
            # Compatibility with old omni.ui
            flags = flags | ui.WINDOW_FLAGS_NO_SCROLL_WITH_MOUSE

        self._main_widget = None
        super().__init__(GraphWindow.title, flags=flags, **kwargs)

        self.frame.set_build_fn(self.on_build_window)

        self.deferred_dock_in("Viewport")
        # make sure the window is docked when viewport doesn't exist
        self._build_task = asyncio.ensure_future(self.__dock_window())

    @staticmethod
    async def __dock_window():
        await omni.kit.app.get_app().next_update_async()
        viewport = ui.Workspace.get_window("Viewport")
        if not viewport:
            window_handle = ui.Workspace.get_window(GraphWindow.title)
            main_dockspace = ui.Workspace.get_window("DockSpace")
            window_handle.dock_in(main_dockspace, ui.DockPosition.BOTTOM)

    def destroy(self):
        if self._main_widget:
            self._main_widget.destroy()
        self._main_widget = None

        super().destroy()

    def on_build_window(self):
        self._main_widget = GraphWidget()
