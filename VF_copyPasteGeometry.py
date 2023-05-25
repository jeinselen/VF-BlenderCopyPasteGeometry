bl_info = {
	'name': 'VF Copy Paste Geometry',
	'author': 'John Einselen - Vectorform LLC',
	'version': (0, 0, 5),
	'blender': (3, 5, 0),
	'location': 'Scene > VF Tools > Copy Paste',
	'description': 'Copy and paste geometry using internal mesh system (prevents duplication of materials)',
	'warning': 'inexperienced developer, use at your own risk',
	'wiki_url': '',
	'tracker_url': '',
	'category': 'Mesh'}

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
		# Switch to object mode to ensure modified object selections are recognised in edit mode
		# Toggling between object/edit is also required for Blender to recognise geometry selection changes (why is this a thing)
		bpy.ops.object.mode_set(mode='OBJECT')
		
		# Save the current object selection
		# To prevent weirdness, only cut/copy geometry from the active object
		selected_objects = [obj for obj in context.selected_objects]
		
		# Get the current active object
		active_object = context.active_object
				
		# Select only the active object
		for obj in context.selected_objects:
			if obj != active_object:
				obj.select_set(False)
		
		# Toggle back into edit mode (even without object selection changes, this is required for Blender geometry selection recognition)
		bpy.ops.object.mode_set(mode='EDIT')
		
		# Split the selected geometry into a new object
		# If copy is enabled, preserve selection state and duplicate the selection first
		original_selection = []
		if active_object.type == 'MESH':
			if self.copy:
				# Vertex selection mode
				if context.tool_settings.mesh_select_mode[0]:
					for i, v in enumerate(active_object.data.vertices):
						original_selection.append( active_object.data.vertices[i].select)
				# Edge selection mode
				elif context.tool_settings.mesh_select_mode[1]:
					original_selection = [e.select for e in active_object.data.edges]
				# Face selection mode
				elif context.tool_settings.mesh_select_mode[2]:
					original_selection = [p.select for p in active_object.data.polygons]
				# Duplicate selection
				bpy.ops.mesh.duplicate()
			# Separate selection
			bpy.ops.mesh.separate(type='SELECTED')
		else:
			if self.copy:
				# Get each curve or surface spline
				for s_i, s in enumerate(active_object.data.splines):
					temp_array = []
					# Get each point in the curve or surface spline
					for p_i, p in enumerate(active_object.data.splines[s_i].points):
						# Save point select status to temporary array
						temp_array.append(active_object.data.splines[s_i].points[p_i].select)
					# Append temporary array to the main array
					original_selection.append(temp_array)
				# Duplicate selection
				bpy.ops.curve.duplicate() # bpy.ops.curve.duplicate_move()
			# Separate selection
			bpy.ops.curve.separate()
		
		# Restore the original selection
		if len(original_selection) > 0:
			if active_object.type == 'MESH':
				# Switch into object mode to set vertex selection state without converting to bmesh
				bpy.ops.object.mode_set(mode='OBJECT')
				
				# Vertex selection mode
				if context.tool_settings.mesh_select_mode[0]:
					for i, v in enumerate(active_object.data.vertices):
						v.select = original_selection[i]
				# Edge selection mode
				elif context.tool_settings.mesh_select_mode[1]:
					for i, e in enumerate(active_object.data.edges):
						e.select = original_selection[i]
				# Face selection mode
				elif context.tool_settings.mesh_select_mode[2]:
					for i, p in enumerate(active_object.data.polygons):
						p.select = original_selection[i]
				
				# Switch back to edit mode
				bpy.ops.object.mode_set(mode='EDIT')
			else:
				for spline_i, s in enumerate(active_object.data.splines):
					for point_i, p in enumerate(s.points):
						p.select = original_selection[spline_i][point_i]
					original_selection.append(temp_array)
		
		# Get the newly created object and data block reference
		# This seems potentially brittle; assumes separated object always shows up as last selected object
		temp_object = context.selected_objects[len(context.selected_objects)-1]
		temp_object.name = 'VF-Clipboard-TEMP'
		data_block = temp_object.data
		
		# Target clipboard name
		clipboard_name = 'VF-PersistentClipboard-' + active_object.type
		
		# Remove previous persistent clipboard data if it exists
		if temp_object.type == 'MESH' and bpy.data.meshes.get(clipboard_name):
			bpy.data.meshes.remove(bpy.data.meshes.get(clipboard_name))
		elif temp_object.type == 'CURVE' and bpy.data.curves.get(clipboard_name):
			bpy.data.curves.remove(bpy.data.curves.get(clipboard_name))
		elif temp_object.type == 'SURFACE' and bpy.data.curves.get(clipboard_name):
			bpy.data.curves.remove(bpy.data.curves.get(clipboard_name))
		
		# Rename the data block and save it as persistent
		data_block = temp_object.data
		data_block.name = clipboard_name
		data_block.use_fake_user = True
				
		# Delete the temporary object
		bpy.data.objects.remove(temp_object)
		
		# If more than one object was originally selected, restore that selection set
		if len(selected_objects) > 0:
			# If we don't change modes when re-selecting the original objects, the selection will be updated but the multiple objects selected will remain in object mode
			bpy.ops.object.mode_set(mode='OBJECT')
			# Re-select previously selected objects
			for obj in selected_objects:
				obj.select_set(True)
			# Switch back to edit mode, ensuring all selected objects are editable
			bpy.ops.object.mode_set(mode='EDIT')
		
		print('element(s) copied')
		return {'FINISHED'}

class VF_PasteGeometry(bpy.types.Operator):
	bl_idname = 'object.vf_paste_geometry'
	bl_label = 'Paste'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		return (
			context.active_object
			and context.active_object.type in {'MESH', 'CURVE', 'SURFACE'}
			and context.mode in {'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE'}
			and (
				bpy.data.meshes.get('VF-PersistentClipboard-' + context.active_object.type)
				or bpy.data.curves.get('VF-PersistentClipboard-' + context.active_object.type)
			)
		)
	
	def execute(self, context):
		# Get the current active object
		active_object = context.active_object
		
		# Select everything, to be inverted after joining
		if active_object.type == 'MESH':
			bpy.ops.mesh.select_all(action='SELECT')
		else:
			bpy.ops.curve.select_all(action='SELECT')
			# This appears to not be working on nurb surfaces, and I don't know why
		
		# Switch to object mode for joining
		bpy.ops.object.mode_set(mode='OBJECT')
		
		# Count total elements before joining (assuming Blender always joins the new geometry at the end of the index)
		element_count = 0
		if active_object.type == 'MESH':
			# Vertex selection mode
			if context.tool_settings.mesh_select_mode[0]:
				element_count = len(active_object.data.vertices)
			# Edge selection mode
			elif context.tool_settings.mesh_select_mode[1]:
				element_count = len(active_object.data.edges)
			# Face selection mode
			elif context.tool_settings.mesh_select_mode[2]:
				element_count = len(active_object.data.polygons)
		else:
			element_count = len(active_object.data.splines)
		
		# Source clipboard name (we've already checked that it exists)
		clipboard_name = 'VF-PersistentClipboard-' + active_object.type
		
		# Create a new object
		if active_object.type == 'MESH':
			pasted_object = bpy.data.objects.new(clipboard_name, bpy.data.meshes[clipboard_name])
		else:
			pasted_object = bpy.data.objects.new(clipboard_name, bpy.data.curves[clipboard_name])
		
		# Link the new object to the scene
		context.scene.collection.objects.link(pasted_object)
		
		# Set the object's location, rotation, and scale to match the active object
		pasted_object.location = active_object.location
		pasted_object.rotation_euler = active_object.rotation_euler
		pasted_object.scale = active_object.scale
		
		# Select the new object
		pasted_object.select_set(True)
		
		# Update the viewport and scene
		context.view_layer.update()
		
		# Join pasted object with active object
		bpy.ops.object.join()
		
		# Switch to edit mode
		bpy.ops.object.mode_set(mode='EDIT')
		
		# Invert selection so that the joined geometry is selected
		if active_object.type == 'MESH':
			bpy.ops.mesh.select_all(action='INVERT')
		else:
			bpy.ops.curve.select_all(action='INVERT')
			# This appears to not be working on nurb surfaces, and I don't know why
		
		print('element(s) pasted')
		return {'FINISHED'}

###########################################################################
# Plugin preferences
	
	# Potential options:
	# Option to disable persistent clipboard data (would not persist between close/open cycles)
	# Option to preserve original location or new location

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