# VF Copy Paste Geometry
This plugin uses persistent mesh and curve data blocks with Blender's Join operator to add copied geometry to the current active object when in edit mode. This approach maintains the correct local materials because everything is handled internally to the current file, but cannot paste between different projects or multiple Blender instances.

If you want copy/paste functionality _outside_ of the current project, you may want to check out [Edit Mode Copy Paste](https://github.com/OlesenJonas/Blender_EditModeCopyPaste) by Olesen Jonas. It uses the Blender buffer system which operates like the Append operator, and will duplicate materials every time an item is pasted within the same project (it behaves as if the pasted element is _always_ external to the current project).

## Installation and Usage
- Download VF_copyPasteGeometry.py
- Open Blender Preferences and navigate to the "Add-ons" tab
- Install and enable the add-on
- It will show up in the VF Tools tab in 3D View panels, where you can cut, copy, paste, along with a clipboard readout to track what kinds of elements are available for pasting
