bl_info = {
	'name': 'VF Copy Paste Geometry',
	'author': 'John Einselen - Vectorform LLC',
	'version': (0, 0, 2),
	'blender': (3, 5, 0),
	'location': 'Scene > VF Tools > Copy Paste',
	'description': 'Copy and paste geometry using internal mesh system (prevents duplication of materials)',
	'warning': 'inexperienced developer, use at your own risk',
	'wiki_url': '',
	'tracker_url': '',
	'category': '3D View'}

import bpy

###########################################################################
# Main classes

class VF_CopyGeometry(bpy.types.Operator):
	bl_idname = 'object.vf_copy_geometry'
	bl_label = 'Copy'
	bl_options = {'REGISTER', 'UNDO'}
	
	copy: bpy.props.BoolProperty()
	
	@classmethod
	def poll(cls, context):
		return (
			context.active_object
			and context.active_object.type in {'MESH', 'CURVE', 'SURFACE'}
			and context.mode in {'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE'}
		)
	
	def execute(self, context):
		# Get the current active object
		active_object = context.active_object
		
		# Save the current selection
		original_selection = []
		if bpy.context.object.type == 'MESH':
			if bpy.context.tool_settings.mesh_select_mode[0]:  # Vertex selection mode
				original_selection = [v.select for v in active_object.data.vertices]
			elif bpy.context.tool_settings.mesh_select_mode[1]:  # Edge selection mode
				original_selection = [e.select for e in active_object.data.edges]
			elif bpy.context.tool_settings.mesh_select_mode[2]:  # Face selection mode
				original_selection = [p.select for p in active_object.data.polygons]
		elif bpy.context.object.type == 'CURVE':
			if bpy.context.mode == 'EDIT_CURVE':
				original_selection = [s.select for s in active_object.data.splines]
		elif bpy.context.object.type == 'SURFACE':
			if bpy.context.mode == 'EDIT_SURFACE':
				original_selection = [s.select for s in active_object.data.splines]
		
		# Split the selection into a new object (duplicate first if copy is enabled)
		if active_object.type == 'MESH':
			if self.copy:
				bpy.ops.mesh.duplicate()
			bpy.ops.mesh.separate(type='SELECTED')
		else:
			if self.copy:
				bpy.ops.curve.duplicate() # bpy.ops.curve.duplicate_move()
			bpy.ops.curve.separate()
		
		# Restore the original selection
		if len(original_selection) > 0:
			if bpy.context.object.type == 'MESH':
				if bpy.context.tool_settings.mesh_select_mode[0]:  # Vertex selection mode
					for i, v in enumerate(active_object.data.vertices):
						v.select = original_selection[i]
						print('Original Vertex Selection: %s'%original_selection[i])
				elif bpy.context.tool_settings.mesh_select_mode[1]:  # Edge selection mode
					for i, e in enumerate(active_object.data.edges):
						e.select = original_selection[i]
						print('Original Edge Selection: %s'%original_selection[i])
				elif bpy.context.tool_settings.mesh_select_mode[2]:  # Face selection mode
					for i, p in enumerate(active_object.data.polygons):
						p.select = original_selection[i]
						print('Original Polygon Selection: %s'%original_selection[i])
			elif bpy.context.object.type == 'CURVE':
				if bpy.context.mode == 'EDIT_CURVE':
					for i, s in enumerate(active_object.data.splines):
						s.select = original_selection[i]
						print('Original Curve Point Selection: %s'%original_selection[i])
			elif bpy.context.object.type == 'SURFACE':
				if bpy.context.mode == 'EDIT_SURFACE':
					for i, s in enumerate(active_object.data.splines):
						s.select = original_selection[i]
						print('Original NURB Point Selection: %s'%original_selection[i])
		
		# Get the newly created object and data block reference
		# This seems potentially brittle; assumes separated object always shows up as last selected object
		temp_object = context.selected_objects[len(context.selected_objects)-1]
		temp_object.name = 'VF-Clipboard-TEMP'
		data_block = temp_object.data
		
		# Remove previous persistent clipboard data if it exists
		if temp_object.type == 'MESH' and bpy.data.meshes.get('VF-PersistentClipboard-MESH'):
			bpy.data.meshes.remove(bpy.data.meshes.get('VF-PersistentClipboard-MESH'))
		elif temp_object.type == 'CURVE' and bpy.data.curves.get('VF-PersistentClipboard-CURVE'):
			bpy.data.curves.remove(bpy.data.curves.get('VF-PersistentClipboard-CURVE'))
		elif temp_object.type == 'SURFACE' and bpy.data.curves.get('VF-PersistentClipboard-SURFACE'):
			bpy.data.curves.remove(bpy.data.curves.get('VF-PersistentClipboard-SURFACE'))
		
		# Rename the data block and save it as persistent
		data_block = temp_object.data
		data_block.name = 'VF-PersistentClipboard-' + active_object.type
		data_block.use_fake_user = True
		
		# Delete the temporary object
		bpy.data.objects.remove(temp_object)
		
		print('geometry copied')
		return {'FINISHED'}

class VF_PasteGeometry(bpy.types.Operator):
	bl_idname = 'object.vf_paste_geometry'
	bl_label = 'Paste'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
#		return context.mode == 'EDIT_MESH'
		return (
			context.active_object
			and context.active_object.type in {'MESH', 'CURVE', 'SURFACE'}
			and context.mode in {'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE'}
			and bpy.data.meshes.get('VF-PersistentClipboard-' + context.active_object.type)
		)
	
	def execute(self, context):
#		bpy.data.meshes.get('VF-PersistentClipboard-MESH')
#		bpy.data.curves.get('VF-PersistentClipboard-CURVE')
#		bpy.data.curves.get('VF-PersistentClipboard-SURFACE')
#		bpy.data.metaballs.get('VF-PersistentClipboard-META')
		
		print('geometry pasted')
		return {'FINISHED'}



###########################################################################
# Plugin preferences
	
	# Option to enable persistent clipboards (preserve unused geometry data blocks)

###########################################################################
# UI rendering class

class VFTOOLS_PT_copy_paste_geometry(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = 'VF Tools'
	bl_order = 3
	bl_options = {'DEFAULT_CLOSED'}
	bl_label = 'Copy Paste Geometry'
	bl_idname = 'VFTOOLS_PT_copy_paste_geometry'
	
	@classmethod
	def poll(cls, context):
		return True
	
	def draw_header(self, context):
		try:
			layout = self.layout
		except Exception as exc:
			print(str(exc) + ' | Error in VF Copy Paste Geometry panel header')
			
	def draw(self, context):
		try:
			layout = self.layout
			layout.use_property_decorate = False # No animation
			
			row = layout.row(align = True)
			button_cut = row.operator(VF_CopyGeometry.bl_idname, text = 'Cut')
			button_cut.copy = False
			button_copy = row.operator(VF_CopyGeometry.bl_idname)
			button_copy.copy = True
			button_paste = row.operator(VF_PasteGeometry.bl_idname)
			
			# Check for existing temporary objects and display the results
			box = layout.box()
			clipboardList = []
			if bpy.data.meshes.get('VF-PersistentClipboard-MESH'):
				clipboardList.append('Mesh')
			if bpy.data.curves.get('VF-PersistentClipboard-CURVE'):
				clipboardList.append('Curve')
			if bpy.data.curves.get('VF-PersistentClipboard-SURFACE'):
				clipboardList.append('Nurb')
			if bpy.data.metaballs.get('VF-PersistentClipboard-META'):
				clipboardList.append('Meta')
			box.label(text = 'Copied: ' + ', '.join(clipboardList))
		except Exception as exc:
			print(str(exc) + ' | Error in VF Vertex Location Keyframes panel')

###########################################################################
# Addon registration functions

classes = (VF_CopyGeometry, VF_PasteGeometry, VFTOOLS_PT_copy_paste_geometry)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	
	
def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

if __name__ == '__main__':
	register()