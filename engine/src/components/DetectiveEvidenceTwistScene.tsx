import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRIGHT_COLORS, FONTS, NOIR_GRID, SAFE_ZONE } from '../theme/tokens';
import { DetectiveEvidenceTwistProps, SpeakerId, WordTimestamp } from '../types';
import { NoirParallaxStage } from './NoirParallaxStage';

const StepOneClueIcon: React.FC<{ isCamera: boolean }> = ({ isCamera }) => {
  if (isCamera) {
    return (
      <svg width="42" height="42" viewBox="0 0 42 42">
        <rect x="5" y="12" width="24" height="16" rx="4" fill="none" stroke={BRIGHT_COLORS.amber} strokeWidth="3" />
        <path d="M29 17 L38 12 V28 L29 23 Z" fill="none" stroke={BRIGHT_COLORS.amber} strokeWidth="2.8" strokeLinejoin="round" />
        <circle cx="15" cy="20" r="3" fill={BRIGHT_COLORS.crimson} />
      </svg>
    );
  }
  // Custom Dialpad *21* Secret Forwarding SVG
  return (
    <svg width="44" height="44" viewBox="0 0 44 44">
      <rect x="6" y="4" width="24" height="36" rx="5" fill="#FFFBEB" stroke={BRIGHT_COLORS.amber} strokeWidth="2.6" />
      {[12, 18, 24].map((cx) =>
        [13, 20, 27].map((cy) => (
          <circle
            key={`${cx}-${cy}`}
            cx={cx}
            cy={cy}
            r="2.1"
            fill={cy === 27 && cx !== 18 ? BRIGHT_COLORS.crimson : BRIGHT_COLORS.amber}
          />
        ))
      )}
      <path d="M27 16 C33 16, 36 12, 39 8" fill="none" stroke={BRIGHT_COLORS.crimson} strokeWidth="3" strokeLinecap="round" />
      <path d="M34 7 H39.5 V12.5" fill="none" stroke={BRIGHT_COLORS.crimson} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

const MysteryInsiderSilhouette: React.FC<{ color: string }> = ({ color }) => (
  <svg width="34" height="34" viewBox="0 0 34 34" style={{ flexShrink: 0 }}>
    <circle cx="17" cy="11" r="6" fill={color} opacity="0.9" />
    <path d="M6 30 C7.5 21.5, 12 19, 17 19 C22 19, 26.5 21.5, 28 30 Z" fill={color} opacity="0.88" />
    <path d="M15.2 22.8 C15.4 21.4, 18.6 21.4, 18.6 23.2 C18.6 24.4, 17 24.7, 17 25.8" fill="none" stroke="#FFFFFF" strokeWidth="1.8" strokeLinecap="round" />
    <circle cx="17" cy="28" r="1.1" fill="#FFFFFF" />
  </svg>
);

export const DetectiveEvidenceTwistScene: React.FC<{
  data: DetectiveEvidenceTwistProps;
  liveLoudness?: number;
  activeSpeaker?: SpeakerId;
  sceneWords?: WordTimestamp[];
  isNoirCinema?: boolean;
}> = ({ data, liveLoudness = 0.35, isNoirCinema = false }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const safeDur = Math.max(1, durationInFrames - 1);
  const localProgress = Math.min(1, Math.max(0, frame / safeDur));
  const isBackdoor = data.variant === 'cctv_backdoor';
  const safeLoudness = Number.isFinite(liveLoudness) ? Math.min(1, Math.max(0, liveLoudness)) : 0.35;

  const card1Start = Math.round((isBackdoor ? 0.08 : 0.06) * durationInFrames);
  const arrowStart = Math.round((isBackdoor ? 0.42 : 0.3) * durationInFrames);
  const card2Start = Math.round((isBackdoor ? 0.5 : 0.44) * durationInFrames);
  const chipRatios = isBackdoor ? [0.56, 0.63, 0.7] : [0.52, 0.6, 0.68];

  const topIn = spring({ frame, fps, config: { damping: 16, stiffness: 185 } });
  const cardOneIn = spring({ frame: Math.max(0, frame - card1Start), fps, config: { damping: 15, stiffness: 195, mass: 0.65 } });
  const stampIn = spring({ frame: Math.max(0, frame - (card1Start + 6)), fps, config: { damping: 11, stiffness: 250, mass: 0.55 } });
  const arrowIn = spring({ frame: Math.max(0, frame - arrowStart), fps, config: { damping: 14, stiffness: 210, mass: 0.6 } });
  const cardTwoIn = spring({ frame: Math.max(0, frame - card2Start), fps, config: { damping: 13, stiffness: 220, mass: 0.65 } });

  const pulse = (Math.sin(frame * 0.17) + 1) / 2;
  const arrowBounceY = Math.sin(frame * 0.2) * 3;
  const docs = (data.exposedItems ?? ['CLUE 01', 'CLUE 02', 'CLUE 03']).slice(0, 3);
  const activeDocIdx = Math.floor(frame / 20) % Math.max(1, docs.length);
  const effectiveTone = data.tone ?? (isBackdoor ? 'amber' : 'crimson');
  const isRecoveryScene = effectiveTone === 'emerald';
  const hasTwoTileSets = Boolean(data.ussdTilesStepTwo && data.ussdTilesStepTwo.length > 0);
  const isCameraClue = isBackdoor && !data.ussdTilesStepOne && data.tone === 'crimson';
  const isDefenseCheck = isBackdoor && (isRecoveryScene || hasTwoTileSets);
  const isTowerRadar = !isBackdoor && Boolean(data.radarPinLabel);
  const isLockedStage = Boolean(data.lockedParallax) || isTowerRadar;

  if (isNoirCinema && data.heroImage) {
    const shotIdx = isBackdoor
      ? localProgress < 0.28 ? 0 : localProgress < 0.56 ? 1 : 2
      : localProgress < 0.5 ? 0 : 1;
    const activeHero =
      shotIdx === 0 && data.secondaryImage
        ? data.secondaryImage
        : data.heroImage;
    const camScale = isBackdoor
      ? shotIdx === 0
        ? interpolate(localProgress, [0, 0.28], [1.05, 1.13], { extrapolateRight: 'clamp' })
        : shotIdx === 1
          ? interpolate(localProgress, [0.28, 0.56], [1.05, 1.11], { extrapolateRight: 'clamp' })
          : interpolate(localProgress, [0.56, 1], [1.05, 1.14], { extrapolateRight: 'clamp' })
      : shotIdx === 0
        ? interpolate(localProgress, [0, 0.5], [1.05, 1.13], { extrapolateRight: 'clamp' })
        : interpolate(localProgress, [0.5, 1], [1.06, 1.15], { extrapolateRight: 'clamp' });
    const camOrigin = isBackdoor
      ? shotIdx >= 1
        ? '50% 44%'
        : '50% 36.5%'
      : isRecoveryScene
        ? '50% 36.5%'
        : '50% 34.63%';
    const handheldX = Math.sin(frame * 0.072 + 2.1) * 4;
    const handheldY = Math.cos(frame * 0.058 + 1.4) * 3;
    const handheldRot = Math.sin(frame * 0.046) * 0.22;
    const cutFlash =
      (isBackdoor && (Math.abs(localProgress - 0.28) < 0.025 || Math.abs(localProgress - 0.56) < 0.025)) ||
      (!isBackdoor && Math.abs(localProgress - 0.5) < 0.026)
        ? 0.32
        : 0;
    const isEraseStep = isBackdoor && (hasTwoTileSets || isDefenseCheck) && localProgress >= 0.5;
    const stepOneTiles =
      data.ussdTilesStepOne ??
      (isDefenseCheck ? ['*', '#', '2', '1', '#'] : ['*', '2', '1', '*']);
    const stepTwoTiles = data.ussdTilesStepTwo ?? ['#', '#', '0', '0', '2', '#'];
    const keypadTiles = isEraseStep ? stepTwoTiles : stepOneTiles;
    const dialStep = isEraseStep
      ? Math.floor(interpolate(localProgress, [0.5, 0.72], [0, keypadTiles.length], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }))
      : hasTwoTileSets || isDefenseCheck
        ? Math.floor(interpolate(localProgress, [0.1, 0.38], [0, keypadTiles.length], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }))
        : Math.floor(interpolate(localProgress, [0.53, 0.74], [0, keypadTiles.length], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }));

    const shotProgress = isBackdoor
      ? shotIdx === 0
        ? interpolate(localProgress, [0, 0.28], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        : shotIdx === 1
          ? interpolate(localProgress, [0.28, 0.56], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })
          : interpolate(localProgress, [0.56, 1], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })
      : shotIdx === 0
        ? interpolate(localProgress, [0, 0.5], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        : interpolate(localProgress, [0.5, 1], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

    return (
      <>
        <div data-ambient="true" style={{ position: 'absolute', inset: 0, overflow: 'hidden', backgroundColor: '#04070F', pointerEvents: 'none' }}>
          <NoirParallaxStage
            key={activeHero}
            imagePath={activeHero}
            shotProgress={shotProgress}
            camScale={camScale}
            camOrigin={camOrigin}
            objectPosition={isBackdoor && shotIdx >= 1 ? '50% 42%' : '50% 50%'}
            handheldX={handheldX}
            handheldY={handheldY}
            handheldRot={handheldRot}
            contrast={1.1}
            brightness={0.93 + safeLoudness * 0.09}
            lockedParallax={isLockedStage}
            parallaxMode={isLockedStage ? 'locked' : 'standard'}
            accentColor={
              isRecoveryScene
                ? 'rgba(52, 211, 153, 0.34)'
                : effectiveTone === 'amber'
                  ? 'rgba(250, 204, 21, 0.34)'
                  : 'rgba(255, 46, 84, 0.34)'
            }
            parallaxStrength={isLockedStage ? 0.1 : 1}
          />
          <div
            data-ambient="true"
            style={{
              position: 'absolute', inset: 0,
              background: 'linear-gradient(180deg, rgba(4, 7, 15, 0.85) 0%, rgba(4, 7, 15, 0.16) 24%, rgba(4, 7, 15, 0.08) 54%, rgba(4, 7, 15, 0.88) 76%, rgba(4, 7, 15, 0.97) 100%)',
            }}
          />
          {isRecoveryScene ? (
            <div
              data-ambient="true"
              style={{
                position: 'absolute',
                inset: 0,
                pointerEvents: 'none',
                background: `radial-gradient(circle at 50% 38%, rgba(250, 204, 21, ${0.14 + pulse * 0.05}) 0%, rgba(16, 185, 129, ${0.16 + safeLoudness * 0.08}) 36%, transparent 68%)`,
              }}
            />
          ) : null}
          {isTowerRadar && data.radarPinLabel ? (
            <div
              data-ambient="true"
              style={{
                position: 'absolute',
                inset: 0,
                pointerEvents: 'none',
                transform: `translate3d(${handheldX}px, ${handheldY}px, 0)`,
              }}
            >
              <div
                data-ambient="true"
                style={{
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  top: 444,
                  display: 'flex',
                  justifyContent: 'center',
                  pointerEvents: 'none',
                }}
              >
                <span
                  data-ambient="true"
                  style={{
                    backgroundColor: 'rgba(6, 10, 20, 0.88)',
                    border: '1.5px solid rgba(250, 204, 21, 0.68)',
                    color: '#FACC15',
                    borderRadius: 999,
                    padding: '6px 16px',
                    fontFamily: FONTS.mono,
                    fontSize: 20,
                    fontWeight: 900,
                    letterSpacing: 0.6,
                    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.65)',
                  }}
                >
                  {data.radarPinLabel}
                </span>
              </div>
              <div
                data-ambient="true"
                style={{
                  position: 'absolute',
                  left: 540 - 185,
                  top: 665 - 185,
                  width: 370,
                  height: 370,
                  borderRadius: '50%',
                  background:
                    'conic-gradient(from 0deg, rgba(255, 46, 84, 0.55) 0deg, rgba(250, 204, 21, 0.22) 32deg, transparent 74deg, transparent 360deg)',
                  opacity: 0.26,
                  transform: `rotate(${frame * 2.6}deg)`,
                  pointerEvents: 'none',
                }}
              />
              <svg
                data-ambient="true"
                width="1080"
                height="1920"
                viewBox="0 0 1080 1920"
                style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
              >
                <circle
                  cx="540"
                  cy="665"
                  r={64 + pulse * 10 + safeLoudness * 14}
                  fill="none"
                  stroke="#FF2E54"
                  strokeWidth="2.6"
                  opacity={0.66 + safeLoudness * 0.24}
                />
                <circle
                  cx="540"
                  cy="665"
                  r={118 + pulse * 15 + safeLoudness * 20}
                  fill="none"
                  stroke="#FACC15"
                  strokeWidth="2.2"
                  strokeDasharray="12 9"
                  opacity={0.56 + pulse * 0.22}
                />
                <circle
                  cx="540"
                  cy="665"
                  r={172 + pulse * 22 + safeLoudness * 26}
                  fill="none"
                  stroke="#FF2E54"
                  strokeWidth="1.9"
                  opacity={0.38 + safeLoudness * 0.26}
                />
                <line x1={540 - 48} y1="665" x2={540 - 20} y2="665" stroke="#FACC15" strokeWidth="2.2" opacity="0.76" />
                <line x1={540 + 20} y1="665" x2={540 + 48} y2="665" stroke="#FACC15" strokeWidth="2.2" opacity="0.76" />
                <line x1="540" y1={665 - 48} x2="540" y2={665 - 20} stroke="#FACC15" strokeWidth="2.2" opacity="0.76" />
                <line x1="540" y1={665 + 20} x2="540" y2={665 + 48} stroke="#FACC15" strokeWidth="2.2" opacity="0.76" />
                <circle
                  cx="540"
                  cy="665"
                  r={16 + safeLoudness * 10}
                  fill="#FF2E54"
                  opacity={0.3 + pulse * 0.2}
                />
                <circle
                  cx="540"
                  cy="665"
                  r={6 + safeLoudness * 5}
                  fill="#FF2E54"
                  stroke="#FACC15"
                  strokeWidth="1.8"
                />
              </svg>
            </div>
          ) : null}
          {cutFlash > 0 ? (
            <div
              data-ambient="true"
              style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: isBackdoor || isRecoveryScene ? '#FACC15' : '#FF2E54',
                opacity: cutFlash,
                mixBlendMode: 'screen',
              }}
            />
          ) : null}
        </div>

        <div
          data-role="stage-card"
          style={{
            position: 'absolute', left: NOIR_GRID.left, top: NOIR_GRID.stageTop, width: NOIR_GRID.width, height: NOIR_GRID.stageHeight,
            boxSizing: 'border-box', padding: '10px 0 12px 0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
          }}
        >
          {/* Top Compact Header Strip (y ~ 308..415, leaving center viewport completely clear) */}
          <div
            style={{
              backgroundColor: 'rgba(7, 11, 22, 0.86)', borderRadius: 22,
              border: `1.5px solid ${
                isRecoveryScene
                  ? 'rgba(16, 185, 129, 0.65)'
                  : effectiveTone === 'amber'
                    ? 'rgba(250, 204, 21, 0.55)'
                    : 'rgba(255, 46, 84, 0.6)'
              }`,
              padding: '13px 22px', boxShadow: '0 14px 34px rgba(0, 0, 0, 0.72)',
              opacity: interpolate(topIn, [0, 1], [0, 1]),
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
              <span
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 20,
                  fontWeight: 900,
                  letterSpacing: 0.4,
                  color: isRecoveryScene ? '#10B981' : effectiveTone === 'amber' ? '#FACC15' : '#FF2E54',
                  minWidth: 0,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                ● {data.badge}
              </span>
              {!isBackdoor && data.crossedOutLabel ? (
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 20,
                    fontWeight: 900,
                    letterSpacing: 0.3,
                    color: '#94A3B8',
                    textDecoration: 'line-through',
                    textDecorationColor: '#FF2E54',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  {data.crossedOutLabel}
                </span>
              ) : null}
            </div>
            <div style={{ fontFamily: FONTS.display, fontSize: data.headline.length > 32 ? 29 : 33, fontWeight: 900, lineHeight: 1.12, color: '#F8FAFC' }}>
              {data.headline}
            </div>
          </div>

          {/* Lower Forensic Overlay (x: 132..948 symmetric, >= 8px clear of iPhone right rail) */}
          {isBackdoor ? (
            <div
              style={{
                width: 816, margin: '0 auto', boxSizing: 'border-box',
                backgroundColor: 'rgba(7, 11, 22, 0.9)', borderRadius: 24,
                border: `2px solid ${isEraseStep || isRecoveryScene ? '#10B981' : '#FACC15'}`,
                padding: '16px 22px', display: 'flex', flexDirection: 'column', gap: 12,
                boxShadow: '0 18px 40px rgba(0, 0, 0, 0.78)',
                opacity: interpolate(cardOneIn, [0, 1], [0, 1]),
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontFamily: FONTS.mono,
                      fontSize: 20,
                      fontWeight: 900,
                      color: isEraseStep || isRecoveryScene ? '#10B981' : '#FACC15',
                    }}
                  >
                    {localProgress >= 0.5 && (data.stepTwoTag || isEraseStep)
                      ? (data.stepTwoTag ?? 'STEP 2')
                      : (data.stepOneTag ?? 'STEP 1')}
                  </div>
                  <div style={{ fontFamily: FONTS.display, fontSize: 27, fontWeight: 900, color: '#FFFFFF', lineHeight: 1.15 }}>
                    {localProgress >= 0.5 ? (data.stepTwoTitle ?? 'Step 2 Verified') : (data.stepOneTitle ?? 'Step 1 Recorded')}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: keypadTiles.length >= 6 ? 5 : keypadTiles.length === 5 ? 6 : 7, flexShrink: 0 }}>
                  {keypadTiles.map((k, kIdx) => {
                    const lit =
                      dialStep > kIdx ||
                      (isEraseStep
                        ? localProgress >= 0.72
                        : hasTwoTileSets || isDefenseCheck
                          ? localProgress >= 0.38
                          : localProgress >= 0.72);
                    return (
                      <span
                        key={`${k}-${kIdx}`}
                        style={{
                          width: keypadTiles.length >= 6 ? 31 : keypadTiles.length === 5 ? 34 : 44,
                          height: keypadTiles.length >= 6 ? 38 : keypadTiles.length === 5 ? 40 : 46,
                          borderRadius: keypadTiles.length >= 5 ? 10 : 12,
                          backgroundColor: isEraseStep || isRecoveryScene
                            ? lit
                              ? '#10B981'
                              : 'rgba(6, 78, 59, 0.92)'
                            : lit
                              ? '#FF2E54'
                              : 'rgba(15, 23, 42, 0.95)',
                          color: lit ? '#FFFFFF' : '#94A3B8',
                          border: `2px solid ${lit ? '#FACC15' : 'rgba(148, 163, 184, 0.35)'}`,
                          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                          fontFamily: FONTS.mono,
                          fontSize: keypadTiles.length >= 6 ? 20 : keypadTiles.length === 5 ? 21 : 24,
                          fontWeight: 900,
                          transform: `scale(${lit ? 1.06 : 0.96})`,
                        }}
                      >
                        {k}
                      </span>
                    );
                  })}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                {docs.map((doc, idx) => (
                  <div
                    key={`${doc}-${idx}`}
                    style={{
                      flex: 1, minWidth: 0, borderRadius: 14, padding: '10px 8px', textAlign: 'center',
                      backgroundColor:
                        idx === activeDocIdx
                          ? (hasTwoTileSets || isDefenseCheck || isRecoveryScene) && localProgress >= 0.55
                            ? 'rgba(16, 185, 129, 0.9)'
                            : 'rgba(225, 29, 72, 0.9)'
                          : 'rgba(15, 23, 42, 0.9)',
                      border: `1.5px solid ${idx === activeDocIdx ? '#FACC15' : 'rgba(248, 250, 252, 0.24)'}`,
                    }}
                  >
                    <span style={{ fontFamily: FONTS.display, fontSize: 20, fontWeight: 900, color: '#FFFFFF' }}>{doc}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div
              style={{
                width: 816, margin: '0 auto', boxSizing: 'border-box',
                backgroundColor: 'rgba(10, 12, 24, 0.9)', borderRadius: 24,
                border: isRecoveryScene ? '2px solid #10B981' : '2.5px solid #FF2E54',
                padding: '18px 24px', display: 'flex', flexDirection: 'column', gap: 10,
                boxShadow: isRecoveryScene
                  ? '0 18px 42px rgba(16, 185, 129, 0.28)'
                  : '0 18px 42px rgba(0, 0, 0, 0.8)',
                opacity: interpolate(cardOneIn, [0, 1], [0, 1]),
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                <span
                  style={{
                    backgroundColor: isRecoveryScene ? '#10B981' : '#FF2E54',
                    color: '#FFFFFF',
                    borderRadius: 999,
                    padding: '5px 12px',
                    fontFamily: FONTS.mono,
                    fontSize: 20,
                    fontWeight: 900,
                    letterSpacing: 0.3,
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  {data.verdictPillLeft ??
                    (isRecoveryScene ? '✓ RECOVERY VERIFIED' : '▲ EVIDENCE CONFIRMED')}
                </span>
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 20,
                    fontWeight: 900,
                    letterSpacing: 0.3,
                    color: '#FACC15',
                    minWidth: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {data.verdictPillRight ??
                    (isRecoveryScene ? 'CASE CLOSED' : 'KEY CLUE LOCKED')}
                </span>
              </div>
              <div style={{ fontFamily: FONTS.display, fontSize: 34, fontWeight: 900, lineHeight: 1.1, color: '#FACC15' }}>
                {data.matchHeadline ?? 'PRIMARY CLUE CONFIRMED'}
              </div>
              <div style={{ fontFamily: FONTS.body, fontSize: 21, fontWeight: 700, color: '#E2E8F0', lineHeight: 1.2 }}>
                {data.matchSubline ?? 'Forensic Timeline Matched'}
              </div>
            </div>
          )}
        </div>
      </>
    );
  }

  const bgWash = isBackdoor
    ? `radial-gradient(circle at 50% 24%, rgba(245, 158, 11, ${0.2 + safeLoudness * 0.1}) 0%, rgba(254, 243, 199, 0.78) 44%, #FFFBEB 85%)`
    : `radial-gradient(circle at 50% 24%, rgba(225, 29, 72, ${0.18 + safeLoudness * 0.14}) 0%, rgba(255, 228, 230, 0.74) 44%, ${BRIGHT_COLORS.bgCanvas} 84%)`;

  const mysteryChips = [
    { key: 'A', label: 'OPTION A', color: BRIGHT_COLORS.crimson, soft: BRIGHT_COLORS.crimsonSoft },
    { key: 'B', label: 'OPTION B', color: BRIGHT_COLORS.cobalt, soft: BRIGHT_COLORS.cobaltSoft },
    { key: 'C', label: 'OPTION C', color: BRIGHT_COLORS.amber, soft: BRIGHT_COLORS.amberSoft },
  ] as const;

  return (
    <>
      <div
        data-ambient="true"
        style={{
          position: 'absolute', inset: -44, pointerEvents: 'none',
          background: `${bgWash}, linear-gradient(${BRIGHT_COLORS.gridLine} 1px, transparent 1px), linear-gradient(90deg, ${BRIGHT_COLORS.gridLine} 1px, transparent 1px)`,
          backgroundSize: '100% 100%, 44px 44px, 44px 44px',
        }}
      >
        <svg data-ambient="true" width="1168" height="2008" viewBox="0 0 1168 2008" style={{ position: 'absolute', inset: 0, opacity: 0.22 }}>
          <line x1="60" y1="260" x2="1108" y2="1520" stroke={BRIGHT_COLORS.crimson} strokeWidth="2" strokeDasharray="9 7" />
          <circle cx="584" cy="960" r={260 + pulse * 30} fill="none" stroke={isBackdoor ? BRIGHT_COLORS.amber : BRIGHT_COLORS.crimson} strokeWidth="2" />
        </svg>
      </div>

      <div
        data-role="stage-card"
        style={{
          position: 'absolute', left: SAFE_ZONE.left, top: 298, width: SAFE_ZONE.usableWidth, height: 974,
          boxSizing: 'border-box', padding: '16px 56px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        }}
      >
        {/* Top Evidence Header Card */}
        <div
          style={{
            backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 24,
            border: `2.5px solid ${isBackdoor ? BRIGHT_COLORS.amberBright : BRIGHT_COLORS.crimson}`,
            padding: '16px 24px', boxShadow: '0 14px 32px rgba(15, 23, 42, 0.08)',
            opacity: interpolate(topIn, [0, 1], [0, 1]),
          }}
        >
          <span
            style={{
              display: 'inline-block', color: '#FFFFFF', borderRadius: 999, padding: '5px 16px',
              backgroundColor: isBackdoor ? BRIGHT_COLORS.amber : BRIGHT_COLORS.crimson,
              fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, letterSpacing: 0.8, marginBottom: 6,
            }}
          >
            {data.badge}
          </span>
          <div style={{ fontFamily: FONTS.display, fontSize: data.headline.length > 34 ? 32 : 36, fontWeight: 900, lineHeight: 1.14, color: BRIGHT_COLORS.textPrimary }}>
            {data.headline}
          </div>
        </div>

        {isBackdoor ? (
          <>
            {/* Step 1: Forensic Mechanism Card */}
            <div
              style={{
                backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 26,
                border: `2.5px solid ${BRIGHT_COLORS.amberBright}`, padding: '20px 24px',
                display: 'flex', alignItems: 'center', gap: 20,
                boxShadow: '0 16px 34px rgba(217, 119, 6, 0.14)',
                opacity: interpolate(cardOneIn, [0, 1], [0, 1]),
                transform: `scale(${interpolate(cardOneIn, [0, 1], [0.93, 1])})`,
              }}
            >
              <div
                style={{
                  width: 76, height: 76, borderRadius: 22, flexShrink: 0,
                  backgroundColor: BRIGHT_COLORS.amberSoft, border: `2px solid ${BRIGHT_COLORS.amberBright}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}
              >
                <StepOneClueIcon isCamera={isCameraClue} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 7, flex: 1 }}>
                <span style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, color: BRIGHT_COLORS.amber }}>
                  STEP 1 · MECHANISM
                </span>
                <div style={{ fontFamily: FONTS.display, fontSize: 32, fontWeight: 900, color: BRIGHT_COLORS.textPrimary, lineHeight: 1.14 }}>
                  {data.stepOneTitle ?? 'Step 1 Recorded'}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <span
                    style={{
                      display: 'inline-block', backgroundColor: BRIGHT_COLORS.crimsonSoft, color: BRIGHT_COLORS.crimson,
                      border: `2px solid ${BRIGHT_COLORS.crimson}`, borderRadius: 12, padding: '5px 14px',
                      fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900,
                    }}
                  >
                    ⚡ {data.stepOneTag ?? 'STEP 1 ACTIVE'}
                  </span>
                  {!isCameraClue ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      {(data.ussdTilesStepOne ?? ['*', '2', '1', '*']).map((k, kIdx) => (
                        <span
                          key={`${k}-${kIdx}`}
                          style={{
                            width: 34, height: 34, borderRadius: 9,
                            backgroundColor: '#0F172A', color: '#FACC15',
                            border: `1.5px solid ${BRIGHT_COLORS.amberBright}`,
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900,
                          }}
                        >
                          {k}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>

            {/* Animated Connector Arrow */}
            <div
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                opacity: interpolate(arrowIn, [0, 1], [0, 1]),
                transform: `translateY(${arrowBounceY}px) scale(${interpolate(arrowIn, [0, 1], [0.88, 1])})`,
              }}
            >
              <span
                style={{
                  backgroundColor: BRIGHT_COLORS.crimson, color: '#FFFFFF', borderRadius: 999, padding: '8px 22px',
                  fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, boxShadow: '0 10px 24px rgba(225, 29, 72, 0.28)',
                }}
              >
                ↓ FORENSIC SEQUENCE ↓
              </span>
            </div>

            {/* Step 2: Impact + 3 Voice-Synced Chips */}
            <div
              style={{
                backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 26, border: `3px solid ${BRIGHT_COLORS.crimson}`,
                padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 15,
                boxShadow: `0 18px ${Math.round(36 + safeLoudness * 16)}px rgba(225, 29, 72, ${(0.16 + safeLoudness * 0.2).toFixed(2)})`,
                opacity: interpolate(cardTwoIn, [0, 1], [0, 1]),
                transform: `scale(${interpolate(cardTwoIn, [0, 1], [0.92, 1])})`,
              }}
            >
              <div>
                <span style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, color: BRIGHT_COLORS.crimson }}>
                  STEP 2 · IMPACT
                </span>
                <div style={{ fontFamily: FONTS.display, fontSize: 32, fontWeight: 900, color: BRIGHT_COLORS.textPrimary, lineHeight: 1.14, marginTop: 4 }}>
                  {data.stepTwoTitle ?? 'Step 2 Verified'}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                {docs.map((doc, idx) => {
                  const chipStart = Math.round((chipRatios[idx] ?? 0.54) * durationInFrames);
                  const chipIn = spring({ frame: Math.max(0, frame - chipStart), fps, config: { damping: 14, stiffness: 260, mass: 0.55 } });
                  const isHot = idx === activeDocIdx;
                  return (
                    <div
                      key={`${doc}-${idx}`}
                      style={{
                        flex: 1, borderRadius: 18, padding: '14px 10px', textAlign: 'center',
                        backgroundColor: isHot ? BRIGHT_COLORS.crimsonSoft : BRIGHT_COLORS.amberSoft,
                        border: `2px solid ${isHot ? BRIGHT_COLORS.crimson : BRIGHT_COLORS.amberBright}`,
                        opacity: interpolate(chipIn, [0, 1], [0, 1]),
                        transform: `scale(${interpolate(chipIn, [0, 1], [0.86, 1])})`,
                      }}
                    >
                      <div style={{ fontFamily: FONTS.display, fontSize: doc.length > 14 ? 22 : 24, fontWeight: 900, color: BRIGHT_COLORS.textPrimary, lineHeight: 1.18 }}>
                        {doc}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Theory #1 Ruled Out + Slashed Red X Stamp */}
            <div
              style={{
                position: 'relative', backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 26,
                border: '2.5px dashed #94A3B8', padding: '20px 24px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
                opacity: interpolate(cardOneIn, [0, 1], [0, 1]),
                transform: `scale(${interpolate(cardOneIn, [0, 1], [0.94, 1])})`,
              }}
            >
              <div>
                <span style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, color: BRIGHT_COLORS.textMuted }}>
                  INITIAL HYPOTHESIS
                </span>
                <div
                  style={{
                    fontFamily: FONTS.display, fontSize: 31, fontWeight: 900, color: '#64748B', marginTop: 4,
                    textDecoration: 'line-through', textDecorationColor: BRIGHT_COLORS.crimson, textDecorationThickness: 4,
                  }}
                >
                  {data.crossedOutLabel ?? 'EXTERNAL VECTOR RULED OUT'}
                </div>
              </div>
              <div
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  backgroundColor: BRIGHT_COLORS.crimson, color: '#FFFFFF', borderRadius: 16, padding: '10px 18px',
                  fontFamily: FONTS.mono, fontSize: 21, fontWeight: 900, flexShrink: 0,
                  boxShadow: '0 10px 22px rgba(225, 29, 72, 0.28)',
                  opacity: interpolate(stampIn, [0, 1], [0, 1]),
                  transform: `scale(${interpolate(stampIn, [0, 1], [1.22, 1])})`,
                }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24">
                  <path d="M5 5 L19 19 M19 5 L5 19" stroke="#FACC15" strokeWidth="3.5" strokeLinecap="round" />
                </svg>
                RULED OUT
              </div>
            </div>

            {/* Connector Pill */}
            <div
              style={{
                display: 'flex', justifyContent: 'center',
                opacity: interpolate(arrowIn, [0, 1], [0, 1]),
                transform: `translateY(${arrowBounceY}px) scale(${interpolate(arrowIn, [0, 1], [0.88, 1])})`,
              }}
            >
              <span style={{ backgroundColor: BRIGHT_COLORS.cobalt, color: '#FFFFFF', borderRadius: 999, padding: '8px 24px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, boxShadow: '0 10px 24px rgba(29, 78, 216, 0.28)' }}>
                ↓ VERIFIED EVIDENCE ↓
              </span>
            </div>

            {/* Verified Twist + 3 Suspect Silhouette Chips */}
            <div
              style={{
                backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 28, border: `3.5px solid ${BRIGHT_COLORS.crimson}`,
                padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14,
                boxShadow: `0 20px ${Math.round(40 + safeLoudness * 18)}px rgba(225, 29, 72, ${(0.18 + safeLoudness * 0.24).toFixed(2)})`,
                opacity: interpolate(cardTwoIn, [0, 1], [0, 1]),
                transform: `scale(${interpolate(cardTwoIn, [0, 1], [0.92, 1])})`,
              }}
            >
              <span style={{ alignSelf: 'flex-start', backgroundColor: BRIGHT_COLORS.crimson, color: '#FFFFFF', borderRadius: 999, padding: '6px 16px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900 }}>
                ● VERIFIED FINDING
              </span>
              <div style={{ fontFamily: FONTS.display, fontSize: (data.matchHeadline ?? '').length > 28 ? 35 : 40, fontWeight: 900, lineHeight: 1.12, color: BRIGHT_COLORS.crimson }}>
                {data.matchHeadline ?? 'PRIMARY CLUE CONFIRMED'}
              </div>
              <div style={{ backgroundColor: BRIGHT_COLORS.amberSoft, border: `2px solid ${BRIGHT_COLORS.amberBright}`, borderRadius: 18, padding: '14px 18px', fontFamily: FONTS.display, fontSize: 25, fontWeight: 900, lineHeight: 1.2, color: BRIGHT_COLORS.textPrimary }}>
                {data.matchSubline ?? 'Forensic Timeline Matched'}
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                {mysteryChips.map((mc, idx) => {
                  const chipStart = Math.round((chipRatios[idx] ?? 0.54) * durationInFrames);
                  const chipIn = spring({ frame: Math.max(0, frame - chipStart), fps, config: { damping: 14, stiffness: 260, mass: 0.55 } });
                  return (
                    <div
                      key={mc.key}
                      style={{
                        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                        backgroundColor: mc.soft, border: `2px solid ${mc.color}`, borderRadius: 16, padding: '9px 12px',
                        opacity: interpolate(chipIn, [0, 1], [0, 1]),
                        transform: `scale(${interpolate(chipIn, [0, 1], [0.86, 1])})`,
                      }}
                    >
                      <MysteryInsiderSilhouette color={mc.color} />
                      <span style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, color: mc.color }}>
                        {mc.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
};
