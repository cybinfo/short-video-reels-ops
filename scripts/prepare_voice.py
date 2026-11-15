#!/usr/bin/env python3
"""Voice synthesis, neural WordBoundary forced alignment, and caption generator for Cyber Jasoos episodes."""

import argparse, array, json, math, os, re, shutil, subprocess, sys, wave
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAY_BIN, AFCONVERT_BIN = Path("/usr/bin/say"), Path("/usr/bin/afconvert")
AUDIO_PYTHON = REPO_ROOT / ".venv_audio" / "bin" / "python"
KOKORO_PYTHON = AUDIO_PYTHON
KOKORO_MODEL = REPO_ROOT / ".venv_audio" / "models" / "kokoro-v1.0.onnx"
KOKORO_VOICES = REPO_ROOT / ".venv_audio" / "models" / "voices-v1.0.bin"
KOKORO_MASTER_AF = "highpass=f=80,acompressor=threshold=-18dB:ratio=2.6:attack=6:release=85,loudnorm=I=-14:TP=-1.2:LRA=9"
EDGE_MASTER_AF = "highpass=f=75,equalizer=f=155:width_type=o:width=1.2:g=2.4,equalizer=f=3600:width_type=o:width=1.4:g=1.6,acompressor=threshold=-19dB:ratio=2.5:attack=8:release=110:makeup=1.8dB,loudnorm=I=-14:TP=-1.2:LRA=9"
DEFAULT_EDGE_VOICES = {"jyoti": "hi-IN-SwaraNeural", "rajat": "hi-IN-MadhurNeural", "narrator": "hi-IN-MadhurNeural", "kabir": "hi-IN-MadhurNeural", "sharma": "hi-IN-MadhurNeural", "chachu": "hi-IN-MadhurNeural"}
DEFAULT_EDGE_RATES = {"jyoti": "+4%", "rajat": "+4%", "narrator": "-3%", "kabir": "-3%", "sharma": "+0%", "chachu": "+5%"}
DEFAULT_EDGE_PITCHES = {"jyoti": "-2Hz", "rajat": "-4Hz", "narrator": "-6Hz", "kabir": "-6Hz", "sharma": "-3Hz", "chachu": "-2Hz"}
DEFAULT_EDGE_FORMANTS = {"jyoti": 1.065, "rajat": 1.12, "narrator": 0.945, "kabir": 0.945, "sharma": 0.985, "chachu": 1.0}


def normalize_edge_clause_text(text: str) -> str:
    clean = re.sub(r"\.{2,}|…+", "", str(text)).strip()
    if not clean:
        return clean
    m_end = re.search(r"([!?.।\"'”’]+)$", clean)
    head, tail = (clean[: m_end.start()], m_end.group(1)) if m_end else (clean, "")
    head = re.sub(r",+", ",", re.sub(r"\s*[!?]+", ",", head))
    return f"{head}{tail}".strip()


def attach_wav_loudness_peaks(wav_path: Path, captions: list[dict]) -> None:
    if not captions:
        return
    if not wav_path.is_file():
        for item in captions:
            item["peak"] = [0.0, 0.0, 0.0, 0.0]
        return
    with wave.open(str(wav_path), "rb") as rf:
        ch, sw, sr, nframes = rf.getnchannels(), rf.getsampwidth(), rf.getframerate(), rf.getnframes()
        raw = rf.readframes(nframes)
    if sw != 2 or nframes <= 0 or sr <= 0:
        for item in captions:
            item["peak"] = [0.0, 0.0, 0.0, 0.0]
        return
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    if ch == 2:
        samples = samples[::2]
    total_n = len(samples)
    if total_n == 0:
        for item in captions:
            item["peak"] = [0.0, 0.0, 0.0, 0.0]
        return
    win = max(1, int(0.020 * sr))
    frame_rms = [
        math.sqrt(sum(x * x for x in sl) / len(sl))
        for i in range(0, max(1, total_n - win + 1), win)
        if (sl := samples[i : i + win : 2] or samples[i : i + win])
    ]
    s_rms = sorted(frame_rms)
    p95 = s_rms[min(len(s_rms) - 1, int(0.95 * (len(s_rms) - 1)))] if s_rms else 0.0
    norm_ref = p95 if p95 > 1.0 else (s_rms[-1] if s_rms else 0.0)
    if norm_ref <= 1e-6:
        for item in captions:
            item["peak"] = [0.0, 0.0, 0.0, 0.0]
        return
    for item in captions:
        s_idx = max(0, min(total_n - 1, int(round(float(item.get("startSec", 0.0)) * sr))))
        e_idx = max(s_idx + 1, min(total_n, int(round(float(item.get("endSec", 0.0)) * sr))))
        span = e_idx - s_idx
        peaks: list[float] = []
        for k in range(4):
            a = s_idx + (span * k) // 4
            b = s_idx + (span * (k + 1)) // 4
            if b <= a:
                b = min(total_n, a + 1)
            sub = samples[a:b]
            rms_i = math.sqrt(sum(x * x for x in sub) / len(sub)) if sub else 0.0
            peaks.append(round(min(1.0, rms_i / norm_ref), 3))
        item["peak"] = peaks


def snap_words_off_silence(wav_path: Path, captions: list[dict]) -> None:
    if not captions or not wav_path.is_file():
        return
    with wave.open(str(wav_path), "rb") as rf:
        ch, sw, sr, nframes = rf.getnchannels(), rf.getsampwidth(), rf.getframerate(), rf.getnframes()
        raw = rf.readframes(nframes)
    if sw != 2 or nframes <= 0 or sr <= 0:
        return
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    if ch == 2:
        samples = samples[::2]
    total_n = len(samples)
    if total_n == 0:
        return
    hop = max(1, int(0.010 * sr))
    hop_rms = [
        math.sqrt(sum(x * x for x in sl) / len(sl))
        for i in range(0, total_n, hop)
        if (sl := samples[i : i + hop : 2] or samples[i : i + hop])
    ]
    if not hop_rms:
        return
    s_rms = sorted(hop_rms)
    p95 = s_rms[min(len(s_rms) - 1, int(0.95 * (len(s_rms) - 1)))]
    norm_ref = p95 if p95 > 1.0 else s_rms[-1]
    if norm_ref <= 1e-6:
        return
    env = [min(1.0, r / norm_ref) for r in hop_rms]
    n_hops, total_dur = len(env), total_n / float(sr)
    hop_sec = hop / float(sr)

    for idx, item in enumerate(captions):
        s_sec, e_sec = float(item.get("startSec", 0.0)), float(item.get("endSec", 0.0))
        hs = max(0, min(n_hops - 1, int(s_sec / hop_sec)))
        he = max(hs + 1, min(n_hops, int(math.ceil(e_sec / hop_sec))))
        peaks = item.get("peak") or []
        cur_max = max((float(p) for p in peaks), default=0.0) if peaks else max(env[hs:he], default=0.0)

        if cur_max < 0.05:
            lo = max(0, hs - 14)
            hi = min(n_hops, he + 14)
            islands: list[tuple[int, int, float]] = []
            cur_s: int | None = None
            for h in range(lo, hi):
                if env[h] >= 0.05:
                    if cur_s is None:
                        cur_s = h
                elif cur_s is not None:
                    islands.append((cur_s, h, max(env[cur_s:h])))
                    cur_s = None
            if cur_s is not None:
                islands.append((cur_s, hi, max(env[cur_s:hi])))
            if not islands:
                continue
            mid_h = 0.5 * (hs + he)
            best_s, best_e, _ = min(islands, key=lambda isl: min(abs(isl[0] - mid_h), abs(isl[1] - mid_h), 0.0 if isl[0] <= mid_h <= isl[1] else 1e9))
            cand_s = max(0.0, best_s * hop_sec)
            cand_e = min(total_dur, max(cand_s + 0.04, best_e * hop_sec))
            if idx > 0:
                ps, pe = float(captions[idx - 1]["startSec"]), float(captions[idx - 1]["endSec"])
                if cand_s < pe:
                    if pe - ps > 0.08:
                        if cand_e <= pe + 0.02:
                            split_t = max(ps + 0.04, min(pe - 0.03, 0.5 * (ps + cand_e)))
                            captions[idx - 1]["endSec"] = round(split_t, 4)
                            cand_s = float(captions[idx - 1]["endSec"])
                            cand_e = max(cand_e, min(total_dur, pe))
                        else:
                            give = max(ps + 0.04, cand_s)
                            captions[idx - 1]["endSec"] = round(give, 4)
                            cand_s = float(captions[idx - 1]["endSec"])
                    else:
                        cand_s = pe
            if idx + 1 < len(captions):
                ns, ne = float(captions[idx + 1]["startSec"]), float(captions[idx + 1]["endSec"])
                if cand_e > ns:
                    if ne - ns > 0.08:
                        push = min(ne - 0.04, cand_e)
                        captions[idx + 1]["startSec"] = round(push, 4)
                        cand_e = float(captions[idx + 1]["startSec"])
                    else:
                        cand_e = ns
            if cand_e > cand_s + 0.015:
                item["startSec"], item["endSec"] = round(cand_s, 4), round(cand_e, 4)
        elif env[hs] < 0.025 or env[he - 1] < 0.025:
            act = [h for h in range(hs, he) if env[h] >= 0.045]
            if act:
                nhs = max(hs, act[0] - 1)
                nhe = min(he, act[-1] + 2)
                if nhe - nhs >= 4 and max(env[nhs:nhe], default=0.0) >= 0.05:
                    ns_sec = round(max(s_sec, nhs * hop_sec), 4)
                    ne_sec = round(min(e_sec, total_dur, nhe * hop_sec), 4)
                    if ne_sec > ns_sec + 0.03:
                        item["startSec"], item["endSec"] = ns_sec, ne_sec


def _norm_token(token: str) -> str:
    return re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", token).lower()


def estimate_syllables(word: str) -> int:
    if not (cleaned := re.sub(r"[^a-z0-9]", "", word.lower())):
        return 1
    digit_groups, alpha = len(re.findall(r"\d+", cleaned)), re.sub(r"\d+", "", cleaned)
    if not alpha:
        return max(1, digit_groups * 2)
    groups = len(re.findall(r"[aeiouy]+", alpha))
    return max(1, groups - (1 if alpha.endswith("e") and not alpha.endswith("le") and groups > 1 else 0) + digit_groups)


def _find_emphasized_indices(words: list[str], highlight_keywords: list[str]) -> set[int]:
    norm_words, emphasized = [_norm_token(w) for w in words], set()
    for kw in highlight_keywords:
        if kw_tokens := [_norm_token(p) for p in str(kw).split() if _norm_token(p)]:
            span = len(kw_tokens)
            emphasized.update(j for i in range(len(norm_words) - span + 1) if norm_words[i : i + span] == kw_tokens for j in range(i, i + span))
    return emphasized


def build_deterministic_word_timestamps(script_segments: list[dict]) -> list[dict]:
    captions: list[dict] = []
    for seg in script_segments:
        seg_start, seg_end = float(seg["startSec"]), float(seg["endSec"])
        window = seg_end - seg_start
        words = [w for w in str(seg.get("narration", "")).split() if w] if window > 0 else []
        if not words:
            continue
        emph_indices = _find_emphasized_indices(words, seg.get("highlightKeywords") or [])
        weights = [float(estimate_syllables(w)) + (0.35 if w[-1] in ".!?,;:" else 0.0) for w in words]
        total_weight, cum = sum(weights) or float(len(words)), 0.0
        for idx, word in enumerate(words):
            w_start = seg_start if idx == 0 else seg_start + window * (cum / total_weight)
            cum += weights[idx]
            w_end = seg_end if idx == len(words) - 1 else seg_start + window * (cum / total_weight)
            s_round, e_round = round(max(seg_start, w_start), 4), round(min(seg_end, w_end), 4)
            e_round = round(min(seg_end, s_round + 1e-4), 4) if e_round <= s_round else e_round
            entry: dict = {"word": word, "startSec": s_round, "endSec": e_round, "emphasis": idx in emph_indices}
            if seg.get("speaker"):
                entry["speaker"] = str(seg["speaker"]).strip().lower()
            captions.append(entry)
        if isinstance(seg.get("ttsClauses"), list) and seg["ttsClauses"]:
            c_spks = [str(c.get("speaker") or seg.get("speaker") or "jyoti").strip().lower() for c in seg["ttsClauses"] for _ in str(c.get("roman", "")).split()]
            if len(c_spks) == len(words):
                for w_i, spk in enumerate(c_spks):
                    captions[len(captions) - len(words) + w_i]["speaker"] = spk
    return captions


def extract_segment_clauses(seg: dict) -> list[dict]:
    narration = " ".join(str(seg.get("narration", "")).split())
    default_spk = str(seg.get("speaker") or "jyoti").strip().lower()
    raw_clauses = seg.get("ttsClauses")
    if isinstance(raw_clauses, list) and raw_clauses:
        out: list[dict] = []
        for idx, item in enumerate(raw_clauses):
            if not isinstance(item, dict):
                raise ValueError(f"Segment '{seg.get('id', idx)}' ttsClauses[{idx}] must be an object.")
            tts_txt = str(item.get("tts") if item.get("tts") is not None else item.get("hi", "")).strip()
            if not str(item.get("roman", "")).strip() or not tts_txt:
                raise ValueError(f"Segment '{seg.get('id', idx)}' ttsClauses[{idx}] requires non-empty 'roman' and 'hi'/'tts'.")
            spk = str(item.get("speaker") or default_spk).strip().lower()
            entry: dict = {"roman": " ".join(str(item["roman"]).split()), "hi": tts_txt, "speaker": spk}
            for opt_k in ("rate", "pitch"):
                if item.get(opt_k) is not None and str(item[opt_k]).strip():
                    entry[opt_k] = str(item[opt_k]).strip()
            if isinstance(item.get("pauseAfter"), (int, float)) and not isinstance(item.get("pauseAfter"), bool):
                entry["pauseAfter"] = float(item["pauseAfter"])
            if item.get("breathBefore") is True:
                entry["breathBefore"] = True
            if item.get("emotion"):
                entry["emotion"] = str(item["emotion"]).strip()
            out.append(entry)
        joined = " ".join(c["roman"] for c in out)
        if joined != narration:
            raise ValueError(f"Segment '{seg.get('id')}' ttsClauses roman mismatch:\n  joined:    {joined!r}\n  narration: {narration!r}")
        return out
    if not narration:
        return []
    rom_parts = [p.strip() for p in re.split(r"(?<=[.!?:;—,])\s+", narration) if p.strip()]
    tts_hi = str(seg.get("ttsHindi", "")).strip()
    if tts_hi:
        hi_parts = [p.strip() for p in re.split(r"(?<=[।.!?:;—,])\s+", tts_hi) if p.strip()]
        if len(hi_parts) == len(rom_parts):
            return [{"roman": r, "hi": h, "speaker": default_spk} for r, h in zip(rom_parts, hi_parts)]
        return [{"roman": narration, "hi": tts_hi, "speaker": default_spk}]
    return [{"roman": p, "hi": p, "speaker": default_spk} for p in rom_parts]


def _tokenize_spoken_words(roman_text: str) -> list[str]:
    raw = [w for w in str(roman_text).split() if w]
    merged: list[str] = []
    for tok in raw:
        if not re.search(r"[A-Za-z0-9]", tok):
            if merged:
                merged[-1] = f"{merged[-1]} {tok}"
            continue
        merged.append(tok)
    return merged or raw


def _map_words_to_neural_spans(
    words: list[str], cs: float, ce: float, raw_spans: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    spans: list[tuple[float, float]] = []
    for rs, re_v in raw_spans:
        s_abs = max(cs, min(ce - 1e-3, cs + float(rs)))
        e_abs = min(ce, max(s_abs + 1e-3, cs + float(re_v)))
        if spans and s_abs < spans[-1][1]:
            mid = 0.5 * (spans[-1][1] + s_abs)
            if mid > spans[-1][0] + 1e-3 and e_abs > mid + 1e-3:
                spans[-1] = (spans[-1][0], mid)
                s_abs = mid
            else:
                s_abs = spans[-1][1]
        if e_abs > s_abs + 1e-4:
            spans.append((s_abs, e_abs))
    n_w, m_s = len(words), len(spans)
    if m_s == 0 or n_w == 0:
        return []
    if n_w == 1:
        return [(spans[0][0], spans[-1][1])]
    if n_w == m_s:
        return spans

    w_wt = [float(estimate_syllables(w)) for w in words]
    tot_w = sum(w_wt) or float(n_w)
    cum_w = [0.0]
    for v in w_wt:
        cum_w.append(cum_w[-1] + v / tot_w)

    s_wt = [max(0.01, b - a) for a, b in spans]
    tot_s = sum(s_wt) or float(m_s)
    cum_s = [0.0]
    for v in s_wt:
        cum_s.append(cum_s[-1] + v / tot_s)

    if n_w < m_s:
        inf = 1e12
        dp = [[inf] * (m_s + 1) for _ in range(n_w + 1)]
        prv = [[0] * (m_s + 1) for _ in range(n_w + 1)]
        dp[0][0] = 0.0
        for i in range(1, n_w + 1):
            punct = words[i - 1][-1] in ",.!?:;—"
            for k in range(i, m_s - (n_w - i) + 1):
                for p in range(i - 1, k):
                    if dp[i - 1][p] >= inf:
                        continue
                    internal_gap_pen = sum(
                        4.0 * max(0.0, (spans[g][0] - spans[g - 1][1]) - 0.09) for g in range(p + 1, k)
                    )
                    pos_err = (cum_s[k] - cum_w[i]) ** 2 if i < n_w else 0.0
                    gap_bonus = (
                        -0.06 * min(0.35, max(0.0, spans[k][0] - spans[k - 1][1]))
                        if (punct and i < n_w and k < m_s)
                        else 0.0
                    )
                    cost = dp[i - 1][p] + pos_err + internal_gap_pen + gap_bonus
                    if cost < dp[i][k]:
                        dp[i][k], prv[i][k] = cost, p
        cuts = [m_s]
        cur_k = m_s
        for i in range(n_w, 0, -1):
            cur_k = prv[i][cur_k]
            cuts.append(cur_k)
        cuts.reverse()
        return [(spans[cuts[i]][0], spans[cuts[i + 1] - 1][1]) for i in range(n_w)]

    inf = 1e12
    dp = [[inf] * (n_w + 1) for _ in range(m_s + 1)]
    prv = [[0] * (n_w + 1) for _ in range(m_s + 1)]
    dp[0][0] = 0.0
    for k in range(1, m_s + 1):
        for i in range(k, n_w - (m_s - k) + 1):
            for p in range(k - 1, i):
                if dp[k - 1][p] >= inf:
                    continue
                pos_err = (cum_w[i] - cum_s[k]) ** 2 if k < m_s else 0.0
                cost = dp[k - 1][p] + pos_err
                if cost < dp[k][i]:
                    dp[k][i], prv[k][i] = cost, p
    w_cuts = [n_w]
    cur_i = n_w
    for k in range(m_s, 0, -1):
        cur_i = prv[k][cur_i]
        w_cuts.append(cur_i)
    w_cuts.reverse()
    out_spans: list[tuple[float, float]] = []
    for k in range(m_s):
        sa, sb = spans[k]
        wi_a, wi_b = w_cuts[k], w_cuts[k + 1]
        sub_wt = w_wt[wi_a:wi_b]
        sub_tot = sum(sub_wt) or float(len(sub_wt))
        acc = 0.0
        for idx_sub, wt_v in enumerate(sub_wt):
            ws_v = sa if idx_sub == 0 else sa + (sb - sa) * (acc / sub_tot)
            acc += wt_v
            we_v = sb if idx_sub == len(sub_wt) - 1 else sa + (sb - sa) * (acc / sub_tot)
            out_spans.append((ws_v, max(ws_v + 1e-4, we_v)))
    return out_spans


def build_clause_locked_word_timestamps(
    script_segments: list[dict],
    clause_timings: list[list[tuple[float, float]]],
    clause_word_spans: list[list[list[tuple[float, float]]]] | None = None,
) -> list[dict]:
    captions: list[dict] = []
    for seg_idx, seg in enumerate(script_segments):
        clauses = extract_segment_clauses(seg)
        timings = clause_timings[seg_idx] if seg_idx < len(clause_timings) else []
        if not clauses or len(clauses) != len(timings):
            seg_fallback = build_deterministic_word_timestamps([seg])
            for item in seg_fallback:
                item.setdefault("speaker", str(seg.get("speaker") or "jyoti").strip().lower())
            captions.extend(seg_fallback)
            continue
        seg_start, seg_end = float(seg["startSec"]), float(seg["endSec"])
        seg_spans = clause_word_spans[seg_idx] if (clause_word_spans and seg_idx < len(clause_word_spans)) else None
        seg_caps: list[dict] = []
        for c_idx, (c, (raw_s, raw_e)) in enumerate(zip(clauses, timings)):
            cs = max(seg_start, min(seg_end - 1e-3, float(raw_s)))
            ce = min(seg_end, max(cs + 1e-3, float(raw_e)))
            c_spans = seg_spans[c_idx] if (seg_spans and c_idx < len(seg_spans)) else None
            if c_spans:
                words = _tokenize_spoken_words(c["roman"])
                mapped = _map_words_to_neural_spans(words, cs, ce, c_spans)
                if len(mapped) == len(words):
                    for w_str, (ws, we) in zip(words, mapped):
                        s_r = round(max(seg_start, ws), 4)
                        e_r = round(min(seg_end, max(s_r + 1e-4, we)), 4)
                        seg_caps.append({"word": w_str, "startSec": s_r, "endSec": e_r, "emphasis": False, "speaker": c["speaker"]})
                    continue
            seg_caps.extend(
                build_deterministic_word_timestamps(
                    [{"startSec": cs, "endSec": ce, "narration": c["roman"], "speaker": c["speaker"], "highlightKeywords": []}]
                )
            )
        emph = _find_emphasized_indices([w["word"] for w in seg_caps], seg.get("highlightKeywords") or [])
        for idx, item in enumerate(seg_caps):
            item["emphasis"] = idx in emph
        captions.extend(seg_caps)
    return captions


def sync_manifest_timings(manifest: dict, seg_end_raw: list[float], total_duration: float) -> None:
    dur_clean: int | float = int(total_duration) if float(total_duration).is_integer() else round(total_duration, 2)
    old_dur = float(manifest.get("durationSeconds") or dur_clean)
    manifest["durationSeconds"] = dur_clean
    segments = manifest.get("scriptSegments") or []
    cursor = 0.0
    for idx, seg in enumerate(segments):
        seg["startSec"] = 0 if idx == 0 else cursor
        if idx == len(segments) - 1:
            seg["endSec"] = dur_clean
        else:
            raw_e = seg_end_raw[idx] if idx < len(seg_end_raw) else cursor + 1.0
            end_v = round(min(float(dur_clean) - 0.1 * (len(segments) - 1 - idx), max(cursor + 0.1, float(raw_e))), 2)
            seg["endSec"] = end_v
            cursor = end_v
    scenes = manifest.get("scenes") or []
    if scenes and len(scenes) == len(segments):
        for idx, sc in enumerate(scenes):
            sc["startSec"] = segments[idx]["startSec"]
            sc["endSec"] = segments[idx]["endSec"]
    elif len(scenes) == 6 and len(segments) >= 5:
        s0, s1, s2, s3 = (float(segments[i]["endSec"]) for i in range(4))
        sc1_end = round(min(s1 - 0.5, s0 + 2.2), 2)
        sc3_end = round(s1 + round(0.62 * (s2 - s1), 2), 2)
        bounds: list[int | float] = [0, sc1_end, round(s1, 2), sc3_end, round(s2, 2), round(s3, 2), dur_clean]
        for idx, sc in enumerate(scenes):
            sc["startSec"], sc["endSec"] = bounds[idx], bounds[idx + 1]
    elif scenes and old_dur > 0:
        scale = float(dur_clean) / old_dur
        sc_cur: int | float = 0
        for idx, sc in enumerate(scenes):
            sc["startSec"] = sc_cur
            sc["endSec"] = dur_clean if idx == len(scenes) - 1 else round(max(float(sc_cur) + 0.1, float(sc["endSec"]) * scale), 2)
            sc_cur = sc["endSec"]


def synthesize_silent_wav(out_wav: Path, duration_seconds: float, sample_rate: int = 44100) -> None:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    remaining = max(1, int(round(duration_seconds * sample_rate)))
    chunk = b"\x00\x00" * min(remaining, sample_rate)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        while remaining > 0:
            step = min(remaining, sample_rate)
            wf.writeframes(chunk[: step * 2])
            remaining -= step


def _convert_to_pcm_wav(src: Path, dst: Path, normalize: bool = False) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    af = "loudnorm=I=-14:TP=-1.5:LRA=11,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-48dB"
    if (ff := shutil.which("ffmpeg")) and subprocess.run([ff, "-y", "-i", str(src), *(("-af", af) if normalize else ()), "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(dst)], capture_output=True, text=True, timeout=60).returncode == 0 and dst.is_file():
        return True
    return bool(AFCONVERT_BIN.is_file() and subprocess.run([str(AFCONVERT_BIN), "-f", "WAVE", "-d", "LEI16@44100", "-c", "1", str(src), str(dst)], capture_output=True, text=True, timeout=60).returncode == 0 and dst.is_file())


def _conform_pcm_wav(
    src_wav: Path, dst_wav: Path, duration_seconds: float, sample_rate: int = 44100, strict_drift: bool = False
) -> float:
    with wave.open(str(src_wav), "rb") as rf:
        ch, sw, sr, nframes = rf.getnchannels(), rf.getsampwidth(), rf.getframerate(), rf.getnframes()
        raw = rf.readframes(nframes)
    if sw != 2 or sr != sample_rate or ch not in (1, 2):
        raise RuntimeError(f"Expected 44100Hz 16-bit PCM WAV, got {sr}Hz {sw * 8}-bit {ch}ch.")
    if ch == 2:
        st = array.array("h")
        st.frombytes(raw)
        mono = array.array("h", ((st[i] + st[i + 1]) // 2 for i in range(0, len(st) - 1, 2)))
        raw, nframes = mono.tobytes(), len(mono)
    raw_dur = nframes / float(sample_rate)
    if strict_drift and abs(raw_dur - duration_seconds) > 0.45:
        raise ValueError(
            f"Synthesized audio ({raw_dur:.2f}s) drifts from manifest durationSeconds ({duration_seconds:.2f}s) by >0.45s without --sync-manifest."
        )
    target = max(1, int(round(duration_seconds * sample_rate)))
    if nframes < target:
        raw += b"\x00\x00" * (target - nframes)
    elif nframes > target:
        raw = raw[: target * 2]
        fade_n = min(target, int(0.015 * sample_rate))
        if fade_n > 1:
            tail = array.array("h")
            tail.frombytes(raw[-fade_n * 2 :])
            tail = array.array("h", (int(tail[i] * (fade_n - 1 - i) / (fade_n - 1)) for i in range(fade_n)))
            raw = raw[: -fade_n * 2] + tail.tobytes()
    dst_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst_wav), "wb") as wf:
        wf.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        wf.writeframes(raw)
    return raw_dur


MLX_WHISPER_BIN = Path(__file__).resolve().parent.parent / ".venv_audio" / "bin" / "mlx_whisper"


def _try_whisper_captions(wav_path: Path, script_segments: list[dict], max_sec: float | None = None) -> list[dict] | None:
    if os.environ.get("CYBERJASOOS_DISABLE_WHISPER") == "1" or os.environ.get("BREACHZERO_DISABLE_WHISPER") == "1":
        return None
    mlx_bin = str(MLX_WHISPER_BIN) if MLX_WHISPER_BIN.is_file() and os.access(MLX_WHISPER_BIN, os.X_OK) else shutil.which("mlx_whisper")
    std_bin = shutil.which("whisper") or shutil.which("whisper-cli")
    if not (mlx_bin or std_bin):
        return None
    tmp_dir = wav_path.parent / f".whisper_tmp_{os.getpid()}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        cmds = [
            *([[mlx_bin, str(wav_path), "--model", "mlx-community/whisper-base-mlx", "--word-timestamps", "True", "--output-format", "json", "--output-dir", str(tmp_dir)]] if mlx_bin else []),
            *([[std_bin, str(wav_path), "--model", "base", "--word_timestamps", "True", "--output-format", "json", "--output-dir", str(tmp_dir)]] if std_bin else []),
        ]
        json_out = tmp_dir / f"{wav_path.stem}.json"
        if not any((json_out.unlink(missing_ok=True), subprocess.run(c, capture_output=True, text=True, timeout=120))[1].returncode == 0 and json_out.is_file() for c in cmds):
            return None
        parsed = json.loads(json_out.read_text(encoding="utf-8"))
        highlights = [kw for seg in script_segments for kw in (seg.get("highlightKeywords") or [])]
        if not (raw_words := [w for s in parsed.get("segments", []) for w in s.get("words", []) if str(w.get("word", "")).strip()]):
            return None
        tokens = [str(w["word"]).strip() for w in raw_words]
        emph, out = _find_emphasized_indices(tokens, highlights), []
        for i, rw in enumerate(raw_words):
            s_val = max(0.0, float(rw.get("start", 0.0)))
            e_val = max(s_val + 1e-4, float(rw.get("end", s_val + 0.05)))
            if max_sec is not None:
                s_val = min(s_val, max(0.0, max_sec - 1e-4))
                e_val = min(max(s_val + 1e-4, e_val), max_sec)
            out.append({"word": tokens[i], "startSec": round(s_val, 4), "endSec": round(e_val, 4), "emphasis": i in emph})
        return out
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


_KOKORO_WORKER_CODE = """
import json, re, sys, wave, numpy as np, kokoro_onnx
req = json.loads(open(sys.argv[1], encoding="utf-8").read())
k = kokoro_onnx.Kokoro(req["model"], req["voices"])
style_cache = {}
def resolve_style(vspec):
    vspec = vspec.strip()
    if vspec not in style_cache:
        if vspec == "hf_sweet":
            style_cache[vspec] = (0.75 * k.get_voice_style("hf_beta") + 0.25 * k.get_voice_style("hf_alpha")).astype(np.float32)
        elif "+" in vspec:
            parts = [p.strip().split("*") for p in vspec.split("+")]
            style_cache[vspec] = sum(float(w) * k.get_voice_style(n.strip()) for w, n in parts).astype(np.float32)
        else:
            style_cache[vspec] = k.get_voice_style(vspec)
    return style_cache[vspec]

voice_map = {
    "jyoti": req.get("defaultVoice") or "hf_sweet",
    "rajat": "hm_omega",
    "narrator": "hm_omega",
    "kabir": "hm_omega",
    "sharma": "hm_psi",
    "chachu": "hm_psi",
}
voice_map.update({str(sp).strip().lower(): str(vs) for sp, vs in (req.get("voiceMap") or {}).items()})

def trim_sil(a, sr, thresh_db=-46.0):
    if a.size == 0:
        return a
    th = 10.0 ** (thresh_db / 20.0)
    win = max(1, int(0.010 * sr))
    pad = np.pad(np.abs(a), (0, win), mode="constant")
    cs = np.cumsum(np.insert(pad ** 2, 0, 0.0))
    rms = np.sqrt((cs[win : win + a.size] - cs[: a.size]) / win)
    idx = np.flatnonzero(rms > th)
    if idx.size == 0:
        return a
    s = max(0, int(idx[0]) - int(0.008 * sr))
    e = min(a.size, int(idx[-1]) + int(0.014 * sr))
    out = a[s:e].copy()
    fn = min(out.size // 4, int(0.004 * sr))
    if fn > 1:
        ramp = np.linspace(0.0, 1.0, fn, dtype=np.float32)
        out[:fn] *= ramp
        out[-fn:] *= ramp[::-1]
    return out

lang, default_speed = req["lang"], float(req["speed"])
speed_map = {str(sp).strip().lower(): float(sv) for sp, sv in (req.get("speedMap") or {}).items()}
segs = req["segments"]

def synth_pass(speed_mult=1.0):
    sr_out, chunks_out, cur_n, c_timings, s_ends = 24000, [], 0, [], []
    for si, clauses in enumerate(segs):
        st = []
        for ci, cl in enumerate(clauses):
            spk = str(cl.get("speaker") or "jyoti").strip().lower()
            style = resolve_style(voice_map.get(spk) or req.get("defaultVoice") or "hf_sweet")
            spk_speed = min(1.65, float(speed_map.get(spk, default_speed)) * speed_mult)
            raw_hi = str(cl.get("hi") or "")
            src_txt = str(cl.get("roman") or raw_hi) if re.search(r"[\\u0600-\\u06FF]", raw_hi) else raw_hi
            ph = k.tokenizer.phonemize(src_txt, lang=lang)
            if lang.startswith("hi"):
                ph = ph.replace("r.", "\u027e")
            wav, sr_out = k.create(ph, voice=style, speed=spk_speed, lang=lang, is_phonemes=True, trim=True)
            wav = trim_sil(np.asarray(wav, dtype=np.float32), sr_out, -46.0)
            cs_sec = cur_n / float(sr_out)
            cur_n += int(wav.size)
            ce_sec = cur_n / float(sr_out)
            st.append([round(cs_sec, 4), round(ce_sec, 4)])
            chunks_out.append(wav)
            if ci < len(clauses) - 1:
                next_spk = str(clauses[ci + 1].get("speaker") or "jyoti").strip().lower()
                pause = 0.160 if next_spk != spk else 0.085
            elif si < len(segs) - 1:
                next_seg = segs[si + 1]
                next_spk = str(next_seg[0].get("speaker") or "jyoti").strip().lower() if next_seg else spk
                pause = 0.160 if next_spk != spk else 0.170
            else:
                pause = 0.110
            p_n = int(round(pause * sr_out))
            chunks_out.append(np.zeros(p_n, dtype=np.float32))
            cur_n += p_n
        c_timings.append(st)
        s_ends.append(round(cur_n / float(sr_out), 4))
    return sr_out, chunks_out, cur_n, c_timings, s_ends

word_count = int(req.get("wordCount") or 0)
sr, chunks, cur_samples, clause_timings, seg_ends = synth_pass(1.0)
first_dur = cur_samples / float(sr)
if first_dur > 57.5:
    sr, chunks, cur_samples, clause_timings, seg_ends = synth_pass(max(1.08, first_dur / 54.5))
elif word_count >= 120 and first_dur > 0 and (word_count / (first_dur / 60.0)) > 184.0:
    target_d = min(56.8, (word_count / 176.0) * 60.0)
    sr, chunks, cur_samples, clause_timings, seg_ends = synth_pass(max(0.82, first_dur / target_d))
full = np.concatenate(chunks) if chunks else np.zeros(sr, dtype=np.float32)
pk = float(np.max(np.abs(full))) if full.size else 0.0
if pk > 0.96:
    full = full * (0.96 / pk)
with wave.open(sys.argv[2], "wb") as wf:
    wf.setparams((1, 2, sr, 0, "NONE", "not compressed"))
    wf.writeframes(np.clip(full * 32767.0, -32768, 32767).astype(np.int16).tobytes())
open(sys.argv[3], "w", encoding="utf-8").write(json.dumps({"rawDur": round(cur_samples / float(sr), 4), "clauseTimings": clause_timings, "segEnds": seg_ends}))
"""


def _run_kokoro_synthesis(segments: list[dict], vc: dict, out_wav: Path, tmp_dir: Path) -> tuple[float, list[float], list[list[tuple[float, float]]]]:
    if not (KOKORO_PYTHON.is_file() and KOKORO_MODEL.is_file() and KOKORO_VOICES.is_file()):
        raise FileNotFoundError(f"Kokoro runtime/models missing under {REPO_ROOT / '.venv_audio'}")
    clauses_by_seg = [extract_segment_clauses(seg) for seg in segments]
    word_count = sum(len(str(seg.get("narration", "")).split()) for seg in segments)
    req_path, raw_wav, meta_path, mastered_wav = tmp_dir / "req.json", tmp_dir / "raw24k.wav", tmp_dir / "meta.json", tmp_dir / "mastered44k.wav"
    req_path.write_text(json.dumps({
        "model": str(KOKORO_MODEL), "voices": str(KOKORO_VOICES),
        "defaultVoice": str(vc.get("kokoroVoice") or "hf_sweet"),
        "voiceMap": vc.get("kokoroVoices") if isinstance(vc.get("kokoroVoices"), dict) else {},
        "lang": str(vc.get("kokoroLang") or "hi"),
        "speed": float(vc.get("kokoroSpeed") or 1.08),
        "speedMap": vc.get("kokoroSpeeds") if isinstance(vc.get("kokoroSpeeds"), dict) else {},
        "wordCount": word_count,
        "segments": clauses_by_seg,
    }, ensure_ascii=False), encoding="utf-8")
    proc = subprocess.run([str(KOKORO_PYTHON), "-c", _KOKORO_WORKER_CODE, str(req_path), str(raw_wav), str(meta_path)], capture_output=True, text=True, timeout=180)
    if proc.returncode != 0 or not raw_wav.is_file() or not meta_path.is_file():
        raise RuntimeError(f"Kokoro neural synthesis failed: {proc.stderr.strip() or proc.stdout.strip()}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    raw_dur = float(meta["rawDur"])
    if raw_dur > 58.0:
        raise RuntimeError(f"Kokoro raw audio ({raw_dur:.2f}s) exceeds 58.0s schema limit; raise kokoroSpeed or tighten script.")
    min_wpm_dur = min(57.5, (word_count / 183.5) * 60.0) if word_count >= 120 else 44.0
    ceil_cap = 58.0 if max(raw_dur, min_wpm_dur) > 56.0 else 56.0
    total_dur = round(max(44.0, min_wpm_dur, raw_dur, min(ceil_cap, math.ceil(raw_dur * 2.0) / 2.0)), 2)
    ff = shutil.which("ffmpeg")
    if ff and subprocess.run([ff, "-y", "-i", str(raw_wav), "-af", KOKORO_MASTER_AF, "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(mastered_wav)], capture_output=True, text=True, timeout=60).returncode == 0 and mastered_wav.is_file():
        _conform_pcm_wav(mastered_wav, out_wav, total_dur)
    elif _convert_to_pcm_wav(raw_wav, mastered_wav):
        _conform_pcm_wav(mastered_wav, out_wav, total_dur)
    else:
        raise RuntimeError("Failed to master/resample Kokoro 24kHz WAV to 44.1kHz PCM.")
    timings = [[(float( pair[0]), float(pair[1])) for pair in seg_t] for seg_t in meta["clauseTimings"]]
    return total_dur, [float(x) for x in meta["segEnds"]], timings


_EDGE_WORKER_CODE = """
import asyncio, json, pathlib, re, shutil, subprocess, sys, wave, numpy as np, edge_tts

req = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
tmp_dir, ff, fp, sr = pathlib.Path(req["tmpDir"]), req["ffmpeg"], shutil.which("ffprobe"), 44100
voice_map = {"jyoti": "hi-IN-SwaraNeural", "rajat": "hi-IN-MadhurNeural", "narrator": "hi-IN-MadhurNeural", "kabir": "hi-IN-MadhurNeural", "sharma": "hi-IN-MadhurNeural", "chachu": "hi-IN-MadhurNeural"}
voice_map.update({str(k).strip().lower(): str(v) for k, v in (req.get("edgeVoices") or {}).items()})
rate_map = {"jyoti": "+4%", "rajat": "+4%", "narrator": "-3%", "kabir": "-3%", "sharma": "+0%", "chachu": "+5%"}
rate_map.update({str(k).strip().lower(): str(v) for k, v in (req.get("edgeRates") or {}).items()})
pitch_map = {"jyoti": "-2Hz", "rajat": "-4Hz", "narrator": "-6Hz", "kabir": "-6Hz", "sharma": "-3Hz", "chachu": "-2Hz"}
pitch_map.update({str(k).strip().lower(): str(v) for k, v in (req.get("edgePitches") or {}).items()})
formant_map = {"jyoti": 1.065, "rajat": 1.12, "narrator": 0.945, "kabir": 0.945, "sharma": 0.985, "chachu": 1.0}
formant_map.update({str(k).strip().lower(): float(v) for k, v in (req.get("edgeFormants") or {}).items()})
rate_delta = int(req.get("rateDeltaPct") or 0)
segs = req["segments"]

def bump_rate_str(r_str, delta):
    if not delta:
        return r_str
    m_r = re.match(r"^\\s*([+-]?\\d+)\\s*%\\s*$", str(r_str))
    b = int(m_r.group(1)) if m_r else 0
    return f"{max(-35, min(65, b + delta)):+d}%"

def norm_clause_hi(txt):
    c = re.sub(r"\\.{2,}|…+", "", str(txt)).strip()
    if not c:
        return c
    m = re.search(r"([!?.।\\\"'”’]+)$", c)
    h, t = (c[: m.start()], m.group(1)) if m else (c, "")
    return f"{re.sub(r',+', ',', re.sub(r'\\s*[!?]+', ',', h))}{t}".strip()

def compute_rms(x, win):
    pad = np.pad(np.abs(x), (0, win), mode="constant")
    cs = np.cumsum(np.insert(pad.astype(np.float64) ** 2, 0, 0.0))
    return np.sqrt(np.maximum(0.0, (cs[win : win + x.size] - cs[: x.size]) / win))

def trim_and_compress(a, sr_hz, rel_thresh_db=-56.0, max_sil=0.55, target_sil=0.26, return_cuts=False):
    if a.size == 0:
        empty = np.zeros(int(0.05 * sr_hz), dtype=np.float32)
        return (empty, 0.0, []) if return_cuts else (empty, 0.0)
    pk = float(np.max(np.abs(a)))
    if pk <= 1e-5:
        empty = np.zeros(int(0.05 * sr_hz), dtype=np.float32)
        return (empty, 0.0, []) if return_cuts else (empty, 0.0)
    win = max(1, int(0.010 * sr_hz))
    rms = compute_rms(a, win)
    th = max(1e-5, pk * (10.0 ** (rel_thresh_db / 20.0)))
    idx = np.flatnonzero(rms > th)
    if idx.size == 0:
        empty = np.zeros(int(0.05 * sr_hz), dtype=np.float32)
        return (empty, 0.0, []) if return_cuts else (empty, 0.0)
    i0 = max(0, int(idx[0]) - int(0.055 * sr_hz))
    lead_trim_sec = i0 / float(sr_hz)
    e = min(a.size, int(idx[-1]) + int(0.165 * sr_hz))
    a = a[i0:e].copy()
    cuts = []
    inner_th = max(1e-5, pk * (10.0 ** (-62.0 / 20.0)))
    silent = compute_rms(a, win) <= inner_th
    if np.any(silent):
        diffs = np.diff(np.concatenate(([False], silent, [False])).astype(np.int8))
        starts, ends = np.flatnonzero(diffs == 1), np.flatnonzero(diffs == -1)
        max_len, keep_len = int(round(max_sil * sr_hz)), int(round(target_sil * sr_hz))
        xfade = min(keep_len // 3, int(0.025 * sr_hz))
        left_n = (keep_len - xfade) // 2
        right_n = keep_len - xfade - left_n
        onset_guard = int(0.055 * sr_hz)
        pieces, cur = [], 0
        for rs, re_idx in zip(starts, ends):
            re_safe = max(rs, re_idx - onset_guard)
            if rs > 0 and re_idx < a.size and (re_safe - rs) > max_len:
                pieces.append(a[cur : rs + left_n])
                if xfade > 0:
                    w = np.linspace(1.0, 0.0, xfade, dtype=np.float32)
                    pieces.append(a[rs + left_n : rs + left_n + xfade] * w + a[re_safe - right_n - xfade : re_safe - right_n] * (1.0 - w))
                pieces.append(a[re_safe - right_n : re_safe])
                cuts.append((rs / float(sr_hz), re_safe / float(sr_hz), (re_safe - rs - keep_len) / float(sr_hz)))
                cur = re_safe
        if pieces:
            pieces.append(a[cur:])
            a = np.concatenate(pieces)
    fn_in = min(a.size // 4, int(0.005 * sr_hz))
    fn_out = min(a.size // 4, int(0.008 * sr_hz))
    if fn_in > 1:
        a[:fn_in] *= np.linspace(0.0, 1.0, fn_in, dtype=np.float32)
    if fn_out > 1:
        a[-fn_out:] *= np.linspace(1.0, 0.0, fn_out, dtype=np.float32)
    return (a, lead_trim_sec, cuts) if return_cuts else (a, lead_trim_sec)

async def synth_all():
    sem = asyncio.Semaphore(4)
    async def one_clause(si, ci, cl):
        spk = str(cl.get("speaker") or "jyoti").strip().lower()
        voice = voice_map.get(spk) or voice_map["jyoti"]
        base_rate = str(cl.get("rate") or rate_map.get(spk) or "+4%")
        rate = bump_rate_str(base_rate, rate_delta)
        pitch = str(cl.get("pitch") or pitch_map.get(spk) or "-2Hz")
        formant = float(formant_map.get(spk, 1.065))
        clean_hi = norm_clause_hi(cl["hi"])
        mp3_p, wav_p = tmp_dir / f"cl_{si}_{ci}.mp3", tmp_dir / f"cl_{si}_{ci}.wav"
        word_bounds = []
        async def _stream_clause():
            buf = bytearray()
            events = []
            comm = edge_tts.Communicate(clean_hi, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
            async for ev in comm.stream():
                if ev.get("type") == "audio":
                    buf.extend(ev["data"])
                elif ev.get("type") == "WordBoundary":
                    events.append(ev)
            mp3_p.write_bytes(bytes(buf))
            return [(ev["offset"] / 1e7, (ev["offset"] + ev["duration"]) / 1e7) for ev in events]
        async with sem:
            last_err = None
            for attempt in range(3):
                try:
                    mp3_p.unlink(missing_ok=True)
                    word_bounds = await asyncio.wait_for(_stream_clause(), timeout=30.0)
                    if mp3_p.is_file() and mp3_p.stat().st_size > 128:
                        break
                except Exception as exc:
                    last_err = exc
                    await asyncio.sleep(0.4 * (attempt + 1))
            else:
                raise RuntimeError(f"edge_tts failed for seg {si} clause {ci}: {last_err}")
        in_sr = 24000
        if fp:
            pr = subprocess.run([fp, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_p)], capture_output=True, text=True, timeout=60)
            if pr.returncode == 0 and pr.stdout.strip().isdigit():
                in_sr = int(pr.stdout.strip())
        if abs(formant - 1.0) <= 0.004:
            tempo_scale = 1.0
            af_chain = "anull"
        else:
            tempo_v = round(min(1.22, max(0.85, 1.0 / formant)), 4) if formant < 1.0 else 1.01
            tempo_scale = max(0.5, round(formant * tempo_v, 6))
            af_chain = (
                f"asetrate=24000*{formant:.4f},aresample={sr},atempo={tempo_v}"
                if in_sr == 24000
                else f"aresample=24000,asetrate=24000*{formant:.4f},aresample={sr},atempo={tempo_v}"
            )
        emo = str(cl.get("emotion") or "").strip().lower()
        diegetic_fx = ""
        if emo == "phone_call" or spk == "chachu":
            diegetic_fx = "highpass=f=340,lowpass=f=3100,acompressor=threshold=-16dB:ratio=3.2:makeup=2dB"
        elif emo == "room_panic" or spk == "sharma":
            diegetic_fx = "highpass=f=110,aecho=0.8:0.86:38:0.16,acompressor=threshold=-17dB:ratio=2.6:makeup=1.5dB"
        if diegetic_fx:
            af_chain = diegetic_fx if af_chain == "anull" else f"{af_chain},{diegetic_fx}"
        r = subprocess.run([ff, "-y", "-i", str(mp3_p), "-ac", "1", "-af", af_chain, "-ar", str(sr), "-c:a", "pcm_s16le", str(wav_p)], capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or not wav_p.is_file():
            raise RuntimeError(f"ffmpeg mp3->wav failed: {r.stderr}")
        with wave.open(str(wav_p), "rb") as rf:
            raw_b = rf.readframes(rf.getnframes())
        trimmed_audio, lead_trim_sec, sil_cuts = trim_and_compress(np.frombuffer(raw_b, dtype=np.int16).astype(np.float32) / 32768.0, sr, return_cuts=True)
        clause_dur = trimmed_audio.size / float(sr)
        def _apply_cuts(t_v):
            rem = 0.0
            for c_start, c_end, c_rem in sil_cuts:
                if t_v >= c_end:
                    rem += c_rem
                elif t_v > c_start:
                    rem += c_rem * ((t_v - c_start) / max(1e-4, c_end - c_start))
            return max(0.0, t_v - rem)
        adj_spans = []
        for ws, we in word_bounds:
            s_t = _apply_cuts(max(0.0, ws - lead_trim_sec) / tempo_scale)
            e_t = _apply_cuts(max(0.02, we - lead_trim_sec) / tempo_scale)
            s_adj = min(clause_dur, s_t)
            e_adj = min(clause_dur, max(0.02, e_t))
            if e_adj <= s_adj:
                s_adj = max(0.0, min(s_adj, clause_dur - 0.02))
                e_adj = min(clause_dur, s_adj + 0.02)
            adj_spans.append([round(s_adj, 4), round(e_adj, 4)])
        return trimmed_audio, adj_spans
    flat = await asyncio.gather(*(one_clause(si, ci, cl) for si, cls in enumerate(segs) for ci, cl in enumerate(cls)))
    out, idx = [], 0
    for cls in segs:
        out.append(flat[idx : idx + len(cls)])
        idx += len(cls)
    return out

def synth_soft_breath(sr_hz, seed_v):
    rng = np.random.default_rng(seed_v)
    n = int(0.085 * sr_hz)
    t = np.linspace(0.0, 1.0, n, dtype=np.float32)
    env = np.sin(np.pi * t) ** 1.8
    raw = rng.normal(0.0, 1.0, n).astype(np.float32)
    # Smooth vocal-tract breath bandpass (~550Hz - 1800Hz) at subtle -31 dB studio booth level
    k = max(3, int(sr_hz / 1700))
    lp_hi = np.convolve(raw, np.ones(k, dtype=np.float32) / k, mode="same")
    k_lo = max(5, int(sr_hz / 480))
    lp_lo = np.convolve(lp_hi, np.ones(k_lo, dtype=np.float32) / k_lo, mode="same")
    band = lp_hi - lp_lo
    pk_b = float(np.max(np.abs(band))) or 1.0
    return np.concatenate([(band / pk_b) * env * 0.026, np.zeros(int(0.028 * sr_hz), dtype=np.float32)])

clause_results = asyncio.run(synth_all())
chunks, cur_samples, clause_timings, clause_word_spans, seg_ends = [], 0, [], [], []
for si, clauses in enumerate(segs):
    st, sw = [], []
    for ci, cl in enumerate(clauses):
        spk = str(cl.get("speaker") or "jyoti").strip().lower()
        if cl.get("breathBefore"):
            br = synth_soft_breath(sr, 9100 + si * 31 + ci)
            chunks.append(br)
            cur_samples += int(br.size)
        wav, w_spans = clause_results[si][ci]
        cs_sec = cur_samples / float(sr)
        cur_samples += int(wav.size)
        ce_sec = cur_samples / float(sr)
        st.append([round(cs_sec, 4), round(ce_sec, 4)])
        sw.append(w_spans)
        chunks.append(wav)
        if cl.get("pauseAfter") is not None:
            pause = float(cl["pauseAfter"])
        elif ci < len(clauses) - 1:
            next_spk = str(clauses[ci + 1].get("speaker") or "jyoti").strip().lower()
            pause = 0.095 if next_spk != spk else 0.085
        elif si < len(segs) - 1:
            pause = 0.11
        else:
            pause = 0.26
        p_n = int(round(pause * sr))
        chunks.append(np.zeros(p_n, dtype=np.float32))
        cur_samples += p_n
    clause_timings.append(st)
    clause_word_spans.append(sw)
    seg_ends.append(round(cur_samples / float(sr), 4))
full = np.concatenate(chunks) if chunks else np.zeros(sr, dtype=np.float32)
pk = float(np.max(np.abs(full))) if full.size else 0.0
if pk > 0.96:
    full = full * (0.96 / pk)
with wave.open(sys.argv[2], "wb") as wf:
    wf.setparams((1, 2, sr, 0, "NONE", "not compressed"))
    wf.writeframes(np.clip(full * 32767.0, -32768, 32767).astype(np.int16).tobytes())
pathlib.Path(sys.argv[3]).write_text(json.dumps({"rawDur": round(cur_samples / float(sr), 4), "clauseTimings": clause_timings, "clauseWordSpans": clause_word_spans, "segEnds": seg_ends}), encoding="utf-8")
"""


def _bump_edge_rate(rate_str: str, delta_pct: int) -> str:
    m = re.match(r"^\s*([+-]?\d+)\s*%\s*$", str(rate_str))
    base = int(m.group(1)) if m else 4
    return f"{max(-35, min(65, base + delta_pct)):+d}%"


def _run_edge_synthesis(
    segments: list[dict], vc: dict, out_wav: Path, tmp_dir: Path
) -> tuple[float, list[float], list[list[tuple[float, float]]], list[list[list[tuple[float, float]]]]]:
    if not AUDIO_PYTHON.is_file():
        raise FileNotFoundError(f"Audio Python venv missing at {AUDIO_PYTHON}")
    ff = shutil.which("ffmpeg")
    if not ff:
        raise FileNotFoundError("ffmpeg is required for --mode edge neural synthesis.")
    clauses_by_seg = [extract_segment_clauses(seg) for seg in segments]
    voices = {**DEFAULT_EDGE_VOICES, **{str(k).strip().lower(): str(v) for k, v in (vc.get("edgeVoices") or {}).items()}} if isinstance(vc.get("edgeVoices"), dict) else dict(DEFAULT_EDGE_VOICES)
    rates = {**DEFAULT_EDGE_RATES, **{str(k).strip().lower(): str(v) for k, v in (vc.get("edgeRates") or {}).items()}} if isinstance(vc.get("edgeRates"), dict) else dict(DEFAULT_EDGE_RATES)
    pitches = {**DEFAULT_EDGE_PITCHES, **{str(k).strip().lower(): str(v) for k, v in (vc.get("edgePitches") or {}).items()}} if isinstance(vc.get("edgePitches"), dict) else dict(DEFAULT_EDGE_PITCHES)
    formants = {**DEFAULT_EDGE_FORMANTS, **{str(k).strip().lower(): float(v) for k, v in (vc.get("edgeFormants") or {}).items()}} if isinstance(vc.get("edgeFormants"), dict) else dict(DEFAULT_EDGE_FORMANTS)
    req_path, raw_wav, meta_path, mastered_wav = tmp_dir / "edge_req.json", tmp_dir / "edge_raw44k.wav", tmp_dir / "edge_meta.json", tmp_dir / "edge_mastered44k.wav"

    def _invoke(cur_rates: dict[str, str], delta_pct: int = 0) -> dict:
        req_path.write_text(json.dumps({
            "tmpDir": str(tmp_dir), "ffmpeg": ff,
            "edgeVoices": voices, "edgeRates": cur_rates, "edgePitches": pitches, "edgeFormants": formants,
            "rateDeltaPct": delta_pct,
            "segments": clauses_by_seg,
        }, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run([str(AUDIO_PYTHON), "-c", _EDGE_WORKER_CODE, str(req_path), str(raw_wav), str(meta_path)], capture_output=True, text=True, timeout=60)
        if proc.returncode != 0 or not raw_wav.is_file() or not meta_path.is_file():
            raise RuntimeError(f"Edge neural synthesis failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return json.loads(meta_path.read_text(encoding="utf-8"))

    meta = _invoke(rates, 0)
    raw_dur = float(meta["rawDur"])
    if raw_dur > 57.95:
        bump = max(2, int(math.ceil((raw_dur / 57.4 - 1.0) * 100.0)))
        meta = _invoke({k: _bump_edge_rate(v, bump) for k, v in rates.items()}, bump)
        raw_dur = float(meta["rawDur"])
    elif raw_dur < 42.0 and raw_dur >= 37.0:
        slow = -max(6, int(math.ceil((1.0 - raw_dur / 45.0) * 100.0)))
        meta = _invoke({k: _bump_edge_rate(v, slow) for k, v in rates.items()}, slow)
        raw_dur = float(meta["rawDur"])
    total_dur = round(raw_dur, 2)
    if not (42.0 <= total_dur <= 58.0):
        raise RuntimeError(f"Edge neural audio ({total_dur:.2f}s) outside [42.0, 58.0]s schema envelope; adjust script length or edgeRates.")
    if subprocess.run([ff, "-y", "-i", str(raw_wav), "-af", EDGE_MASTER_AF, "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(mastered_wav)], capture_output=True, text=True, timeout=60).returncode == 0 and mastered_wav.is_file():
        _conform_pcm_wav(mastered_wav, out_wav, total_dur)
    else:
        raise RuntimeError("Failed to master Edge neural WAV to 44.1kHz PCM.")
    timings = [[(float(pair[0]), float(pair[1])) for pair in seg_t] for seg_t in meta["clauseTimings"]]
    word_spans = [
        [[(float(sp[0]), float(sp[1])) for sp in cl_sp] for cl_sp in seg_sp]
        for seg_sp in (meta.get("clauseWordSpans") or [])
    ]
    return total_dur, [float(x) for x in meta["segEnds"]], timings, word_spans


def prepare_episode_voice(
    episode_path: Path, mode: str = "draft", input_audio: Path | None = None,
    voice: str = "Daniel", rate: int = 185, output_dir: Path | None = None,
    whisper: bool = False, sync_manifest: bool = False,
) -> tuple[Path, Path]:
    manifest = json.loads(episode_path.read_text(encoding="utf-8"))
    ep_id, duration = manifest["id"], float(manifest.get("durationSeconds", 48.0))
    segments = manifest.get("scriptSegments", [])
    vc = manifest.get("voiceConfig") if isinstance(manifest.get("voiceConfig"), dict) else {}
    target_dir = output_dir or (REPO_ROOT / "engine" / "public" / "audio")
    target_dir.mkdir(parents=True, exist_ok=True)
    out_wav, out_captions = target_dir / f"{ep_id}.wav", target_dir / f"{ep_id}.captions.json"
    clause_timings: list[list[tuple[float, float]]] | None = None
    clause_word_spans: list[list[list[tuple[float, float]]]] | None = None

    if mode == "recorded":
        if input_audio is None or not input_audio.is_file():
            raise FileNotFoundError(f"--mode recorded requires existing --input file: {input_audio}")
        tmp_wav = target_dir / f".tmp_rec_{ep_id}_{os.getpid()}.wav"
        try:
            src_wav = tmp_wav if _convert_to_pcm_wav(input_audio, tmp_wav, normalize=True) else input_audio
            raw_dur = _conform_pcm_wav(src_wav, out_wav, duration)
            if abs(raw_dur - duration) > 0.25:
                print(f"[prepare_voice] Conformed recorded audio ({raw_dur:.2f}s -> {duration:.2f}s).", file=sys.stderr)
        except wave.Error as exc:
            raise RuntimeError(f"Unsupported or corrupt audio input '{input_audio}': {exc}") from exc
        finally:
            tmp_wav.unlink(missing_ok=True)
    elif mode in ("kokoro", "edge"):
        tmp_dir = target_dir / f".tmp_{mode}_{ep_id}_{os.getpid()}"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        try:
            if mode == "edge":
                total_dur, seg_ends, clause_timings, clause_word_spans = _run_edge_synthesis(segments, vc, out_wav, tmp_dir)
            else:
                total_dur, seg_ends, clause_timings = _run_kokoro_synthesis(segments, vc, out_wav, tmp_dir)
            if sync_manifest:
                sync_manifest_timings(manifest, seg_ends, total_dur)
                episode_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                duration = float(manifest["durationSeconds"])
                segments = manifest["scriptSegments"]
            else:
                _conform_pcm_wav(out_wav, out_wav, duration, strict_drift=True)
                timed_segs = [dict(s) for s in segments]
                cur = 0.0
                for idx, s in enumerate(timed_segs):
                    s["startSec"] = cur
                    s["endSec"] = duration if idx == len(timed_segs) - 1 else round(min(duration - 0.1, seg_ends[idx]), 4)
                    cur = float(s["endSec"])
                segments = timed_segs
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        tmp_dir = target_dir / f".tmp_{ep_id}_{os.getpid()}"
        synthesized, timed_segments = False, [dict(s) for s in segments]
        try:
            if SAY_BIN.is_file() and AFCONVERT_BIN.is_file() and segments:
                tmp_dir.mkdir(parents=True, exist_ok=True)
                sr, any_seg_ok = 44100, False
                probe_rate = max(145, min(225, int(vc.get("targetWpm", rate) if vc.get("targetWpm") is not None else rate)))
                pcm_buf = bytearray(max(1, int(round(duration * sr))) * 2)
                for idx, seg in enumerate(segments):
                    text = str(seg.get("narration", "")).strip()
                    s_sec, e_sec = float(seg["startSec"]), float(seg["endSec"])
                    window = e_sec - s_sec
                    target_dur, budget, cur_rate = max(0.45, window - 0.22), max(0.45, window - 0.08), probe_rate
                    if not text or window <= 0:
                        continue
                    seg_aiff, seg_wav = tmp_dir / f"seg_{idx}.aiff", tmp_dir / f"seg_{idx}.wav"
                    for attempt in range(3):
                        seg_aiff.unlink(missing_ok=True)
                        seg_wav.unlink(missing_ok=True)
                        cmds = ([str(SAY_BIN), "-v", voice, "-r", str(cur_rate), "-o", str(seg_aiff), text],
                                [str(SAY_BIN), "-r", str(cur_rate), "-o", str(seg_aiff), text])
                        ok = any(subprocess.run(c, capture_output=True, text=True, timeout=60).returncode == 0 and seg_aiff.is_file()
                                 and _convert_to_pcm_wav(seg_aiff, seg_wav) for c in cmds)
                        if not ok:
                            break
                        with wave.open(str(seg_wav), "rb") as rf:
                            frames, seg_dur = rf.readframes(rf.getnframes()), rf.getnframes() / float(rf.getframerate())
                        if (attempt == 0 and seg_dur <= budget and (window - seg_dur) <= 0.45) or (attempt == 1 and seg_dur <= budget) or attempt == 2:
                            start_idx = max(0, int(round(s_sec * sr))) * 2
                            seg_end_byte = int(round(e_sec * sr)) * 2
                            max_bytes = min(len(frames), max(0, min(len(pcm_buf), seg_end_byte) - start_idx))
                            pcm_buf[start_idx : start_idx + max_bytes] = frames[:max_bytes]
                            timed_segments[idx]["endSec"] = round(min(e_sec, s_sec + (max_bytes / 2) / sr), 4)
                            any_seg_ok = True
                            break
                        cur_rate = (
                            max(140, min(285, int(round(probe_rate * (seg_dur / target_dur)))))
                            if attempt == 0
                            else min(320, int(cur_rate * (seg_dur / max(0.35, budget - 0.06)) + 8))
                        )
                if any_seg_ok:
                    with wave.open(str(out_wav), "wb") as wf:
                        wf.setparams((1, 2, sr, 0, "NONE", "not compressed"))
                        wf.writeframes(bytes(pcm_buf))
                    segments, synthesized = timed_segments, True
            if not synthesized:
                synthesize_silent_wav(out_wav, duration)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    force_whisper = (
        os.environ.get("CYBERJASOOS_FORCE_WHISPER") == "1"
        or os.environ.get("BREACHZERO_FORCE_WHISPER") == "1"
    )
    run_whisper = (mode == "recorded") or whisper or force_whisper
    if clause_timings is not None and not whisper:
        captions = build_clause_locked_word_timestamps(segments, clause_timings, clause_word_spans=clause_word_spans)
    else:
        captions = (_try_whisper_captions(out_wav, segments, max_sec=duration) if run_whisper else None) or build_deterministic_word_timestamps(segments)
    attach_wav_loudness_peaks(out_wav, captions)
    snap_words_off_silence(out_wav, captions)
    attach_wav_loudness_peaks(out_wav, captions)
    out_captions.write_text(json.dumps(captions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if sync_manifest:
        vc_mut = manifest.setdefault("voiceConfig", {})
        if mode == "recorded":
            vc_mut["mode"], vc_mut["engineLicense"] = "recorded", "OWN_VOICE"
        elif mode == "kokoro":
            vc_mut["mode"], vc_mut["engineLicense"] = "kokoro_neural", "APACHE_2_0"
        elif mode == "edge":
            vc_mut["mode"] = "edge_neural"
            if vc_mut.get("engineLicense") != "COMMERCIAL_API":
                vc_mut["engineLicense"] = "EDGE_READ_ALOUD_PREVIEW"
        scenes_mut = manifest.get("scenes") or []
        if scenes_mut and isinstance(scenes_mut[-1], dict) and scenes_mut[-1].get("kind") == "detective_suspect_board":
            sc_last = scenes_mut[-1]
            props_last = sc_last.get("props") or {}
            if isinstance(props_last.get("optionTimingsSec"), list):
                s_start = float(sc_last.get("startSec") or 0.0)
                w_map = {str(w.get("word", "")): round(float(w["startSec"]) - s_start, 3) for w in captions if float(w.get("startSec", 0.0)) >= s_start - 0.05}
                for cue_triplet in (("do", "jeb", "aur"), ("Hotel", "Daftaron", "Shaadi")):
                    if all(k in w_map for k in cue_triplet):
                        props_last["optionTimingsSec"] = [w_map[k] for k in cue_triplet]
                        break
        episode_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_wav, out_captions


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Prepare episode WAV audio and word captions.")
    p.add_argument("--episode", required=True, help="Path to episode JSON manifest.")
    p.add_argument("--mode", choices=("draft", "kokoro", "edge", "recorded"), default="draft")
    p.add_argument("--input", dest="input_file", help="Recorded voice file for --mode recorded.")
    p.add_argument("--voice", default="Daniel", help="macOS say voice for --mode draft.")
    p.add_argument("--rate", type=int, default=185, help="Speech rate (WPM) for --mode draft.")
    p.add_argument("--output-dir", help="Optional custom output directory.")
    p.add_argument("--whisper", action="store_true", help="Force Whisper word alignment in draft mode.")
    p.add_argument("--sync-manifest", action="store_true", help="Sync durationSeconds, scriptSegments, and scenes to synthesized timings.")
    args = p.parse_args(argv)
    ep_path = Path(args.episode)
    if not ep_path.is_file():
        print(f"Episode manifest not found: {ep_path}", file=sys.stderr)
        return 1
    try:
        wav_path, cap_path = prepare_episode_voice(
            ep_path, mode=args.mode, input_audio=Path(args.input_file) if args.input_file else None,
            voice=args.voice, rate=args.rate, output_dir=Path(args.output_dir) if args.output_dir else None,
            whisper=args.whisper, sync_manifest=args.sync_manifest,
        )
    except Exception as exc:
        print(f"Voice preparation failed: {exc}", file=sys.stderr)
        return 1
    print(f"Generated audio:    {wav_path}\nGenerated captions: {cap_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
