import React, { useMemo } from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRIGHT_COLORS, COLORS, FONTS, NOIR_GRID, SAFE_ZONE } from '../theme/tokens';
import { ScriptSegment, SpeakerId, WordTimestamp } from '../types';

interface WordChunk {
  words: WordTimestamp[];
  startSec: number;
  endSec: number;
  speaker?: SpeakerId;
}

const normalizeToken = (raw: string): string =>
  raw.toLowerCase().replace(/[^a-z0-9%$]/g, '');

const deriveWordsFromSegments = (segments: ScriptSegment[]): WordTimestamp[] => {
  const derived: WordTimestamp[] = [];

  for (const seg of segments) {
    const rawTokens = seg.narration.trim().split(/\s+/).filter(Boolean);
    if (rawTokens.length === 0) continue;

    const emphasisSet = new Set<string>();
    for (const kw of seg.highlightKeywords) {
      for (const part of kw.split(/\s+/)) {
        const clean = normalizeToken(part);
        if (clean.length >= 2) emphasisSet.add(clean);
      }
    }

    const weights = rawTokens.map((t) => Math.max(2, t.length));
    const totalWeight = weights.reduce((acc, w) => acc + w, 0);
    const span = Math.max(0.1, seg.endSec - seg.startSec);

    let cursor = seg.startSec;
    rawTokens.forEach((word, idx) => {
      const dur = (weights[idx] / totalWeight) * span;
      const clean = normalizeToken(word);
      derived.push({
        word,
        startSec: cursor,
        endSec: cursor + dur,
        emphasis: emphasisSet.has(clean),
        speaker: seg.speaker,
      });
      cursor += dur;
    });
  }

  return derived;
};

const PRIMARY_SPEAKERS = new Set(['kabir', 'jyoti', 'rajat', 'narrator']);

export const WordCaptions: React.FC<{
  words: WordTimestamp[];
  segments: ScriptSegment[];
  isBrightTheme?: boolean;
  isNoirCinema?: boolean;
  liveLoudness?: number;
  activeSpeaker?: SpeakerId;
  sceneWords?: WordTimestamp[];
  speakerLabels?: Partial<Record<SpeakerId, string>>;
  hideSpeakerPill?: boolean;
  companyName?: string;
}> = ({
  words,
  segments,
  isBrightTheme = false,
  isNoirCinema = false,
  liveLoudness = 0.35,
  activeSpeaker,
  speakerLabels,
  hideSpeakerPill = false,
  companyName = 'SERIES',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeSec = frame / fps;
  const captionHeight = SAFE_ZONE.captionBottom - SAFE_ZONE.captionTop;
  const safeLoudness = Number.isFinite(liveLoudness)
    ? Math.min(1, Math.max(0, liveLoudness))
    : 0.35;

  const hasDualSpeakers = useMemo(() => {
    const speakerSet = new Set<string>();
    for (const w of words) {
      if (w.speaker) speakerSet.add(w.speaker);
    }
    for (const s of segments) {
      if (s.speaker) speakerSet.add(s.speaker);
    }
    return speakerSet.size >= 2;
  }, [words, segments]);

  const chunks = useMemo<WordChunk[]>(() => {
    const effective =
      words.length > 0 ? words : deriveWordsFromSegments(segments);
    const grouped: WordChunk[] = [];
    const chunkSize = isNoirCinema ? 3 : 4;

    let bucket: WordTimestamp[] = [];
    for (const item of effective) {
      const prev = bucket[bucket.length - 1];
      const speakerSwitched =
        prev && item.speaker && prev.speaker && item.speaker !== prev.speaker;
      const longPause = prev && item.startSec - prev.endSec > (isNoirCinema ? 0.18 : 0.22);
      const endedSentence = Boolean(prev && /[.!?:]["']?$/.test(prev.word));

      if (
        bucket.length >= chunkSize ||
        speakerSwitched ||
        longPause ||
        endedSentence
      ) {
        if (bucket.length > 0) {
          grouped.push({
            words: bucket,
            startSec: bucket[0].startSec,
            endSec: bucket[bucket.length - 1].endSec,
            speaker: bucket[0].speaker,
          });
        }
        bucket = [item];
      } else {
        bucket.push(item);
      }
    }
    if (bucket.length > 0) {
      grouped.push({
        words: bucket,
        startSec: bucket[0].startSec,
        endSec: bucket[bucket.length - 1].endSec,
        speaker: bucket[0].speaker,
      });
    }
    return grouped;
  }, [words, segments, isNoirCinema]);

  const activeChunk =
    chunks.find(
      (c) => currentTimeSec >= c.startSec && currentTimeSec <= c.endSec
    ) ??
    chunks.find(
      (c) =>
        currentTimeSec >= c.startSec - 0.06 && currentTimeSec <= c.endSec + 0.1
    );

  if (!activeChunk) {
    return null;
  }

  let activeIdx = activeChunk.words.findIndex(
    (w) => currentTimeSec >= w.startSec && currentTimeSec < w.endSec
  );
  if (activeIdx === -1) {
    for (let i = activeChunk.words.length - 1; i >= 0; i--) {
      if (currentTimeSec >= activeChunk.words[i].startSec) {
        activeIdx = i;
        break;
      }
    }
  }
  if (activeIdx === -1) activeIdx = 0;

  const captionLeft = SAFE_ZONE.captionLeft ?? SAFE_ZONE.left;
  const captionWidth = SAFE_ZONE.captionWidth ?? SAFE_ZONE.usableWidth;
  const totalChars = activeChunk.words.reduce((acc, w) => acc + w.word.length, 0);
  const chunkSpeaker: SpeakerId = activeChunk.speaker ?? activeSpeaker ?? 'jyoti';
  const isCameo = Boolean(chunkSpeaker && !PRIMARY_SPEAKERS.has(chunkSpeaker));
  const showCameoPill = isCameo && !hideSpeakerPill;
  const resolvedCameoLabel =
    (chunkSpeaker && speakerLabels?.[chunkSpeaker]) || 'VOICE AUDIO';
  const isCallCameo = /call|phone/i.test(resolvedCameoLabel);
  const isRajat = hasDualSpeakers && chunkSpeaker === 'rajat';
  const wordFontSize = isNoirCinema
    ? isCameo
      ? totalChars > 22
        ? 40
        : 46
      : totalChars > 22
        ? 44
        : 52
    : hasDualSpeakers
      ? totalChars > 26
        ? 35
        : 40
      : totalChars > 28
        ? 38
        : 44;
  const speakerAccent = isBrightTheme
    ? isRajat
      ? '#FBBF24'
      : '#38BDF8'
    : isRajat
      ? COLORS.amber
      : COLORS.cyan;
  const borderAccent = isBrightTheme
    ? isRajat
      ? '#F59E0B'
      : '#38BDF8'
    : isRajat
      ? 'rgba(255, 176, 32, 0.44)'
      : 'rgba(0, 240, 255, 0.34)';

  if (isNoirCinema) {
    const cameoTagColor = isCallCameo ? '#34D399' : '#FBBF24';
    const cameoIdleColor = !isCameo
      ? '#FFFFFF'
      : isCallCameo
        ? '#ECFDF5'
        : '#FEF3C7';

    return (
      <div
        data-role="word-captions"
        style={{
          position: 'absolute',
          left: 132,
          top: SAFE_ZONE.captionTop,
          width: 816,
          height: captionHeight,
          zIndex: 15,
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: showCameoPill ? 6 : 0,
          padding: '0 16px',
          pointerEvents: 'none',
        }}
      >
        {showCameoPill ? (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '4px 14px',
              borderRadius: 999,
              backgroundColor: 'rgba(6, 10, 20, 0.9)',
              border: `1.5px solid ${cameoTagColor}`,
              boxShadow: '0 8px 20px rgba(0, 0, 0, 0.72)',
              fontFamily: FONTS.mono,
              fontSize: 20,
              fontWeight: 900,
              letterSpacing: 0.6,
              lineHeight: 1.15,
              color: cameoTagColor,
              whiteSpace: 'nowrap',
            }}
          >
            {`● ${resolvedCameoLabel}`}
          </span>
        ) : null}

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'center',
            gap: isCameo ? '4px 16px' : '6px 18px',
            maxWidth: 784,
          }}
        >
          {activeChunk.words.map((item, idx) => {
            const isActive = idx === activeIdx;
            const ageFrames = Math.max(0, (currentTimeSec - item.startSec) * fps);
            const pop = spring({
              frame: isActive ? ageFrames : 0,
              fps,
              config: { damping: 12, stiffness: 310, mass: 0.45 },
            });
            const scale = isActive
              ? interpolate(pop, [0, 1], [0.94, 1.07 + safeLoudness * 0.04])
              : 1;
            const wordColor = isActive
              ? item.emphasis
                ? '#FF2E54'
                : '#FACC15'
              : item.emphasis
                ? '#FDE68A'
                : cameoIdleColor;
            const activeGlow = item.emphasis
              ? 'rgba(255, 46, 84, 0.72)'
              : 'rgba(250, 204, 21, 0.65)';

            return (
              <span
                key={`${item.word}-${item.startSec}-${idx}`}
                style={{
                  display: 'inline-block',
                  fontFamily: FONTS.display,
                  fontSize: wordFontSize,
                  fontWeight: 900,
                  lineHeight: 1.12,
                  letterSpacing: 0.4,
                  color: wordColor,
                  WebkitTextStroke: '2px rgba(2, 6, 23, 0.96)',
                  paintOrder: 'stroke fill',
                  transform: `scale(${scale})`,
                  textShadow: isActive
                    ? `0 0 26px ${activeGlow}, 0 4px 14px rgba(0, 0, 0, 0.96), 0 2px 4px rgba(0, 0, 0, 0.98)`
                    : '0 4px 14px rgba(0, 0, 0, 0.96), 0 2px 4px rgba(0, 0, 0, 0.98)',
                }}
              >
                {item.word}
              </span>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div
      data-role="word-captions"
      style={{
        position: 'absolute',
        left: captionLeft,
        top: SAFE_ZONE.captionTop,
        width: captionWidth,
        height: captionHeight,
        zIndex: 15,
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: hasDualSpeakers ? 4 : 0,
          padding: hasDualSpeakers ? '8px 24px 10px' : '12px 26px',
          borderRadius: 20,
          backgroundColor: isBrightTheme
            ? BRIGHT_COLORS.captionBg
            : 'rgba(6, 10, 18, 0.93)',
          border: `${isBrightTheme ? 2 : 1.5}px solid ${borderAccent}`,
          boxShadow: isBrightTheme
            ? `0 16px 38px rgba(15, 23, 42, 0.36), 0 0 0 3px ${
                isRajat ? 'rgba(245, 158, 11, 0.28)' : 'rgba(56, 189, 248, 0.28)'
              }`
            : '0 16px 40px rgba(0, 0, 0, 0.74)',
          maxWidth: captionWidth,
          boxSizing: 'border-box',
        }}
      >
        {hasDualSpeakers ? (
          <span
            style={{
              fontFamily: FONTS.mono,
              fontSize: 20,
              fontWeight: 800,
              letterSpacing: 1.0,
              lineHeight: 1.1,
              color: speakerAccent,
              textTransform: 'uppercase',
            }}
          >
            {isBrightTheme
              ? isRajat
                ? `● RAJAT · ${companyName}`
                : `● JYOTI · ${companyName}`
              : isRajat
                ? '● RAJAT // CYBER LEAD'
                : '● JYOTI // THREAT HUNTER'}
          </span>
        ) : null}

        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '5px 16px',
          }}
        >
          {activeChunk.words.map((item, idx) => {
            const isActive = idx === activeIdx;
            const ageFrames = Math.max(0, (currentTimeSec - item.startSec) * fps);
            const pop = spring({
              frame: isActive ? ageFrames : 0,
              fps,
              config: { damping: 12, stiffness: 280, mass: 0.5 },
            });
            const peakTarget = isBrightTheme ? 1.04 + safeLoudness * 0.05 : 1.08;
            const scale = isActive ? interpolate(pop, [0, 1], [0.95, peakTarget]) : 1;
            const activeColor = isBrightTheme
              ? item.emphasis
                ? BRIGHT_COLORS.captionEmphasisCoral
                : BRIGHT_COLORS.captionActiveYellow
              : item.emphasis
                ? isRajat
                  ? COLORS.emerald
                  : COLORS.crimson
                : speakerAccent;
            const glowTone = isBrightTheme
              ? item.emphasis
                ? 'rgba(251, 113, 133, 0.48)'
                : 'rgba(250, 204, 21, 0.45)'
              : item.emphasis
                ? isRajat
                  ? 'rgba(0, 230, 118, 0.55)'
                  : 'rgba(255, 46, 84, 0.55)'
                : isRajat
                  ? 'rgba(255, 176, 32, 0.55)'
                  : 'rgba(0, 240, 255, 0.52)';

            return (
              <span
                key={`${item.word}-${item.startSec}-${idx}`}
                style={{
                  display: 'inline-block',
                  fontFamily: FONTS.display,
                  fontSize: wordFontSize,
                  fontWeight: 900,
                  lineHeight: 1.12,
                  letterSpacing: 0.4,
                  color: isActive ? activeColor : '#FFFFFF',
                  transform: `scale(${scale})`,
                  textShadow: isActive
                    ? `0 0 22px ${glowTone}, 0 3px 10px rgba(0, 0, 0, 0.85)`
                    : '0 2px 8px rgba(0, 0, 0, 0.8)',
                }}
              >
                {item.word}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};
