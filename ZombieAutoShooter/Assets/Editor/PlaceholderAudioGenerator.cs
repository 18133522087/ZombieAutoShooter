using System;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

// 程序化生成占位音效/BGM（无外部素材、无第三方包）。
// 菜单：Tools/ZombieAutoShooter/Generate Placeholder Audio
public static class PlaceholderAudioGenerator
{
    const int SR = 44100;
    const string OutDir = "Assets/Audio";

    enum Wave { Sine, Square, Saw, Triangle, Noise }

    [MenuItem("Tools/ZombieAutoShooter/Generate Placeholder Audio")]
    public static void MenuGenerate()
    {
        int n = GenerateAll();
        Debug.Log("[PlaceholderAudioGenerator] generated " + n + " clips into " + OutDir);
    }

    public static int GenerateAll()
    {
        if (!AssetDatabase.IsValidFolder(OutDir))
            AssetDatabase.CreateFolder("Assets", "Audio");

        int c = 0;
        c += Save("pistol_shoot",  Sweep(0.12f, 900f, 300f, Wave.Square, 0.55f, 0f, 0f, 0.08f));
        c += Save("rifle_shoot",   Sweep(0.08f, 1200f, 500f, Wave.Square, 0.45f, 0f, 0f, 0.10f));
        c += Save("shotgun_shoot", Mix(Sweep(0.18f, 120f, 60f, Wave.Sine, 0.45f, 0f, 0.05f, 0.6f),
                                      Gain(NoiseBurst(0.18f, 0.6f, 3f), 0.55f)));
        c += Save("bullet_hit",    NoiseBurst(0.08f, 0.6f, 4f));
        c += Save("enemy_die",     Sweep(0.20f, 300f, 80f, Wave.Saw, 0.5f, 0f, 0.05f, 0.15f));
        c += Save("player_hurt",   Mix(Sweep(0.25f, 200f, 100f, Wave.Square, 0.45f, 0f, 0.05f, 0f),
                                      Gain(NoiseBurst(0.25f, 0.5f, 2f), 0.45f)));
        c += Save("orb_pickup",    Seq(new float[] { 880f, 1320f }, 0.05f, Wave.Sine, 0.4f));
        c += Save("level_up",      Seq(new float[] { 523f, 659f, 784f, 1046f }, 0.10f, Wave.Sine, 0.45f));
        c += Save("ui_click",      Sweep(0.05f, 1000f, 1000f, Wave.Sine, 0.4f, 0f, 0.2f, 0f));
        c += Save("victory",       Seq(new float[] { 523f, 659f, 784f, 1046f }, 0.25f, Wave.Sine, 0.5f));
        c += Save("defeat",        Seq(new float[] { 392f, 330f, 262f, 196f }, 0.25f, Wave.Sine, 0.5f));
        c += Save("boss_spawn",    Mix(Sweep(0.8f, 60f, 40f, Wave.Saw, 0.55f, 0.1f, 0.2f, 0.2f),
                                      Gain(NoiseBurst(0.8f, 0.5f, 1f), 0.45f)));
        c += Save("boss_dash",     Sweep(0.3f, 2000f, 300f, Wave.Noise, 0.5f, 0.02f, 0.1f, 0f));
        c += Save("revive",        Sweep(0.5f, 330f, 660f, Wave.Sine, 0.5f, 0.05f, 0.2f, 0f));
        c += Save("bgm_main",      Bgm(8f));

        AssetDatabase.Refresh();
        return c;
    }

    // ---------- 合成 ----------
    static float[] Sweep(float sec, float f0, float f1, Wave wave, float amp, float attack, float release, float noise)
    {
        int n = Mathf.Max(2, (int)(sec * SR));
        var d = new float[n];
        var rnd = new System.Random(12345);
        double phase = 0.0;
        double logRatio = (f0 > 0f && f1 > 0f) ? Math.Log(f1 / f0) : 0.0;
        for (int i = 0; i < n; i++)
        {
            float u = (float)i / (n - 1);
            float f = f0 * (float)Math.Exp(logRatio * u);
            phase += 2.0 * Math.PI * f / SR;
            float s = Osc(wave, phase, rnd);
            if (noise > 0f) s = Mathf.Lerp(s, (float)(rnd.NextDouble() * 2.0 - 1.0), noise);
            d[i] = s * amp * Env(u, attack, release);
        }
        return d;
    }

    static float[] Seq(float[] freqs, float noteSec, Wave wave, float amp)
    {
        int per = Mathf.Max(2, (int)(noteSec * SR));
        var d = new float[per * freqs.Length];
        for (int k = 0; k < freqs.Length; k++)
        {
            for (int i = 0; i < per; i++)
            {
                float u = (float)i / per;
                float env = Mathf.Min(1f, u / 0.02f) * Mathf.Exp(-3.5f * u);
                double phase = 2.0 * Math.PI * freqs[k] * i / SR;
                d[k * per + i] += Osc(wave, phase, null) * amp * env;
            }
        }
        return d;
    }

    static float[] NoiseBurst(float sec, float amp, float decay)
    {
        int n = Mathf.Max(2, (int)(sec * SR));
        var d = new float[n];
        var rnd = new System.Random(777);
        for (int i = 0; i < n; i++)
        {
            float u = (float)i / n;
            d[i] = (float)(rnd.NextDouble() * 2.0 - 1.0) * amp * Mathf.Exp(-decay * u * 4f);
        }
        return d;
    }

    static float[] Bgm(float sec)
    {
        int n = Mathf.Max(4, (int)(sec * SR));
        var d = new float[n];
        float[][] chords = new float[][]
        {
            new float[] { 261.63f, 329.63f, 392.00f },
            new float[] { 220.00f, 261.63f, 329.63f },
            new float[] { 174.61f, 220.00f, 261.63f },
            new float[] { 196.00f, 246.94f, 293.66f }
        };
        float[] gains = new float[] { 0.32f, 0.24f, 0.18f };
        int seg = n / chords.Length;
        for (int k = 0; k < chords.Length; k++)
        {
            int start = k * seg;
            int end = (k == chords.Length - 1) ? n : start + seg;
            for (int i = start; i < end; i++)
            {
                float u = (float)(i - start) / (end - start);
                float env = Mathf.Sin(Mathf.PI * u); // 段首段尾为 0，保证循环无爆音
                float v = 0f;
                for (int v2 = 0; v2 < chords[k].Length; v2++)
                    v += Mathf.Sin(2f * Mathf.PI * chords[k][v2] * i / SR) * gains[v2];
                d[i] = v * env * 0.55f;
            }
        }
        return d;
    }

    static float Osc(Wave w, double phase, System.Random rnd)
    {
        switch (w)
        {
            case Wave.Sine: return (float)Math.Sin(phase);
            case Wave.Square: return Math.Sin(phase) >= 0.0 ? 1f : -1f;
            case Wave.Saw:
            {
                double t = phase / (2.0 * Math.PI);
                t -= Math.Floor(t);
                return (float)(2.0 * t - 1.0);
            }
            case Wave.Triangle:
            {
                double t = phase / (2.0 * Math.PI);
                t -= Math.Floor(t);
                return (float)(4.0 * Math.Abs(t - 0.5) - 1.0);
            }
            case Wave.Noise:
                return rnd != null ? (float)(rnd.NextDouble() * 2.0 - 1.0) : 0f;
        }
        return 0f;
    }

    static float Env(float u, float attack, float release)
    {
        if (attack > 0f && u < attack) return u / attack;
        if (release > 0f && u > 1f - release) return (1f - u) / release;
        return 1f;
    }

    static float[] Gain(float[] a, float g)
    {
        var d = new float[a.Length];
        for (int i = 0; i < a.Length; i++) d[i] = a[i] * g;
        return d;
    }

    static float[] Mix(float[] a, float[] b)
    {
        int n = Mathf.Max(a.Length, b.Length);
        var d = new float[n];
        for (int i = 0; i < n; i++)
        {
            float va = i < a.Length ? a[i] : 0f;
            float vb = i < b.Length ? b[i] : 0f;
            d[i] = va + vb;
        }
        return d;
    }

    // ---------- 写 WAV + 导入设置 ----------
    static int Save(string name, float[] data)
    {
        string rel = OutDir + "/" + name + ".wav";
        WriteWav(rel, data, 0.88f);
        AssetDatabase.ImportAsset(rel, ImportAssetOptions.ForceUpdate);
        var ai = AssetImporter.GetAtPath(rel) as AudioImporter;
        if (ai != null)
        {
            var s = ai.defaultSampleSettings;
            s.loadType = (name == "bgm_main") ? AudioClipLoadType.CompressedInMemory : AudioClipLoadType.DecompressOnLoad;
            if (name != "bgm_main") s.compressionFormat = AudioCompressionFormat.PCM;
            s.preloadAudioData = true;
            ai.defaultSampleSettings = s;
            ai.forceToMono = true;
            ai.SaveAndReimport();
        }
        return 1;
    }

    static void WriteWav(string relPath, float[] data, float peak)
    {
        float max = 0f;
        for (int i = 0; i < data.Length; i++) max = Mathf.Max(max, Mathf.Abs(data[i]));
        float k = (max > peak) ? peak / max : 1f;

        int n = data.Length;
        int bytes = n * 2;
        using (var fs = new FileStream(relPath, FileMode.Create, FileAccess.Write))
        using (var bw = new BinaryWriter(fs))
        {
            bw.Write(Encoding.ASCII.GetBytes("RIFF"));
            bw.Write(36 + bytes);
            bw.Write(Encoding.ASCII.GetBytes("WAVE"));
            bw.Write(Encoding.ASCII.GetBytes("fmt "));
            bw.Write(16);
            bw.Write((short)1);       // PCM
            bw.Write((short)1);       // mono
            bw.Write(SR);
            bw.Write(SR * 2);
            bw.Write((short)2);
            bw.Write((short)16);
            bw.Write(Encoding.ASCII.GetBytes("data"));
            bw.Write(bytes);
            for (int i = 0; i < n; i++)
            {
                float v = Mathf.Clamp(data[i] * k, -1f, 1f);
                bw.Write((short)(v * 32000f));
            }
        }
    }
}
