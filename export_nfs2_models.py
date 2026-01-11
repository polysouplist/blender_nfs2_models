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
		
		print("Reading scene data for main collection %s..." % (main_collection.name))
		
		objects = main_collection.objects
		object_index = -1
		
		try:
			header_unk0 = main_collection["header_unk0"]
		except:
			print("WARNING: collection %s is missing parameter %s. Assuming some value (0)." % (main_collection.name, '"header_unk0"'))
			header_unk0 = 0
		try:
			header_unk1 = [id_to_int(i) for i in main_collection["header_unk1"]]
		except:
			print("WARNING: collection %s is missing parameter %s. Assuming some value (0)." % (main_collection.name, '"header_unk1"'))
			header_unk1 = [0 for _ in range(32)]
		
		header_unk2 = 0	#Always == 0x0
		
		object_by_index = {}
		for obj in objects:
			if obj.type == 'MESH' and "object_index" in obj:
				idx = obj["object_index"]
				if idx in object_by_index:
					print(f"WARNING: Duplicate object_index {idx}! Skipping duplicate.")
					continue
				object_by_index[idx] = obj
		
		GeoMeshes = []
		
		for index in range(32):
			if index in object_by_index:
				object = object_by_index[index]
				
				num_vrtx, num_plgn, vertices, polygons, status = read_object(object)
				
				if status == 1:
					return {'CANCELLED'}
				
				pos_scale = 65536
				pos = Matrix(np.linalg.inv(m) @ object.matrix_world)
				pos = pos.to_translation()
				pos = [round(pos[0]*pos_scale), round(pos[1]*pos_scale), round(pos[2]*pos_scale)]
				
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
				
				GeoMesh = [num_vrtx, num_plgn, pos, object_unk0, object_unk1, object_unk2, object_unk3, object_unk4, vertices, polygons]			
			else:
				GeoMesh = [0, 0, [0, 0, 0], 0, 0, 0, 1, 1, [], []]
			
			GeoMeshes.append(GeoMesh)
		
		GeoGeometry = [header_unk0, header_unk1, header_unk2, GeoMeshes]
		
		## Writing data
		print("\tWriting data...")
		writing_time = time.time()

		write_GeoGeometry(file_path, GeoGeometry, game_version)

		elapsed_time = time.time() - writing_time
		print("\t... %.4fs" % elapsed_time)	
	
	print("Finished")
	elapsed_time = time.time() - start_time
	print("Elapsed time: %.4fs" % elapsed_time)
	return {'FINISHED'}


def read_object(object):
	num_vrtx = 0
	num_plgn = 0
	vertices = []
	polygons = []
	
	# Inits
	mesh = object.data
	bm = bmesh.new()
	bm.from_mesh(mesh)
	
	vert_scale = 256
	for vert in bm.verts:
		if vert.hide == False:
			vertices.append([round(vert_co*vert_scale) for i, vert_co in enumerate(vert.co)])
			num_vrtx += 1
	
	face_unk0 = bm.faces.layers.int.get("face_unk0")
	#is_triangle = bm.faces.layers.int.get("is_triangle")
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
				return (num_vrtx, num_plgn, vertices, polygons, 1)
			
			vertex_indices = []
			for vert in face.verts:
				vert_index = vert.index
				if vert_index > 0xFF:
					print("ERROR: vertex index forming face higher than the supported by the game on mesh %s. It cannot be above 255." % mesh.name)
					return (num_vrtx, num_plgn, vertices, polygons, 1)
				vertex_indices.append(vert_index)
			
			if len(face.verts) == 3:
				is_triangle = True
				try:
					if face[flip_normal] == True:
						vertex_indices = [vertex_indices[0], vertex_indices[2], vertex_indices[1], vertex_indices[1]]
					else:
						vertex_indices = [vertex_indices[0], vertex_indices[1], vertex_indices[2], vertex_indices[2]]
				except:
					vertex_indices = [vertex_indices[0], vertex_indices[1], vertex_indices[2], vertex_indices[2]]
			elif len(face.verts) == 4:
				is_triangle = False
				try:
					if face[flip_normal] == True:
						vertex_indices = [vertex_indices[0], vertex_indices[3], vertex_indices[2], vertex_indices[1]]
					else:
						vertex_indices = [vertex_indices[0], vertex_indices[1], vertex_indices[2], vertex_indices[3]]
				except:
					vertex_indices = [vertex_indices[0], vertex_indices[1], vertex_indices[2], vertex_indices[3]]
			
			if None in [uv_flip, double_sided, unknown_4, unknown_5, brake_light, is_wheel]:
				try:
					mapping = (is_triangle, False, face[flip_normal], False, False, False, False, False)
				except:
					mapping = (is_triangle, False, False, False, False, False, False, False)
			else:
				mapping = [is_triangle, face[uv_flip], face[flip_normal], face[double_sided], face[unknown_4], face[unknown_5], face[brake_light], face[is_wheel]]
			
			try:
				unk0 = face[face_unk0].to_bytes(3, "little")
			except:
				unk0 = (0).to_bytes(3, "little")
			
			try:
				if mesh.materials[face.material_index] == None:
					print("ERROR: face without material found on mesh %s." % mesh.name)
					return (num_vrtx, num_plgn, vertices, polygons, 1)
			except:
				print("ERROR: face without material found on mesh %s." % mesh.name)
				return (num_vrtx, num_plgn, vertices, polygons, 1)
			
			material_name = mesh.materials[face.material_index].name
			texture_name = (material_name[:4].encode('ascii'))
			
			polygons.append([mapping, unk0, vertex_indices, texture_name])
			num_plgn += 1
	
	bm.clear()
	bm.free()
	
	return (num_vrtx, num_plgn, vertices, polygons, 0)


def write_GeoGeometry(file_path, GeoGeometry, game_version):
	os.makedirs(os.path.dirname(file_path), exist_ok = True)
	
	header_unk0, header_unk1, header_unk2, GeoMeshes = GeoGeometry
	
	with open(file_path, "wb") as f:
		# Writing header
		f.write(struct.pack('<I', header_unk0))
		for i in range(32):
			try:
				f.write(struct.pack('<I', header_unk1[i]))
			except:
				f.write(struct.pack('<I', 0))
		f.write(struct.pack('<Q', header_unk2))
		
		for i in range(0, len(GeoMeshes)):
			num_vrtx, num_plgn, pos, object_unk0, object_unk1, object_unk2, object_unk3, object_unk4, vertices, polygons = GeoMeshes[i]
			
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
				for j in range(0, num_vrtx):
					f.write(struct.pack('<3h', *vertices[j]))
				if num_vrtx % 2 == 1:	#Data offset, happens when num_vrtx is odd
					if game_version == 'OPT_A':
						f.write(b'\x42\x45\x4E\x44' + b'\x00' * 0x2)
					else:
						f.write(struct.pack('<3h', 0, 0, 0))
			
			if num_plgn > 0:
				for j in range(0, num_plgn):
					mapping, unk0, vertex_indices, texture_name = polygons[j]
					mapping = mapping_encode(mapping, "little")
					f.write(mapping)
					f.write(unk0)
					f.write(struct.pack('<4B', *vertex_indices))
					f.write(texture_name)
	
	return 0


def mapping_encode(mapping, endian):
	mapping_value = 0
	
	mapping_names = [
		"is_triangle",
		"uv_flip",
		"flip_normal",
		"double_sided",
		"unknown_4",
		"unknown_5",
		"brake_light",
		"is_wheel"
	]
	
	for i, value in enumerate(mapping):
		if value:
			mapping_value |= (1 << i)
	
	packed_value = (
		(mapping_value & 0xFF)
	)
	
	mapping_bytes = packed_value.to_bytes(1, byteorder=endian)
	
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
