# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.ui as ui
import rtx.reshade
from typing import Callable

reshade = rtx.reshade.acquire_reshade_interface()


class ComboListItem(ui.AbstractItem):
    def __init__(self, text):
        super().__init__()
        self.model = ui.SimpleStringModel(text)

class ComboListModel(ui.AbstractItemModel):
    def __init__(self, parent_model, items):
        super().__init__()
        self._current_index = parent_model
        self._current_index.add_value_changed_fn(lambda a: self._item_changed(None))
        self._items = [ComboListItem(item) for item in items]

    def get_item_children(self, item):
        return self._items

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model


class ReshadeUniformValue(ui.AbstractItem, ui.AbstractValueModel):
    def __init__(self, handle, component: int, reshade_ctx):
        ui.AbstractItem.__init__(self)
        ui.AbstractValueModel.__init__(self)
        self._handle = handle
        self._component = component
        self._reshade_ctx = reshade_ctx

    def get_value_as_int(self) -> int:
        return reshade.get_uniform_value_as_int(self._reshade_ctx, self._handle, self._component)
    def get_value_as_bool(self) -> bool:
        return reshade.get_uniform_value_as_bool(self._reshade_ctx, self._handle, self._component)
    def get_value_as_float(self) -> float:
        return reshade.get_uniform_value_as_float(self._reshade_ctx, self._handle, self._component)

    def set_value(self, value):
        if isinstance(value, int):
            reshade.set_uniform_value_as_int(self._reshade_ctx, self._handle, self._component, value)
        else:
            reshade.set_uniform_value_as_float(self._reshade_ctx, self._handle, self._component, float(value))
        self._value_changed()

class ReshadeUniformVectorValue(ui.AbstractItemModel):
    def __init__(self, handle, component_count: int, reshade_ctx):
        super().__init__()
        self._items = [ ReshadeUniformValue(handle, component, reshade_ctx) for component in range(component_count) ]
        for item in self._items:
            item.add_value_changed_fn(lambda a, item=item: self._item_changed(item))

    def get_item_children(self, item):
        return self._items

    def get_item_value_model(self, item, column_id):
        return item

    def begin_edit(self, item):
        pass # Crashes without this
    def end_edit(self, item):
        pass # Crashes without this


class ReshadeUniformItem(ui.AbstractItem):
    def __init__(self, handle, reshade_ctx):
        super().__init__()

        type_info = reshade.get_uniform_type(handle)
        self._name = reshade.get_uniform_name(handle)
        self._base_type = type_info[0]
        self._components = type_info[1]

        self._ui_type = reshade.get_uniform_annotation_as_string(handle, "ui_type")
        self._ui_label = reshade.get_uniform_annotation_as_string(handle, "ui_label")
        self._ui_tooltip = reshade.get_uniform_annotation_as_string(handle, "ui_tooltip")

        ui_min = reshade.get_uniform_annotation_as_float(handle, "ui_min")
        ui_max = reshade.get_uniform_annotation_as_float(handle, "ui_max")
        if (ui_min == ui_max):
            self._ui_min = 0
            self._ui_max = 1
        else:
            self._ui_min = ui_min
            self._ui_max = ui_max

        self._ui_step = reshade.get_uniform_annotation_as_float(handle, "ui_step")

        ui_items = reshade.get_uniform_annotation_as_string(handle, "ui_items")
        self._ui_items = ui_items.split(';') if ui_items else []
        if self._ui_items and not self._ui_items[-1]: # Delete last item if empty
            del self._ui_items[-1]

        self.model = ReshadeUniformValue(handle, 0, reshade_ctx) if self._components == 1 else ReshadeUniformVectorValue(handle, self._components, reshade_ctx)


class ReshadeEffectListItem(ui.AbstractItem):
    def __init__(self, effect, reshade_ctx):
        super().__init__()
        self._name = reshade.get_effect_name(effect)
        self._uniforms = []
        for handle in reshade.get_uniform_list(reshade_ctx, effect):
            if reshade.get_uniform_annotation_as_string(handle, "source"):
                continue # Skip uniforms that have a custom source
            self._uniforms.append(ReshadeUniformItem(handle, reshade_ctx))


class ReshadeVariableEditorModel(ui.AbstractItemModel):
    def __init__(self, reshade_ctx):
        super().__init__()
        self._effects = []
        for handle in reshade.get_effect_list(reshade_ctx):
            effect = ReshadeEffectListItem(handle, reshade_ctx)
            if not effect._uniforms:
                continue # Skip effects that have not configurable uniforms
            self._effects.append(effect)

    def get_item_children(self, item):
        if item is None:
            return self._effects
        elif isinstance(item, ReshadeEffectListItem):
            return item._uniforms

    def get_item_value_model(self, item, column_id):
        if item is None:
            return None
        else:
            return item.model

    def get_item_value_model_count(self, item):
        return 1

class ReshadeVariableEditorDelegate(ui.AbstractItemDelegate):
    def build_branch(self, model, item, column_id, level, expanded):
        with ui.HStack(width=20*level, height=0):
            if level == 0:
                triangle_alignment = ui.Alignment.RIGHT_CENTER
                if expanded:
                    triangle_alignment = ui.Alignment.CENTER_BOTTOM
                ui.Spacer(width=3)
                ui.Triangle(alignment=triangle_alignment, width=10, height=10, style={"background_color": 0xFFFFFFFF})
                ui.Spacer(width=7)
            else:
                ui.Spacer()

    def build_widget(self, model, item, column_id, level, expanded):
        with ui.VStack():
            ui.Spacer(height=2.5)
            if level == 1: # Effect list level
                ui.Label(item._name)
            else: # Uniform list level
                with ui.HStack(width=500, spacing=5):
                    if item._base_type == 1:
                        self.create_bool_widget(item)
                    elif item._base_type >= 2 and item._base_type <= 5:
                        self.create_int_widget(item)
                    elif item._base_type >= 6 and item._base_type <= 7:
                        self.create_float_widget(item)
                    else:
                        return

                    label = ui.Label(item._ui_label if item._ui_label else item._name)
                    if item._ui_tooltip:
                        label.set_tooltip(item._ui_tooltip)
            ui.Spacer(height=2.5)

    def create_bool_widget(self, uniform):
        if uniform._components != 1:
            return
        if uniform._ui_type == "combo":
            return ui.ComboBox(ComboListModel(uniform.model, ["False", "True"]))
        else:
            return ui.CheckBox(uniform.model)

    def create_int_widget(self, uniform):
        if uniform._components == 1:
            return self.create_int_widget_scalar(uniform)
        else:
            return self.create_int_widget_vector(uniform)

    def create_int_widget_scalar(self, uniform):
        if uniform._ui_type == "combo" or uniform._ui_type == "list" or uniform._ui_type == "radio":
            return ui.ComboBox(ComboListModel(uniform.model, uniform._ui_items))
        if uniform._ui_type == "slider":
            return ui.IntSlider(uniform.model, min=int(uniform._ui_min), max=int(uniform._ui_max), step=int(uniform._ui_step))
        elif uniform._ui_type == "drag":
            return ui.IntDrag(uniform.model, min=int(uniform._ui_min), max=int(uniform._ui_max))
        else:
            return ui.IntField(uniform.model)

    def create_int_widget_vector(self, uniform):
        if uniform._ui_type == "drag":
            return ui.MultiIntDragField(uniform.model, min=int(uniform._ui_min), max=int(uniform._ui_max), h_spacing=2)
        else:
            return ui.MultiIntField(uniform.model, h_spacing=2)

    def create_float_widget(self, uniform):
        if uniform._components == 1:
            return self.create_float_widget_scalar(uniform)
        else:
            return self.create_float_widget_vector(uniform)

    def create_float_widget_scalar(self, uniform):
        if uniform._ui_type == "slider":
            return ui.FloatSlider(uniform.model, min=float(uniform._ui_min), max=float(uniform._ui_max), step=float(uniform._ui_step))
        elif uniform._ui_type == "drag":
            return ui.FloatDrag(uniform.model, min=float(uniform._ui_min), max=float(uniform._ui_max))
        else:
            return ui.FloatField(uniform.model)

    def create_float_widget_vector(self, uniform):
        if uniform._ui_type == "drag":
           return ui.MultiFloatDragField(uniform.model, min=float(uniform._ui_min), max=float(uniform._ui_max), h_spacing=2)
        elif uniform._ui_type == "color":
            with ui.HStack(spacing=2):
                widget = ui.MultiFloatDragField(uniform.model, min=float(uniform._ui_min), max=float(uniform._ui_max), h_spacing=2)
                ui.ColorWidget(uniform.model, width=0, height=0)
                return widget
        else:
            return ui.MultiFloatField(uniform.model, h_spacing=2)



class ReshadeTechniqueModel(ui.AbstractValueModel):
    def __init__(self, handle, reshade_ctx):
        super().__init__()
        self._handle = handle
        self._reshade_ctx = reshade_ctx

    def get_value_as_bool(self) -> bool:
        return reshade.get_technique_enabled(self._reshade_ctx, self._handle)

    def set_value(self, value: bool):
        reshade.set_technique_enabled(self._reshade_ctx, self._handle, value)
        self._value_changed()


class ReshadeTechniqueListItem(ui.AbstractItem):
    def __init__(self, handle, reshade_ctx):
        super().__init__()

        self._name = reshade.get_technique_name(handle)
        self._ui_label = reshade.get_technique_annotation_as_string(handle, "ui_label")
        self._ui_tooltip = reshade.get_technique_annotation_as_string(handle, "ui_tooltip")

        self.model = ReshadeTechniqueModel(handle, reshade_ctx)


class ReshadeTechniqueEditorModel(ui.AbstractItemModel):
    def __init__(self, reshade_ctx):
        super().__init__()
        self._techniques = [ ReshadeTechniqueListItem(handle, reshade_ctx) for handle in reshade.get_technique_list(reshade_ctx) ]

    def get_item_children(self, item):
        if item is not None:
            return []
        return self._techniques

    def get_item_value_model(self, item, column_id):
        if item is None:
            return None
        return item.model

    def get_item_value_model_count(self, item):
        return 1


class ReshadeTechniqueEditorDelegate(ui.AbstractItemDelegate):
    def build_branch(self, model, item, column_id, level, expanded):
        pass

    def build_widget(self, model, item, column_id, level, expanded):
        with ui.VStack():
            ui.Spacer(height=2.5)
            with ui.HStack(width=0, height=0, spacing=5):
                ui.CheckBox(item.model)
                label = ui.Label(item._ui_label if item._ui_label else item._name)
                if item._ui_tooltip:
                    label.set_tooltip(item._ui_tooltip)
            ui.Spacer(height=2.5)


class ReshadeWindow:
    def __init__(self, on_visibility_changed_fn: Callable):
        self._window = ui.Window("ReShade", width=500, height=500)
        self._window.set_visibility_changed_fn(on_visibility_changed_fn)
        self._reshade_ctx = None

        try:
            from omni.kit.viewport.utility import get_active_viewport
            viewport = get_active_viewport()
            self._reshade_ctx = reshade.get_context(viewport.usd_context_name)
        except (ImportError, AttributeError):
            pass

        if self._reshade_ctx is None:
            with self._window.frame:
                with ui.VStack():
                    ui.Spacer()
                    ui.Label("ReShade context not available", alignment=ui.Alignment.CENTER, style={"font_size": 48})
                    ui.Spacer()
            import carb
            carb.log_error(f"ReShade context not available for Viewport {viewport}")
            return

        self._update_sub = reshade.subscribe_to_update_events(self._reshade_ctx, self._on_update)
        self._build_ui()

    def destroy(self):
        self._window = None
        self._update_sub = None

    def _build_ui(self):
        reshade_ctx = self._reshade_ctx
        self._tmodel = ReshadeTechniqueEditorModel(reshade_ctx)
        self._tdelegate = ReshadeTechniqueEditorDelegate()
        self._vmodel = ReshadeVariableEditorModel(reshade_ctx)
        self._vdelegate = ReshadeVariableEditorDelegate()

        with self._window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(height=0, spacing=5):
                    self._tview = ui.TreeView(
                        self._tmodel,
                        delegate=self._tdelegate,
                        root_visible=False,
                        header_visible=False)
                    ui.Line()
                    self._vview = ui.TreeView(
                        self._vmodel,
                        delegate=self._vdelegate,
                        root_visible=False,
                        header_visible=False,
                        expand_on_branch_click=True)

    def _on_update(self):
        self._build_ui()
