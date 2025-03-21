# USD Nucleus Organizer extension for NVIDIA Omniverse

![Preview](exts/omni.usd.nucleus.organizer-0.1.0/data/preview.png)

This project is to standardize the asset import process for GliaCloud's R&D purposes (currently only for internal use).

Namely, it will:

1. Run asset converter on selected files with GliaCloud's desired configuration.
2. Create Nucleus (or USDSearch) tags using an automated method (TBD).
3. Place the asset at the desired path within our Nucleus server (TBD).

## Enable extension
1. Fork and clone this repo, for example in `C:\Users\gliacloud\Documents\Omniverse-Projects\usd-nucleus-organizer`.
2. In the Omniverse App, open Extension Manager: Window → Extensions.
3. In the Extension Manager Window open the settings page, found at the small gear button in the top left bar.
4. In the settings page there is a list of Extension Search Paths. Add the path to the exts subfolder of the cloned repo as another search path: `C:\Users\gliacloud\Documents\Omniverse-Projects\usd-nucleus-organizer\exts`
5. Navigate to the Third Party tab of the Extensions Manager and find the newly-added `omni.usd.nucleus.organizer` extension. Toggle on the extension and check 'Autoload' if desired.
