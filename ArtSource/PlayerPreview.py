"""
ZombieAutoShooter - 主角风格预览模型 v2（低多边形 Q 版幸存者）
Blender 5.2 headless 生成 + FBX 导出。

用法:
  blender --background --factory-startup --python PlayerPreview.py

v2 改动: 加肩部球体衔接、袖子独立色、胸前斜挎带+背包带、嘴部、
        手枪放大、手臂改为带倒角长方体（低多边形更干净）。
"""
import bpy
import math
import os

OUT_DIR = r"D:\MYGAME\ZombieAutoShooter\ArtSource"
OUT_FBX = os.path.join(OUT_DIR, "PlayerPreview.fbx")
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)


def make_mat(name, rgb, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return m


M_SKIN   = make_mat("MAT_Skin",    (0.86, 0.66, 0.50))
M_JACKET = make_mat("MAT_Jacket",  (0.15, 0.34, 0.56))
M_SLEEVE = make_mat("MAT_Sleeve",  (0.11, 0.26, 0.46))
M_PANTS  = make_mat("MAT_Pants",   (0.20, 0.21, 0.24))
M_BOOT   = make_mat("MAT_Boots",   (0.33, 0.21, 0.12))
M_CAP    = make_mat("MAT_Cap",     (0.24, 0.40, 0.24))
M_GUN    = make_mat("MAT_Gun",     (0.11, 0.11, 0.13), rough=0.55, metal=0.6)
M_SCARF  = make_mat("MAT_Scarf",   (0.86, 0.34, 0.14))
M_PACK   = make_mat("MAT_Pack",    (0.29, 0.33, 0.19))
M_EYE    = make_mat("MAT_Eye",     (0.04, 0.04, 0.05), rough=0.35)


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)


def bevel(obj, width=0.025, segments=2):
    md = obj.modifiers.new("bevel", "BEVEL")
    md.width = width
    md.segments = segments
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(50)


def box(name, size, loc, rot=(0, 0, 0), mat=M_JACKET, bev=0.02, seg=2):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev > 0:
        bevel(o, bev, seg)
    assign(o, mat)
    return o


def sphere(name, r, loc, scale=(1, 1, 1), mat=M_SKIN, segs=14, rings=9):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, mat)
    return o


def cyl(name, r, h, loc, rot=(0, 0, 0), mat=M_JACKET, verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    assign(o, mat)
    return o


def torus(name, major, minor, loc, mat=M_SCARF):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=16, minor_segments=8, location=loc)
    o = bpy.context.active_object
    o.name = name
    assign(o, mat)
    return o


parts = []

# ---------- 腿 + 靴 ----------
for sx in (-1, 1):
    side = "L" if sx < 0 else "R"
    parts.append(box("Leg_" + side, (0.150, 0.170, 0.620), (0.112 * sx, 0.0, 0.470),
                     mat=M_PANTS, bev=0.03))
    parts.append(box("Boot_" + side, (0.180, 0.300, 0.140), (0.112 * sx, -0.045, 0.075),
                     mat=M_BOOT, bev=0.035))

# ---------- 胯 + 腰带 ----------
parts.append(box("Hips", (0.360, 0.250, 0.220), (0, 0, 0.760), mat=M_PANTS, bev=0.04))
parts.append(box("Belt", (0.385, 0.270, 0.070), (0, 0, 0.885), mat=M_BOOT, bev=0.02))
parts.append(box("Buckle", (0.070, 0.030, 0.055), (0, -0.142, 0.885), mat=M_GUN, bev=0.010, seg=1))

# ---------- 躯干 ----------
parts.append(box("Torso", (0.410, 0.280, 0.490), (0, 0, 1.145), mat=M_JACKET, bev=0.055, seg=3))
parts.append(box("Zipper", (0.028, 0.020, 0.460), (0, -0.150, 1.145), mat=M_PANTS, bev=0.008, seg=1))
# 胸前斜挎带
parts.append(box("Strap", (0.060, 0.024, 0.600), (0.010, -0.152, 1.150),
                 rot=(0, math.radians(28), 0), mat=M_BOOT, bev=0.010, seg=1))
# 背包带（前面两条）
for sx in (-1, 1):
    parts.append(box("PackStrap_" + ("L" if sx < 0 else "R"), (0.050, 0.020, 0.380),
                     (0.130 * sx, -0.150, 1.140), mat=M_PACK, bev=0.008, seg=1))

# ---------- 背包 ----------
parts.append(box("Backpack", (0.300, 0.170, 0.330), (0, 0.225, 1.150), mat=M_PACK, bev=0.05, seg=3))
parts.append(box("PackTop", (0.220, 0.130, 0.080), (0, 0.230, 1.345), mat=M_PACK, bev=0.03))
parts.append(box("PackPocket", (0.200, 0.060, 0.140), (0, 0.320, 1.090), mat=M_PACK, bev=0.02))

# ---------- 肩 + 手臂 + 手 ----------
for sx in (-1, 1):
    side = "L" if sx < 0 else "R"
    ang = math.radians(10) * (-1 if sx < 0 else 1)
    parts.append(sphere("Shoulder_" + side, 0.105, (0.205 * sx, 0.0, 1.345), mat=M_SLEEVE, segs=12, rings=7))
    parts.append(box("Arm_" + side, (0.135, 0.150, 0.400), (0.288 * sx, 0.0, 1.105),
                     rot=(0, ang, 0), mat=M_SLEEVE, bev=0.03))
    parts.append(sphere("Hand_" + side, 0.080, (0.318 * sx, -0.015, 0.880), mat=M_SKIN))

# ---------- 脖子 + 围巾 + 头 ----------
parts.append(cyl("Neck", 0.070, 0.110, (0, 0, 1.395), mat=M_SKIN))
parts.append(torus("Scarf", 0.160, 0.050, (0, 0, 1.375)))
parts.append(sphere("Head", 0.255, (0, 0, 1.590), scale=(1.0, 0.96, 1.02), mat=M_SKIN))

for sx in (-1, 1):
    side = "L" if sx < 0 else "R"
    parts.append(sphere("Eye_" + side, 0.038, (0.090 * sx, -0.238, 1.605), mat=M_EYE, segs=10, rings=6))
# 嘴（一条短线）
parts.append(box("Mouth", (0.075, 0.012, 0.016), (0, -0.248, 1.505), mat=M_EYE, bev=0.004, seg=1))

# ---------- 棒球帽 ----------
parts.append(cyl("CapCrown", 0.262, 0.105, (0, 0.010, 1.795), mat=M_CAP, verts=16))
parts.append(sphere("CapTop", 0.262, (0, 0.010, 1.800), scale=(1.0, 1.0, 0.42), mat=M_CAP, segs=16, rings=8))
parts.append(box("CapVisor", (0.300, 0.190, 0.035), (0, -0.230, 1.755),
                 rot=(math.radians(-6), 0, 0), mat=M_CAP, bev=0.012, seg=1))

# ---------- 手枪（右手，朝前）----------
parts.append(box("GunBody", (0.075, 0.340, 0.110), (0.330, -0.175, 0.900), mat=M_GUN, bev=0.012, seg=1))
parts.append(box("GunGrip", (0.062, 0.085, 0.165), (0.330, -0.015, 0.830),
                 rot=(math.radians(14), 0, 0), mat=M_GUN, bev=0.012, seg=1))
parts.append(box("GunSight", (0.022, 0.050, 0.030), (0.330, -0.330, 0.945), mat=M_GUN, bev=0.005, seg=1))

# ---------- 组织层级 ----------
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
root = bpy.context.active_object
root.name = "PlayerPreview"
for o in parts:
    o.parent = root
    o.matrix_parent_inverse = root.matrix_world.inverted()

tri = 0
for o in parts:
    if o.type == 'MESH':
        o.data.calc_loop_triangles()
        tri += len(o.data.loop_triangles)

bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=False,
    use_mesh_modifiers=True,
    mesh_smooth_type='OFF',
    bake_anim=False,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
    path_mode='AUTO',
    embed_textures=False,
)
print("EXPORT_OK=%s" % OUT_FBX)
print("FBX_BYTES=%d" % os.path.getsize(OUT_FBX))
print("OBJECTS=%d TRIS=%d" % (len(parts), tri))
