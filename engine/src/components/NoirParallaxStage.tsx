import React, { useEffect, useState } from 'react';
import { Img, interpolate, staticFile, useCurrentFrame } from 'remotion';

export interface NoirParallaxStageProps {
  imagePath: string;
  shotProgress: number;
  camScale: number;
  camOrigin?: string;
  objectPosition?: string;
  handheldX?: number;
  handheldY?: number;
  handheldRot?: number;
  contrast?: number;
  brightness?: number;
  accentColor?: string;
  parallaxStrength?: number;
  lockedParallax?: boolean;
  parallaxMode?: 'standard' | 'macro' | 'locked';
}

interface BokehMote {
  cx: number;
  cy: number;
  size: number;
  opacity: number;
  driftX: number;
  driftY: number;
  speed: number;
  phase: number;
  warm: boolean;
}

const BOKEH_MOTES: readonly BokehMote[] = [
  { cx: 165, cy: 430, size: 16, opacity: 0.28, driftX: 18, driftY: -34, speed: 0.032, phase: 0.4, warm: true },
  { cx: 310, cy: 615, size: 22, opacity: 0.20, driftX: -14, driftY: -42, speed: 0.026, phase: 1.3, warm: false },
  { cx: 470, cy: 385, size: 12, opacity: 0.30, driftX: 12, driftY: -28, speed: 0.041, phase: 2.1, warm: true },
  { cx: 635, cy: 520, size: 18, opacity: 0.22, driftX: -16, driftY: -38, speed: 0.029, phase: 2.9, warm: false },
  { cx: 845, cy: 465, size: 14, opacity: 0.26, driftX: 15, driftY: -32, speed: 0.036, phase: 3.7, warm: true },
  { cx: 215, cy: 845, size: 24, opacity: 0.18, driftX: 20, driftY: -46, speed: 0.024, phase: 4.4, warm: false },
  { cx: 590, cy: 790, size: 18, opacity: 0.24, driftX: 16, driftY: -36, speed: 0.031, phase: 0.9, warm: false },
  { cx: 775, cy: 885, size: 12, opacity: 0.32, driftX: -13, driftY: -27, speed: 0.044, phase: 1.8, warm: true },
];

export const NoirParallaxStage: React.FC<NoirParallaxStageProps> = ({
  imagePath,
  shotProgress,
  camScale,
  camOrigin = '50% 50%',
  objectPosition = '50% 50%',
  handheldX = 0,
  handheldY = 0,
  handheldRot = 0,
  contrast = 1.06,
  brightness = 0.96,
  accentColor = 'rgba(250, 204, 21, 0.36)',
  parallaxStrength = 1.0,
  lockedParallax = false,
  parallaxMode,
}) => {
  const frame = useCurrentFrame();
  const [bgFailed, setBgFailed] = useState(false);
  const [fgFailed, setFgFailed] = useState(false);

  useEffect(() => {
    setBgFailed(false);
    setFgFailed(false);
  }, [imagePath]);

  const safeProgress = Number.isFinite(shotProgress)
    ? Math.min(1, Math.max(0, shotProgress))
    : 0;
  const safeScale = Number.isFinite(camScale) ? camScale : 1.06;
  const safeContrast = Number.isFinite(contrast)
    ? Math.min(1.25, Math.max(0.9, contrast))
    : 1.06;
  const safeBrightness = Number.isFinite(brightness)
    ? Math.min(1.15, Math.max(0.72, brightness))
    : 0.96;
  // 0ms GPU cost exposure modulation over #04070F base canvas (zero CSS filter: blur)
  const stageOpacity = Math.min(
    1,
    Math.max(0.76, safeBrightness * (0.98 + (safeContrast - 1) * 0.14))
  );

  const isCharPlate =
    imagePath.startsWith('characters/') &&
    !imagePath.startsWith('characters/fg/') &&
    !imagePath.startsWith('characters/bg/');
  const isMacro = parallaxMode === 'macro';
  const isLocked = Boolean(lockedParallax) || parallaxMode === 'locked';
  const bgPath =
    isCharPlate && !isMacro
      ? imagePath.replace(/^characters\//, 'characters/bg/').replace(/\.png$/i, '.jpg')
      : imagePath;
  const fgPath = isCharPlate && !isMacro
    ? imagePath.replace(/^characters\//, 'characters/fg/')
    : null;

  const effStrength = isLocked
    ? Math.min(0.12, parallaxStrength)
    : isMacro
      ? Math.min(0.35, parallaxStrength)
      : parallaxStrength;

  // Layer 1: Pre-baked Optical Rack-Focused Background Plate (0ms CPU blur cost, ±5.5px gentle drift)
  const bgX =
    handheldX +
    interpolate(safeProgress, [0, 1], [5.5, -5.5], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
      effStrength;
  const bgY =
    handheldY +
    interpolate(safeProgress, [0, 1], [-2.0, 2.0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
      effStrength;
  const bgScale = safeScale * 1.022;

  // Layer 2: Lightweight Radial-Gradient Mid-Plane Bokeh Motes (behind FG matte, 0ms filter cost)
  const midX =
    handheldX * 0.65 +
    interpolate(safeProgress, [0, 1], [2.0, -2.0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
      effStrength;
  const midY =
    handheldY * 0.65 +
    interpolate(safeProgress, [0, 1], [4, -9], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
      effStrength;

  // Layer 3: Razor-Sharp Neural Foreground RGBA Matte (halo-free 1.036x scale & ±5.5px drift)
  const fgX =
    handheldX +
    interpolate(safeProgress, [0, 1], [-5.5, 5.5], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
      effStrength;
  const fgY =
    handheldY +
    interpolate(safeProgress, [0, 1], [2.0, -2.0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) *
      effStrength;
  const fgScale = safeScale * (isLocked ? 1.004 : 1.036);

  return (
    <div
      data-ambient="true"
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
        opacity: stageOpacity,
      }}
    >
      <Img
        data-ambient="true"
        src={staticFile(bgFailed ? imagePath : bgPath)}
        alt=""
        onError={() => {
          if (!bgFailed && bgPath !== imagePath) {
            setBgFailed(true);
          }
        }}
        style={{
          position: 'absolute',
          inset: 0,
          width: '1080px',
          height: '1920px',
          objectFit: 'cover',
          objectPosition,
          transform: `translate3d(${bgX.toFixed(2)}px, ${bgY.toFixed(2)}px, 0) rotate(${handheldRot.toFixed(3)}deg) scale(${bgScale.toFixed(4)})`,
          transformOrigin: camOrigin,
        }}
      />

      <div
        data-ambient="true"
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          transform: `translate3d(${midX.toFixed(2)}px, ${midY.toFixed(2)}px, 0)`,
        }}
      >
        {BOKEH_MOTES.map((m, idx) => {
          const cycle = (frame * m.speed + m.phase) % (Math.PI * 2);
          const x = m.cx + Math.sin(cycle) * m.driftX;
          const y = m.cy + m.driftY * safeProgress + Math.cos(cycle * 0.8) * 9;
          const twinkle = 0.78 + 0.22 * Math.sin(frame * 0.09 + m.phase * 1.7);
          const coreColor = m.warm ? 'rgba(253, 230, 138, 0.95)' : accentColor;
          return (
            <div
              key={idx}
              data-ambient="true"
              style={{
                position: 'absolute',
                left: x - m.size / 2,
                top: y - m.size / 2,
                width: m.size,
                height: m.size,
                borderRadius: '50%',
                opacity: m.opacity * twinkle,
                background: `radial-gradient(circle, ${coreColor} 0%, transparent 72%)`,
              }}
            />
          );
        })}
      </div>

      {fgPath && !fgFailed ? (
        <Img
          data-ambient="true"
          src={staticFile(fgPath)}
          alt=""
          onError={() => setFgFailed(true)}
          style={{
            position: 'absolute',
            inset: 0,
            width: '1080px',
            height: '1920px',
            objectFit: 'cover',
            objectPosition,
            transform: `translate3d(${fgX.toFixed(2)}px, ${fgY.toFixed(2)}px, 0) rotate(${handheldRot.toFixed(3)}deg) scale(${fgScale.toFixed(4)})`,
            transformOrigin: camOrigin,
          }}
        />
      ) : null}
    </div>
  );
};
