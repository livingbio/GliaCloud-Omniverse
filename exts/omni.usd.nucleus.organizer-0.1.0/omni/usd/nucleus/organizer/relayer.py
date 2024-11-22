from pxr import Usd, Sdf
import omni.usd
import carb

def parent_prims(prims: list[Usd.Prim],
                 new_parent: Sdf.Path,
                 layers: list[Sdf.Layer] = None) -> bool:

    if not prims:
        carb.log_warn("No prim")
        return False

    # Only consider prims not already parented to the new parent
    prims = [
        prim for prim in prims if prim.GetPath().GetParentPath() != new_parent
    ]
    if not prims:
        carb.log_warn("No filtered prim")
        return False

    if layers is None:
        stage = prims[0].GetStage()
        layers = stage.GetLayerStack()

    edit_batch = Sdf.BatchNamespaceEdit()
    for prim in prims:
        carb.log_warn(prim.GetPath())
        edit = Sdf.NamespaceEdit.Reparent(
            prim.GetPath(),
            new_parent,
            -1
        )
        edit_batch.Add(edit)

    any_edits_made = False
    with Sdf.ChangeBlock():
        for layer in layers:
            carb.log_warn(layer.CanApply(edit_batch))
           
            applied = layer.Apply(edit_batch)
            if applied:
                any_edits_made = True
    carb.log_warn("No edits")
    return any_edits_made

asset_path = r'C:/Users/gliacloud/Documents/Omniverse-Projects/usd-nucleus-organizer/exts/omni.usd.nucleus.organizer-0.1.0/data/outputs/coffee_table_2.usd'
asset_stage = Usd.Stage.Open(asset_path)
asset_layer: Sdf.Layer = asset_stage.GetRootLayer()

curr_stage = omni.usd.get_context().get_stage()
curr_layer: Sdf.Layer = curr_stage.GetRootLayer()

curr_layer.subLayerPaths = [asset_path]

prim_list = [asset_stage.GetDefaultPrim()]
carb.log_warn(prim_list[0])
parent_path = curr_stage.GetDefaultPrim().GetPrimPath()

carb.log_warn(parent_prims(prims=prim_list, new_parent=parent_path, layers=[curr_layer]))


del asset_stage


