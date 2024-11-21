from omni.asset_validator.core import BaseRuleChecker, Suggestion
from pxr import Usd, UsdGeom

from pxr import Usd, Sdf
import omni.usd

def parent_prims(prims: list[Usd.Prim],
                 new_parent: Sdf.Path,
                 layers: list[Sdf.Layer] = None) -> bool:
    """Move Prims to a new parent in given layers.

    Note:
        This will only reparent prims to the new parent if the new parent
        exists in the layer.

    Arguments:
        prims (list[Usd.Prim]): The prims to move the new parent
        new_parent (Sdf.Path): Parent path to be moved to.
        layers (list[Sdf.Layer]): The layers to apply the reparenting
            in. If None are provided the stage's full layer stack will be used.

    """
    if not prims:
        return False

    # Only consider prims not already parented to the new parent
    prims = [
        prim for prim in prims if prim.GetPath().GetParentPath() != new_parent
    ]
    if not prims:
        return False

    if layers is None:
        stage = prims[0].GetStage()
        layers = stage.GetLayerStack()

    edit_batch = Sdf.BatchNamespaceEdit()
    for prim in prims:
        edit = Sdf.NamespaceEdit.Reparent(
            prim.GetPath(),
            new_parent,
            -1
        )
        edit_batch.Add(edit)

    any_edits_made = False
    with Sdf.ChangeBlock():
        for layer in layers:
            applied = layer.Apply(edit_batch)
            if applied:
                any_edits_made = True

    return any_edits_made

from pxr import Usd, Sdf
import omni.usd

stage = omni.usd.get_context().get_stage()
old_layer: Sdf.Layer = Sdf.Layer.CreateNew('C:/Users/gliacloud/Documents/Omniverse-Projects/usd-nucleus-organizer/exts/omni.usd.nucleus.organizer-0.1.0/data/coffee_table_2.usd')

new_layer = stage.GetRootLayer()
new_layer.subLayerPaths.append(new_layer)

prim_list = [old_layer.GetDefaultPrim()]
parent_prim = new_layer.GetDefaultPrimAsPath()

print(parent_prim(prims=prim_list, new_parent=parent_prim, layers=[new_layer]))


class RotationChecker(BaseRuleChecker):
    
    @classmethod
    def _add_up_axis(cls, stage: Usd.Stage, _location: Usd.Prim):
        axis: UsdGeom.Tokens = UsdGeom.Tokens.z
        UsdGeom.SetStageUpAxis(stage, axis)
        
    @classmethod
    def _add_up_axis(cls, stage: Usd.Stage, _location: Usd.Prim):
        axis: UsdGeom.Tokens = UsdGeom.Tokens.z
        UsdGeom.SetStageUpAxis(stage, axis)
        
        default_prim = stage.GetDefaultPrim()
        default_prim_xformable = UsdGeom.Xformable(default_prim)
        default_prim_xform_op = default_prim_xformable.AddRotateXOp()
        default_prim_xform_op.Set(90)
        
    
    def CheckStage(self, stage: Usd.Stage):
        
        if not stage.HasAuthoredMetadata(UsdGeom.Tokens.upAxis):
            self._AddFailedCheck(
                message="Stage does not specify an upAxis.",
                suggestion=Suggestion(
                    message="adds Z upAxis to file metadata",
                    callable=self._add_up_axis,
                ))
        elif UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
            self._AddFailedCheck(
                message="UpAxis should be Z",
                suggestion=Suggestion(
                    message="Changes upAxis to Z and rotates prim accordingly",
                    callable=self._handle_upAxis_change
                )
            )