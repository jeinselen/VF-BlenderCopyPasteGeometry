bl_info = {
	"name": "VF Copy Paste Geometry",
	"author": "John Einselen - Vectorform LLC",
	"version": (0, 0, 1),
	"blender": (3, 5, 0),
	"location": "Scene > VF Tools > Copy Paste",
	"description": "Copy and paste geometry using internal mesh system (prevents duplication of materials)",
	"warning": "inexperienced developer, use at your own risk",
	"wiki_url": "",
	"tracker_url": "",
	"category": "3D View"}

import bpy

###########################################################################
# Main classes

class VF_CopyGeometry(bpy.types.Operator):
	bl_idname = "object.vf_copy_geometry"
	bl_label = "Copy"
	bl_options = {'REGISTER', 'UNDO'}
	
	copy: bpy.props.BoolProperty()
	
	@classmethod
	def poll(cls, context):
#		return context.mode == 'EDIT_MESH'
		return (
			context.mode in {'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_METABALL'}
			and context.active_object
			and context.active_object.type in {'MESH', 'CURVE', 'SURFACE', 'META'}
#			and context.active_object.data.total_vert_sel + context.active_object.data.total_edge_sel + context.active_object.data.total_face_sel > 0
		)
	
	def execute(self, context):
		# Select the desired object
#		obj = bpy.context.active_object
		
		# Switch to Edit Mode (the poll should ensure this, but just in case?)
#		bpy.context.view_layer.objects.active = obj
#		bpy.ops.object.mode_set(mode='EDIT')
		
		# Duplicate the selection if copy is enabled
		if self.copy:
			bpy.ops.mesh.duplicate()
			bpy.ops.curve.duplicate_move()
		
		# Separate the selection into a new object
		bpy.ops.mesh.separate(type='SELECTED')
		bpy.ops.curve.separate()
		
		
		# Get the newly created object
		# This seems potentially brittle; assumes separated object always shows up as last selected object
		temp_object = bpy.context.selected_objects[len(bpy.context.selected_objects)-1]
		
		# Rename the object
		temp_object.name = "VF-Clipboard-TEMP"
		
		# Get the data block reference
		data_block = temp_object.data
		
		# Remove previous persistent clipboard data if it exists
		if temp_object.type == "MESH" and bpy.data.meshes.get("VF-PersistentClipboard-MESH"):
			bpy.data.meshes.remove(bpy.data.meshes.get("VF-PersistentClipboard-MESH"))
		elif temp_object.type == "CURVE" and bpy.data.curves.get("VF-PersistentClipboard-CURVE"):
			bpy.data.curves.remove(bpy.data.curves.get("VF-PersistentClipboard-CURVE"))
		elif temp_object.type == "SURFACE" and bpy.data.curves.get("VF-PersistentClipboard-SURFACE"):
			bpy.data.curves.remove(bpy.data.curves.get("VF-PersistentClipboard-SURFACE"))
		elif temp_object.type == "META" and bpy.data.metaballs.get("VF-PersistentClipboard-META"):
			bpy.data.metaballs.remove(bpy.data.metaballs.get("VF-PersistentClipboard-META"))
		
		# Rename the mesh data block and save it as persistent
		data_block = temp_object.data
		data_block.name = "VF-PersistentClipboard-" + context.active_object.type
		data_block.use_fake_user = True
		
		# Delete the temporary object
		bpy.data.objects.remove(temp_object)
		
		print("copy geometry")
		return {'FINISHED'}

class VF_PasteGeometry(bpy.types.Operator):
	bl_idname = "object.vf_paste_geometry"
	bl_label = "Paste"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
#		return context.mode == 'EDIT_MESH'
		return (
			context.mode in {'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_METABALL'}
			and context.active_object
			and context.active_object.type in {'MESH', 'CURVE', 'SURFACE', 'META'}
			and bpy.data.meshes.get("VF-PersistentClipboard-" + context.active_object.type)
		)
	
	def execute(self, context):
#		bpy.data.meshes.get("VF-PersistentClipboard-MESH")
#		bpy.data.curves.get("VF-PersistentClipboard-CURVE")
#		bpy.data.curves.get("VF-PersistentClipboard-SURFACE")
#		bpy.data.metaballs.get("VF-PersistentClipboard-META")
		
		print("paste geometry")
		return {'FINISHED'}



###########################################################################
# Plugin preferences
	
	# Option to enable persistent clipboards (preserve unused geometry data blocks)

###########################################################################
# UI rendering class

class VFTOOLS_PT_copy_paste_geometry(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'VF Tools'
	bl_order = 3
	bl_options = {'DEFAULT_CLOSED'}
	bl_label = "Copy Paste Geometry"
	bl_idname = "VFTOOLS_PT_copy_paste_geometry"
	
	@classmethod
	def poll(cls, context):
		return True
	
	def draw_header(self, context):
		try:
			layout = self.layout
		except Exception as exc:
			print(str(exc) + " | Error in VF Vertex Location Keyframes panel header")
			
	def draw(self, context):
		try:
			layout = self.layout
			layout.use_property_decorate = False # No animation
			
			row = layout.row(align = True)
			button_cut = row.operator(VF_CopyGeometry.bl_idname, text = "Cut")
			button_cut.copy = False
			button_copy = row.operator(VF_CopyGeometry.bl_idname)
			button_copy.copy = True
			button_paste = row.operator(VF_PasteGeometry.bl_idname)
			
			# Check for existing temporary objects and display the results
			box = layout.box()
			clipboardList = []
			if bpy.data.meshes.get("VF-PersistentClipboard-MESH"):
				clipboardList.append("Mesh")
			if bpy.data.curves.get("VF-PersistentClipboard-CURVE"):
				clipboardList.append("Curve")
			if bpy.data.curves.get("VF-PersistentClipboard-SURFACE"):
				clipboardList.append("Nurb")
			if bpy.data.metaballs.get("VF-PersistentClipboard-META"):
				clipboardList.append("Meta")
			box.label(text = "Copied: " + ", ".join(clipboardList))
		except Exception as exc:
			print(str(exc) + " | Error in VF Vertex Location Keyframes panel")

###########################################################################
# Addon registration functions

classes = (VF_CopyGeometry, VF_PasteGeometry, VFTOOLS_PT_copy_paste_geometry)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	
	
def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()