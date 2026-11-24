using UnityEngine;

/// <summary>
/// 主角风格预览用的程序化动画（无骨骼，摆动各部件）。
/// 只用于 StylePreview 场景演示；正式游戏里会换成骨骼动画或同类实现。
/// </summary>
[DisallowMultipleComponent]
public class PlayerPreviewAnimator : MonoBehaviour
{
    [Header("走位演示")]
    public bool walk = true;
    public float radius = 1.7f;
    public float angularSpeed = 0.85f;   // rad/s

    [Header("动画幅度")]
    public float stepFrequency = 2.1f;   // 每秒步频
    public float bobHeight = 0.045f;
    public float legSwing = 24f;
    public float armSwing = 14f;
    public float aimArmAngle = -72f;     // 右臂前举瞄准

    private Transform wrapper;
    private Transform pivotLegL, pivotLegR, pivotArmL, pivotArmR;
    private Transform weaponSocket;
    private Transform weapon;
    private Vector3 basePos;
    private float t;

    private void Awake()
    {
        // 加一层世界坐标 wrapper，这样所有摆动都可以用世界轴
        wrapper = new GameObject(name + "_AnimRoot").transform;
        wrapper.position = transform.position;
        wrapper.rotation = Quaternion.identity;
        transform.SetParent(wrapper, true);
        basePos = wrapper.position;

        Transform legL = FindDeep("Leg_L");
        Transform legR = FindDeep("Leg_R");
        Transform armL = FindDeep("Arm_L");
        Transform armR = FindDeep("Arm_R");

        pivotLegL = MakePivot("Pivot_Leg_L", legL);
        pivotLegR = MakePivot("Pivot_Leg_R", legR);
        pivotArmL = MakePivot("Pivot_Arm_L", armL);
        pivotArmR = MakePivot("Pivot_Arm_R", armR);

        Attach(pivotLegL, "Leg_L", "Boot_L");
        Attach(pivotLegR, "Leg_R", "Boot_R");
        Attach(pivotArmL, "Arm_L", "Hand_L");
        Attach(pivotArmR, "Arm_R", "Hand_R");

        // 武器：挂在 WeaponSocket 下，但每帧强制枪口朝角色正前方（不跟随举臂角度）
        weaponSocket = FindDeep("WeaponSocket");
        if (weaponSocket != null && weaponSocket.childCount > 0)
        {
            weapon = weaponSocket.GetChild(0);
        }
    }

    private Transform FindDeep(string n)
    {
        Transform[] all = GetComponentsInChildren<Transform>(true);
        for (int i = 0; i < all.Length; i++)
        {
            if (all[i].name == n) return all[i];
        }
        return null;
    }

    /// <summary>在肢体顶部（关节）建一个枢轴，返回枢轴。</summary>
    private Transform MakePivot(string pivotName, Transform part)
    {
        if (part == null) return null;
        Renderer r = part.GetComponent<Renderer>();
        Bounds b = r != null ? r.bounds : new Bounds(part.position, Vector3.one * 0.2f);

        Transform p = new GameObject(pivotName).transform;
        p.SetParent(wrapper, false);
        p.position = new Vector3(b.center.x, b.max.y, b.center.z);
        p.rotation = Quaternion.identity;
        return p;
    }

    private void Attach(Transform pivot, params string[] partNames)
    {
        if (pivot == null) return;
        for (int i = 0; i < partNames.Length; i++)
        {
            Transform part = FindDeep(partNames[i]);
            if (part != null) part.SetParent(pivot, true);
        }
    }

    private void Update()
    {
        if (wrapper == null) return;
        t += Time.deltaTime;

        float phase = t * stepFrequency;
        float swing = Mathf.Sin(phase * Mathf.PI * 2f);

        // 环绕走位 + 朝向前进方向
        float a = t * angularSpeed;
        Vector3 offset = new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)) * radius;
        Vector3 tangent = new Vector3(-Mathf.Sin(a), 0f, Mathf.Cos(a));

        float bob = Mathf.Abs(Mathf.Sin(phase * Mathf.PI)) * bobHeight;
        wrapper.position = basePos + offset + new Vector3(0f, bob, 0f);
        if (walk)
        {
            wrapper.rotation = Quaternion.LookRotation(tangent, Vector3.up);
        }

        if (pivotLegL != null) pivotLegL.localRotation = Quaternion.Euler(swing * legSwing, 0f, 0f);
        if (pivotLegR != null) pivotLegR.localRotation = Quaternion.Euler(-swing * legSwing, 0f, 0f);
        if (pivotArmL != null) pivotArmL.localRotation = Quaternion.Euler(-swing * armSwing, 0f, 0f);
        if (pivotArmR != null) pivotArmR.localRotation = Quaternion.Euler(aimArmAngle + swing * 4f, 0f, 0f);
    }

    private void LateUpdate()
    {
        // 让手里的枪保持水平朝前（只跟随身体朝向，不跟随举臂的俯仰）
        if (weapon != null && weaponSocket != null && wrapper != null)
        {
            weapon.position = weaponSocket.position;
            weapon.rotation = wrapper.rotation * Quaternion.Euler(-90f, 0f, 0f);
        }
    }
}
