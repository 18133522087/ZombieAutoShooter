using System.Collections;
using System.IO;
using UnityEngine;

/// <summary>
/// 预览动画帧录制：Play Mode 里按固定 fps 截图到 Temp 目录（不进 Assets），
/// 之后用外部脚本合成 GIF / 视频。仅用于风格预览。
/// </summary>
public class PreviewFrameRecorder : MonoBehaviour
{
    public float fps = 12f;
    public float seconds = 3.2f;
    public float warmup = 0.6f;
    public string outDirRelativeToProject = "Temp/anim_capture";

    private IEnumerator Start()
    {
        yield return new WaitForSeconds(warmup);

        string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", outDirRelativeToProject));
        Directory.CreateDirectory(dir);

        int frames = Mathf.Max(1, Mathf.RoundToInt(fps * seconds));
        for (int i = 0; i < frames; i++)
        {
            ScreenCapture.CaptureScreenshot(Path.Combine(dir, "frame_" + i.ToString("000") + ".png"));
            yield return new WaitForSeconds(1f / fps);
        }

        Debug.Log("[PreviewFrameRecorder] CAPTURE_DONE frames=" + frames + " dir=" + dir);
    }
}
