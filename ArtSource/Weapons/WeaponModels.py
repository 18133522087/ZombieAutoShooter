"""
ZombieAutoShooter - 枪械美术资源（低多边形，纯色）
Blender 5.2 headless：生成 手枪 / 散弹枪 / 突击步枪，分别导出 FBX。

坐标约定：枪口朝 -Y（Blender 前方），枪身向上 +Z；握把根部在原点。
导出到 Unity 后：枪口朝 +Z（角色前方），握把原点即挂点，另带 Muzzle 空物体。
"""
import bpy
import math
import os

OUT_DIR = r"D:\MYGAME\ZombieAutoShooter\ArtSource\Weapons"
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)


def make_mat(name, rgb, rough=0.55, metal=0.35):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return m


M_METAL   = make_mat("MAT_GunMetal",   (0.12, 0.12, 0.14), rough=0.45, metal=0.65)
M_POLYMER = make_mat("MAT_GunPolymer", (0.17, 0.17, 0.19), rough=0.75, metal=0.05)
M_WOOD    = make_mat("MAT_GunWood",    (0.35, 0.22, 0.12), rough=0.7,  metal=0.0)
M_ACCENT  = make_mat("MAT_GunAccent",  (0.90, 0.45, 0.12), rough=0.5,  metal=0.2)


def clear_objects():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def assign(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


def bev(o, w=0.004, seg=1):
    md = o.modifiers.new("bevel", "BEVEL")
    md.width = w
    md.segments = seg
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(50)


def box(parts, name, size, loc, rot=(0, 0, 0), m=M_METAL, b=0.004, seg=1):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if b > 0:
        bev(o, b, seg)
    assign(o, m)
    parts.append(o)
    return o


def cyl(parts, name, r, h, loc, rot=(math.radians(90), 0, 0), m=M_METAL, verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    assign(o, m)
    parts.append(o)
    return o


def sph(parts, name, r, loc, m=M_METAL, segs=10, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    assign(o, m)
    parts.append(o)
    return o


def finalize(parts, root_name, muzzle_loc):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    root = bpy.context.active_object
    root.name = root_name
    for o in parts:
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()

    bpy.ops.object.empty_add(type='ARROWS', location=muzzle_loc)
    muzzle = bpy.context.active_object
    muzzle.name = "Muzzle"
    muzzle.parent = root
    muzzle.matrix_parent_inverse = root.matrix_world.inverted()

    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for o in parts:
        o.select_set(True)
    muzzle.select_set(True)
    bpy.context.view_layer.objects.active = root


def export(path):
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        use_mesh_modifiers=True,
        mesh_smooth_type='OFF',
        bake_anim=False,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        path_mode='AUTO',
        embed_textures=False,
    )
    print("EXPORT_OK=%s bytes=%d" % (path, os.path.getsize(path)))


# ============================================================
# 1) 手枪
# ============================================================
def build_pistol():
    clear_objects()
    parts = []
    box(parts, "Slide", (0.048, 0.240, 0.070), (0, -0.075, 0.035), m=M_METAL)
    box(parts, "Frame", (0.044, 0.150, 0.048), (0, -0.045, -0.012), m=M_POLYMER)
    box(parts, "Grip", (0.044, 0.075, 0.145), (0, 0.030, -0.095), rot=(math.radians(-12), 0, 0), m=M_POLYMER)
    box(parts, "GripPanel", (0.048, 0.055, 0.100), (0, 0.032, -0.095), rot=(math.radians(-12), 0, 0), m=M_ACCENT, b=0.002)
    box(parts, "GuardBottom", (0.012, 0.060, 0.010), (0, -0.005, -0.065), m=M_METAL, b=0.002)
    box(parts, "GuardFront", (0.012, 0.010, 0.048), (0, -0.035, -0.042), m=M_METAL, b=0.002)
    cyl(parts, "Barrel", 0.017, 0.055, (0, -0.212, 0.035), m=M_METAL)
    box(parts, "FrontSight", (0.012, 0.020, 0.016), (0, -0.180, 0.080), m=M_METAL, b=0.002)
    box(parts, "RearSight", (0.034, 0.014, 0.014), (0, 0.028, 0.080), m=M_METAL, b=0.002)
    sph(parts, "MuzzleFlashPoint", 0.011, (0, -0.240, 0.035), m=M_ACCENT, segs=8, rings=5)

    finalize(parts, "Pistol", (0, -0.245, 0.035))
    export(os.path.join(OUT_DIR, "Pistol.fbx"))


# ============================================================
# 2) 散弹枪
# ============================================================
def build_shotgun():
    clear_objects()
    parts = []
    box(parts, "Receiver", (0.064, 0.210, 0.092), (0, -0.045, 0.048), m=M_METAL)
    cyl(parts, "Barrel", 0.022, 0.420, (0, -0.350, 0.060), m=M_METAL)
    cyl(parts, "MagTube", 0.017, 0.340, (0, -0.330, 0.008), m=M_POLYMER)
    box(parts, "Pump", (0.072, 0.150, 0.062), (0, -0.290, 0.008), m=M_WOOD)
    box(parts, "StockGrip", (0.050, 0.080, 0.140), (0, 0.045, -0.060), rot=(math.radians(-12), 0, 0), m=M_WOOD)
    box(parts, "Stock", (0.052, 0.280, 0.110), (0, 0.180, 0.030), rot=(math.radians(-7), 0, 0), m=M_WOOD)
    box(parts, "StockButt", (0.056, 0.040, 0.130), (0, 0.315, 0.012), rot=(math.radians(-7), 0, 0), m=M_POLYMER)
    box(parts, "GuardBottom", (0.014, 0.070, 0.012), (0, 0.035, -0.115), m=M_METAL, b=0.002)
    box(parts, "SightRear", (0.030, 0.020, 0.016), (0, 0.020, 0.098), m=M_METAL, b=0.002)
    sph(parts, "SightFront", 0.013, (0, -0.545, 0.082), m=M_ACCENT, segs=8, rings=5)
    box(parts, "ShellHolder", (0.040, 0.060, 0.030), (0.048, -0.100, 0.070), m=M_ACCENT, b=0.003)

    finalize(parts, "Shotgun", (0, -0.560, 0.060))
    export(os.path.join(OUT_DIR, "Shotgun.fbx"))


# ============================================================
# 3) 突击步枪
# ============================================================
def build_rifle():
    clear_objects()
    parts = []
    box(parts, "Receiver", (0.058, 0.300, 0.095), (0, -0.090, 0.048), m=M_METAL)
    cyl(parts, "Barrel", 0.018, 0.330, (0, -0.410, 0.050), m=M_METAL)
    box(parts, "Handguard", (0.062, 0.230, 0.075), (0, -0.300, 0.045), m=M_POLYMER)
    box(parts, "Magazine", (0.046, 0.095, 0.210), (0, -0.130, -0.045), rot=(math.radians(8), 0, 0), m=M_METAL)
    box(parts, "Grip", (0.046, 0.075, 0.145), (0, 0.030, -0.065), rot=(math.radians(-12), 0, 0), m=M_POLYMER)
    box(parts, "Stock", (0.050, 0.240, 0.095), (0, 0.190, 0.030), m=M_POLYMER)
    box(parts, "StockPad", (0.054, 0.030, 0.110), (0, 0.315, 0.028), m=M_METAL, b=0.003)
    box(parts, "TopRail", (0.026, 0.200, 0.020), (0, -0.120, 0.105), m=M_METAL, b=0.002)
    box(parts, "SightRear", (0.030, 0.020, 0.022), (0, 0.005, 0.125), m=M_METAL, b=0.002)
    box(parts, "SightFront", (0.022, 0.020, 0.026), (0, -0.300, 0.100), m=M_METAL, b=0.002)
    box(parts, "AccentStripe", (0.062, 0.060, 0.020), (0, -0.180, 0.030), m=M_ACCENT, b=0.002)
    box(parts, "Foregrip", (0.036, 0.040, 0.100), (0, -0.250, -0.010), rot=(math.radians(-10), 0, 0), m=M_POLYMER)
    box(parts, "TriggerGuard", (0.012, 0.070, 0.012), (0, 0.020, -0.088), m=M_METAL, b=0.002)

    finalize(parts, "Rifle", (0, -0.585, 0.050))
    export(os.path.join(OUT_DIR, "Rifle.fbx"))


build_pistol()
build_shotgun()
build_rifle()
print("ALL_DONE")
