import asyncio
import os
import copy
import omni.ext
from omni.kit.menu.utils import MenuItemDescription
import carb.settings

import carb.dictionary

# import omni.kit.viewport
import omni.timeline


import webbrowser
from functools import partial
from pxr import Usd, Gf, Sdf

# from watchdog.events import FileSystemEventHandler
# from watchdog.observers import Observer
__DEBUG_MENU__ = False
__MENU_NAME__="Reshade"
import random  # test


class ReshadeMenuHookExt(omni.ext.IExt):
    def set_effect_from_timeline(self, preset):
        if preset != "Disable":
            # carb.settings.get_settings().set("/rtx/reshade/enable", False)
            # asyncio.ensure_future(self._delayed_toggle_effect(preset))
            self.lean_toggle_effect(preset)
        else:
            carb.settings.get_settings().set("/rtx/reshade/enable", False)

    async def reload_reshade_menu(self):
        await omni.kit.app.get_app().next_update_async()
        omni.kit.menu.utils.remove_menu_items(self.menu_list, self.menu_name)
        self._presets_dict = self._make_presets_dict(self._presets_path)
        # print("dict")
        # print(self._presets_dict)

        self.menu_build()

    def menu_build(self):
        def off_switch(self):
            carb.settings.get_settings().set("/rtx/reshade/enable", False)

        def menu_toggletest(self):
            self._test_running = not self._test_running
            if self._test_running:
                asyncio.ensure_future(self._test_cycle())
                print("reshade test start")
            else:
                print("reshade test end")

        def menu_reload_presets(self):
            asyncio.ensure_future(self.reload_reshade_menu())

        def set_effect(self, preset):
            self.lean_toggle_effect(preset)

        def set_key_for_curr_preset(self):
            stage = omni.usd.get_context().get_stage()
            prim = stage.GetPrimAtPath("/World/ReshadePrim")
            if not prim.IsValid():
                omni.kit.commands.execute("CreatePrimCommand", prim_path="/World/ReshadePrim", prim_type="Xform")
            prim = stage.GetPrimAtPath("/World/ReshadePrim")
            if not prim.HasAttribute("ReshadeToken"):
                attr = prim.CreateAttribute("ReshadeToken", Sdf.ValueTypeNames.Token, custom=False)
            attr = prim.GetAttribute("ReshadeToken")

            curr_preset = carb.settings.get_settings().get("/rtx/reshade/presetFilePath")
            new_current_second = self._timeline.get_current_time()
            tc = self._get_time_code(new_current_second)

            if carb.settings.get_settings().get("/rtx/reshade/enable") and curr_preset != "":
                attr.Set(self._get_key_token_from_preset(curr_preset), tc)
            else:
                attr.Set("Disable", tc)

        def edit_current_preset(self):
            curr_preset = carb.settings.get_settings().get("/rtx/reshade/presetFilePath")
            curr_preset = os.path.normpath(curr_preset).replace("\\", "/")
            webbrowser.open(curr_preset)

        self.menu_list = [MenuItemDescription(name="Disable", onclick_fn=lambda: off_switch(self))]

        if __DEBUG_MENU__:
            self.menu_list.append(
                MenuItemDescription(name="Debug:autoswitch presets", onclick_fn=partial(menu_toggletest, self=self))
            )  # debug

        self.menu_list.append(
            MenuItemDescription(
                name="Set Key For Current Preset", onclick_fn=partial(set_key_for_curr_preset, self=self)
            )
        )

        self.menu_list.append(
            MenuItemDescription(name="Edit Current Preset", onclick_fn=partial(edit_current_preset, self=self))
        )
        self.menu_list.append(
            MenuItemDescription(name="Reload Menu", onclick_fn=partial(menu_reload_presets, self=self))
        )

        self._effect_list = []

        self.presets_submenu_list = []
        for folder in self._presets_dict:
            presets_in_folder = []
            for preset in self._presets_dict[folder]:
                preset_name = os.path.splitext(os.path.basename(preset))[0].title()
                presets_in_folder.append(
                    MenuItemDescription(name=preset_name, onclick_fn=partial(set_effect, preset=preset, self=self))
                )
                if ("glow" in preset) or ("glare" in preset):
                    self._effect_list.append(preset)  # debug

            folder_name = os.path.basename(folder).title()
            # self.menu_list.append(MenuItemDescription(name=folder_name, sub_menu=presets_in_folder))
            self.presets_submenu_list.append(MenuItemDescription(name=folder_name, sub_menu=presets_in_folder))
        # self.presets_submenu_list.append(
        #     MenuItemDescription(name="-------")
        # )  # plug to work around not shown sub-menu-only items

        # self.menu_list.append(MenuItemDescription(name="Presets", sub_menu=self.presets_submenu_list))
        print(self.presets_submenu_list)
        self.menu_list.append(MenuItemDescription(name="Presets", sub_menu=self.presets_submenu_list))

        omni.kit.menu.utils.add_menu_items(self.menu_list, self.menu_name, 9999)
        omni.kit.menu.utils.rebuild_menus()

    def on_startup(self, ext_id):
        # self.rendersettings = carb.settings.get_settings()
        # self.is_enabled = self.rendersettings.get("/rtx/reshade/enable")
        self.menu_name=__MENU_NAME__;
        self._presets_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id) + "/presets/"
        self._fx_path=omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id) + "/presets/"+"/fx/"
        # print("Presets path:",self._presets_path)
        self._presets_dict = self._make_presets_dict(self._presets_path)
        self.menu_build()

        self._last_preset_token = ""

        self._timeline = omni.timeline.get_timeline_interface()
        timeline_stream = self._timeline.get_timeline_event_stream()
        self._sub = timeline_stream.create_subscription_to_pop(self._on_timeline_event)

        self._test_running = False  # debug

    def _on_timeline_event(self, e):
        stage = omni.usd.get_context().get_stage()
        if stage is not None:
            prim = stage.GetPrimAtPath("/World/ReshadePrim")
            if not prim.IsValid():
                return
            if not prim.HasAttribute("ReshadeToken"):
                return
            attr = prim.GetAttribute("ReshadeToken")
            tc = self._get_time_code(self._timeline.get_current_time())
            curr_token = attr.Get(time=tc)
            if curr_token != self._last_preset_token:
                self._last_preset_token = curr_token
                self.set_effect_from_timeline(self._get_preset_from_key_token(curr_token))

    def _get_time_code(self, in_seconds):
        return Usd.TimeCode(
            omni.usd.get_frame_time_code(in_seconds, omni.usd.get_context().get_stage().GetTimeCodesPerSecond())
        )

    def on_shutdown(self):
        omni.kit.menu.utils.remove_menu_items(self.menu_list, self.menu_name)

    def lean_toggle_effect(self, preset):
        fp = os.path.normpath(preset).replace("\\", "/")  # preset is a full path to ini file
        sd = os.path.dirname(preset)
        
        s = carb.settings.get_settings()
        s.set("/rtx/reshade/presetFilePath", fp)
        s.set("/rtx/reshade/effectSearchDirPath", self._fx_path)
        s.set("/rtx/reshade/textureSearchDirPath", self._fx_path) #textures are usually hardcoded inside fx
        s.set("/rtx/reshade/enable", True)

    async def _delayed_toggle_effect(self, preset):
        await omni.kit.app.get_app().next_update_async()
        # fp = self._presets_path + effect + f"/preset.ini"
        fp = preset  # preset is a full path to ini file
        sd = os.path.dirname(preset)
        s = carb.settings.get_settings()
        s.set("/rtx/reshade/presetFilePath", fp)
        s.set("/rtx/reshade/effectSearchDirPath", self._fx_path)
        s.set("/rtx/reshade/textureSearchDirPath", self._fx_path) #textures are usually hardcoded inside fx
        

        await omni.kit.app.get_app().next_update_async()
        s = carb.settings.get_settings()
        s.set("/rtx/reshade/enable", True)

    def _make_presets_dict(self, path):
        d = self._get_directory_list(path)
        self._presets_zip = zip(d[0], d[1])
        self._presets_dict = dict(self._presets_zip)
        # for k,v in self._presets_dict.items():
        # os.path.normpath(k).replace('\\','/')
        # os.path.normpath(v).replace('\\','/')
        return self._presets_dict

    def _get_directory_list(self, path):
        # carb.log_warn("")
        def listdir_fullpath(d):
            return [os.path.join(d, f) for f in os.listdir(d)]

        directoryList = []
        fileList = []
        # return nothing if path is a file
        if os.path.isfile(path):
            return []
        # add dir to directorylist if it contains .ini files
        ini_files = [f for f in listdir_fullpath(path) if f.endswith(".ini")]
        if len(ini_files) > 0:
            fileList.append(ini_files)
            directoryList.append(path)
        # recurse
        for d in os.listdir(path):
            new_path = os.path.join(path, d)
            if os.path.isdir(new_path):
                dummy = self._get_directory_list(new_path)
                directoryList += dummy[0]
                fileList += dummy[1]
        return (directoryList, fileList)

    def _get_key_token_from_preset(self, preset):
        new_token = os.path.os.path.relpath(preset, self._presets_path).replace("\\", "/")
        # new_token=preset.replace(self._presets_path,"\\")
        return new_token

    def _get_preset_from_key_token(self, token):
        if token != "Disable":
            preset = os.path.join(self._presets_path, token)
            preset = os.path.normpath(preset).replace("\\", "/")
        else:
            preset = "Disable"
        return preset

    async def _test_cycle(self):

        if not self._test_running:
            return
        await omni.kit.app.get_app().next_update_async()

        idx = random.randrange(len(self._effect_list))

        preset = self._effect_list[idx]

        preset_name = os.path.splitext(os.path.basename(preset))[0]
        print("test %s" % preset_name)
        # preset in self.presets_dict[folder]
        s = carb.settings.get_settings()
        fp = preset.replace("\\", "/")
        sd = os.path.dirname(preset)
        # s.set("/rtx/reshade/presetFilePath", fp)
        # s.set("/rtx/reshade/enable", False)
        s.set("/rtx/reshade/presetFilePath", fp)
        s.set("/rtx/reshade/effectSearchDirPath", sd)
        s.set("/rtx/reshade/textureSearchDirPath", sd)
        s.set("/rtx/reshade/enable", True)

        await asyncio.sleep(0.7)
        await omni.kit.app.get_app().next_update_async()
        asyncio.ensure_future(self._test_cycle())

    async def _test_cycle_random(self):
        if not self._test_running:
            return
        await omni.kit.app.get_app().next_update_async()

        idx = random.randrange(len(self._effect_list))

        preset = self._effect_list[idx]

        preset_name = os.path.splitext(os.path.basename(preset))[0]
        print("test %s" % preset_name)
        # preset in self.presets_dict[folder]
        s = carb.settings.get_settings()
        fp = preset.replace("\\", "/")
        sd = os.path.dirname(preset)
        # s.set("/rtx/reshade/presetFilePath", fp)
        # s.set("/rtx/reshade/enable", False)
        s.set("/rtx/reshade/presetFilePath", fp)
        s.set("/rtx/reshade/effectSearchDirPath", sd)
        s.set("/rtx/reshade/textureSearchDirPath", sd)
        s.set("/rtx/reshade/enable", True)

        await asyncio.sleep(2)
        await omni.kit.app.get_app().next_update_async()
        asyncio.ensure_future(self._test_cycle_random())
