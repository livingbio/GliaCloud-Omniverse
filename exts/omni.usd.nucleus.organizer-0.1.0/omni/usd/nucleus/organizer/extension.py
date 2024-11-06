import omni.ext
import omni.ui as ui

import asyncio

import omni.kit.asset_converter as converter

def progress_callback(current_step: int, total: int):
    # Show progress
    print(f"{current_step} of {total}")

async def convert(input_asset_path, output_asset_path):
    task_manager = omni.kit.asset_converter.get_instance()
    task = task_manager.create_converter_task(input_asset_path, output_asset_path, progress_callback)
    success = await task.wait_until_finished()
    if not success:
        detailed_status_code = task.get_status()
        detailed_status_error_string = task.get_error_message()
        ...

...



# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print(f"[omni.hello.world] some_public_function was called with {x}")
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[omni.hello.world] MyExtension startup")

        self._count = 0

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")

                # style=Styles.BROWSE_BTN,
                # name="browse",
                # width=20,
                # tooltip="Browse..." if get_file_importer() is not None else "File importer not available",
                # clicked_fn=lambda model_weak=weakref.ref(model), stage_weak=weakref.ref(stage), layer_weak=weakref.ref(
                #     layer
                # ) if layer else None: show_asset_file_picker(
                #     "Select Payload..." if use_payloads else "Select Reference...",
                #     assign_value_fn,
                #     model_weak,
                #     stage_weak,
                #     layer_weak=layer_weak,
                #     on_selected_fn=assign_reference_value,
                # ),
                # enabled=get_file_importer() is not None,
                # visible=not is_live and not in_session,

                input_path = "tests/simple_sphere.obj"
                output_path = "tests/simple_sphere.usd"
                
                ui.Button("Import", clicked_fn=asyncio.ensure_future(convert(input_path, output_path)))

                def on_click():
                    self._count += 1
                    label.text = f"count: {self._count}"

                def on_reset():
                    self._count = 0
                    label.text = "empty"

                on_reset()

                with ui.HStack():
                    ui.Button("Add", clicked_fn=on_click)
                    ui.Button("Reset", clicked_fn=on_reset)

    def on_shutdown(self):
        print("[omni.hello.world] MyExtension shutdown")
