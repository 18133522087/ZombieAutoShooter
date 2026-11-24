"""
ZombieAutoShooter - 僵尸美术资源（低多边形 Q 版，纯色）
Blender 5.2 headless：生成 3 个僵尸并分别导出 FBX。

- ZombieMelee  : 近战僵尸（绿色皮肤 / 破衣 / 前伸双臂）     高约 1.75m
- ZombieRanged : 远程僵尸（紫色兜帽 / 背上酸囊 / 手托酸球） 高约 1.75m
- BossZombie   : Boss（巨大 / 暗红皮肤 / 骨刺 / 装甲片）     高约 3.05m
"""
import bpy
import math
import os
from mathutils import Vector

OUT_DIR = r"D:\MYGAME\ZombieAutoShooter\ArtSource\Enemies"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 场景与材质（只初始化一次，三个角色共用） ----------
bpy.ops.wm.read_factory_settings(use_empty=True)


def make_mat(name, rgb, rough=0.9, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return m


M_SKIN_GREEN = make_mat("MAT_ZSkinGreen", (0.40, 0.55, 0.30))
M_SKIN_PALE  = make_mat("MAT_ZSkinPale",  (0.55, 0.66, 0.58))
M_SKIN_BOSS  = make_mat("MAT_ZSkinBoss",  (0.52, 0.17, 0.14))
M_HAIR       = make_mat("MAT_ZHair",      (0.10, 0.09, 0.07))
M_SHIRT      = make_mat("MAT_ZShirt",     (0.32, 0.28, 0.23))
M_PANTS      = make_mat("MAT_ZPants",     (0.23, 0.24, 0.24))
M_BOOTS      = make_mat("MAT_ZBoots",     (0.15, 0.13, 0.11))
M_BONE       = make_mat("MAT_ZBone",      (0.86, 0.83, 0.70), rough=0.6)
M_EYE        = make_mat("MAT_ZEye",       (1.00, 0.86, 0.10), rough=0.3)
M_BLOOD      = make_mat("MAT_ZBlood",     (0.38, 0.06, 0.06), rough=0.55)
M_ROBE       = make_mat("MAT_ZRobe",      (0.40, 0.21, 0.50))
M_ACID       = make_mat("MAT_ZAcid",      (0.45, 0.90, 0.25), rough=0.4)
M_ARMOR      = make_mat("MAT_ZArmor",     (0.19, 0.20, 0.23), rough=0.45, metal=0.6)


def clear_objects():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


# ---------- 几何工具 ----------
def assign(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


def bev(o, w=0.02, seg=2):
    md = o.modifiers.new("bevel", "BEVEL")
    md.width = w
    md.segments = seg
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(50)


def box(parts, name, size, loc, rot=(0, 0, 0), m=None, b=0.02, seg=2):
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


def sph(parts, name, r, loc, scale=(1, 1, 1), m=None, segs=14, rings=9):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, m)
    parts.append(o)
    return o


def cyl(parts, name, r, h, loc, rot=(0, 0, 0), m=None, verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    assign(o, m)
    parts.append(o)
    return o


def cone(parts, name, r1, r2, h, loc, rot=(0, 0, 0), m=None, verts=8):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    assign(o, m)
    parts.append(o)
    return o


def cone_dir(parts, name, r1, length, base, direction, m=None, verts=7):
    """从 base 点沿 direction 方向伸出的尖刺（底面嵌在 base 里，避免悬空）。"""
    d = Vector(direction).normalized()
    center = Vector(base) + d * (length * 0.5)
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=0.0, depth=length,
                                    location=(center.x, center.y, center.z))
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    assign(o, m)
    parts.append(o)
    return o


def finalize(parts, root_name):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    root = bpy.context.active_object
    root.name = root_name
    for o in parts:
        o.parent = root
        o.matrix_parent_inverse = root.matrix_world.inverted()
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    return root


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
# 1) 近战僵尸（驼背 / 前伸双臂）
# ============================================================
def build_melee():
    clear_objects()
    parts = []
    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        box(parts, "Leg_" + side, (0.155, 0.175, 0.600), (0.113 * sx, 0.0, 0.450), m=M_PANTS, b=0.03)
        box(parts, "Boot_" + side, (0.175, 0.290, 0.130), (0.113 * sx, -0.045, 0.075), m=M_BOOTS, b=0.03)

    box(parts, "Hips", (0.345, 0.240, 0.210), (0, 0, 0.735), m=M_PANTS, b=0.035)
    box(parts, "Torso", (0.395, 0.255, 0.470), (0, -0.02, 1.095), rot=(math.radians(14), 0, 0), m=M_SHIRT, b=0.05, seg=3)
    box(parts, "Belly", (0.170, 0.030, 0.150), (0.05, -0.145, 0.935), m=M_SKIN_GREEN, b=0.02, seg=1)
    box(parts, "Rag1", (0.090, 0.030, 0.170), (-0.13, -0.140, 0.880), rot=(0, 0, math.radians(10)), m=M_SHIRT, b=0.01, seg=1)
    box(parts, "Rag2", (0.070, 0.030, 0.120), (0.14, -0.135, 0.905), rot=(0, 0, math.radians(-14)), m=M_SHIRT, b=0.01, seg=1)
    box(parts, "Blood1", (0.140, 0.012, 0.120), (-0.10, -0.150, 1.130), m=M_BLOOD, b=0.008, seg=1)
    box(parts, "Blood2", (0.070, 0.012, 0.080), (0.13, -0.148, 1.010), m=M_BLOOD, b=0.008, seg=1)

    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        sph(parts, "Shoulder_" + side, 0.098, (0.205 * sx, -0.02, 1.295), m=M_SKIN_GREEN, segs=12, rings=7)
        box(parts, "Arm_" + side, (0.115, 0.130, 0.430), (0.245 * sx, -0.130, 1.140),
            rot=(math.radians(-52), 0, math.radians(6 * sx)), m=M_SKIN_GREEN, b=0.025)
        sph(parts, "Hand_" + side, 0.072, (0.285 * sx, -0.330, 0.975), m=M_SKIN_GREEN)

    cyl(parts, "Neck", 0.065, 0.100, (0, -0.055, 1.345), rot=(math.radians(14), 0, 0), m=M_SKIN_GREEN)
    sph(parts, "Head", 0.230, (0, -0.085, 1.535), scale=(1.0, 0.98, 1.0), m=M_SKIN_GREEN)
    box(parts, "Hair1", (0.150, 0.100, 0.050), (0, -0.020, 1.715), rot=(0, 0, math.radians(8)), m=M_HAIR, b=0.01, seg=1)
    box(parts, "Hair2", (0.090, 0.070, 0.045), (0.10, -0.010, 1.700), m=M_HAIR, b=0.01, seg=1)

    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        sph(parts, "Eye_" + side, 0.033, (0.082 * sx, -0.300, 1.560), m=M_EYE, segs=10, rings=6)

    box(parts, "Mouth", (0.120, 0.020, 0.045), (0, -0.300, 1.455), m=M_HAIR, b=0.006, seg=1)
    for i in range(3):
        box(parts, "Tooth_%d" % i, (0.022, 0.020, 0.030), (-0.035 + i * 0.035, -0.310, 1.470), m=M_BONE, b=0.004, seg=1)
    box(parts, "Wound", (0.090, 0.015, 0.020), (0.03, -0.305, 1.630), rot=(0, 0, math.radians(-16)), m=M_BLOOD, b=0.005, seg=1)

    finalize(parts, "ZombieMelee")
    export(os.path.join(OUT_DIR, "ZombieMelee.fbx"))


# ============================================================
# 2) 远程僵尸（兜帽吐酸者）
# ============================================================
def build_ranged():
    clear_objects()
    parts = []
    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        box(parts, "Leg_" + side, (0.150, 0.170, 0.600), (0.110 * sx, 0.0, 0.450), m=M_PANTS, b=0.03)
        box(parts, "Boot_" + side, (0.170, 0.280, 0.125), (0.110 * sx, -0.040, 0.072), m=M_BOOTS, b=0.03)

    box(parts, "Hips", (0.330, 0.230, 0.200), (0, 0, 0.735), m=M_PANTS, b=0.035)
    box(parts, "Torso", (0.380, 0.250, 0.480), (0, 0, 1.100), rot=(math.radians(6), 0, 0), m=M_ROBE, b=0.05, seg=3)
    box(parts, "RobeSkirt", (0.360, 0.250, 0.230), (0, 0.005, 0.860), rot=(math.radians(-6), 0, 0), m=M_ROBE, b=0.04, seg=2)
    sph(parts, "Hood", 0.255, (0, 0.010, 1.585), scale=(1.02, 1.02, 0.95), m=M_ROBE, segs=16, rings=9)
    sph(parts, "Face", 0.190, (0, -0.085, 1.575), scale=(1.0, 0.72, 1.0), m=M_SKIN_PALE, segs=14, rings=8)

    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        sph(parts, "Eye_" + side, 0.030, (0.068 * sx, -0.225, 1.600), m=M_ACID, segs=10, rings=6)

    box(parts, "Mouth", (0.090, 0.020, 0.035), (0, -0.230, 1.505), m=M_HAIR, b=0.005, seg=1)

    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        sph(parts, "Shoulder_" + side, 0.095, (0.195 * sx, 0, 1.300), m=M_ROBE, segs=12, rings=7)
        box(parts, "Arm_" + side, (0.130, 0.140, 0.400), (0.255 * sx, -0.040, 1.130),
            rot=(math.radians(-18), 0, math.radians(8 * sx)), m=M_ROBE, b=0.03)
        sph(parts, "Hand_" + side, 0.072, (0.290 * sx, -0.150, 0.940), m=M_SKIN_PALE)

    sph(parts, "AcidBall", 0.090, (0.300, -0.245, 0.925), m=M_ACID, segs=14, rings=8)
    sph(parts, "AcidSac", 0.215, (0, 0.235, 1.290), scale=(1.0, 0.95, 1.15), m=M_ACID, segs=14, rings=8)
    cyl(parts, "Tube_L", 0.032, 0.320, (-0.12, 0.150, 1.390), rot=(math.radians(28), 0, math.radians(18)), m=M_ACID, verts=8)
    cyl(parts, "Tube_R", 0.032, 0.320, (0.12, 0.150, 1.390), rot=(math.radians(28), 0, math.radians(-18)), m=M_ACID, verts=8)
    box(parts, "Hole", (0.110, 0.015, 0.130), (-0.08, -0.135, 1.150), m=M_SKIN_PALE, b=0.008, seg=1)

    finalize(parts, "ZombieRanged")
    export(os.path.join(OUT_DIR, "ZombieRanged.fbx"))


# ============================================================
# 3) Boss（变异巨尸）
# ============================================================
def build_boss():
    clear_objects()
    parts = []
    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        box(parts, "Leg_" + side, (0.290, 0.330, 1.000), (0.235 * sx, 0.0, 0.760), m=M_SKIN_BOSS, b=0.05, seg=3)
        box(parts, "Boot_" + side, (0.330, 0.460, 0.230), (0.235 * sx, -0.070, 0.120), m=M_ARMOR, b=0.05, seg=3)

    box(parts, "Hips", (0.700, 0.430, 0.380), (0, 0, 1.360), m=M_SKIN_BOSS, b=0.06, seg=3)
    box(parts, "Belt", (0.730, 0.450, 0.110), (0, 0, 1.520), m=M_ARMOR, b=0.025, seg=2)
    box(parts, "Torso", (0.880, 0.540, 0.780), (0, -0.03, 1.990), rot=(math.radians(8), 0, 0), m=M_SKIN_BOSS, b=0.09, seg=3)

    for i in range(3):
        box(parts, "Rib_%d" % i, (0.560 - i * 0.05, 0.070, 0.070), (0, -0.290, 2.230 - i * 0.150), m=M_BONE, b=0.015, seg=1)
    box(parts, "ChestCavity", (0.430, 0.045, 0.420), (0, -0.245, 2.080), m=M_BLOOD, b=0.02, seg=2)
    box(parts, "Sternum", (0.090, 0.070, 0.160), (0, -0.300, 2.360), m=M_BONE, b=0.012, seg=1)

    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        sph(parts, "Shoulder_" + side, 0.235, (0.500 * sx, -0.02, 2.290), m=M_SKIN_BOSS, segs=14, rings=8)
        box(parts, "Pauldron_" + side, (0.300, 0.380, 0.220), (0.520 * sx, -0.02, 2.430),
            rot=(0, math.radians(-12 * sx), 0), m=M_ARMOR, b=0.04, seg=2)
        box(parts, "Arm_" + side, (0.235, 0.255, 0.560), (0.560 * sx, -0.060, 2.010),
            rot=(math.radians(-10), 0, math.radians(7 * sx)), m=M_SKIN_BOSS, b=0.04, seg=3)
        box(parts, "Forearm_" + side, (0.250, 0.270, 0.520), (0.600 * sx, -0.310, 1.700),
            rot=(math.radians(-42), 0, 0), m=M_SKIN_BOSS, b=0.05, seg=3)
        sph(parts, "Fist_" + side, 0.190, (0.615 * sx, -0.560, 1.480), m=M_SKIN_BOSS, segs=14, rings=8)
        # 前臂外侧骨刺：从肘部外侧向外前方伸出，底面嵌进前臂
        for k in range(2):
            zoff = -0.13 + k * 0.26
            base_f = (0.600 * sx + 0.10 * sx, -0.310 + 0.669 * zoff, 1.700 + 0.743 * zoff)
            cone_dir(parts, "ForearmSpike_%s_%d" % (side, k), 0.050, 0.210,
                     base_f, (0.85 * sx, -0.45, 0.25), m=M_BONE, verts=6)
        # 肩部骨刺：从肩球外侧向外上方
        cone_dir(parts, "ShoulderSpike_%s" % side, 0.060, 0.300,
                 (0.560 * sx, -0.060, 2.400), (0.70 * sx, -0.22, 0.68), m=M_BONE, verts=7)

    cyl(parts, "Neck", 0.140, 0.160, (0, -0.070, 2.520), m=M_SKIN_BOSS)
    sph(parts, "Head", 0.290, (0, -0.110, 2.800), scale=(1.0, 0.98, 1.05), m=M_SKIN_BOSS, segs=16, rings=9)
    box(parts, "Jaw", (0.360, 0.300, 0.140), (0, -0.190, 2.610), m=M_SKIN_BOSS, b=0.03, seg=2)

    for sx in (-1, 1):
        side = "L" if sx < 0 else "R"
        sph(parts, "Eye_" + side, 0.048, (0.108 * sx, -0.375, 2.830), m=M_EYE, segs=10, rings=6)
        # 弯角：底面嵌进头骨
        cone_dir(parts, "Horn_" + side, 0.075, 0.340,
                 (0.121 * sx, -0.132, 2.983), (0.55 * sx, -0.10, 0.83), m=M_BONE, verts=7)

    box(parts, "Mouth", (0.240, 0.030, 0.070), (0, -0.400, 2.690), m=M_HAIR, b=0.008, seg=1)
    for i in range(4):
        box(parts, "Tooth_%d" % i, (0.035, 0.030, 0.050), (-0.075 + i * 0.050, -0.410, 2.710), m=M_BONE, b=0.006, seg=1)
    # 背部骨刺：底面嵌进后背，向上后方伸出
    back_defs = [
        ((0.0, 0.190, 2.330), (0.0, 0.55, 0.84), 0.36),
        ((0.0, 0.205, 2.070), (0.0, 0.62, 0.78), 0.32),
        ((0.0, 0.215, 1.810), (0.0, 0.68, 0.73), 0.28),
    ]
    for i in range(3):
        cone_dir(parts, "BackSpike_%d" % i, 0.075, back_defs[i][2],
                 back_defs[i][0], back_defs[i][1], m=M_BONE, verts=7)
    box(parts, "Scar", (0.320, 0.020, 0.040), (0.10, -0.275, 1.930), rot=(0, 0, math.radians(22)), m=M_BLOOD, b=0.008, seg=1)

    finalize(parts, "BossZombie")
    export(os.path.join(OUT_DIR, "BossZombie.fbx"))


build_melee()
build_ranged()
build_boss()
print("ALL_DONE")
