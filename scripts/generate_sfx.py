#!/usr/bin/env python3
"""Deterministic stdlib synthesizer for Breach Zero commercial-safe 44.1kHz WAV SFX."""

from __future__ import annotations

import math
from pathlib import Path
import random
import struct
import wave

SAMPLE_RATE = 44100
PEAK_CEILING = 0.55
REPO_ROOT = Path(__file__).resolve().parent.parent
SFX_DIR = REPO_ROOT / "engine" / "public" / "sfx"


def _raised_cosine_fade(samples: list[float], fade_in_sec: float, fade_out_sec: float) -> None:
    n = len(samples)
    fade_in = min(n, max(1, int(fade_in_sec * SAMPLE_RATE)))
    fade_out = min(n, max(1, int(fade_out_sec * SAMPLE_RATE)))
    for i in range(fade_in):
        samples[i] *= 0.5 * (1.0 - math.cos(math.pi * i / fade_in))
    for i in range(fade_out):
        idx = n - 1 - i
        samples[idx] *= 0.5 * (1.0 - math.cos(math.pi * i / fade_out))
    samples[0] = 0.0
    samples[-1] = 0.0


def _normalize_and_write(path: Path, samples: list[float], target_peak: float = 0.52) -> dict[str, float | int]:
    peak = max((abs(s) for s in samples), default=0.0)
    capped_target = min(PEAK_CEILING, target_peak)
    scale = (capped_target / peak) if peak > 1e-9 else 0.0
    pcm = bytearray(len(samples) * 2)
    actual_peak = 0.0
    for i, s in enumerate(samples):
        val = max(-PEAK_CEILING, min(PEAK_CEILING, s * scale))
        if abs(val) > actual_peak:
            actual_peak = abs(val)
        struct.pack_into("<h", pcm, i * 2, int(round(val * 32767.0)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)
    return {"frames": len(samples), "duration_s": round(len(samples) / SAMPLE_RATE, 3), "peak": round(actual_peak, 4)}


def synth_cold_open_impact() -> list[float]:
    dur = 0.65
    n = int(round(dur * SAMPLE_RATE))
    rng = random.Random(10101)
    out = [0.0] * n
    phase = 0.0
    prev_noise = 0.0
    hp_state = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 30.0 + (58.0 - 30.0) * ((1.0 - t / dur) ** 1.65)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        sub_env = math.exp(-t * 4.4) * (1.0 - (t / dur) ** 3)
        sub = (math.sin(phase) + 0.24 * math.sin(2.0 * phase) * math.exp(-t * 8.5)) * sub_env
        transient = 0.0
        if t < 0.018:
            raw = rng.uniform(-1.0, 1.0)
            hp_state = 0.82 * (hp_state + raw - prev_noise)
            prev_noise = raw
            tr_env = math.sin(math.pi * min(1.0, t / 0.0025) * 0.5) * ((1.0 - t / 0.018) ** 2)
            snap = math.sin(2.0 * math.pi * (1450.0 - 900.0 * (t / 0.018)) * t)
            transient = (0.58 * hp_state + 0.42 * snap) * tr_env * 0.72
        out[i] = sub + transient
    _raised_cosine_fade(out, 0.002, 0.035)
    return out


def synth_soc_alert_ping() -> list[float]:
    dur = 0.36
    n = int(round(dur * SAMPLE_RATE))
    out = [0.0] * n
    pulses = ((0.0, 880.0, 17.5, 0.85), (0.095, 1320.0, 14.5, 1.0))
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 0.0
        for start, freq, decay, gain in pulses:
            dt = t - start
            if dt >= 0.0:
                att = 0.5 * (1.0 - math.cos(math.pi * min(1.0, dt / 0.0035)))
                env = att * math.exp(-dt * decay)
                val += gain * env * (math.sin(2.0 * math.pi * freq * dt) + 0.16 * math.sin(4.0 * math.pi * freq * dt))
        out[i] = val
    _raised_cosine_fade(out, 0.002, 0.025)
    return out


def synth_blueprint_whoosh() -> list[float]:
    dur = 0.30
    n = int(round(dur * SAMPLE_RATE))
    rng = random.Random(20202)
    out = [0.0] * n
    low = 0.0
    band = 0.0
    phase = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        u = t / dur
        if u < 0.44:
            s = 0.5 * (1.0 - math.cos(math.pi * (u / 0.44)))
            fc = 220.0 + (680.0 - 220.0) * s
        else:
            s = 0.5 * (1.0 - math.cos(math.pi * ((u - 0.44) / 0.56)))
            fc = 680.0 + (260.0 - 680.0) * s
        f_svf = 2.0 * math.sin(math.pi * fc / SAMPLE_RATE)
        noise = rng.uniform(-1.0, 1.0)
        low += f_svf * band
        high = noise - low - 0.34 * band
        band += f_svf * high
        phase += 2.0 * math.pi * fc / SAMPLE_RATE
        env = math.sin(math.pi * u) ** 1.25
        out[i] = env * (0.82 * band + 0.18 * math.sin(phase))
    _raised_cosine_fade(out, 0.006, 0.018)
    return out


def synth_stamp_slam() -> list[float]:
    dur = 0.38
    n = int(round(dur * SAMPLE_RATE))
    rng = random.Random(30303)
    out = [0.0] * n
    phase = 0.0
    low = 0.0
    band = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 38.0 + (95.0 - 38.0) * math.exp(-t * 24.0)
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        thud = (math.sin(phase) + 0.30 * math.sin(2.0 * phase) * math.exp(-t * 16.0)) * math.exp(-t * 9.8)
        body = 0.0
        if t < 0.032:
            f_svf = 2.0 * math.sin(math.pi * 920.0 / SAMPLE_RATE)
            low += f_svf * band
            high = rng.uniform(-1.0, 1.0) - low - 0.45 * band
            band += f_svf * high
            b_env = (1.0 - t / 0.032) ** 2
            body = (0.65 * band + 0.35 * math.sin(2.0 * math.pi * 310.0 * t)) * b_env * 0.68
        out[i] = thud + body
    _raised_cosine_fade(out, 0.002, 0.028)
    return out


def synth_payoff_chime() -> list[float]:
    dur = 0.55
    n = int(round(dur * SAMPLE_RATE))
    out = [0.0] * n
    voices = ((523.25, 0.000, 1.00), (659.25, 0.014, 0.82), (783.99, 0.028, 0.74), (987.77, 0.042, 0.66))
    for i in range(n):
        t = i / SAMPLE_RATE
        acc = 0.0
        for idx, (freq, onset, gain) in enumerate(voices):
            dt = t - onset
            if dt >= 0.0:
                att = 0.5 * (1.0 - math.cos(math.pi * min(1.0, dt / 0.007)))
                env = att * math.exp(-dt * (4.6 + 0.65 * idx))
                tone = math.sin(2.0 * math.pi * freq * dt) + 0.14 * math.sin(2.0 * math.pi * (freq * 2.001) * dt)
                acc += gain * env * tone
        out[i] = acc
    _raised_cosine_fade(out, 0.003, 0.055)
    return out


def synth_cliffhanger_tick() -> list[float]:
    dur = 8.5
    n = int(round(dur * SAMPLE_RATE))
    out = [0.0] * n
    for beat in range(9):
        for offset, gain in ((0.0, 0.85), (0.22, 0.52)):
            start_idx = int(round((beat * 1.0 + offset) * SAMPLE_RATE))
            pulse_len = int(round(0.18 * SAMPLE_RATE))
            for j in range(pulse_len):
                idx = start_idx + j
                if idx >= n:
                    break
                dt = j / SAMPLE_RATE
                att = 0.5 * (1.0 - math.cos(math.pi * min(1.0, dt / 0.008)))
                env = att * math.exp(-dt * 19.0) * (1.0 - j / pulse_len)
                out[idx] += gain * env * (math.sin(2.0 * math.pi * 46.0 * dt) + 0.28 * math.sin(2.0 * math.pi * 92.0 * dt))
    tick_len = int(round(0.012 * SAMPLE_RATE))
    for step in range(17):
        start_idx = int(round(step * 0.5 * SAMPLE_RATE))
        accent = 0.78 if (step % 2 == 0) else 0.56
        for j in range(tick_len):
            idx = start_idx + j
            if idx >= n:
                break
            dt = j / SAMPLE_RATE
            att = 0.5 * (1.0 - math.cos(math.pi * min(1.0, dt / 0.0012)))
            env = att * math.exp(-dt * 260.0) * (1.0 - j / tick_len)
            tick = math.sin(2.0 * math.pi * 2200.0 * dt) + 0.24 * math.sin(2.0 * math.pi * 4400.0 * dt)
            out[idx] += accent * env * tick
    _raised_cosine_fade(out, 0.003, 0.045)
    return out


def synth_dark_thriller_bed() -> list[float]:
    """60.0s seamless dark-thriller suspense bed (<420Hz low-passed for clear speech)."""
    loop_dur, total_dur, beat_sec = 15.0, 60.0, 0.625  # 96 BPM -> 24 exact beats per 15s phrase
    loop_n = int(round(loop_dur * SAMPLE_RATE))
    warmup_n = int(round(2.5 * SAMPLE_RATE))
    alpha = 1.0 - math.exp(-2.0 * math.pi * 350.0 / SAMPLE_RATE)  # 3-pole cascade < 420 Hz
    lp1 = lp2 = lp3 = 0.0
    phrase = [0.0] * loop_n
    two_pi = 2.0 * math.pi

    for step in range(-warmup_n, loop_n):
        t = (step % loop_n) / SAMPLE_RATE
        beat_pos = (t % beat_sec) / beat_sec
        bar_pos = (t % (4.0 * beat_sec)) / (4.0 * beat_sec)
        swell = 0.78 + 0.22 * (0.5 - 0.5 * math.cos(two_pi * t / loop_dur))

        # 55 Hz A1 deep sub-bass pulse on the 96 BPM bar/half-bar grid
        sub_gate = 0.62 + 0.38 * (0.5 + 0.5 * math.cos(two_pi * bar_pos * 2.0)) ** 1.6
        sub = 0.52 * sub_gate * math.sin(two_pi * 55.0 * t)

        # Subtle 110 Hz muted lub-dub heartbeat pulse every 0.625s (96 BPM)
        hb = 0.0
        for onset, amp in ((0.0, 0.34), (0.30, 0.19)):
            dt = (beat_pos - onset) * beat_sec
            if 0.0 <= dt < 0.17:
                att = 0.5 * (1.0 - math.cos(math.pi * min(1.0, dt / 0.018)))
                env = att * math.exp(-dt * 24.0) * (1.0 - dt / 0.17)
                hb += amp * env * (math.sin(two_pi * 110.0 * dt) + 0.45 * math.sin(two_pi * 55.0 * dt))

        # Soft dark A-minor pad (220 Hz A3 + 261.6 Hz C4 + 164.8 Hz E3) with integer-cycle chorus
        pad_a = math.sin(two_pi * 220.0 * t) + 0.65 * math.sin(two_pi * (220.0 + 1.0 / loop_dur) * t)
        pad_c = math.sin(two_pi * 261.6 * t) + 0.60 * math.sin(two_pi * (261.6 - 1.0 / loop_dur) * t)
        pad_e = 0.55 * math.sin(two_pi * 164.8 * t + 0.6)
        pad_lfo = 0.72 + 0.28 * math.sin(two_pi * (2.0 / loop_dur) * t)
        raw = swell * (sub + hb + 0.19 * pad_lfo * (0.46 * pad_a + 0.36 * pad_c + 0.28 * pad_e))

        lp1 += alpha * (raw - lp1)
        lp2 += alpha * (lp1 - lp2)
        lp3 += alpha * (lp2 - lp3)
        if step >= 0:
            phrase[step] = lp3

    repeats = int(round(total_dur / loop_dur))
    return phrase * repeats


def synth_noir_thriller_bed() -> list[float]:
    """60.0s phone-speaker-audible Hindi crime-noir suspense bed (sub heartbeat + bowed minor cello/pad)."""
    loop_dur, total_dur, beat_sec = 15.0, 60.0, 0.75  # 80 BPM tense noir pulse -> 20 exact beats per 15s
    loop_n = int(round(loop_dur * SAMPLE_RATE))
    phrase = [0.0] * loop_n
    two_pi = 2.0 * math.pi
    for step in range(loop_n):
        t = step / SAMPLE_RATE
        beat_pos = (t % beat_sec) / beat_sec
        swell = 0.74 + 0.26 * (0.5 - 0.5 * math.cos(two_pi * t / loop_dur))
        # Bowed dark D-minor cello drone (73.42 Hz D2 + 146.83 Hz D3 + 220 Hz A3 + 440 Hz A4 whisper)
        d2 = 0.44 * math.sin(two_pi * 73.42 * t)
        d3 = 0.36 * math.sin(two_pi * 146.83 * t + 0.18 * math.sin(two_pi * 0.2 * t))
        f3 = 0.22 * math.sin(two_pi * 174.61 * t)
        a3 = 0.26 * math.sin(two_pi * 220.0 * t + 0.25)
        bb3_tension = 0.14 * (0.5 - 0.5 * math.cos(two_pi * t / 7.5)) * math.sin(two_pi * 233.08 * t)
        # Phone-audible lub-dub heartbeat + soft 780Hz wristwatch tick on alternating beats
        hb = 0.0
        for onset, amp in ((0.0, 0.52), (0.27, 0.30)):
            dt = (beat_pos - onset) * beat_sec
            if 0.0 <= dt < 0.16:
                att = 0.5 * (1.0 - math.cos(math.pi * min(1.0, dt / 0.012)))
                env = att * math.exp(-dt * 22.0) * (1.0 - dt / 0.16)
                hb += amp * env * (math.sin(two_pi * 68.0 * dt) + 0.55 * math.sin(two_pi * 136.0 * dt) + 0.22 * math.sin(two_pi * 272.0 * dt))
        tick = 0.0
        if beat_pos * beat_sec < 0.016:
            dt_k = beat_pos * beat_sec
            tick = 0.16 * math.exp(-dt_k * 220.0) * math.sin(two_pi * 1180.0 * dt_k)
        phrase[step] = swell * (0.48 * (d2 + d3 + f3 + a3 + bb3_tension) + hb + tick)
    return phrase * int(round(total_dur / loop_dur))


def synth_cash_drain_ticks() -> list[float]:
    """2.2s rapid descending digital bank-account drain ticks ending in a hollow zero-balance alarm."""
    dur = 2.2
    n = int(round(dur * SAMPLE_RATE))
    out = [0.0] * n
    two_pi = 2.0 * math.pi
    for step in range(22):
        onset = 0.04 + step * 0.072
        s_i = int(round(onset * SAMPLE_RATE))
        freq = 1680.0 - step * 34.0
        t_len = int(round(0.036 * SAMPLE_RATE))
        for j in range(t_len):
            if s_i + j >= n:
                break
            dt = j / SAMPLE_RATE
            env = math.sin(math.pi * min(1.0, dt / 0.003) * 0.5) * math.exp(-dt * 95.0)
            out[s_i + j] += 0.68 * env * (math.sin(two_pi * freq * dt) + 0.32 * math.sin(two_pi * (freq * 1.5) * dt))
    # Final zero-balance warning double-tone at 1.66s
    for p_on, f_alarm in ((1.66, 540.0), (1.84, 405.0)):
        s_i = int(round(p_on * SAMPLE_RATE))
        a_len = int(round(0.30 * SAMPLE_RATE))
        for j in range(a_len):
            if s_i + j >= n:
                break
            dt = j / SAMPLE_RATE
            env = math.sin(math.pi * min(1.0, dt / 0.008) * 0.5) * math.exp(-dt * 9.5)
            out[s_i + j] += 0.85 * env * (math.sin(two_pi * f_alarm * dt) + 0.45 * math.sin(two_pi * (f_alarm * 2.0) * dt) + 0.35 * math.sin(two_pi * 82.0 * dt))
    _raised_cosine_fade(out, 0.004, 0.035)
    return out


def synth_ussd_dial_tones() -> list[float]:
    """1.55s high-clarity phone-speaker ITU-T DTMF keypad dial (* 2 1 *) + forwarding latch beep."""
    dur = 1.55
    n = int(round(dur * SAMPLE_RATE))
    out = [0.0] * n
    two_pi = 2.0 * math.pi
    # * (941+1209), 2 (697+1336), 1 (697+1209), * (941+1209) with crisp harmonic presence for tiny speakers
    keys = ((0.02, 941.0, 1209.0), (0.23, 697.0, 1336.0), (0.44, 697.0, 1209.0), (0.65, 941.0, 1209.0))
    tone_len = int(round(0.145 * SAMPLE_RATE))
    for onset, f_lo, f_hi in keys:
        s_i = int(round(onset * SAMPLE_RATE))
        for j in range(tone_len):
            if s_i + j >= n:
                break
            dt = j / SAMPLE_RATE
            att = 0.5 * (1.0 - math.cos(math.pi * min(1.0, dt / 0.004)))
            rel = 0.5 * (1.0 - math.cos(math.pi * min(1.0, (tone_len - 1 - j) / max(1, int(0.010 * SAMPLE_RATE)))))
            click = 0.35 * math.exp(-dt * 260.0) * math.sin(two_pi * 2850.0 * dt)
            tones = 0.65 * math.sin(two_pi * f_lo * dt) + 1.05 * math.sin(two_pi * f_hi * dt) + 0.32 * math.sin(two_pi * (f_hi * 2.0) * dt)
            out[s_i + j] += att * rel * tones + click
    # Forwarding confirmation double-latch ping at 0.90s + 1.04s
    for p_on, f_latch in ((0.90, 1318.5), (1.04, 1760.0)):
        s_l = int(round(p_on * SAMPLE_RATE))
        for j in range(int(round(0.36 * SAMPLE_RATE))):
            if s_l + j >= n:
                break
            dt = j / SAMPLE_RATE
            env = math.sin(math.pi * min(1.0, dt / 0.005) * 0.5) * math.exp(-dt * 9.0)
            out[s_l + j] += 0.85 * env * (math.sin(two_pi * f_latch * dt) + 0.42 * math.sin(two_pi * (f_latch * 1.5) * dt))
    _raised_cosine_fade(out, 0.003, 0.03)
    return out


def synth_noir_suspect_slam() -> list[float]:
    """0.40s crisp camera-shutter + metallic dossier stamp + bass impact for mobile speakers."""
    dur = 0.40
    n = int(round(dur * SAMPLE_RATE))
    rng = random.Random(40404)
    out = [0.0] * n
    two_pi = 2.0 * math.pi
    phase = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 56.0 + 125.0 * math.exp(-t * 30.0)
        phase += two_pi * freq / SAMPLE_RATE
        punch = 0.82 * (math.sin(phase) + 0.48 * math.sin(2.0 * phase)) * math.exp(-t * 13.5)
        shutter = 0.0
        if t < 0.024:
            shutter = (0.58 * rng.uniform(-1.0, 1.0) + 0.52 * math.sin(two_pi * 2150.0 * t) + 0.36 * math.sin(two_pi * 3650.0 * t)) * ((1.0 - t / 0.024) ** 1.6) * 1.15
        elif 0.038 <= t < 0.064:
            dt2 = t - 0.038
            shutter = (0.45 * rng.uniform(-1.0, 1.0) + 0.62 * math.sin(two_pi * 2680.0 * dt2)) * ((1.0 - dt2 / 0.026) ** 1.6) * 0.92
        out[i] = punch + shutter
    _raised_cosine_fade(out, 0.002, 0.025)
    return out


def synth_shaadi_distant_intro() -> list[float]:
    """3.60s faint distant Indian shaadi shehnai + warm dholak room-tone that cuts dead on a sub-drop at 3.35s."""
    dur = 3.60
    n = int(round(dur * SAMPLE_RATE))
    out = [0.0] * n
    two_pi = 2.0 * math.pi
    alpha = 1.0 - math.exp(-two_pi * 1250.0 / SAMPLE_RATE)
    lp1 = lp2 = 0.0
    # Gentle Raga Yaman / festive auspicious intervals (D4=293.66, F#4=369.99, A4=440.0, B4=493.88, A4=440.0)
    notes = ((0.0, 0.85, 293.66), (0.85, 1.65, 369.99), (1.65, 2.55, 440.0), (2.55, 3.32, 493.88))
    for i in range(n):
        t = i / SAMPLE_RATE
        if t < 3.32:
            vib = 1.0 + 0.0085 * math.sin(two_pi * 5.6 * t)
            f0 = 293.66
            for ns, ne, nf in notes:
                if ns <= t < ne:
                    f0 = nf * vib
                    break
            # Nasal double-reed shehnai odd/even harmonic warmth + soft tanpura drone (D3 + A3)
            reed = 0.42 * math.sin(two_pi * f0 * t) + 0.54 * math.sin(two_pi * 2.0 * f0 * t) + 0.31 * math.sin(two_pi * 3.0 * f0 * t)
            drone = 0.25 * math.sin(two_pi * 146.83 * t) + 0.18 * math.sin(two_pi * 220.0 * t)
            # Soft distant dholak pulse every 0.42s
            dh_dt = t % 0.42
            dhol = 0.34 * math.exp(-dh_dt * 24.0) * math.sin(two_pi * (96.0 + 35.0 * math.exp(-dh_dt * 30.0)) * dh_dt)
            fade_in = min(1.0, t / 0.35)
            raw = fade_in * (0.42 * reed + 0.35 * drone + dhol)
            lp1 += alpha * (raw - lp1)
            lp2 += alpha * (lp1 - lp2)
            out[i] = lp2
        else:
            # Sudden tape/heart-stop sub-bass drop right at 3.32s when Sharma Ji sees Rs 0!
            dt_drop = t - 3.32
            f_drop = 48.0 + 95.0 * math.exp(-dt_drop * 18.0)
            out[i] = 0.95 * math.exp(-dt_drop * 11.5) * math.sin(two_pi * f_drop * dt_drop)
    _raised_cosine_fade(out, 0.01, 0.03)
    return out


def generate_all_sfx(output_dir: Path = SFX_DIR) -> dict[str, dict[str, float | int]]:
    specs = (
        ("cold-open-impact.wav", synth_cold_open_impact, 0.54),
        ("soc-alert-ping.wav", synth_soc_alert_ping, 0.48),
        ("blueprint-whoosh.wav", synth_blueprint_whoosh, 0.50),
        ("stamp-slam.wav", synth_stamp_slam, 0.54),
        ("payoff-chime.wav", synth_payoff_chime, 0.48),
        ("cliffhanger-tick.wav", synth_cliffhanger_tick, 0.50),
        ("dark-thriller-bed.wav", synth_dark_thriller_bed, 0.2512),
        ("noir-thriller-bed.wav", synth_noir_thriller_bed, 0.34),
        ("cash-drain-ticks.wav", synth_cash_drain_ticks, 0.54),
        ("ussd-dial-tones.wav", synth_ussd_dial_tones, 0.78),
        ("noir-suspect-slam.wav", synth_noir_suspect_slam, 0.72),
        ("shaadi-distant-intro.wav", synth_shaadi_distant_intro, 0.42),
    )
    return {name: _normalize_and_write(output_dir / name, fn(), peak) for name, fn, peak in specs}


if __name__ == "__main__":
    results = generate_all_sfx()
    for fname, meta in results.items():
        print(f"{fname}: {meta['duration_s']:.2f}s | {meta['frames']} frames | peak={meta['peak']:.4f}")
