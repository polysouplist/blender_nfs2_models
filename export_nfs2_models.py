#-*- coding:utf-8 -*-

# Blender Need for Speed II (1997) exporter Add-on
# Add-on developed by PolySoupList


bl_info = {
	"name": "Export to Need for Speed II (1997) models format (.geo)",
	"description": "Save objects as Need for Speed II (1997) files",
	"author": "PolySoupList",
	"version": (1, 0, 0),
	"blender": (3, 6, 23),
	"location": "File > Export > Need for Speed II (1997) (.geo)",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"support": "COMMUNITY",
	"category": "Import-Export"}


import bpy
from bpy.types import Operator
from bpy.props import (
	StringProperty,
	BoolProperty,
	EnumProperty
)
from bpy_extras.io_utils import (
	ExportHelper,
	orientation_helper,
	axis_conversion,
)
import bmesh
import math
from mathutils import Matrix
import os
import time
import struct
import numpy as np


def main(context, export_path, game_version, m):
	os.system('cls')
	start_time = time.time()
	
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode='OBJECT')
	
	for main_collection in bpy.context.scene.collection.children:
		is_hidden = bpy.context.view_layer.layer_collection.children.get(main_collection.name).hide_viewport
		is_excluded = bpy.context.view_layer.layer_collection.children.get(main_collection.name).exclude
		
		if is_hidden or is_excluded:
			print("WARNING: skipping main collection %s since it is hidden or excluded." % (main_collection.name))
			print("")
			continue
		
		file_path = os.path.join(export_path, main_collection.name)
		os.makedirs(os.path.dirname(file_path), exist_ok = True)
		
		print("Reading scene data for main collection %s..." % (main_collection.name))
		
		objects = main_collection.objects
		object_index = -1
		
		with open(file_path, "wb") as f:
			try:
				header_unk0 = main_collection["header_unk0"]
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming some value (0)." % (main_collection.name, '"header_unk0"'))
				header_unk0 = 0
			try:
				if len(main_collection["header_unk1"]) == 32:
					header_unk1 = [id_to_int(i) for i in main_collection["header_unk1"]]
				else:
					print("ERROR: collection %s has invalid parameter %s. It should be an array of 32 items." % (main_collection.name, '"header_unk1"'))
					return {"CANCELLED"}
			except:
				print("WARNING: collection %s is missing parameter %s. Assuming some value (0)." % (main_collection.name, '"header_unk1"'))
				header_unk1 = [0 for _ in range(32)]
			
			header_unk2 = 0	#Always == 0x0
			
			# Writing header
			f.write(struct.pack('<I', header_unk0))
			f.write(struct.pack('<32I', *header_unk1))
			f.write(struct.pack('<Q', header_unk2))
			
			object_by_index = {}
			for obj in objects:
				if obj.type == 'MESH' and "object_index" in obj:
					idx = obj["object_index"]
					if idx in object_by_index:
						print(f"WARNING: Duplicate object_index {idx}! Skipping duplicate.")
						continue
					object_by_index[idx] = obj
			
			for index in range(32):
				if index in object_by_index:
					object = object_by_index[index]
					
					num_vrtx = 0
					num_plgn = 0
					vertices = []
					polygons = []
					
					# Inits
					mesh = object.data
					bm = bmesh.new()
					bm.from_mesh(mesh)
					
					pos_scale = 65536
					pos = Matrix(np.linalg.inv(m) @ object.matrix_world)
					pos = pos.to_translation()
					pos = [round(pos[0]*pos_scale),
						   round(pos[1]*pos_scale),
						   round(pos[2]*pos_scale)]
					try:
						object_unk0 = id_to_int(object["object_unk0"])
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value (0)." % (object.name, '"object_unk0"'))
						object_unk0 = 0
					try:
						object_unk1 = id_to_int(object["object_unk1"])
					except:
						print("WARNING: object %s is missing parameter %s. Assuming some value (0)." % (object.name, '"object_unk1"'))
						object_unk1 = 0
					
					object_unk2 = 0	#Always == 0x0
					object_unk3 = 1	#Always == 0x1
					object_unk4 = 1	#Always == 0x1
					
					vert_scale = 256
					for vert in bm.verts:
						if vert.hide == False:
							vertices.append([round(vert_co*vert_scale) for i, vert_co in enumerate(vert.co)])
							num_vrtx += 1
					
					face_unk0 = bm.faces.layers.int.get("face_unk0")
					is_triangle = bm.faces.layers.int.get("is_triangle")
					uv_flip = bm.faces.layers.int.get("uv_flip")
					flip_normal = bm.faces.layers.int.get("flip_normal")
					double_sided = bm.faces.layers.int.get("double_sided")
					unknown_4 = bm.faces.layers.int.get("unknown_4")
					unknown_5 = bm.faces.layers.int.get("unknown_5")
					brake_light = bm.faces.layers.int.get("brake_light")
					is_wheel = bm.faces.layers.int.get("is_wheel")
					
					for face in bm.faces:
						if face.hide == False:
							if len(face.verts) > 4 or len(face.verts) < 3:
								print("ERROR: non triangular or quad face on mesh %s." % mesh.name)
								return {"CANCELLED"}
							if len(face.verts) == 3:
								face[is_triangle] = True
								vert = face.verts
								if face[flip_normal] == 1:
									vertex_indices = [vert[0].index, vert[2].index, vert[1].index, vert[1].index]
								else:
									vertex_indices = [vert[0].index, vert[1].index, vert[2].index, vert[2].index]
							elif len(face.verts) == 4:
								face[is_triangle] = False
								vert = face.verts
								if face[flip_normal] == 1:
									vertex_indices = [vert[0].index, vert[3].index, vert[2].index, vert[1].index]
								else:
									vertex_indices = [vert[0].index, vert[1].index, vert[2].index, vert[3].index]
							
							mapping = [face[is_triangle], face[uv_flip], face[flip_normal], face[double_sided], face[unknown_4], face[unknown_5], face[brake_light], face[is_wheel]]
							mapping = mapping_encode(mapping, "little")
							
							try:
								unk0 = face[face_unk0].to_bytes(3, "little")
							except:
								unk0 = (0).to_bytes(3, "little")
							
							try:
								if mesh.materials[face.material_index] == None:
									print("ERROR: face without material found on mesh %s." % mesh.name)
									return {"CANCELLED"}
							except:
								print("ERROR: face without material found on mesh %s." % mesh.name)
								return {"CANCELLED"}
							
							material_name = mesh.materials[face.material_index].name
							texture_name = (material_name[:4].encode('ascii'))
							
							polygons.append([mapping, unk0, vertex_indices, texture_name])
							num_plgn += 1
					
					bm.clear()
					bm.free()
					
					# Writing body
					f.write(struct.pack('<I', num_vrtx))
					f.write(struct.pack('<I', num_plgn))
					f.write(struct.pack('<3i', *pos))
					f.write(struct.pack('<I', object_unk0))
					f.write(struct.pack('<I', object_unk1))
					f.write(struct.pack('<Q', object_unk2))
					f.write(struct.pack('<Q', object_unk3))
					f.write(struct.pack('<Q', object_unk4))
					
					if num_vrtx > 0:
						for i in range(0, num_vrtx):
							f.write(struct.pack('<3h', *vertices[i]))
						if num_vrtx % 2 == 1:	#Data offset, happens when num_vrtx is odd
							if game_version == 'OPT_A':
								f.write(b'\x42\x45\x4E\x44' + b'\x00' * 0x2)
							else:
								f.write(struct.pack('<3h', 0, 0, 0))
					
					if num_plgn > 0:
						for i in range(0, num_plgn):
							mapping, unk0, vertex_indices, texture_name = polygons[i]
							f.write(mapping)
							f.write(unk0)
							f.write(struct.pack('<4B', *vertex_indices))
							f.write(texture_name)
				
				else:
					f.write(struct.pack('<I', 0))
					f.write(struct.pack('<I', 0))
					f.write(struct.pack('<3i', 0, 0, 0))
					f.write(struct.pack('<I', 0))
					f.write(struct.pack('<I', 0))
					f.write(struct.pack('<Q', 0))
					f.write(struct.pack('<Q', 1))
					f.write(struct.pack('<Q', 1))
	
	print("Finished")
	elapsed_time = time.time() - start_time
	print("Elapsed time: %.4fs" % elapsed_time)
	return {'FINISHED'}


def mapping_encode(mapping, endian):
	# Step 1: Pack mapping into a 8-bit integer
	mapping_value = 0
	mapping_names = [
	"is_triangle", "uv_flip", "flip_normal", "double_sided",
	"unknown_4", "unknown_5", "brake_light", "is_wheel"
	]
	
	# Set the corresponding mapping bits
	for i, value in enumerate(mapping):
		if value:  # Set the bit at position i if the mapping is 1
			mapping_value |= (1 << i)  # Bitwise OR to set the i-th bit
	
	# Step 2: Pack everything into a 8-bit integer using bit shifting
	packed_value = (
		(mapping_value & 0xFF)            # 4 bits for mapping
	)
	
	# Step 3: Convert the packed 8-bit integer to a 1-byte sequence
	mapping_bytes = packed_value.to_bytes(1, byteorder=endian)
	
	# Step 4: Print the output as hexadecimal byte
	#hex_output = ' '.join(f'{byte:02X}' for byte in mapping_bytes)
	
	return mapping_bytes


def id_to_int(id):
	id_old = id
	id = id.replace('_', '')
	id = id.replace(' ', '')
	id = id.replace('-', '')
	id = ''.join(id[::-1][x:x+2][::-1] for x in range(0, len(id), 2))
	return int(id, 16)


@orientation_helper(axis_forward='-Y', axis_up='Z')
class ExportNFS2(Operator, ExportHelper):
	"""Export as a Need for Speed II (1997) Model file"""
	bl_idname = "export_nfs2.data"
	bl_label = "Export to folder"
	bl_options = {'PRESET'}

	filename_ext = ""
	use_filter_folder = True

	filter_glob: StringProperty(
			options={'HIDDEN'},
			default="*.geo",
			maxlen=255,
			)
	
	game_version: EnumProperty(
		name="Game version",
		description="Choose the resource version you want to load",
		items=(('OPT_A', "NFS2", "Need for Speed II"),
			   ('OPT_B', "NFS2SE", "Need for Speed II: Special Edition")),
		default='OPT_A',
		)

	
	def execute(self, context):
		userpath = self.properties.filepath
		if os.path.isfile(userpath):
			self.report({"ERROR"}, "Please select a directory not a file\n" + userpath)
			return {"CANCELLED"}
		
		global_matrix = axis_conversion(from_forward='Z', from_up='Y', to_forward=self.axis_forward, to_up=self.axis_up).to_4x4()
		
		status = main(context, self.filepath, self.game_version, global_matrix)
		
		if status == {"CANCELLED"}:
			self.report({"ERROR"}, "Exporting has been cancelled. Check the system console for information.")
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
		col.label(text="Settings", icon="SETTINGS")
		
		box.prop(operator, "game_version")
		
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


def menu_func_export(self, context):
	pcoll = preview_collections["main"]
	my_icon = pcoll["my_icon"]
	self.layout.operator(ExportNFS2.bl_idname, text="Need for Speed II (1997) (.geo)", icon_value=my_icon.icon_id)


classes = (
		ExportNFS2,
)

preview_collections = {}


def register():
	import bpy.utils.previews
	pcoll = bpy.utils.previews.new()
	
	my_icons_dir = os.path.join(os.path.dirname(__file__), "polly_icons")
	pcoll.load("my_icon", os.path.join(my_icons_dir, "nfs2_icon.png"), 'IMAGE')

	preview_collections["main"] = pcoll
	
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
	for pcoll in preview_collections.values():
		bpy.utils.previews.remove(pcoll)
	preview_collections.clear()
	
	for cls in classes:
		bpy.utils.unregister_class(cls)
	bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
	register()
