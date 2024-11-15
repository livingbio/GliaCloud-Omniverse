https://docs.omniverse.nvidia.com/auto-config/latest/overview.html

# create button
# Needed config for asset validation
- z-up
- stage units in meters
- 


# Implementing MVC software-design

Model:
- completely independent of UI
    - can have many different 
- registers views & controllers
    - register instance of custom asset importer class


View: how UI is displayed, regardless of values



Control:

https://docs.omniverse.nvidia.com/services/latest/tutorials/viewport-capture/index.html

https://forum.aousd.org/t/api-basics-for-designing-a-manage-edits-editor-for-usd/676/3


1. Call Asset Converter on file.
2. Begin checks & corresponding fixes
    - Scale
    - Rotation
    - Set World prim to have Type = Xform
    - ...
    
3. Create controllers for easy manipulation if checks fail
4. Capture stage
    - change orientation of camera to predetermined orientation
    - translate camera to be looking at center of object's bounding box
    - move back sufficiently for bounding box to fit inside "frustum"

https://forums.developer.nvidia.com/t/modifying-usdz-files-in-omniverse-painful-cannot-save-the-result-in-a-way-that-works/297290/3


services -- things that don't need UI: 
1. import & convert asset
2. optimize scene

window -- things that do need UI:
1. OrganizedUSDModel
    - Bounding Box Dimensions
    - Screenshot of pivot
    - Pivot position


TagBuilder:

