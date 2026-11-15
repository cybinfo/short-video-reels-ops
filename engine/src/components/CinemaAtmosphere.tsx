import React from 'react';
import {Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONTS, NOIR_GRID} from '../theme/tokens';

const BOKEH_PARTICLES = Array.from({length: 16}).map((_, idx) => ({
  id: idx,
  baseX: ((idx * 173 + 61) % 980) + 50,
  baseY: ((idx * 257 + 120) % 1760) + 80,
  size: 5 + (idx % 4) * 3.5,
  speedY: 0.55 + (idx % 5) * 0.22,
  swayAmp: 12 + (idx % 3) * 8,
  swayFreq: 0.032 + (idx % 4) * 0.009,
  isCrimson: idx % 4 === 0,
  baseAlpha: 0.14 + (idx % 3) * 0.08,
}));

export const CinemaAtmosphere: React.FC<{
  liveLoudness: number;
  loopHeroImage?: string;
  coldOpenTag?: string;
  seriesLabel?: string;
  hasHookSceneCard?: boolean;
}> = ({
  liveLoudness,
  loopHeroImage,
  coldOpenTag,
  seriesLabel = 'SERIES',
  hasHookSceneCard = true,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const safeLoudness = Number.isFinite(liveLoudness)
    ? Math.min(1, Math.max(0, liveLoudness))
    : 0.35;

  // Suppress floating cold-open banner whenever DetectiveCrimeHookScene renders its own hook card (max 2 UI cards at Frame 0)
  const coldOpenFrames = Math.round(1.85 * fps);
  const showColdOpen = Boolean(coldOpenTag) && !hasHookSceneCard && frame < coldOpenFrames;
  const coldOpenOpacity = showColdOpen
    ? interpolate(frame, [0, 5, coldOpenFrames - 8, coldOpenFrames], [0, 0.94, 0.94, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  // Final 16-frame seamless loop dissolve back to opening shot
  const loopTailStart = Math.max(0, durationInFrames - 16);
  const loopFadeOpacity =
    loopHeroImage && frame >= loopTailStart
      ? interpolate(frame, [loopTailStart, durationInFrames - 1], [0, 0.62], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 0;

  return (
    <div
      data-ambient="true"
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 7,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      {/* Subtle 35mm Film Grain Matrix (0ms GPU blur cost) */}
      <div
        data-ambient="true"
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.055,
          backgroundImage:
            'radial-gradient(rgba(255, 255, 255, 0.7) 1px, transparent 0), radial-gradient(rgba(250, 204, 21, 0.5) 1px, transparent 0)',
          backgroundSize: '26px 26px',
          backgroundPosition: `${(frame * 7) % 26}px ${(frame * 11) % 26}px, ${((frame * 13) + 13) % 26}px ${((frame * 5) + 9) % 26}px`,
        }}
      />

      {/* Floating Warm Gold & Crimson Dust Bokeh Particles */}
      {BOKEH_PARTICLES.map((p) => {
        const y = ((p.baseY - frame * p.speedY) % 1920 + 1920) % 1920;
        const x = p.baseX + Math.sin(frame * p.swayFreq + p.id) * p.swayAmp;
        const alpha = p.baseAlpha * (0.75 + safeLoudness * 0.45);
        const col = p.isCrimson ? 'rgba(255, 46, 84, 0.9)' : 'rgba(250, 204, 21, 0.9)';
        return (
          <span
            key={p.id}
            data-ambient="true"
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: p.size * 1.8,
              height: p.size * 1.8,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${col} 0%, transparent 72%)`,
              opacity: alpha,
            }}
          />
        );
      })}

      {/* Subtle 35mm Anamorphic Vignette & Audio-Reactive Edge Rim Glow */}
      <div
        data-ambient="true"
        style={{
          position: 'absolute',
          inset: 0,
          boxShadow: `inset 0 0 110px rgba(2, 5, 14, 0.72), inset 0 0 42px rgba(225, 29, 72, ${
            0.05 + safeLoudness * 0.08
          })`,
        }}
      />

      {/* Optional Cold-Open Title Stamp (only for scenes without a built-in hook card) */}
      {showColdOpen ? (
        <div
          data-ambient="true"
          style={{
            position: 'absolute',
            left: NOIR_GRID.left,
            top: 425,
            width: NOIR_GRID.width,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 6,
            opacity: coldOpenOpacity,
            transform: `scale(${interpolate(frame, [0, coldOpenFrames], [0.96, 1.03])})`,
          }}
        >
          <span
            data-ambient="true"
            style={{
              backgroundColor: 'rgba(225, 29, 72, 0.92)',
              border: '1.5px solid #FACC15',
              color: '#FFFFFF',
              borderRadius: 999,
              padding: '6px 18px',
              fontFamily: FONTS.mono,
              fontSize: 20,
              fontWeight: 900,
              letterSpacing: 1.8,
            }}
          >
            {seriesLabel}
          </span>
          <span
            data-ambient="true"
            style={{
              fontFamily: FONTS.display,
              fontSize: 44,
              fontWeight: 900,
              letterSpacing: 1.0,
              color: '#FEF08A',
              textShadow: '0 6px 26px rgba(0, 0, 0, 0.96), 0 2px 6px rgba(0, 0, 0, 0.98)',
              textAlign: 'center',
            }}
          >
            {coldOpenTag}
          </span>
        </div>
      ) : null}

      {/* Seamless Visual Loop Dissolve into Frame 0 */}
      {loopFadeOpacity > 0 && loopHeroImage ? (
        <Img
          data-ambient="true"
          src={staticFile(loopHeroImage)}
          alt=""
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: '50% 34%',
            opacity: loopFadeOpacity,
            filter: 'brightness(0.75) contrast(1.08)',
          }}
        />
      ) : null}
    </div>
  );
};
