import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { CommentSpotlightProps } from '../types';

export const CommentSpotlightCard: React.FC<{ data: CommentSpotlightProps }> = ({
  data,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;

  const cardIn = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 130, mass: 0.9 },
  });
  const ringSweep = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: { damping: 22, stiffness: 90 },
  });
  const stampSlam = spring({
    frame: Math.max(0, frame - 16),
    fps,
    config: { damping: 11, stiffness: 210, mass: 0.7 },
  });

  const palette =
    data.verdictTone === 'success'
      ? { fg: COLORS.emerald, bg: COLORS.emeraldMuted }
      : data.verdictTone === 'warning'
        ? { fg: COLORS.amber, bg: COLORS.amberMuted }
        : { fg: COLORS.crimson, bg: COLORS.crimsonMuted };

  const clampedPct = Math.max(0, Math.min(100, data.percentage));
  const animatedPct = Math.round(interpolate(ringSweep, [0, 1], [0, clampedPct]));
  const radius = 114;
  const circumference = 2 * Math.PI * radius;
  const strokeOffset =
    circumference - (circumference * (clampedPct * ringSweep)) / 100;

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
        padding: '30px 34px',
        backgroundColor: COLORS.bgPanel,
        border: `1.5px solid ${COLORS.borderSubtle}`,
        borderRadius: 24,
        opacity: interpolate(cardIn, [0, 1], [0, 1]),
        transform: `translateY(${interpolate(cardIn, [0, 1], [28, 0])}px)`,
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.55)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span
          style={{
            fontFamily: FONTS.mono,
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: 1.5,
            color: COLORS.cyan,
            backgroundColor: COLORS.cyanMuted,
            padding: '8px 16px',
            borderRadius: 8,
            border: '1px solid rgba(0, 240, 255, 0.35)',
          }}
        >
          COMMUNITY VOTE RECAP
        </span>
        <span style={{ fontFamily: FONTS.mono, fontSize: 20, fontWeight: 700, color: COLORS.textMuted }}>
          PREVIOUS POLL RESULT
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 38,
          backgroundColor: COLORS.bgPanelElevated,
          border: `1px solid ${COLORS.borderSubtle}`,
          borderRadius: 20,
          padding: '30px 34px',
        }}
      >
        <div style={{ position: 'relative', width: 268, height: 268, flexShrink: 0 }}>
          <svg width={268} height={268} style={{ transform: 'rotate(-90deg)' }}>
            <circle cx={134} cy={134} r={radius} fill="none" stroke="rgba(148, 163, 184, 0.16)" strokeWidth={22} />
            <circle
              cx={134}
              cy={134}
              r={radius}
              fill="none"
              stroke={palette.fg}
              strokeWidth={22}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeOffset}
            />
          </svg>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ fontFamily: FONTS.display, fontSize: 72, fontWeight: 900, color: COLORS.textPrimary, lineHeight: 1 }}>
              {animatedPct}%
            </span>
            <span style={{ fontFamily: FONTS.mono, fontSize: 20, fontWeight: 700, color: COLORS.textSecondary, marginTop: 8 }}>
              MAJORITY
            </span>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: FONTS.display, fontSize: 48, fontWeight: 900, lineHeight: 1.12, color: COLORS.textPrimary, marginBottom: 20 }}>
            {animatedPct}% PICKED <span style={{ color: COLORS.cyan }}>OPTION {data.optionPicked}</span>
          </div>
          <div style={{ width: '100%', height: 18, borderRadius: 999, backgroundColor: 'rgba(6, 10, 18, 0.75)', overflow: 'hidden', border: `1px solid ${COLORS.borderSubtle}` }}>
            <div style={{ width: `${clampedPct * ringSweep}%`, height: '100%', backgroundColor: palette.fg, boxShadow: `0 0 16px ${palette.fg}` }} />
          </div>
        </div>
      </div>

      <div
        style={{
          backgroundColor: 'rgba(6, 10, 18, 0.72)',
          border: `1px solid ${COLORS.borderSubtle}`,
          borderLeft: `6px solid ${COLORS.cyan}`,
          borderRadius: '10px 18px 18px 10px',
          padding: '26px 32px',
        }}
      >
        <div style={{ fontFamily: FONTS.mono, fontSize: 20, fontWeight: 700, color: COLORS.textMuted, letterSpacing: 1.2, marginBottom: 10 }}>
          TOP VOTER COMMENT
        </div>
        <div style={{ fontFamily: FONTS.body, fontSize: 32, fontWeight: 600, lineHeight: 1.38, color: COLORS.textPrimary, fontStyle: 'italic' }}>
          &ldquo;{data.voterQuote}&rdquo;
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', padding: '18px 28px 28px' }}>
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: data.verdictLabel.length > 24 ? 29 : 35,
            fontWeight: 900,
            letterSpacing: 2.0,
            lineHeight: 1.2,
            textAlign: 'center',
            maxWidth: '90%',
            boxSizing: 'border-box',
            color: palette.fg,
            backgroundColor: palette.bg,
            border: `3.5px solid ${palette.fg}`,
            borderRadius: 14,
            padding: '14px 28px',
            textTransform: 'uppercase',
            opacity: interpolate(stampSlam, [0, 0.25, 1], [0, 1, 1]),
            transform: `scale(${interpolate(stampSlam, [0, 1], [2.05, 1])}) rotate(-2.2deg)`,
            boxShadow: `0 0 28px ${palette.bg}`,
          }}
        >
          {data.verdictLabel}
        </div>
      </div>
    </div>
  );
};
