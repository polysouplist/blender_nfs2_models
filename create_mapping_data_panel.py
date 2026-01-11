bl_info = {
	"name": "Mapping Properties Panels",
	"author": "PolySoupList",
	"version": (1, 0, 0),
	"blender": (3, 6, 23),
	"location": "Properties Panel > Object Data Properties",
	"description": "Quick access to mapping properties",
	"category": "UI",
}


import bpy
import bmesh


class FaceUnk0Panel(bpy.types.Panel):
	"""Creates a Panel in the Mesh properties window"""
	bl_label = "Face Unk 0"
	bl_idname = "OBJECT_PT_FaceUnk0"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"
	ebm = dict()
	
	@classmethod
	def poll(cls, context):
		if context.mode == 'EDIT_MESH':
			me = context.edit_object.data
			fl = me.polygon_layers_int.get("face_unk0") or me.polygon_layers_int.new(name="face_unk0")
			
			ret = False
			if fl:
				cls.ebm.setdefault(me.name, bmesh.from_edit_mesh(me))
				ret = True
				#return True
			
			if ret == True:
				return True
		
		cls.ebm.clear()
		return False
	
	def draw(self, context):
		layout = self.layout
		me = context.edit_object.data
		layout.prop(me, "face_unk0")


class MappingPanel(bpy.types.Panel):
	"""Creates a Panel in the Mesh properties window"""
	bl_label = "Mapping"
	bl_idname = "OBJECT_PT_Mapping"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"
	ebm = dict()
	
	@classmethod
	def poll(cls, context):
		if context.mode == 'EDIT_MESH':
			me = context.edit_object.data
			f1 = me.polygon_layers_int.get("is_triangle") or me.polygon_layers_int.new(name="is_triangle")
			f2 = me.polygon_layers_int.get("uv_flip") or me.polygon_layers_int.new(name="uv_flip")
			f3 = me.polygon_layers_int.get("flip_normal") or me.polygon_layers_int.new(name="flip_normal")
			f4 = me.polygon_layers_int.get("alpha_clip") or me.polygon_layers_int.new(name="alpha_clip")
			f5 = me.polygon_layers_int.get("double_sided") or me.polygon_layers_int.new(name="double_sided")
			f6 = me.polygon_layers_int.get("unknown") or me.polygon_layers_int.new(name="unknown")
			f7 = me.polygon_layers_int.get("brake_light") or me.polygon_layers_int.new(name="brake_light")
			f8 = me.polygon_layers_int.get("is_wheel") or me.polygon_layers_int.new(name="is_wheel")
			
			if not False in [f1, f2, f3, f4, f5, f6, f7, f8]:
				cls.ebm.setdefault(me.name, bmesh.from_edit_mesh(me))
				return True

		cls.ebm.clear()
		return False

	def draw(self, context):
		layout = self.layout
		me = context.edit_object.data
		
		box = layout.box()
		box.prop(me, "is_triangle")
		box.prop(me, "uv_flip")
		box.prop(me, "flip_normal")
		box.prop(me, "alpha_clip")
		box.prop(me, "double_sided")
		box.prop(me, "unknown")
		box.prop(me, "brake_light")
		box.prop(me, "is_wheel")


def set_int_face_unk0(self, value):
	bm = FaceUnk0Panel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the face unk0 layer
	face_unk0 = (bm.faces.layers.int.get("face_unk0") or bm.faces.layers.int.new("face_unk0"))

	af = None
	for elem in reversed(bm.select_history):
		if isinstance(elem, bmesh.types.BMFace):
			af = elem
			break
	if af:
		af[face_unk0] = value
		bmesh.update_edit_mesh(self)

def get_int_face_unk0(self):
	bm = FaceUnk0Panel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	face_unk0 = bm.faces.layers.int.get("face_unk0") or bm.faces.layers.int.new("face_unk0")

	for elem in reversed(bm.select_history):
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[face_unk0])
	
	return 0


def set_int_is_triangle(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("is_triangle") or bm.faces.layers.int.new("is_triangle"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def set_int_uv_flip(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("uv_flip") or bm.faces.layers.int.new("uv_flip"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def set_int_flip_normal(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("flip_normal") or bm.faces.layers.int.new("flip_normal"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def set_int_alpha_clip(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("alpha_clip") or bm.faces.layers.int.new("alpha_clip"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def set_int_double_sided(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("double_sided") or bm.faces.layers.int.new("double_sided"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def set_int_unknown(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("unknown") or bm.faces.layers.int.new("unknown"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def set_int_brake_light(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("brake_light") or bm.faces.layers.int.new("brake_light"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def set_int_is_wheel(self, value):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))

	# get the mapping layer
	mapping = (bm.faces.layers.int.get("is_wheel") or bm.faces.layers.int.new("is_wheel"))

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			elem[mapping] = value
			bmesh.update_edit_mesh(self)


def get_int_is_triangle(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("is_triangle") or bm.faces.layers.int.new("is_triangle")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def get_int_uv_flip(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("uv_flip") or bm.faces.layers.int.new("uv_flip")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def get_int_flip_normal(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("flip_normal") or bm.faces.layers.int.new("flip_normal")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def get_int_alpha_clip(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("alpha_clip") or bm.faces.layers.int.new("alpha_clip")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def get_int_double_sided(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("double_sided") or bm.faces.layers.int.new("double_sided")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def get_int_unknown(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("unknown") or bm.faces.layers.int.new("unknown")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def get_int_brake_light(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("brake_light") or bm.faces.layers.int.new("brake_light")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def get_int_is_wheel(self):
	bm = MappingPanel.ebm.setdefault(self.name, bmesh.from_edit_mesh(self))
	flag = bm.faces.layers.int.get("is_wheel") or bm.faces.layers.int.new("is_wheel")

	selected_faces = [x for x in bm.faces if x.select]
	for elem in selected_faces:
		if isinstance(elem, bmesh.types.BMFace):
			return(elem[flag])
	
	return 0


def register():
	for klass in CLASSES:
		bpy.utils.register_class(klass)
	
	bpy.types.Mesh.face_unk0 = bpy.props.IntProperty(name="Face Unk 0", description="Face Unk 0", min=-8388608, max=8388607, get=get_int_face_unk0, set=set_int_face_unk0)
	
	bpy.types.Mesh.is_triangle = bpy.props.BoolProperty(name="is_triangle", description="Is triangle? Used on faces where the 3rd and 4th vertices are the same", default=True, get=get_int_is_triangle, set=set_int_is_triangle)
	bpy.types.Mesh.uv_flip = bpy.props.BoolProperty(name="uv_flip", description="Uv flip? Used on faces with flipped texture coordinates", default=False, get=get_int_uv_flip, set=set_int_uv_flip)
	bpy.types.Mesh.flip_normal = bpy.props.BoolProperty(name="flip_normal", description="Flip normal? Used on faces with an inverted normal vector", default=False, get=get_int_flip_normal, set=set_int_flip_normal)
	bpy.types.Mesh.alpha_clip = bpy.props.BoolProperty(name="alpha_clip", description="Alpha clip? Used on faces to determine binary opacity in software mode", default=False, get=get_int_alpha_clip, set=set_int_alpha_clip)
	bpy.types.Mesh.double_sided = bpy.props.BoolProperty(name="double_sided", description="Double sided? Used on faces that are visible from both sides", default=False, get=get_int_double_sided, set=set_int_double_sided)
	bpy.types.Mesh.unknown = bpy.props.BoolProperty(name="unknown", description="Unknown? Unknown", default=False, get=get_int_unknown, set=set_int_unknown)
	bpy.types.Mesh.brake_light = bpy.props.BoolProperty(name="brake_light", description="Brake light? Used on faces with a brake light texture", default=False, get=get_int_brake_light, set=set_int_brake_light)
	bpy.types.Mesh.is_wheel = bpy.props.BoolProperty(name="is_wheel", description="Is wheel? Used on faces with a wheel texture", default=False, get=get_int_is_wheel, set=set_int_is_wheel)


def unregister():
	for klass in CLASSES:
		bpy.utils.unregister_class(klass)
	
	delattr(bpy.types.Mesh, "face_unk0")
	
	delattr(bpy.types.Mesh, "is_triangle")
	delattr(bpy.types.Mesh, "uv_flip")
	delattr(bpy.types.Mesh, "flip_normal")
	delattr(bpy.types.Mesh, "alpha_clip")
	delattr(bpy.types.Mesh, "double_sided")
	delattr(bpy.types.Mesh, "unknown")
	delattr(bpy.types.Mesh, "brake_light")
	delattr(bpy.types.Mesh, "is_wheel")


CLASSES = [FaceUnk0Panel, MappingPanel]


if __name__ == "__main__":
	register()
