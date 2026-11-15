import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONTS, SAFE_ZONE } from '../theme/tokens';
import { NetworkAttackGraphProps, NetworkNode } from '../types';

const TIER_META: Record<
  NetworkNode['tier'],
  { label: string; fg: string; bg: string }
> = {
  untracked: { label: 'UNTRACKED', fg: COLORS.amber, bg: COLORS.amberMuted },
  public: { label: 'PUBLIC', fg: COLORS.cyan, bg: COLORS.cyanMuted },
  internal: { label: 'INTERNAL', fg: COLORS.emerald, bg: COLORS.emeraldMuted },
  restricted: { label: 'RESTRICTED', fg: COLORS.amber, bg: COLORS.amberMuted },
  crown_jewel: { label: 'CROWN JEWEL', fg: COLORS.crimson, bg: COLORS.crimsonMuted },
};

const CANVAS_WIDTH = 876;
const CANVAS_HEIGHT = 840;
const CARD_HALF_W = 185;
const CARD_HALF_H = 66;

const getNodePosition = (index: number, total: number) => {
  if (total <= 2) {
    const step = CANVAS_HEIGHT / (total + 1);
    return { x: CANVAS_WIDTH / 2, y: step * (index + 1) };
  }
  if (total === 3) {
    const coords3 = [
      { x: 438, y: 115 },
      { x: 205, y: 495 },
      { x: 671, y: 690 },
    ];
    return coords3[index] ?? { x: 438, y: 420 };
  }
  if (total === 4) {
    const coords4 = [
      { x: 215, y: 115 },
      { x: 661, y: 295 },
      { x: 215, y: 505 },
      { x: 661, y: 705 },
    ];
    return coords4[index] ?? { x: 438, y: 420 };
  }
  const coords5 = [
    { x: 215, y: 105 },
    { x: 661, y: 225 },
    { x: 215, y: 425 },
    { x: 661, y: 560 },
    { x: 438, y: 745 },
  ];
  return coords5[index] ?? { x: 438, y: 420 };
};

interface Point {
  x: number;
  y: number;
}

const evalCubic = (p0: Point, c1: Point, c2: Point, p3: Point, t: number): Point => {
  const u = 1 - t;
  const b0 = u * u * u;
  const b1 = 3 * u * u * t;
  const b2 = 3 * u * t * t;
  const b3 = t * t * t;
  return {
    x: b0 * p0.x + b1 * c1.x + b2 * c2.x + b3 * p3.x,
    y: b0 * p0.y + b1 * c1.y + b2 * c2.y + b3 * p3.y,
  };
};

export const NetworkAttackGraph: React.FC<{ data: NetworkAttackGraphProps }> = ({
  data,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stageHeight = SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop;
  const visibleNodes = data.nodes.slice(0, 5);

  const posMap = new Map<string, Point>();
  visibleNodes.forEach((node, idx) => {
    posMap.set(node.id, getNodePosition(idx, visibleNodes.length));
  });

  const dashShift = -(frame * 4.2);
  const packetT = (frame % 42) / 42;
  const beatTwoFrame = Math.round(fps * 2.0);
  const beatThreeFrame = Math.round(fps * 3.2);

  const computedEdges = data.edges
    .map((edge, idx) => {
      const from = posMap.get(edge.from);
      const to = posMap.get(edge.to);
      if (!from || !to) return null;

      const isAttack = Boolean(edge.attackPath);
      const useSidePort = !isAttack && to.y - from.y < 230 && from.x < to.x;

      const p0: Point = useSidePort
        ? { x: from.x + CARD_HALF_W, y: from.y }
        : { x: from.x, y: from.y + CARD_HALF_H };
      const p3: Point = isAttack
        ? { x: to.x, y: to.y - CARD_HALF_H - 4 }
        : { x: to.x, y: to.y - CARD_HALF_H - 24 };

      const midY = (p0.y + p3.y) / 2;
      let c1: Point = { x: p0.x, y: midY };
      let c2: Point = { x: p3.x, y: midY };
      let pillT = idx === 0 ? 0.45 : 0.52;

      if (useSidePort) {
        c1 = { x: p0.x + 140, y: p0.y };
        c2 = { x: p3.x, y: p3.y - 70 };
        pillT = 0.42;
      } else if (visibleNodes.length === 4) {
        pillT = 0.5;
      } else if (from.x === 438 && to.x > 550 && to.y - from.y > 400) {
        c1 = { x: 545, y: p0.y + 130 };
        c2 = { x: p3.x, y: p3.y - 170 };
        pillT = 0.52;
      }

      const pillPt = evalCubic(p0, c1, c2, p3, pillT);
      const pillWidth = Math.max(210, Math.round(edge.label.length * 11.4 + 42));
      const clampedPillX = Math.max(
        pillWidth / 2 + 8,
        Math.min(CANVAS_WIDTH - pillWidth / 2 - 8, pillPt.x)
      );
      const packetPt = evalCubic(p0, c1, c2, p3, packetT);

      const revealStart = idx === 0 ? 4 : idx === 1 ? beatTwoFrame : beatThreeFrame;
      const edgeSpring = spring({
        frame: Math.max(0, frame - revealStart),
        fps,
        config: { damping: 14, stiffness: 180 },
      });
      const edgeOpacity = frame < revealStart ? 0 : interpolate(edgeSpring, [0, 1], [0, 1]);

      return {
        edge,
        idx,
        isAttack,
        p0,
        c1,
        c2,
        p3,
        d: `M ${p0.x} ${p0.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${p3.x} ${p3.y}`,
        pillX: clampedPillX,
        pillY: pillPt.y,
        pillWidth,
        packetPt,
        edgeOpacity,
      };
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);

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
        padding: '24px 32px',
        backgroundColor: COLORS.bgPanel,
        border: `1.5px solid ${COLORS.borderSubtle}`,
        borderRadius: 24,
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.55)',
      }}
    >
      <div style={{ marginBottom: 12 }}>
        <div
          style={{
            fontFamily: FONTS.display,
            fontSize: 36,
            fontWeight: 900,
            lineHeight: 1.15,
            color: COLORS.textPrimary,
          }}
        >
          {data.title}
        </div>
        <div
          style={{
            fontFamily: FONTS.body,
            fontSize: 21,
            lineHeight: 1.25,
            color: COLORS.textSecondary,
            marginTop: 4,
          }}
        >
          {data.subtitle}
        </div>
      </div>

      <div style={{ position: 'relative', width: CANVAS_WIDTH, height: CANVAS_HEIGHT, flex: 1, minHeight: 0 }}>
        {/* Layer 1: Cubic Bezier Connectors + Arrowheads + Live Attack Packet */}
        <svg
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          style={{ position: 'absolute', inset: 0, overflow: 'visible', zIndex: 1 }}
        >
          <defs>
            <marker
              id="arrow-attack"
              markerUnits="userSpaceOnUse"
              markerWidth="16"
              markerHeight="16"
              refX="13"
              refY="8"
              orient="auto"
            >
              <path d="M 0 1 L 15 8 L 0 15 z" fill={COLORS.crimson} />
            </marker>
            <marker
              id="arrow-safe"
              markerUnits="userSpaceOnUse"
              markerWidth="14"
              markerHeight="14"
              refX="11"
              refY="7"
              orient="auto"
            >
              <path d="M 0 1 L 13 7 L 0 13 z" fill={COLORS.emerald} />
            </marker>
          </defs>

          {computedEdges.map((ce) => {
            const strokeColor = ce.isAttack ? COLORS.crimson : COLORS.emerald;
            return (
              <g key={`curve-${ce.idx}`} opacity={ce.edgeOpacity}>
                <path
                  d={ce.d}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={ce.isAttack ? 5 : 3.5}
                  strokeDasharray={ce.isAttack ? '14 9' : '8 8'}
                  strokeDashoffset={ce.isAttack ? dashShift : 0}
                  markerEnd={ce.isAttack ? 'url(#arrow-attack)' : undefined}
                />
                {ce.isAttack ? (
                  <circle
                    cx={ce.packetPt.x}
                    cy={ce.packetPt.y}
                    r={9}
                    fill={COLORS.crimson}
                    stroke={COLORS.textPrimary}
                    strokeWidth={2.5}
                  />
                ) : null}
              </g>
            );
          })}
        </svg>

        {/* Layer 2: Centered 370x132 Node Cards */}
        {visibleNodes.map((node, idx) => {
          const pos = posMap.get(node.id) ?? { x: 438, y: 420 };
          const meta = TIER_META[node.tier];
          const revealStart =
            idx === 0 ? 0 : idx === 1 ? 8 : idx === 2 ? beatTwoFrame : beatThreeFrame;
          const nodeIn = spring({
            frame: Math.max(0, frame - revealStart),
            fps,
            config: { damping: 14, stiffness: 175, mass: 0.75 },
          });
          const nodeOpacity = frame < revealStart ? 0 : interpolate(nodeIn, [0, 1], [0, 1]);
          const nodeScale =
            idx >= 2
              ? interpolate(nodeIn, [0, 1], [1.08, 1])
              : interpolate(nodeIn, [0, 1], [0.88, 1]);

          const isThreatActorOrigin = idx === 0 && node.tier === 'public';
          const borderCol = isThreatActorOrigin
            ? COLORS.amber
            : node.compromised
              ? COLORS.crimson
              : meta.fg;

          return (
            <div
              key={node.id}
              data-node-card="true"
              style={{
                position: 'absolute',
                left: pos.x - CARD_HALF_W,
                top: pos.y - CARD_HALF_H,
                width: CARD_HALF_W * 2,
                height: CARD_HALF_H * 2,
                boxSizing: 'border-box',
                padding: '14px 20px',
                borderRadius: 16,
                backgroundColor: COLORS.bgPanelElevated,
                border: `2.5px solid ${borderCol}`,
                boxShadow: node.compromised
                  ? `0 0 28px ${isThreatActorOrigin ? COLORS.amberMuted : COLORS.crimsonMuted}`
                  : '0 12px 28px rgba(0, 0, 0, 0.45)',
                opacity: nodeOpacity,
                transform: `scale(${nodeScale})`,
                zIndex: 2,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 16,
                    fontWeight: 800,
                    color: meta.fg,
                    backgroundColor: meta.bg,
                    padding: '3px 10px',
                    borderRadius: 6,
                    letterSpacing: 0.8,
                  }}
                >
                  {meta.label}
                </span>
                {node.compromised ? (
                  <span
                    style={{
                      fontFamily: FONTS.mono,
                      fontSize: 16,
                      fontWeight: 800,
                      color: isThreatActorOrigin ? COLORS.amber : COLORS.crimson,
                    }}
                  >
                    {isThreatActorOrigin ? '● THREAT ACTOR' : '● BREACHED'}
                  </span>
                ) : null}
              </div>
              <div>
                <div
                  style={{
                    fontFamily: FONTS.display,
                    fontSize: 24,
                    fontWeight: 800,
                    lineHeight: 1.15,
                    color: COLORS.textPrimary,
                  }}
                >
                  {node.label}
                </div>
                <div
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 16,
                    lineHeight: 1.2,
                    color: COLORS.textSecondary,
                    marginTop: 4,
                  }}
                >
                  {node.sublabel}
                </div>
              </div>
            </div>
          );
        })}

        {/* Layer 3: Non-Colliding 18px Edge Pills + WAF ✕ BLOCKED Shield Badges */}
        <svg
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          style={{ position: 'absolute', inset: 0, overflow: 'visible', zIndex: 3, pointerEvents: 'none' }}
        >
          {computedEdges.map((ce) => {
            const strokeColor = ce.isAttack ? COLORS.crimson : COLORS.emerald;
            return (
              <g key={`pill-${ce.idx}`} opacity={ce.edgeOpacity}>
                {!ce.isAttack ? (
                  <g>
                    <rect
                      x={ce.p3.x - 74}
                      y={ce.p3.y - 16}
                      width={148}
                      height={32}
                      rx={8}
                      fill="#071B17"
                      stroke={COLORS.emerald}
                      strokeWidth={2}
                    />
                    <text
                      x={ce.p3.x}
                      y={ce.p3.y + 6}
                      textAnchor="middle"
                      fill={COLORS.emerald}
                      style={{ fontFamily: FONTS.mono, fontSize: 16, fontWeight: 900, letterSpacing: 0.8 }}
                    >
                      ✕ BLOCKED
                    </text>
                  </g>
                ) : null}

                <rect
                  x={ce.pillX - ce.pillWidth / 2}
                  y={ce.pillY - 19}
                  width={ce.pillWidth}
                  height={38}
                  rx={10}
                  fill={COLORS.bgCanvas}
                  stroke={strokeColor}
                  strokeWidth={2}
                />
                <text
                  x={ce.pillX}
                  y={ce.pillY + 6}
                  textAnchor="middle"
                  fill={ce.isAttack ? COLORS.crimson : COLORS.emerald}
                  style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 800 }}
                >
                  {ce.edge.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};
