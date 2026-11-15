import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { BreachTerminalProps, TerminalLogLine } from '../types';

const levelStyle = (level: TerminalLogLine['level']) => {
  if (level === 'alert') {
    return { fg: COLORS.crimson, bg: COLORS.crimsonMuted, tag: 'ALERT' };
  }
  if (level === 'warn') {
    return { fg: COLORS.amber, bg: COLORS.amberMuted, tag: 'WARN ' };
  }
  return { fg: COLORS.cyan, bg: 'rgba(0, 240, 255, 0.06)', tag: 'INFO ' };
};

const formatAnimatedMetric = (raw: string, progress: number): { hero: string | null; rest: string } => {
  const leadMatch = raw.match(
    /^(Rs\.?\s*)?(\d+(?:,\d+)*(?:\.\d+)?)(\s*(?:LAKH|CRORE|CR)|[KMB%S])?\s+(.+)$/i
  );
  if (leadMatch) {
    const [, prefix = '', numStr, suffix = '', rest] = leadMatch;
    const cleanNum = parseFloat(numStr.replace(/,/g, ''));
    const decimals = numStr.includes('.') ? numStr.split('.')[1].length : 0;
    const current = cleanNum * progress;
    const formatted =
      decimals > 0
        ? current.toFixed(decimals)
        : Math.round(current).toLocaleString('en-IN');
    return { hero: `${prefix}${formatted}${suffix}`.trim(), rest };
  }
  const zeroMatch = raw.match(/^ZERO\s+(.+)$/i);
  if (zeroMatch) {
    return { hero: 'ZERO', rest: zeroMatch[1] };
  }
  const trailMatch = raw.match(/^(.+?)\s+(\d+(?:\.\d+)?S)$/i);
  if (trailMatch) {
    const [, rest, numSuffix] = trailMatch;
    const numVal = parseFloat(numSuffix);
    const decimals = numSuffix.includes('.') ? 1 : 0;
    const cur = (numVal * progress).toFixed(decimals);
    return { hero: `${cur}S`, rest };
  }
  return { hero: null, rest: raw };
};

export const BreachAlertTerminal: React.FC<{ data: BreachTerminalProps }> = ({
  data,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;

  const shellIn = spring({
    frame,
    fps,
    config: { damping: 17, stiffness: 145 },
  });

  const counterSweep = spring({
    frame: Math.max(0, frame - 3),
    fps,
    config: { damping: 20, stiffness: 95 },
  });

  const flashAlpha = interpolate((Math.sin(frame * 0.34) + 1) / 2, [0, 1], [0.55, 1]);
  const sevPalette =
    data.severity === 'WARNING'
      ? { fg: COLORS.amber, bg: COLORS.amberMuted }
      : { fg: COLORS.crimson, bg: COLORS.crimsonMuted };

  const cursorVisible = Math.floor(frame / 10) % 2 === 0;
  const parsedMetric = formatAnimatedMetric(data.metricBadge, Math.min(1, counterSweep));
  const barFillPct = Math.min(100, Math.round(interpolate(counterSweep, [0, 1], [14, 96])));

  const statusBeat = Math.floor(frame / 40);
  const statusLabel =
    statusBeat === 0
      ? 'SCANNING TELEMETRY STREAM...'
      : statusBeat === 1
        ? 'CORRELATING PACKET SIGNATURES...'
        : 'LIVE PACKET CAPTURE // FORENSIC LOCK';

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
        backgroundColor: '#070D19',
        border: `2px solid ${sevPalette.fg}`,
        borderRadius: 22,
        overflow: 'hidden',
        opacity: interpolate(shellIn, [0, 1], [0, 1]),
        transform: `scale(${interpolate(shellIn, [0, 1], [0.97, 1])})`,
        boxShadow: `0 24px 64px rgba(0, 0, 0, 0.65), 0 0 36px ${sevPalette.bg}`,
      }}
    >
      {/* SOC Window Titlebar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 26px',
          backgroundColor: COLORS.bgPanelElevated,
          borderBottom: `1px solid ${COLORS.borderSubtle}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ width: 13, height: 13, borderRadius: '50%', backgroundColor: COLORS.crimson }} />
          <span style={{ width: 13, height: 13, borderRadius: '50%', backgroundColor: COLORS.amber }} />
          <span style={{ width: 13, height: 13, borderRadius: '50%', backgroundColor: COLORS.emerald }} />
          <span
            style={{
              fontFamily: FONTS.mono,
              fontSize: 19,
              fontWeight: 700,
              color: COLORS.textSecondary,
              marginLeft: 8,
            }}
          >
            {data.windowTitle}
          </span>
        </div>

        <div
          style={{
            fontFamily: FONTS.mono,
            fontSize: 17,
            fontWeight: 800,
            letterSpacing: 1.2,
            color: sevPalette.fg,
            backgroundColor: sevPalette.bg,
            border: `1.5px solid ${sevPalette.fg}`,
            borderRadius: 999,
            padding: '5px 15px',
            opacity: flashAlpha,
            whiteSpace: 'nowrap',
          }}
        >
          ● {data.severity}
        </div>
      </div>

      {/* Hero Metric Counter Banner (56px Display + Animated Threat Bar) */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          padding: '20px 28px',
          backgroundColor: 'rgba(255, 46, 84, 0.1)',
          borderBottom: `1px solid ${COLORS.borderSubtle}`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontFamily: FONTS.mono, fontSize: 17, fontWeight: 700, color: COLORS.textSecondary, letterSpacing: 1 }}>
            INCIDENT CLOCK // {data.timestamp}
          </span>
          <span style={{ fontFamily: FONTS.mono, fontSize: 17, fontWeight: 800, color: sevPalette.fg }}>
            EXPOSURE INDEX: {barFillPct}%
          </span>
        </div>

        {parsedMetric.hero ? (
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 18, flexWrap: 'wrap' }}>
            <span
              style={{
                fontFamily: FONTS.display,
                fontSize: 56,
                fontWeight: 900,
                lineHeight: 1.0,
                color: sevPalette.fg,
                letterSpacing: -0.5,
                textShadow: `0 0 24px ${sevPalette.bg}`,
              }}
            >
              {parsedMetric.hero}
            </span>
            <span
              style={{
                fontFamily: FONTS.display,
                fontSize: 28,
                fontWeight: 800,
                lineHeight: 1.15,
                color: COLORS.textPrimary,
                letterSpacing: 0.4,
              }}
            >
              {parsedMetric.rest}
            </span>
          </div>
        ) : (
          <div
            style={{
              fontFamily: FONTS.display,
              fontSize: parsedMetric.rest.length > 30 ? 36 : 44,
              fontWeight: 900,
              lineHeight: 1.1,
              color: sevPalette.fg,
            }}
          >
            {parsedMetric.rest}
          </div>
        )}

        <div
          data-ambient="true"
          style={{
            width: '100%',
            height: 10,
            borderRadius: 999,
            backgroundColor: 'rgba(6, 10, 18, 0.82)',
            border: `1px solid ${COLORS.borderSubtle}`,
            overflow: 'hidden',
          }}
        >
          <div
            data-ambient="true"
            style={{
              width: `${barFillPct}%`,
              height: '100%',
              borderRadius: 999,
              background: `linear-gradient(90deg, ${COLORS.amber} 0%, ${sevPalette.fg} 100%)`,
              boxShadow: `0 0 14px ${sevPalette.fg}`,
            }}
          />
        </div>
      </div>

      {/* Staggered SOC Telemetry Log Stream (Every 1.35s = 40 frames) */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: 16,
          padding: '22px 28px',
          minHeight: 0,
        }}
      >
        {data.logLines.map((line, index) => {
          const triggerFrame = 4 + index * 40;
          const lineSpring = spring({
            frame: Math.max(0, frame - triggerFrame),
            fps,
            config: { damping: 15, stiffness: 165 },
          });
          const isVisible = frame >= triggerFrame;
          const tone = levelStyle(line.level);
          const isActiveCursor =
            isVisible &&
            (index === data.logLines.length - 1 || frame < 4 + (index + 1) * 40);

          return (
            <div
              key={`${line.time}-${index}`}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: '18px 22px',
                borderRadius: 16,
                backgroundColor: isVisible ? tone.bg : 'rgba(13, 21, 38, 0.45)',
                border: `1px solid ${isVisible ? 'rgba(148, 163, 184, 0.2)' : 'rgba(148, 163, 184, 0.08)'}`,
                borderLeft: `6px solid ${isVisible ? tone.fg : COLORS.borderSubtle}`,
                opacity: isVisible ? interpolate(lineSpring, [0, 1], [0.15, 1]) : 0.22,
                transform: `translateX(${isVisible ? interpolate(lineSpring, [0, 1], [-22, 0]) : 0}px)`,
              }}
            >
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 19,
                  fontWeight: 700,
                  color: COLORS.textMuted,
                  flexShrink: 0,
                }}
              >
                [{line.time}]
              </span>
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 18,
                  fontWeight: 800,
                  color: tone.fg,
                  backgroundColor: 'rgba(6, 10, 18, 0.65)',
                  padding: '4px 10px',
                  borderRadius: 6,
                  flexShrink: 0,
                }}
              >
                {tone.tag}
              </span>
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 23,
                  fontWeight: 600,
                  lineHeight: 1.35,
                  color: isVisible ? COLORS.textPrimary : COLORS.textMuted,
                  flex: 1,
                }}
              >
                {isVisible ? line.text : 'AWAITING PACKET DECRYPTION...'}
                {isActiveCursor && cursorVisible ? (
                  <span style={{ color: tone.fg, marginLeft: 8 }}>▋</span>
                ) : null}
              </span>
            </div>
          );
        })}
      </div>

      {/* Bottom Active Pulsing Status Strip */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 28px',
          backgroundColor: COLORS.bgPanelElevated,
          borderTop: `1px solid ${COLORS.borderSubtle}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span
            style={{
              width: 11,
              height: 11,
              borderRadius: '50%',
              backgroundColor: COLORS.cyan,
              opacity: flashAlpha,
              boxShadow: `0 0 10px ${COLORS.cyan}`,
            }}
          />
          <span
            style={{
              fontFamily: FONTS.mono,
              fontSize: 17,
              fontWeight: 800,
              letterSpacing: 1,
              color: COLORS.cyan,
            }}
          >
            {statusLabel}
          </span>
        </div>
        <span
          style={{
            fontFamily: FONTS.mono,
            fontSize: 16,
            fontWeight: 700,
            color: COLORS.textSecondary,
          }}
        >
          BPF FILTER // PORT 443 · S3 · SIEM
        </span>
      </div>
    </div>
  );
};
