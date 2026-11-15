import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { PayoffProofCardProps } from '../types';

export const PayoffProofCard: React.FC<{ data: PayoffProofCardProps }> = ({
  data,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;

  const topCardIn = spring({
    frame,
    fps,
    config: { damping: 16, stiffness: 145 },
  });

  // Beat 2: Slam in Verified Breach Parallel card at frame >= 42 (+1.4s)
  const breachRevealFrame = 42;
  const bottomCardIn = spring({
    frame: Math.max(0, frame - breachRevealFrame),
    fps,
    config: { damping: 14, stiffness: 175, mass: 0.8 },
  });
  const showBottomCard = frame >= breachRevealFrame;
  const impactPulse = (Math.sin(frame * 0.28) + 1) / 2;
  const statGlow = interpolate(impactPulse, [0, 1], [12, 28]);

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
        gap: 22,
      }}
    >
      {/* Top Half: Save-Worthy Golden Rule Takeaway Card (Frame 0) */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '28px 34px',
          borderRadius: 24,
          backgroundColor: COLORS.bgPanelElevated,
          border: `2px solid ${COLORS.cyan}`,
          boxShadow: `0 20px 50px rgba(0, 0, 0, 0.5), 0 0 28px ${COLORS.cyanMuted}`,
          opacity: interpolate(topCardIn, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(topCardIn, [0, 1], [-24, 0])}px)`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span
            style={{
              fontFamily: FONTS.mono,
              fontSize: 17,
              fontWeight: 800,
              letterSpacing: 1.4,
              color: COLORS.cyan,
              backgroundColor: COLORS.cyanMuted,
              border: `1px solid ${COLORS.cyan}`,
              borderRadius: 8,
              padding: '6px 15px',
            }}
          >
            ★ CISO GOLDEN RULE // SAVE THIS
          </span>
        </div>

        <div
          style={{
            fontFamily: FONTS.display,
            fontSize: data.takeawayHeadline.length > 32 ? 36 : 42,
            fontWeight: 900,
            lineHeight: 1.12,
            color: COLORS.textPrimary,
          }}
        >
          {data.takeawayHeadline}
        </div>

        <div
          style={{
            backgroundColor: 'rgba(6, 10, 18, 0.8)',
            borderLeft: `6px solid ${COLORS.cyan}`,
            borderRadius: '8px 16px 16px 8px',
            padding: '18px 24px',
            fontFamily: FONTS.body,
            fontSize: 25,
            fontWeight: 600,
            lineHeight: 1.34,
            color: COLORS.textPrimary,
          }}
        >
          {data.coreRule}
        </div>
      </div>

      {/* Bottom Half: Verified Real-World Breach Case File (Slams in at Frame 42 / +1.4s) */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '28px 34px',
          borderRadius: 24,
          backgroundColor: COLORS.bgPanel,
          border: `2px solid ${COLORS.crimson}`,
          boxShadow: `0 20px 50px rgba(0, 0, 0, 0.55), 0 0 ${statGlow}px ${COLORS.crimsonMuted}`,
          opacity: showBottomCard ? interpolate(bottomCardIn, [0, 1], [0, 1]) : 0,
          transform: showBottomCard
            ? `translateY(${interpolate(bottomCardIn, [0, 1], [34, 0])}px) scale(${interpolate(bottomCardIn, [0, 1], [0.96, 1])})`
            : 'translateY(34px) scale(0.96)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 14 }}>
          <span
            style={{
              fontFamily: FONTS.mono,
              fontSize: 17,
              fontWeight: 800,
              letterSpacing: 1.2,
              color: COLORS.crimson,
              backgroundColor: COLORS.crimsonMuted,
              border: `1.5px solid ${COLORS.crimson}`,
              borderRadius: 8,
              padding: '6px 14px',
              whiteSpace: 'nowrap',
              flexShrink: 0,
              opacity: interpolate(impactPulse, [0, 1], [0.8, 1]),
            }}
          >
            ● VERIFIED BREACH PARALLEL
          </span>
          <span
            style={{
              fontFamily: FONTS.display,
              fontSize: 20,
              fontWeight: 800,
              lineHeight: 1.2,
              textAlign: 'right',
              color: COLORS.textSecondary,
            }}
          >
            {data.realBreachName}
          </span>
        </div>

        <div
          style={{
            display: 'inline-block',
            alignSelf: 'flex-start',
            backgroundColor: COLORS.crimsonMuted,
            border: `1.5px solid ${COLORS.crimson}`,
            borderRadius: 14,
            padding: '10px 20px',
            boxShadow: `0 0 ${statGlow}px ${COLORS.crimsonMuted}`,
            fontFamily: FONTS.display,
            fontSize: data.realBreachStat.length > 42 ? 35 : 42,
            fontWeight: 900,
            lineHeight: 1.12,
            color: COLORS.crimson,
          }}
        >
          {data.realBreachStat}
        </div>

        <div
          style={{
            backgroundColor: 'rgba(255, 46, 84, 0.08)',
            border: `1px solid rgba(255, 46, 84, 0.35)`,
            borderRadius: 16,
            padding: '16px 22px',
          }}
        >
          <div
            style={{
              fontFamily: FONTS.mono,
              fontSize: 16,
              fontWeight: 800,
              color: COLORS.amber,
              letterSpacing: 1.2,
              marginBottom: 6,
            }}
          >
            ROOT CAUSE ANALYSIS
          </div>
          <div
            style={{
              fontFamily: FONTS.body,
              fontSize: 23,
              fontWeight: 600,
              lineHeight: 1.32,
              color: COLORS.textPrimary,
            }}
          >
            {data.realBreachCause}
          </div>
        </div>
      </div>
    </div>
  );
};
