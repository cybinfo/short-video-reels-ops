import React, { useState } from 'react';
import {
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { BRIGHT_COLORS, COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { SpeakerId, WordTimestamp } from '../types';

const CisoFallbackSilhouette: React.FC = () => (
  <svg
    width={60}
    height={60}
    viewBox="0 0 60 60"
    style={{ display: 'block', flexShrink: 0 }}
  >
    <defs>
      <linearGradient id="cisoBgGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#0D1B33" />
        <stop offset="100%" stopColor="#1B1026" />
      </linearGradient>
    </defs>
    <rect width="60" height="60" rx="30" fill="url(#cisoBgGrad)" />
    {/* Shoulders / Tactical Jacket */}
    <path
      d="M11 56 C13 43, 21 39, 30 39 C39 39, 47 43, 49 56 Z"
      fill="#1E293B"
      stroke={COLORS.cyan}
      strokeWidth="1.5"
    />
    {/* Head Silhouette */}
    <circle cx="30" cy="24" r="10.5" fill="#334155" stroke={COLORS.cyan} strokeWidth="1.4" />
    {/* Cyber Visor + Comms Mic */}
    <rect x="21" y="21" width="18" height="5" rx="2.5" fill={COLORS.cyan} opacity="0.92" />
    <path d="M39 26 L44 30 L35 32" fill="none" stroke={COLORS.crimson} strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const SeasonHudHeader: React.FC<{
  companyName: string;
  season: number;
  episode: number;
  totalEpisodes: number;
  domain: string;
  progress?: number;
  spoilerFlipSec?: number;
  cliffhangerStartSec?: number;
  activeSpeaker?: SpeakerId;
  hasDualSpeakers?: boolean;
  isBrightTheme?: boolean;
  liveLoudness?: number;
  sceneWords?: WordTimestamp[];
}> = ({
  companyName,
  episode,
  totalEpisodes,
  domain,
  spoilerFlipSec = 14,
  cliffhangerStartSec,
  activeSpeaker = 'jyoti',
  hasDualSpeakers = true,
  isBrightTheme = false,
  liveLoudness = 0.35,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const [jyotiFailed, setJyotiFailed] = useState(false);
  const [rajatFailed, setRajatFailed] = useState(false);

  const entrance = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 150, mass: 0.8 },
  });

  const translateY = interpolate(entrance, [0, 1], [-14, 0]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  // Cold-Open (0:00–0:03.2) & Cliffhanger Avatar Pop
  const coldOpenEnd = Math.round(fps * 3.2);
  const cliffhangerStart =
    cliffhangerStartSec !== undefined
      ? Math.round(fps * cliffhangerStartSec)
      : Math.max(0, durationInFrames - Math.round(fps * 8));
  const isHighAlertPop = frame < coldOpenEnd || frame >= cliffhangerStart;

  const pulseWave = (Math.sin(frame * 0.28) + 1) / 2;
  const spoilerFlipFrame = Math.round(fps * spoilerFlipSec);
  const showDomain = frame >= spoilerFlipFrame;
  const domainFlip = spring({
    frame: Math.max(0, frame - spoilerFlipFrame),
    fps,
    config: { damping: 16, stiffness: 170 },
  });

  const episodeCode = String(episode).padStart(2, '0');
  const totalCode = String(totalEpisodes).padStart(2, '0');
  const domainFontSize = domain.length > 38 ? 15 : domain.length > 26 ? 16 : 18;

  const isRajatActive = hasDualSpeakers && activeSpeaker === 'rajat';
  const jyotiActive = !isRajatActive;
  const safeLoudness = Number.isFinite(liveLoudness)
    ? Math.min(1, Math.max(0, liveLoudness))
    : 0.35;
  const activeBrightScale = 1.04 + safeLoudness * 0.09;
  const ringSpread = -(2 + safeLoudness * 3.5);
  const ringAlpha = Math.min(1, 0.24 + safeLoudness * 0.76);
  const glowPx = Math.round(10 + safeLoudness * 18);
  const glowOpacity = (0.26 + safeLoudness * 0.5).toFixed(2);

  const speakerAccent = isBrightTheme
    ? isRajatActive
      ? BRIGHT_COLORS.amber
      : '#0284C7'
    : isRajatActive
      ? COLORS.amber
      : COLORS.cyan;

  const hudBorderColor = isBrightTheme
    ? isHighAlertPop
      ? BRIGHT_COLORS.crimson
      : isRajatActive
        ? BRIGHT_COLORS.amberBright
        : '#0EA5E9'
    : isHighAlertPop
      ? COLORS.crimson
      : isRajatActive
        ? 'rgba(255, 176, 32, 0.42)'
        : 'rgba(0, 240, 255, 0.36)';

  return (
    <div
      data-role="hud-header"
      style={{
        position: 'absolute',
        left: SAFE_ZONE.left,
        top: SAFE_ZONE.hudTop,
        width: SAFE_ZONE.usableWidth,
        height: SAFE_ZONE.hudHeight,
        zIndex: 10,
        backgroundColor: isBrightTheme
          ? 'rgba(255, 255, 255, 0.96)'
          : 'rgba(13, 21, 38, 0.94)',
        border: `${isBrightTheme ? 2 : 1.5}px solid ${hudBorderColor}`,
        borderRadius: 22,
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 14,
        padding: isBrightTheme ? '0 32px 0 22px' : '0 18px',
        opacity,
        transform: `translateY(${translateY}px)`,
        boxShadow: isBrightTheme
          ? isHighAlertPop
            ? '0 14px 32px rgba(225, 29, 72, 0.2), 0 4px 12px rgba(15, 23, 42, 0.08)'
            : isRajatActive
              ? '0 12px 28px rgba(245, 158, 11, 0.18), 0 4px 10px rgba(15, 23, 42, 0.06)'
              : '0 12px 28px rgba(2, 132, 199, 0.16), 0 4px 10px rgba(15, 23, 42, 0.06)'
          : isHighAlertPop
            ? `0 12px 32px rgba(0, 0, 0, 0.55), 0 0 24px ${COLORS.crimsonMuted}`
            : '0 12px 30px rgba(0, 0, 0, 0.5)',
      }}
    >
      {/* Left: Dual Cyber-Duo Avatars (Jyoti + Rajat) + Live Comms Bars + Active Speaker Stack */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {/* JYOTI AVATAR */}
          <div
            style={{
              position: 'relative',
              width: isBrightTheme ? 68 : 60,
              height: isBrightTheme ? 68 : 60,
              borderRadius: '50%',
              padding: 2.5,
              boxSizing: 'border-box',
              background: jyotiActive
                ? isBrightTheme
                  ? 'linear-gradient(135deg, #06B6D4 0%, #0284C7 100%)'
                  : `linear-gradient(135deg, ${COLORS.cyan} 0%, ${COLORS.crimson} 100%)`
                : 'rgba(148, 163, 184, 0.45)',
              boxShadow: jyotiActive
                ? isBrightTheme
                  ? `0 0 ${glowPx}px rgba(6, 182, 212, ${glowOpacity})`
                  : `0 0 18px rgba(0, 240, 255, 0.55), 0 0 10px ${COLORS.crimsonMuted}`
                : 'none',
              transform: `scale(${
                jyotiActive
                  ? isBrightTheme
                    ? activeBrightScale
                    : isHighAlertPop
                      ? 1.1
                      : 1.05
                  : 0.88
              })`,
              opacity: jyotiActive ? 1 : isBrightTheme ? 0.72 : 0.56,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {jyotiActive ? (
              <div
                data-ambient="true"
                style={{
                  position: 'absolute',
                  inset: isBrightTheme ? ringSpread : -3,
                  borderRadius: '50%',
                  border: `2px solid ${
                    isBrightTheme
                      ? '#06B6D4'
                      : isHighAlertPop && pulseWave > 0.5
                        ? COLORS.crimson
                        : COLORS.cyan
                  }`,
                  opacity: isBrightTheme
                    ? ringAlpha
                    : interpolate(pulseWave, [0, 1], [0.35, 0.9]),
                  pointerEvents: 'none',
                }}
              />
            ) : null}
            <div
              style={{
                width: isBrightTheme ? 63 : 55,
                height: isBrightTheme ? 63 : 55,
                borderRadius: '50%',
                overflow: 'hidden',
                backgroundColor: isBrightTheme ? BRIGHT_COLORS.bgSubtle : COLORS.bgCanvas,
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <CisoFallbackSilhouette />
              {!jyotiFailed ? (
                <img
                  src={staticFile('brand/jyoti-avatar.png')}
                  alt=""
                  onError={() => setJyotiFailed(true)}
                  style={{
                    position: 'absolute',
                    inset: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />
              ) : null}
            </div>
          </div>

          {/* RAJAT AVATAR */}
          {hasDualSpeakers ? (
            <div
              style={{
                position: 'relative',
                width: isBrightTheme ? 68 : 60,
                height: isBrightTheme ? 68 : 60,
                borderRadius: '50%',
                padding: 2.5,
                boxSizing: 'border-box',
                background: isRajatActive
                  ? isBrightTheme
                    ? `linear-gradient(135deg, ${BRIGHT_COLORS.amberBright} 0%, ${BRIGHT_COLORS.saffron} 100%)`
                    : `linear-gradient(135deg, ${COLORS.amber} 0%, ${COLORS.cyan} 100%)`
                  : 'rgba(148, 163, 184, 0.45)',
                boxShadow: isRajatActive
                  ? isBrightTheme
                    ? `0 0 ${glowPx}px rgba(245, 158, 11, ${glowOpacity})`
                    : `0 0 18px rgba(255, 176, 32, 0.55), 0 0 10px ${COLORS.cyanMuted}`
                  : 'none',
                transform: `scale(${
                  isRajatActive
                    ? isBrightTheme
                      ? activeBrightScale
                      : isHighAlertPop
                        ? 1.1
                        : 1.05
                    : 0.88
                })`,
                opacity: isRajatActive ? 1 : isBrightTheme ? 0.72 : 0.56,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {isRajatActive ? (
                <div
                  data-ambient="true"
                  style={{
                    position: 'absolute',
                    inset: isBrightTheme ? ringSpread : -3,
                    borderRadius: '50%',
                    border: `2px solid ${isBrightTheme ? BRIGHT_COLORS.amberBright : COLORS.amber}`,
                    opacity: isBrightTheme
                      ? ringAlpha
                      : interpolate(pulseWave, [0, 1], [0.35, 0.9]),
                    pointerEvents: 'none',
                  }}
                />
              ) : null}
              <div
                style={{
                  width: isBrightTheme ? 63 : 55,
                  height: isBrightTheme ? 63 : 55,
                  borderRadius: '50%',
                  overflow: 'hidden',
                  backgroundColor: isBrightTheme ? BRIGHT_COLORS.bgSubtle : COLORS.bgCanvas,
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <CisoFallbackSilhouette />
                {!rajatFailed ? (
                  <img
                    src={staticFile('brand/rajat-avatar.png')}
                    alt=""
                    onError={() => setRajatFailed(true)}
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                    }}
                  />
                ) : null}
              </div>
            </div>
          ) : null}
        </div>

        {/* 4 Animated Live Comms Waveform Bars */}
        <div
          data-ambient="true"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            height: 42,
            flexShrink: 0,
          }}
        >
          {[0, 1, 2, 3].map((barIdx) => {
            const barWeights = [22, 34, 28, 18] as const;
            const shimmer = 0.86 + 0.14 * Math.sin(frame * 0.44 + barIdx * 1.4);
            const wave =
              (Math.sin(frame * 0.38 + barIdx * 1.35) +
                Math.cos(frame * 0.23 + barIdx * 0.9) +
                2) /
              4;
            const barH = isBrightTheme
              ? Math.round(6 + safeLoudness * barWeights[barIdx] * shimmer)
              : Math.round(interpolate(wave, [0, 1], [10, 36]));
            const barCol = isBrightTheme
              ? isRajatActive
                ? barIdx % 2 === 1
                  ? BRIGHT_COLORS.saffron
                  : BRIGHT_COLORS.amberBright
                : barIdx % 2 === 1
                  ? '#0284C7'
                  : '#06B6D4'
              : isRajatActive
                ? barIdx % 2 === 1
                  ? COLORS.emerald
                  : COLORS.amber
                : isHighAlertPop && barIdx % 2 === 1
                  ? COLORS.crimson
                  : COLORS.cyan;
            return (
              <span
                key={barIdx}
                style={{
                  width: 4,
                  height: barH,
                  borderRadius: 999,
                  backgroundColor: barCol,
                  boxShadow: isBrightTheme ? 'none' : `0 0 8px ${barCol}`,
                }}
              />
            );
          })}
        </div>

        {/* Active Speaker + Duo Case Stack */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div
            style={{
              fontFamily: FONTS.mono,
              fontSize: 16,
              fontWeight: 800,
              letterSpacing: 0.6,
              color: speakerAccent,
              lineHeight: 1.15,
              whiteSpace: 'nowrap',
            }}
          >
            {isBrightTheme
              ? isRajatActive
                ? `RAJAT · ${companyName}`
                : `JYOTI · ${companyName}`
              : isRajatActive
                ? 'RAJAT // CYBER LEAD'
                : 'JYOTI // THREAT HUNTER'}{' '}
            <span
              style={{
                color: isBrightTheme ? BRIGHT_COLORS.textSecondary : COLORS.textMuted,
                fontWeight: 700,
              }}
            >
              · EP {episodeCode}/{totalCode}
            </span>
          </div>
          <div
            style={{
              fontFamily: FONTS.display,
              fontSize: companyName.length > 14 ? 18 : 20,
              fontWeight: 900,
              letterSpacing: 0.25,
              color: isBrightTheme ? BRIGHT_COLORS.textPrimary : COLORS.textPrimary,
              lineHeight: 1.15,
              whiteSpace: 'nowrap',
            }}
          >
            {hasDualSpeakers
              ? `JYOTI x RAJAT · ${companyName.toUpperCase()} #${episodeCode}`
              : `${companyName.toUpperCase()} BREACH CASE #${episodeCode}`}
          </div>
        </div>
      </div>

      {/* Right: Anti-Spoiler Badge (0:00–0:14) -> Security Domain Pill (0:14+) */}
      {!showDomain ? (
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 17,
            fontWeight: 800,
            letterSpacing: 0.8,
            color: isBrightTheme ? BRIGHT_COLORS.crimson : COLORS.crimson,
            backgroundColor: isBrightTheme ? BRIGHT_COLORS.crimsonSoft : COLORS.crimsonMuted,
            border: `${isBrightTheme ? 2 : 1.5}px solid ${
              isBrightTheme ? BRIGHT_COLORS.crimson : COLORS.crimson
            }`,
            borderRadius: 999,
            padding: '8px 16px',
            whiteSpace: 'nowrap',
            flexShrink: 0,
            opacity: interpolate(pulseWave, [0, 1], [0.82, 1]),
            boxShadow: isBrightTheme ? 'none' : `0 0 18px ${COLORS.crimsonMuted}`,
          }}
        >
          {isBrightTheme ? `● LIVE MYSTERY · PART ${episode}` : '● LIVE CASE // 02:14 AM'}
        </div>
      ) : (
        <div
          style={{
            fontFamily: FONTS.display,
            fontSize: domainFontSize,
            fontWeight: 800,
            letterSpacing: 0.3,
            lineHeight: 1.15,
            textAlign: 'right',
            maxWidth: hasDualSpeakers ? 310 : 420,
            color: isBrightTheme ? BRIGHT_COLORS.cobalt : COLORS.cyan,
            backgroundColor: isBrightTheme ? BRIGHT_COLORS.cobaltSoft : COLORS.cyanMuted,
            border: `1.5px solid ${
              isBrightTheme ? BRIGHT_COLORS.cobaltBorder : 'rgba(0, 240, 255, 0.45)'
            }`,
            borderRadius: 14,
            padding: '7px 15px',
            textWrap: 'balance',
            opacity: interpolate(domainFlip, [0, 1], [0, 1]),
            transform: `translateY(${interpolate(domainFlip, [0, 1], [10, 0])}px)`,
          }}
        >
          {domain.toUpperCase().replace(/-/g, '\u2011')}
        </div>
      )}
    </div>
  );
};
