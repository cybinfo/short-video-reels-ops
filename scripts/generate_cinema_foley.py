#!/usr/bin/env python3
"""Procedural cinema foley WAV synthesizer (44.1kHz, 16-bit mono PCM, zero CC-BY-NC)."""

from __future__ import annotations

from pathlib import Path
import wave
import numpy as np
from scipy import signal

SAMPLE_RATE = 44100
PEAK_CEILING = 0.58
REPO_ROOT = Path(__file__).resolve().parent.parent
SFX_DIR = REPO_ROOT / "engine" / "public" / "sfx"


def _apply_cosine_fades(buf: np.ndarray, fade_in_s: float, fade_out_s: float) -> np.ndarray:
    out = buf.astype(np.float64, copy=True)
    n = out.size
    fi = min(n, max(2, int(round(fade_in_s * SAMPLE_RATE))))
    fo = min(n, max(2, int(round(fade_out_s * SAMPLE_RATE))))
    out[:fi] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(fi) / fi))
    out[-fo:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(fo) / fo))
    out[0] = 0.0
    out[-1] = 0.0
    return out


def _write_mono_wav(path: Path, samples: np.ndarray, target_peak: float = 0.52) -> dict[str, float | int]:
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    cap = min(PEAK_CEILING, target_peak)
    scaled = samples * (cap / peak) if peak > 1e-9 else np.zeros_like(samples)
    clipped = np.clip(scaled, -PEAK_CEILING, PEAK_CEILING)
    pcm = np.round(clipped * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return {
        "frames": int(samples.size),
        "duration_s": round(samples.size / SAMPLE_RATE, 3),
        "peak": round(float(np.max(np.abs(clipped))), 4),
    }


def synth_bank_sms_chime() -> np.ndarray:
    """0.70s two-note glass smartphone notification ping (1046.5Hz -> 1318.5Hz at 0.11s + 170Hz haptic buzz)."""
    dur = 0.70
    n = int(round(dur * SAMPLE_RATE))
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    out = np.zeros(n, dtype=np.float64)

    # Subtle 170Hz linear-resonant smartphone haptic buzz under the alert onset
    for buzz_on, buzz_len, amp in ((0.004, 0.068, 0.22), (0.106, 0.078, 0.18)):
        mask = (t >= buzz_on) & (t < buzz_on + buzz_len)
        dt = t[mask] - buzz_on
        env = np.sin(np.pi * dt / buzz_len) ** 1.3
        out[mask] += amp * env * (np.sin(2.0 * np.pi * 170.0 * dt) + 0.18 * np.sin(2.0 * np.pi * 340.0 * dt))

    # Two-note crystalline glass ping: C6 (1046.5Hz) at 0.00s -> E6 (1318.5Hz) at 0.11s
    notes = ((0.004, 1046.5, 9.2, 0.86), (0.114, 1318.5, 6.4, 1.00))
    for onset, freq, decay, gain in notes:
        mask = t >= onset
        dt = t[mask] - onset
        att = 0.5 * (1.0 - np.cos(np.pi * np.minimum(1.0, dt / 0.003)))
        env = att * np.exp(-dt * decay)
        glass = (
            np.sin(2.0 * np.pi * freq * dt)
            + 0.24 * np.exp(-dt * 18.0) * np.sin(2.0 * np.pi * (freq * 2.0) * dt)
            + 0.09 * np.exp(-dt * 32.0) * np.sin(2.0 * np.pi * (freq * 2.756) * dt)
        )
        out[mask] += gain * env * glass

    return _apply_cosine_fades(out, 0.002, 0.045)


def synth_rooftop_wind_drip() -> np.ndarray:
    """5.20s midnight terrace wind swell (180-620Hz bandpass) + 2 water-tank drips at 1.1s & 3.4s."""
    dur = 5.20
    n = int(round(dur * SAMPLE_RATE))
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    rng = np.random.default_rng(20261115)

    # Midnight terrace wind swell (180-620Hz Butterworth bandpass + slow gust modulation)
    white = rng.normal(0.0, 1.0, n)
    sos_wind = signal.butter(4, [180.0, 620.0], btype="bandpass", fs=SAMPLE_RATE, output="sos")
    wind_band = signal.sosfiltfilt(sos_wind, white)
    wind_band /= max(1e-9, float(np.max(np.abs(wind_band))))
    breath_env = (np.sin(np.pi * t / dur) ** 0.75) * (0.58 + 0.42 * np.sin(2.0 * np.pi * 0.36 * t - 0.5) ** 2)
    out = 0.34 * wind_band * breath_env

    # Crisp water-tank drips at 1.10s and 3.40s (950Hz -> 1480Hz 35ms upward sine chirp + tank reflections)
    drip_dur = 0.035
    drip_n = int(round(drip_dur * SAMPLE_RATE))
    dt = np.arange(drip_n, dtype=np.float64) / SAMPLE_RATE
    chirp_wave = signal.chirp(dt, f0=950.0, f1=1480.0, t1=drip_dur, method="quadratic", phi=-90.0)
    drip_env = np.sin(np.pi * np.minimum(1.0, dt / 0.004) * 0.5) * np.exp(-dt * 68.0)
    drip_kernel = chirp_wave * drip_env

    for drip_t, amp in ((1.10, 0.95), (3.40, 0.88)):
        for delay_s, echo_gain in ((0.0, 1.0), (0.046, 0.28), (0.094, 0.11)):
            s_idx = int(round((drip_t + delay_s) * SAMPLE_RATE))
            e_idx = min(n, s_idx + drip_n)
            if e_idx > s_idx:
                out[s_idx:e_idx] += amp * echo_gain * drip_kernel[: e_idx - s_idx]

    return _apply_cosine_fades(out, 0.060, 0.120)


def synth_keypad_tap_seq() -> np.ndarray:
    """2.10s sequence of 6 capacitive glass screen taps + subtle confirmation tone at 1.65s."""
    dur = 2.10
    n = int(round(dur * SAMPLE_RATE))
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(74221)

    tap_times = (0.05, 0.32, 0.58, 0.85, 1.12, 1.38)
    tap_freqs = (1920.0, 2080.0, 1980.0, 2160.0, 2040.0, 2240.0)
    tap_len = int(round(0.028 * SAMPLE_RATE))
    dt_tap = np.arange(tap_len, dtype=np.float64) / SAMPLE_RATE
    sos_click = signal.butter(2, [1600.0, 4800.0], btype="bandpass", fs=SAMPLE_RATE, output="sos")

    for tap_t, f_glass in zip(tap_times, tap_freqs):
        s_idx = int(round(tap_t * SAMPLE_RATE))
        e_idx = min(n, s_idx + tap_len)
        m = e_idx - s_idx
        dt = dt_tap[:m]
        burst = signal.sosfilt(sos_click, rng.normal(0.0, 1.0, m))
        burst /= max(1e-9, float(np.max(np.abs(burst))))
        click = 0.35 * burst * np.exp(-dt * 420.0)
        glass = 0.68 * np.sin(2.0 * np.pi * f_glass * dt) * np.exp(-dt * 210.0)
        thud = 0.32 * np.sin(2.0 * np.pi * 215.0 * dt) * np.exp(-dt * 145.0)
        att = 0.5 * (1.0 - np.cos(np.pi * np.minimum(1.0, dt / 0.0012)))
        out[s_idx:e_idx] += att * (click + glass + thud)

    # Subtle dual-step confirmation tone at 1.65s
    for onset, freq, gain in ((1.65, 880.0, 0.42), (1.715, 1174.66, 0.48)):
        mask = t >= onset
        dt = t[mask] - onset
        att = 0.5 * (1.0 - np.cos(np.pi * np.minimum(1.0, dt / 0.004)))
        out[mask] += gain * att * np.exp(-dt * 11.5) * np.sin(2.0 * np.pi * freq * dt)

    return _apply_cosine_fades(out, 0.003, 0.040)


def synth_dawn_temple_bell() -> np.ndarray:
    """3.20s warm Indian morning brass puja ghanti (528Hz + 1056Hz, 1588Hz, 2420Hz partials)."""
    dur = 3.20
    n = int(round(dur * SAMPLE_RATE))
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    onset = 0.015
    out = np.zeros(n, dtype=np.float64)
    mask = t >= onset
    dt = t[mask] - onset
    att = 0.5 * (1.0 - np.cos(np.pi * np.minimum(1.0, dt / 0.0035)))

    partials = (
        (528.0, 1.00, 1.35, 0.9),
        (1056.0, 0.56, 1.85, 1.5),
        (1588.0, 0.34, 2.45, 2.1),
        (2420.0, 0.22, 3.30, 2.8),
        (3176.0, 0.09, 5.40, 0.0),
    )
    bell = np.zeros_like(dt)
    for freq, amp, decay, beat_hz in partials:
        primary = np.sin(2.0 * np.pi * freq * dt)
        shimmer = 0.32 * np.sin(2.0 * np.pi * (freq + beat_hz) * dt + 0.35) if beat_hz > 0 else 0.0
        bell += amp * np.exp(-dt * decay) * (primary + shimmer)

    clapper = 0.24 * np.exp(-dt * 95.0) * np.sin(2.0 * np.pi * 1890.0 * dt)
    out[mask] = att * (bell + clapper)
    return _apply_cosine_fades(out, 0.003, 0.090)


def main() -> int:
    specs = (
        ("bank-sms-chime.wav", synth_bank_sms_chime, 0.52),
        ("rooftop-wind-drip.wav", synth_rooftop_wind_drip, 0.48),
        ("keypad-tap-seq.wav", synth_keypad_tap_seq, 0.50),
        ("dawn-temple-bell.wav", synth_dawn_temple_bell, 0.50),
    )
    for filename, fn, peak in specs:
        meta = _write_mono_wav(SFX_DIR / filename, fn(), target_peak=peak)
        print(f"[foley] {filename:<24} {meta['duration_s']:>5.2f}s  ({meta['frames']} frames, peak={meta['peak']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
