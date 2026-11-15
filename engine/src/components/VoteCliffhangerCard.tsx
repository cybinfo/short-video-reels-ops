import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { VoteCliffhangerProps, VoteOptionItem } from '../types';

const OPTION_ACCENT: Record<VoteOptionItem['key'], { fg: string; bg: string }> = {
  A: { fg: COLORS.cyan, bg: COLORS.cyanMuted },
  B: { fg: COLORS.amber, bg: COLORS.amberMuted },
  C: { fg: COLORS.crimson, bg: COLORS.crimsonMuted },
};

export const VoteCliffhangerCard: React.FC<{ data: VoteCliffhangerProps }> = ({
  data,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;
  const sec = frame / fps;

  const pulse = (Math.sin(frame * 0.3) + 1) / 2;
  const badgeScale = interpolate(pulse, [0, 1], [0.98, 1.03]);
  const headerIn = spring({ frame, fps, config: { damping: 16, stiffness: 145 } });
  const ctaIn = spring({
    frame: Math.max(0, frame - 18),
    fps,
    config: { damping: 15, stiffness: 155 },
  });

  const isFinalBridgeWindow = frame >= Math.max(0, durationInFrames - Math.round(fps * 1.5));
  const promptFontSize =
    data.crisisPrompt.length > 95 ? 31 : data.crisisPrompt.length > 75 ? 35 : 38;

  return (
    <div
      data-role="stage-card"
      style={{
        position: 'absolute',
        left: SAFE_ZONE.left,
        top: SAFE_ZONE.stageTop,
        width: SAFE_ZONE.usableWidth,
        height: stageHeight,
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '26px 34px',
        backgroundColor: COLORS.bgPanel,
        border: `2px solid ${COLORS.crimson}`,
        borderRadius: 24,
        boxShadow: `0 24px 64px rgba(0, 0, 0, 0.6), 0 0 36px ${COLORS.crimsonMuted}`,
      }}
    >
      {/* Top Countdown + Crisis Prompt (right padding keeps text <= x=935) */}
      <div
        style={{
          paddingRight: 42,
          opacity: interpolate(headerIn, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(headerIn, [0, 1], [-18, 0])}px)`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <span
            style={{
              fontFamily: FONTS.mono,
              fontSize: 17,
              fontWeight: 900,
              letterSpacing: 1.4,
              color: COLORS.crimson,
              backgroundColor: COLORS.crimsonMuted,
              border: `1.5px solid ${COLORS.crimson}`,
              borderRadius: 999,
              padding: '7px 16px',
              transform: `scale(${badgeScale})`,
              display: 'inline-block',
            }}
          >
            ⏱ {data.countdownLabel}
          </span>
          <span style={{ fontFamily: FONTS.mono, fontSize: 17, fontWeight: 800, color: COLORS.cyan, letterSpacing: 1.1 }}>
            YOUR CALL, CISO
          </span>
        </div>

        <div
          style={{
            fontFamily: FONTS.display,
            fontSize: promptFontSize,
            fontWeight: 900,
            lineHeight: 1.18,
            color: COLORS.textPrimary,
          }}
        >
          {data.crisisPrompt}
        </div>
      </div>

      {/* 3 Stacked Option Cards with Sequential A -> B -> C Spoken Spotlight */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, margin: '12px 0' }}>
        {data.options.map((opt, idx) => {
          const cardIn = spring({
            frame: Math.max(0, frame - (6 + idx * 6)),
            fps,
            config: { damping: 15, stiffness: 155 },
          });
          const accent = OPTION_ACCENT[opt.key];

          const isSingleSpotlight =
            (opt.key === 'A' && sec >= 2.0 && sec < 3.4) ||
            (opt.key === 'B' && sec >= 3.4 && sec < 4.8) ||
            (opt.key === 'C' && sec >= 4.8 && sec < 6.2);
          const isAllGlow = sec >= 6.2;
          const isHighlighted = isSingleSpotlight || isAllGlow;
          const glowPx = interpolate(pulse, [0, 1], [16, 32]);

          return (
            <div
              key={opt.key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 20,
                padding: '18px 44px 18px 22px',
                borderRadius: 18,
                backgroundColor: isHighlighted
                  ? 'rgba(19, 31, 56, 0.98)'
                  : COLORS.bgPanelElevated,
                border: isHighlighted
                  ? `2.5px solid ${accent.fg}`
                  : `1.5px solid rgba(148, 163, 184, 0.32)`,
                opacity: interpolate(cardIn, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(cardIn, [0, 1], [38, 0])}px)`,
                boxShadow: isHighlighted
                  ? `0 0 ${glowPx}px ${accent.bg}, 0 12px 26px rgba(0, 0, 0, 0.45)`
                  : '0 8px 20px rgba(0, 0, 0, 0.32)',
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 14,
                  backgroundColor: accent.bg,
                  border: `2px solid ${accent.fg}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: FONTS.mono,
                  fontSize: 34,
                  fontWeight: 900,
                  color: accent.fg,
                  flexShrink: 0,
                  transform: isSingleSpotlight ? 'scale(1.07)' : 'scale(1)',
                  boxShadow: isHighlighted ? `0 0 18px ${accent.bg}` : 'none',
                }}
              >
                {opt.key}
              </div>

              <div style={{ flex: 1, minWidth: 0, paddingRight: 28 }}>
                <div
                  style={{
                    fontFamily: FONTS.display,
                    fontSize: 26,
                    fontWeight: 800,
                    lineHeight: 1.15,
                    color: isHighlighted ? COLORS.textPrimary : COLORS.textSecondary,
                    marginBottom: 5,
                  }}
                >
                  {opt.label}
                </div>
                <div
                  style={{
                    fontFamily: FONTS.body,
                    fontSize: 20,
                    fontWeight: 500,
                    lineHeight: 1.28,
                    color: COLORS.textSecondary,
                  }}
                >
                  {opt.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Glowing CTA Footer + Final 1.5s Cyan Loop Bridge Pulse */}
      <div
        style={{
          padding: '16px 46px',
          borderRadius: 16,
          backgroundColor: COLORS.cyanMuted,
          border: `2px solid ${COLORS.cyan}`,
          textAlign: 'center',
          opacity: interpolate(ctaIn, [0, 1], [0, 1]),
          boxShadow: isFinalBridgeWindow
            ? `0 0 36px ${COLORS.cyan}`
            : `0 0 24px ${COLORS.cyanMuted}`,
        }}
      >
        <div
          style={{
            fontFamily: FONTS.display,
            fontSize: data.ctaLine.length > 62 ? 24 : 26,
            fontWeight: 900,
            lineHeight: 1.2,
            color: COLORS.cyan,
            letterSpacing: 0.4,
          }}
        >
          {data.ctaLine}
        </div>
        {data.loopBridgeText ? (
          <div
            style={{
              fontFamily: FONTS.mono,
              fontSize: 17,
              fontWeight: 800,
              color: isFinalBridgeWindow ? COLORS.cyan : COLORS.textSecondary,
              marginTop: 6,
              opacity: isFinalBridgeWindow ? interpolate(pulse, [0, 1], [0.75, 1]) : 0.92,
              textShadow: isFinalBridgeWindow ? `0 0 14px ${COLORS.cyan}` : 'none',
            }}
          >
            {data.loopBridgeText}
          </div>
        ) : null}
      </div>
    </div>
  );
};
