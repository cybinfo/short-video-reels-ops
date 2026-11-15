import React from 'react';
import { COLORS, FONTS, SAFE_ZONE, VIDEO_SPECS } from '../theme/tokens';

export const SafeZoneOverlay: React.FC<{ visible?: boolean }> = ({
  visible = false,
}) => {
  if (!visible) {
    return null;
  }

  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;
  const captionHeight = SAFE_ZONE.captionBottom - SAFE_ZONE.captionTop;
  const captionLeft = SAFE_ZONE.captionLeft ?? SAFE_ZONE.left;
  const captionWidth = SAFE_ZONE.captionWidth ?? SAFE_ZONE.usableWidth;

  const badgeStyle: React.CSSProperties = {
    fontFamily: FONTS.mono,
    fontSize: 17,
    fontWeight: 700,
    letterSpacing: 1.1,
    padding: '6px 12px',
    borderRadius: 6,
    display: 'inline-block',
  };

  return (
    <div
      data-ambient="true"
      style={{
        position: 'absolute',
        inset: 0,
        width: VIDEO_SPECS.width,
        height: VIDEO_SPECS.height,
        pointerEvents: 'none',
        zIndex: 999,
      }}
    >
      {/* Top OS / Reels Chrome (0..185) */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: VIDEO_SPECS.width,
          height: 185,
          backgroundColor: 'rgba(255, 46, 84, 0.14)',
          borderBottom: `2px dashed ${COLORS.crimson}`,
          boxSizing: 'border-box',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'center',
          paddingTop: 28,
        }}
      >
        <span
          style={{
            ...badgeStyle,
            backgroundColor: 'rgba(6, 10, 18, 0.88)',
            color: COLORS.crimson,
            border: `1px solid ${COLORS.crimson}`,
          }}
        >
          REELS TOP CHROME UNSAFE ZONE (0..185)
        </span>
      </div>

      {/* Instagram 4:5 Profile Grid Guide (285..1635) */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 285,
          width: VIDEO_SPECS.width,
          height: 1635 - 285,
          borderTop: `2px dotted ${COLORS.amber}`,
          borderBottom: `2px dotted ${COLORS.amber}`,
          boxSizing: 'border-box',
        }}
      />

      {/* Lower-Right Reels Action Rail (948..1080, 920..1490) */}
      <div
        style={{
          position: 'absolute',
          left: 948,
          top: 920,
          width: VIDEO_SPECS.width - 948,
          height: 1490 - 920,
          backgroundColor: 'rgba(255, 46, 84, 0.14)',
          borderLeft: `2px dashed ${COLORS.crimson}`,
          boxSizing: 'border-box',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span
          style={{
            ...badgeStyle,
            backgroundColor: 'rgba(6, 10, 18, 0.88)',
            color: COLORS.crimson,
            border: `1px solid ${COLORS.crimson}`,
            transform: 'rotate(-90deg)',
            whiteSpace: 'nowrap',
          }}
        >
          REELS ICON RAIL (948..1080)
        </span>
      </div>

      {/* Bottom Caption / Scrubber Drawer (1490..1920) */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 1490,
          width: VIDEO_SPECS.width,
          height: VIDEO_SPECS.height - 1490,
          backgroundColor: 'rgba(255, 46, 84, 0.14)',
          borderTop: `2px dashed ${COLORS.crimson}`,
          boxSizing: 'border-box',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'center',
          paddingTop: 24,
        }}
      >
        <span
          style={{
            ...badgeStyle,
            backgroundColor: 'rgba(6, 10, 18, 0.88)',
            color: COLORS.crimson,
            border: `1px solid ${COLORS.crimson}`,
          }}
        >
          BOTTOM CAPTION / SCRUBBER DRAWER (1490..1920)
        </span>
      </div>

      {/* Safe HUD Comms Box (70..1010, 196..282) */}
      <div
        style={{
          position: 'absolute',
          left: SAFE_ZONE.left,
          top: SAFE_ZONE.hudTop,
          width: SAFE_ZONE.usableWidth,
          height: SAFE_ZONE.hudHeight,
          border: `2px dashed ${COLORS.amber}`,
          backgroundColor: 'rgba(255, 176, 32, 0.04)',
          boxSizing: 'border-box',
        }}
      />

      {/* Safe Stage Box (70..1010, 296..1276 — centered x = 540, inside 4:5 grid) */}
      <div
        style={{
          position: 'absolute',
          left: SAFE_ZONE.left,
          top: SAFE_ZONE.stageTop,
          width: SAFE_ZONE.usableWidth,
          height: stageHeight,
          border: `2px dashed ${COLORS.cyan}`,
          backgroundColor: 'rgba(0, 240, 255, 0.03)',
          boxSizing: 'border-box',
          padding: 12,
        }}
      >
        <span
          style={{
            ...badgeStyle,
            backgroundColor: 'rgba(6, 10, 18, 0.88)',
            color: COLORS.cyan,
            border: `1px solid ${COLORS.cyan}`,
          }}
        >
          STAGE BOX ({SAFE_ZONE.left}..{SAFE_ZONE.right}, {SAFE_ZONE.stageTop}..
          {SAFE_ZONE.stageBottom} · CENTER 540)
        </span>
      </div>

      {/* Safe WordCaptions Box (140..940, 1296..1468 — centered x = 540) */}
      <div
        style={{
          position: 'absolute',
          left: captionLeft,
          top: SAFE_ZONE.captionTop,
          width: captionWidth,
          height: captionHeight,
          border: `2px dashed ${COLORS.emerald}`,
          backgroundColor: 'rgba(16, 185, 129, 0.04)',
          boxSizing: 'border-box',
          padding: 10,
        }}
      >
        <span
          style={{
            ...badgeStyle,
            backgroundColor: 'rgba(6, 10, 18, 0.88)',
            color: COLORS.emerald,
            border: `1px solid ${COLORS.emerald}`,
          }}
        >
          REELS CAPTIONS ({captionLeft}..{captionLeft + captionWidth},{' '}
          {SAFE_ZONE.captionTop}..{SAFE_ZONE.captionBottom})
        </span>
      </div>
    </div>
  );
};
