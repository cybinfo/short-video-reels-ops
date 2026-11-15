import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { AssetTierMatrixProps, AssetTierRow } from '../types';

const TONE_MAP: Record<
  AssetTierRow['colorTone'],
  { fg: string; bg: string }
> = {
  crimson: { fg: COLORS.crimson, bg: COLORS.crimsonMuted },
  amber: { fg: COLORS.amber, bg: COLORS.amberMuted },
  cyan: { fg: COLORS.cyan, bg: COLORS.cyanMuted },
  emerald: { fg: COLORS.emerald, bg: COLORS.emeraldMuted },
};

export const AssetTierMatrix: React.FC<{ data: AssetTierMatrixProps }> = ({
  data,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;
  const sec = frame / fps;
  const glowPulse = (Math.sin(frame * 0.24) + 1) / 2;
  const activeQuery = data.activeTier?.trim().toLowerCase();

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
        padding: '26px 32px',
        backgroundColor: COLORS.bgPanel,
        border: `1.5px solid ${COLORS.borderSubtle}`,
        borderRadius: 24,
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.55)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 18,
        }}
      >
        <div>
          <div
            style={{
              fontFamily: FONTS.mono,
              fontSize: 16,
              fontWeight: 700,
              color: COLORS.cyan,
              letterSpacing: 1.5,
              marginBottom: 4,
            }}
          >
            ASSET CLASSIFICATION FRAMEWORK
          </div>
          <div
            style={{
              fontFamily: FONTS.display,
              fontSize: 35,
              fontWeight: 900,
              lineHeight: 1.15,
              color: COLORS.textPrimary,
            }}
          >
            {data.title}
          </div>
        </div>
      </div>

      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: 14,
          minHeight: 0,
        }}
      >
        {data.tiers.map((row, idx) => {
          const slideIn = spring({
            frame: Math.max(0, frame - idx * 6),
            fps,
            config: { damping: 16, stiffness: 150 },
          });

          const palette = TONE_MAP[row.colorTone];
          const matchesConfiguredActive = Boolean(
            activeQuery &&
              (row.name.toLowerCase() === activeQuery ||
                row.tag.toLowerCase() === activeQuery ||
                `tier ${row.rank}` === activeQuery)
          );
          const isPrimaryTarget = activeQuery ? matchesConfiguredActive : row.rank === 3;

          // Dynamic 2.5s Beat Spotlight: 0..2.5s -> T1, 2.5..6.5s -> activeTier (T3), 6.5s+ -> T4 alongside activeTier
          const isBeatOne = sec < 2.5 && row.rank === 1;
          const isBeatTwo = sec >= 2.5 && sec < 6.5 && isPrimaryTarget;
          const isBeatThree = sec >= 6.5 && (isPrimaryTarget || row.rank === 4);
          const isSpotlight = isBeatOne || isBeatTwo || isBeatThree;

          const glowRadius = interpolate(glowPulse, [0, 1], [18, 36]);

          return (
            <div
              key={`${row.rank}-${row.name}`}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                padding: '18px 26px',
                borderRadius: 18,
                backgroundColor: isSpotlight
                  ? 'rgba(19, 31, 56, 0.98)'
                  : COLORS.bgPanelElevated,
                border: isSpotlight
                  ? `3px solid ${palette.fg}`
                  : `1px solid ${COLORS.borderSubtle}`,
                borderLeft: `8px solid ${palette.fg}`,
                boxShadow: isSpotlight
                  ? `0 0 ${glowRadius}px ${palette.bg}`
                  : '0 8px 20px rgba(0, 0, 0, 0.3)',
                opacity: interpolate(slideIn, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(slideIn, [0, 1], [42, 0])}px)`,
              }}
            >
              {/* Row 1: [T#] + Name (28px) on left, single non-wrapping [TAG] pill (17px) on right */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 14,
                  marginBottom: 10,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
                  <span
                    style={{
                      fontFamily: FONTS.mono,
                      fontSize: 19,
                      fontWeight: 900,
                      color: palette.fg,
                      backgroundColor: palette.bg,
                      padding: '5px 12px',
                      borderRadius: 8,
                      whiteSpace: 'nowrap',
                      flexShrink: 0,
                    }}
                  >
                    T{row.rank}
                  </span>
                  <span
                    style={{
                      fontFamily: FONTS.display,
                      fontSize: 28,
                      fontWeight: 800,
                      lineHeight: 1.15,
                      color: COLORS.textPrimary,
                    }}
                  >
                    {row.name}
                  </span>
                </div>

                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 17,
                    fontWeight: 800,
                    color: palette.fg,
                    backgroundColor: palette.bg,
                    border: `1.5px solid ${palette.fg}`,
                    padding: '5px 14px',
                    borderRadius: 999,
                    letterSpacing: 0.8,
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  {row.tag}
                </span>
              </div>

              {/* Row 2: Examples (20px) on left, BLAST: blastRadius (17px mono nowrap) on right */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 18,
                }}
              >
                <div
                  style={{
                    fontFamily: FONTS.body,
                    fontSize: 20,
                    fontWeight: 500,
                    color: COLORS.textSecondary,
                    lineHeight: 1.28,
                    flex: 1,
                    minWidth: 0,
                  }}
                >
                  {row.examples}
                </div>

                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 17,
                    fontWeight: 700,
                    color: isSpotlight ? palette.fg : COLORS.textSecondary,
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  BLAST: {row.blastRadius}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
