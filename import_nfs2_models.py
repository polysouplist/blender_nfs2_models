#-*- coding:utf-8 -*-

# Blender Need for Speed II (1997) importer Add-on
# Add-on developed by PolySoupList


bl_info = {
	"name": "Import Need for Speed II (1997) models format (.geo)",
	"description": "Import meshes files from Need for Speed II (1997)",
	"author": "PolySoupList",
	"version": (1, 0, 0),
	"blender": (3, 6, 23),
	"location": "File > Import > Need for Speed II (1997) (.geo)",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"support": "COMMUNITY",
	"category": "Import-Export"}


import bpy
from bpy.types import (
	Operator,
	OperatorFileListElement
)
from bpy.props import (
	StringProperty,
	BoolProperty,
	CollectionProperty
)
from bpy_extras.io_utils import (
	ImportHelper,
	orientation_helper,
	axis_conversion,
)
import bmesh
import math
from mathutils import Matrix
import os
import time
import struct


def main(context, file_path, clear_scene, global_matrix):
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode='OBJECT')
	
	if clear_scene == True:
		print("Clearing scene...")
		clearScene(context)
	
	status = import_nfs2_models(context, file_path, clear_scene, global_matrix)
	
	return status


def import_nfs2_models(context, file_path, clear_scene, m):
	start_time = time.time()
	
	main_collection_name = os.path.basename(file_path)
	main_collection = bpy.data.collections.new(main_collection_name)
	bpy.context.scene.collection.children.link(main_collection)
	
	print("Importing file %s" % os.path.basename(file_path))
	
	with open(file_path, "rb") as f:
		header_unk0 = struct.unpack('<I', f.read(0x4))[0]
		main_collection["header_unk0"] = header_unk0
		
		header_unk1 = struct.unpack('<32I', f.read(0x80))
		main_collection["header_unk1"] = [int_to_id(i) for i in header_unk1]
		
		header_unk2 = struct.unpack('<Q', f.read(0x8))[0]	#Always == 0x0
		
		for index in range(32):
			vertices = []
			faces = []
			additional_data = []
			
			geoPartName = get_geoPartNames(index)
			num_vrtx = struct.unpack('<I', f.read(0x4))[0]
			num_plgn = struct.unpack('<I', f.read(0x4))[0]
			pos = struct.unpack('<3i', f.read(0xC))
			pos = [pos[0]/65536, pos[1]/65536, pos[2]/65536]
			
			object_unk0 = struct.unpack('<I', f.read(0x4))[0]
			object_unk1 = struct.unpack('<I', f.read(0x4))[0]
			object_unk2 = struct.unpack('<Q', f.read(0x8))[0]	#Always == 0x0
			object_unk3 = struct.unpack('<Q', f.read(0x8))[0]	#Always == 0x1
			object_unk4 = struct.unpack('<Q', f.read(0x8))[0]	#Always == 0x1
			
			for i in range (num_vrtx):
				vertex = struct.unpack('<3h', f.read(0x6))
				vertex = [vertex[0]/256, vertex[1]/256, vertex[2]/256]
				vertices.append ((vertex[0], vertex[1], vertex[2]))
			if num_vrtx % 2 == 1:	#Data offset, happens when num_vrtx is odd
				additional_data = f.read(0x6)
			
			for i in range(num_plgn):
				mapping = mapping_decode(f.read(0x1), "little")
				unk0 = int.from_bytes(f.read(0x3), "little")  
				vertex_indices = struct.unpack('<4B', f.read(0x4))
				texture_name = f.read(0x4)
				
				faces.append([mapping, unk0, vertex_indices, texture_name])
			
			if num_vrtx > 0:
				#==================================================================================================
				#Building Mesh
				#==================================================================================================
				me_ob = bpy.data.meshes.new(geoPartName)
				obj = bpy.data.objects.new(geoPartName, me_ob)
				
				#Get a BMesh representation
				bm = bmesh.new()
				
				#Creating new properties
				face_unk0 = (bm.faces.layers.int.get("face_unk0") or bm.faces.layers.int.new("face_unk0"))
				is_triangle = (bm.faces.layers.int.get("is_triangle") or bm.faces.layers.int.new("is_triangle"))
				uv_flip = (bm.faces.layers.int.get("uv_flip") or bm.faces.layers.int.new("uv_flip"))
				flip_normal = (bm.faces.layers.int.get("flip_normal") or bm.faces.layers.int.new("flip_normal"))
				double_sided = (bm.faces.layers.int.get("double_sided") or bm.faces.layers.int.new("double_sided"))
				unknown_4 = (bm.faces.layers.int.get("unknown_4") or bm.faces.layers.int.new("unknown_4"))
				unknown_5 = (bm.faces.layers.int.get("unknown_5") or bm.faces.layers.int.new("unknown_5"))
				brake_light = (bm.faces.layers.int.get("brake_light") or bm.faces.layers.int.new("brake_light"))
				is_wheel = (bm.faces.layers.int.get("is_wheel") or bm.faces.layers.int.new("is_wheel"))
				
				BMVert_dictionary = {}
				
				uvName = "UVMap" #or UV1Map
				uv_layer = bm.loops.layers.uv.get(uvName) or bm.loops.layers.uv.new(uvName)
				
				for i, position in enumerate(vertices):
					BMVert = bm.verts.new(position)
					BMVert.index = i
					BMVert_dictionary[i] = BMVert
				
				for i, face in enumerate(faces):
					mapping, unk0, vertex_indices, texture_name = face
					
					if mapping[0][1] == 1:	#is_triangle
						face_vertices = [BMVert_dictionary[vertex_indices[0]], BMVert_dictionary[vertex_indices[1]], BMVert_dictionary[vertex_indices[2]]]
						face_uvs = [[0, 0], [1, 0], [1, 1]]
						if mapping[1][1] == 1:	#uv_flip
							face_uvs = [[0, 1], [1, 1], [1, 0]]
					else:
						face_vertices = [BMVert_dictionary[vertex_indices[0]], BMVert_dictionary[vertex_indices[1]], BMVert_dictionary[vertex_indices[2]], BMVert_dictionary[vertex_indices[3]]]
						face_uvs = [[0, 1], [1, 1], [1, 0], [0, 0]]
						if mapping[1][1] == 1:	#uv_flip
							face_uvs = [[0, 0], [1, 0], [1, 1], [0, 1]]
					try:
						BMFace = bm.faces.get(face_vertices) or bm.faces.new(face_vertices)
					except:
						pass
					if BMFace.index != -1:
						BMFace = BMFace.copy(verts=False, edges=False)
					BMFace.index = i
					BMFace[face_unk0] = unk0
					BMFace[is_triangle] = mapping[0][1]
					BMFace[uv_flip] = mapping[1][1]
					BMFace[flip_normal] = mapping[2][1]
					BMFace[double_sided] = mapping[3][1]
					BMFace[unknown_4] = mapping[4][1]
					BMFace[unknown_5] = mapping[5][1]
					BMFace[brake_light] = mapping[6][1]
					BMFace[is_wheel] = mapping[7][1]
					
					material_name = str(texture_name, 'ascii')
					mat = bpy.data.materials.get(material_name)
					if mat == None:
						mat = bpy.data.materials.new(material_name)
						mat.use_nodes = True
						mat.name = material_name
						
						if mat.node_tree.nodes[0].bl_idname != "ShaderNodeOutputMaterial":
							mat.node_tree.nodes[0].name = material_name
					
					if mat.name not in me_ob.materials:
						me_ob.materials.append(mat)
					
					BMFace.material_index = me_ob.materials.find(mat.name)
					
					for loop, uv in zip(BMFace.loops, face_uvs):
						loop[uv_layer].uv = uv
					
					if mapping[2][1] == 1:	#flip_normal
						BMFace.normal_flip()
				
				#Finish up, write the bmesh back to the mesh
				bm.to_mesh(me_ob)
				bm.free()
				
				if additional_data:
					me_ob["additional_data"] = additional_data
				obj["object_index"] = index
				obj["object_unk0"] = int_to_id(object_unk0)
				obj["object_unk1"] = int_to_id(object_unk1)
				main_collection.objects.link(obj)
				bpy.context.view_layer.objects.active = obj
				obj.matrix_world = m @ Matrix.Translation(pos)
	
	## Adjusting scene
	for window in bpy.context.window_manager.windows:
		for area in window.screen.areas:
			if area.type == 'VIEW_3D':
				for space in area.spaces:
					if space.type == 'VIEW_3D':
						space.shading.type = 'MATERIAL'
				region = next(region for region in area.regions if region.type == 'WINDOW')
				override = bpy.context.copy()
				override['area'] = area
				override['region'] = region
				bpy.ops.view3d.view_all(override, use_all_regions=False, center=False)
	
	print("Finished")
	elapsed_time = time.time() - start_time
	print("Elapsed time: %.4fs" % elapsed_time)
	return {'FINISHED'}


def get_geoPartNames(index):
	geoPartNames = {0: "High-Poly Additional Body Part",
					1: "High-Poly Main Body Part",
					2: "High-Poly Ground Part",
					3: "High-Poly Front Part",
					4: "High-Poly Back Part",
					5: "High-Poly Left Side Part",
					6: "High-Poly Right Side Part",
					7: "High-Poly Additional Left Side Part",
					8: "High-Poly Additional Right Side Part",
					9: "High-Poly Spoiler Part",
					10: "High-Poly Additional Part",
					11: "High-Poly Backlights",
					12: "High-Poly Front Right Wheel",
					13: "High-Poly Front Right Wheel Part",
					14: "High-Poly Front Left Wheel",
					15: "High-Poly Front Left Wheel Part",
					16: "High-Poly Rear Right Wheel",
					17: "High-Poly Rear Right Wheel Part",
					18: "High-Poly Rear Left Wheel",
					19: "High-Poly Rear Left Wheel Part",
					20: "Medium-Poly Additional Body Part",
					21: "Medium-Poly Main Body Part",
					22: "Medium-Poly Ground Part",
					23: "Low-Poly Wheel Part",
					24: "Low-Poly Main Part",
					25: "Low-Poly Side Part",
					26: "Reserved space for part",
					27: "Reserved space for part",
					28: "Reserved space for part",
					29: "Reserved space for part",
					30: "Reserved space for part",
					31: "Reserved space for part"}
	
	return geoPartNames[index]


def mapping_decode(mapping, endian):
	# Step 1: Swap the endianness
	# Convert bytes to an integer, swap the endianness using `int.from_bytes`.
	swapped = int.from_bytes(mapping, byteorder=endian)  # Swap to little-endian
	
	# Step 2: Convert to binary string
	# Convert the integer to a binary string, padding with leading zeros to make it 8 bits.
	binary_str = format(swapped, '008b')
	
	# Step 3: Split the bits according to specified offsets and lengths and convert them to integers
	mapping = int(binary_str[0:8], 2)      # Offset 0, length 8
	
	# Step 4: Unpack the mapping using bit shifts
	mapping_names = [
		"is_triangle",			# Bit 0
		"uv_flip",				# Bit 1
		"flip_normal",			# Bit 2
		"double_sided",			# Bit 3
		"unknown_4",			# Bit 4
		"unknown_5",			# Bit 5
		"brake_light",			# Bit 6
		"is_wheel"				# Bit 7
	]
	
	# Extracting each mapping's state
	mapping_values = [(mapping >> i) & 1 for i in range(8)]
	
	mapping = [(name, value) for name, value in zip(mapping_names, mapping_values)]
	
	## Keeping only the used mapping (those with value 1)
	#used_mapping = [(name, value) for name, value in zip(mapping_names, mapping_values) if value == 1]
	
	return(mapping)


def int_to_id(id):
	id = str(hex(int(id)))[2:].upper().zfill(8)
	id = '_'.join([id[::-1][x : x+2][::-1] for x in range(0, len(id), 2)])
	return id


def clearScene(context): # OK
	#for obj in bpy.context.scene.objects:
	#	obj.select_set(True)
	#bpy.ops.object.delete()

	for block in bpy.data.objects:
		#if block.users == 0:
		bpy.data.objects.remove(block, do_unlink = True)

	for block in bpy.data.meshes:
		if block.users == 0:
			bpy.data.meshes.remove(block)

	for block in bpy.data.materials:
		if block.users == 0:
			bpy.data.materials.remove(block)

	for block in bpy.data.textures:
		if block.users == 0:
			bpy.data.textures.remove(block)

	for block in bpy.data.images:
		if block.users == 0:
			bpy.data.images.remove(block)
	
	for block in bpy.data.cameras:
		if block.users == 0:
			bpy.data.cameras.remove(block)
	
	for block in bpy.data.lights:
		if block.users == 0:
			bpy.data.lights.remove(block)
	
	for block in bpy.data.armatures:
		if block.users == 0:
			bpy.data.armatures.remove(block)
	
	for block in bpy.data.collections:
		if block.users == 0:
			bpy.data.collections.remove(block)
		else:
			bpy.data.collections.remove(block, do_unlink=True)


@orientation_helper(axis_forward='-Y', axis_up='Z')
class ImportNFS2(Operator, ImportHelper):
	"""Load a Need for Speed II (1997) model file"""
	bl_idname = "import_nfs2.data"  # important since its how bpy.ops.import_test.some_data is constructed
	bl_label = "Import models"
	bl_options = {'PRESET'}
	
	# ImportHelper mixin class uses this
	filename_ext = ".geo"
	
	filter_glob: StringProperty(
			options={'HIDDEN'},
			default="*.geo",
			maxlen=255,  # Max internal buffer length, longer would be clamped.
			)
	
	files: CollectionProperty(
			type=OperatorFileListElement,
			)
	
	directory: StringProperty(
			# subtype='DIR_PATH' is not needed to specify the selection mode.
			subtype='DIR_PATH',
			)
	
	# List of operator properties, the attributes will be assigned
	# to the class instance from the operator settings before calling.
	
	clear_scene: BoolProperty(
			name="Clear scene",
			description="Check in order to clear the scene",
			default=True,
			)
	
	def execute(self, context): # OK
		global_matrix = axis_conversion(from_forward='Z', from_up='Y', to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()
		
		if len(self.files) > 1:
			os.system('cls')
		
			files_path = []
			for file_elem in self.files:
				files_path.append(os.path.join(self.directory, file_elem.name))
			
			print("Importing %d files" % len(files_path))
			
			if self.clear_scene == True:
				print("Clearing initial scene...")
				clearScene(context)
				print("Setting 'clear_scene' to False now...")
				self.clear_scene = False
			
			print()
			
			for file_path in files_path:
				status = main(context, file_path, self.clear_scene, global_matrix)
				
				if status == {"CANCELLED"}:
					self.report({"ERROR"}, "Importing of file %s has been cancelled. Check the system console for information." % os.path.splitext(os.path.basename(file_path))[0])
				
				print()
				
			return {'FINISHED'}
		elif os.path.isfile(self.filepath) == False:
			os.system('cls')
			
			files_path = []
			for file in os.listdir(self.filepath):
				file_path = os.path.join(self.filepath, file)
				if os.path.isfile(file_path) == True:
					files_path.append(file_path)
				print("Importing %d files" % len(files_path))
			
			for file_path in files_path:
				status = main(context, file_path, self.clear_scene, global_matrix)
				
				if status == {"CANCELLED"}:
					self.report({"ERROR"}, "Importing of file %s has been cancelled. Check the system console for information." % os.path.splitext(os.path.basename(file_path))[0])
				
				print()
				
			return {'FINISHED'}
		else:
			os.system('cls')
			
			status = main(context, self.filepath, self.clear_scene, global_matrix)
			
			if status == {"CANCELLED"}:
				self.report({"ERROR"}, "Importing has been cancelled. Check the system console for information.")
			
			return status
	
	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False  # No animation.
		
		sfile = context.space_data
		operator = sfile.active_operator
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Preferences", icon="OPTIONS")
		
		box.prop(operator, "clear_scene")
		
		##
		box = layout.box()
		split = box.split(factor=0.75)
		col = split.column(align=True)
		col.label(text="Blender orientation", icon="OBJECT_DATA")
		
		row = box.row(align=True)
		row.label(text="Forward axis")
		row.use_property_split = False
		row.prop_enum(operator, "axis_forward", 'X', text='X')
		row.prop_enum(operator, "axis_forward", 'Y', text='Y')
		row.prop_enum(operator, "axis_forward", 'Z', text='Z')
		row.prop_enum(operator, "axis_forward", '-X', text='-X')
		row.prop_enum(operator, "axis_forward", '-Y', text='-Y')
		row.prop_enum(operator, "axis_forward", '-Z', text='-Z')
		
		row = box.row(align=True)
		row.label(text="Up axis")
		row.use_property_split = False
		row.prop_enum(operator, "axis_up", 'X', text='X')
		row.prop_enum(operator, "axis_up", 'Y', text='Y')
		row.prop_enum(operator, "axis_up", 'Z', text='Z')
		row.prop_enum(operator, "axis_up", '-X', text='-X')
		row.prop_enum(operator, "axis_up", '-Y', text='-Y')
		row.prop_enum(operator, "axis_up", '-Z', text='-Z')


def menu_func_import(self, context): # OK
	pcoll = preview_collections["main"]
	my_icon = pcoll["my_icon"]
	self.layout.operator(ImportNFS2.bl_idname, text="Need for Speed II (1997) (.geo)", icon_value=my_icon.icon_id)


classes = (
		ImportNFS2,
)

preview_collections = {}


def register(): # OK
	import bpy.utils.previews
	pcoll = bpy.utils.previews.new()
	
	my_icons_dir = os.path.join(os.path.dirname(__file__), "polly_icons")
	pcoll.load("my_icon", os.path.join(my_icons_dir, "nfs2_icon.png"), 'IMAGE')

	preview_collections["main"] = pcoll
	
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister(): # OK
	for pcoll in preview_collections.values():
		bpy.utils.previews.remove(pcoll)
	preview_collections.clear()
	
	for cls in classes:
		bpy.utils.unregister_class(cls)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
	register()
