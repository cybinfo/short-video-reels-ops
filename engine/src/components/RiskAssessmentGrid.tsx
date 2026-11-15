import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { RiskHeatmapProps, RiskItemRow } from '../types';

const ACTION_STYLE: Record<RiskItemRow['action'], { fg: string; bg: string }> = {
  MITIGATE: { fg: COLORS.cyan, bg: COLORS.cyanMuted },
  AVOID: { fg: COLORS.crimson, bg: COLORS.crimsonMuted },
  TRANSFER: { fg: COLORS.amber, bg: COLORS.amberMuted },
  ACCEPT: { fg: COLORS.emerald, bg: COLORS.emeraldMuted },
};

const cellColor = (score: number) => {
  if (score >= 16) return 'rgba(255, 46, 84, 0.36)';
  if (score >= 9) return 'rgba(255, 176, 32, 0.30)';
  if (score >= 4) return 'rgba(0, 240, 255, 0.18)';
  return 'rgba(16, 185, 129, 0.18)';
};

export const RiskAssessmentGrid: React.FC<{ data: RiskHeatmapProps }> = ({
  data,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;
  const levels: Array<1 | 2 | 3 | 4 | 5> = [5, 4, 3, 2, 1];
  const cols: Array<1 | 2 | 3 | 4 | 5> = [1, 2, 3, 4, 5];

  const gridIn = spring({ frame, fps, config: { damping: 17, stiffness: 140 } });
  const sec = frame / fps;
  const activeBeatIdx = sec < 3.0 ? 0 : sec < 6.0 ? 1 : sec < 9.0 ? 2 : 3;

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
        padding: '24px 30px',
        backgroundColor: COLORS.bgPanel,
        border: `1.5px solid ${COLORS.borderSubtle}`,
        borderRadius: 24,
        opacity: interpolate(gridIn, [0, 1], [0, 1]),
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.55)',
      }}
    >
      {/* Header + Available Budget */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 14, marginBottom: 14 }}>
        <div style={{ fontFamily: FONTS.display, fontSize: 31, fontWeight: 900, lineHeight: 1.15, color: COLORS.textPrimary }}>
          {data.title}
        </div>
        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 17,
            fontWeight: 800,
            color: COLORS.emerald,
            backgroundColor: COLORS.emeraldMuted,
            border: `1.5px solid ${COLORS.emerald}`,
            borderRadius: 10,
            padding: '7px 14px',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          BUDGET: {data.budgetAvailable}
        </div>
      </div>

      {/* 5x5 Likelihood x Impact Mini-Heatmap */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 24,
          padding: '16px 22px',
          borderRadius: 18,
          backgroundColor: COLORS.bgPanelElevated,
          border: `1px solid ${COLORS.borderSubtle}`,
          marginBottom: 16,
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {levels.map((lVal) => (
            <div key={lVal} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span style={{ fontFamily: FONTS.mono, fontSize: 16, fontWeight: 700, color: COLORS.textMuted, width: 28 }}>
                L{lVal}
              </span>
              {cols.map((iVal) => {
                const matched = data.items.filter(
                  (it) => it.likelihood === lVal && it.impact === iVal
                );
                const score = lVal * iVal;
                return (
                  <div
                    key={`${lVal}-${iVal}`}
                    style={{
                      width: 68,
                      height: 38,
                      borderRadius: 8,
                      backgroundColor: cellColor(score),
                      border: matched.length
                        ? `2px solid ${COLORS.textPrimary}`
                        : '1px solid rgba(148, 163, 184, 0.16)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontFamily: FONTS.mono,
                      fontSize: 16,
                      fontWeight: 800,
                      color: matched.length ? COLORS.textPrimary : COLORS.textMuted,
                    }}
                  >
                    {matched.length ? matched.map((m) => m.id).join(',') : score}
                  </div>
                );
              })}
            </div>
          ))}
          <div style={{ display: 'flex', gap: 6, paddingLeft: 34, marginTop: 2 }}>
            {cols.map((c) => (
              <span key={c} style={{ width: 68, textAlign: 'center', fontFamily: FONTS.mono, fontSize: 16, fontWeight: 700, color: COLORS.textMuted }}>
                I{c}
              </span>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 800, color: COLORS.cyan }}>
            5×5 RISK MATRIX (L × I)
          </div>
          <div style={{ fontFamily: FONTS.body, fontSize: 19, color: COLORS.textSecondary, lineHeight: 1.35 }}>
            Compare <strong style={{ color: COLORS.textPrimary }}>Annualized Loss (ALE)</strong> against remediation cost before allocating budget.
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 2 }}>
            <span style={{ fontFamily: FONTS.mono, fontSize: 16, fontWeight: 700, color: COLORS.crimson, backgroundColor: COLORS.crimsonMuted, padding: '4px 10px', borderRadius: 6 }}>16–25 CRIT</span>
            <span style={{ fontFamily: FONTS.mono, fontSize: 16, fontWeight: 700, color: COLORS.amber, backgroundColor: COLORS.amberMuted, padding: '4px 10px', borderRadius: 6 }}>9–15 HIGH</span>
            <span style={{ fontFamily: FONTS.mono, fontSize: 16, fontWeight: 700, color: COLORS.cyan, backgroundColor: COLORS.cyanMuted, padding: '4px 10px', borderRadius: 6 }}>1–8 LOW</span>
          </div>
        </div>
      </div>

      {/* Prioritized Asset Risk Cards with Dynamic 3s Spotlight Sweep */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12, justifyContent: 'space-between', minHeight: 0 }}>
        {data.items.slice(0, 4).map((item, idx) => {
          const rowIn = spring({
            frame: Math.max(0, frame - (8 + idx * 6)),
            fps,
            config: { damping: 16, stiffness: 150 },
          });
          const act = ACTION_STYLE[item.action];
          const score = item.likelihood * item.impact;
          const isSpotlight = idx === activeBeatIdx || (sec >= 9.5 && idx === 0);

          return (
            <div
              key={item.id}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 22px',
                borderRadius: 16,
                backgroundColor: isSpotlight ? 'rgba(19, 31, 56, 0.98)' : COLORS.bgPanelElevated,
                border: isSpotlight ? `2px solid ${act.fg}` : `1px solid ${COLORS.borderSubtle}`,
                borderLeft: `7px solid ${act.fg}`,
                boxShadow: isSpotlight ? `0 0 22px ${act.bg}` : 'none',
                opacity: interpolate(rowIn, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(rowIn, [0, 1], [20, 0])}px)`,
              }}
            >
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontFamily: FONTS.mono, fontSize: 17, fontWeight: 800, color: COLORS.cyan }}>
                    [{item.id}]
                  </span>
                  <span style={{ fontFamily: FONTS.display, fontSize: 24, fontWeight: 800, color: COLORS.textPrimary }}>
                    {item.asset}
                  </span>
                  <span style={{ fontFamily: FONTS.mono, fontSize: 17, color: COLORS.textSecondary }}>
                    (L{item.likelihood}×I{item.impact}={score})
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 22, marginTop: 6, fontFamily: FONTS.mono, fontSize: 19 }}>
                  <span style={{ color: COLORS.crimson, fontWeight: 700 }}>ALE: {item.annualLoss}</span>
                  <span style={{ color: COLORS.emerald, fontWeight: 700 }}>FIX: {item.fixCost}</span>
                </div>
              </div>

              <div
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 18,
                  fontWeight: 900,
                  color: act.fg,
                  backgroundColor: act.bg,
                  border: `1.5px solid ${act.fg}`,
                  borderRadius: 10,
                  padding: '9px 18px',
                  letterSpacing: 1,
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                }}
              >
                {item.action}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
