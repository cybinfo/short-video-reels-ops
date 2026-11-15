import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRIGHT_COLORS, FONTS, NOIR_GRID, SAFE_ZONE } from '../theme/tokens';
import { DetectiveCrimeHookProps, SpeakerId, WordTimestamp } from '../types';
import { NoirParallaxStage } from './NoirParallaxStage';

const formatIndianNumber = (num: number): string => {
  const rounded = Math.max(0, Math.round(num));
  const str = String(rounded);
  if (str.length <= 3) return str;
  const last3 = str.slice(-3);
  const rest = str.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',');
  return `${rest},${last3}`;
};

const PRIMARY_SPEAKERS = new Set(['kabir', 'jyoti', 'rajat', 'narrator']);

export const DetectiveCrimeHookScene: React.FC<{
  data: DetectiveCrimeHookProps;
  liveLoudness?: number;
  activeSpeaker?: SpeakerId;
  sceneWords?: WordTimestamp[];
  isNoirCinema?: boolean;
  speakerLabels?: Partial<Record<SpeakerId, string>>;
}> = ({ data, liveLoudness = 0.35, activeSpeaker, isNoirCinema = false, speakerLabels }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const safeDur = Math.max(1, durationInFrames - 1);
  const localProgress = Math.min(1, Math.max(0, frame / safeDur));
  const safeLoudness = Number.isFinite(liveLoudness) ? Math.min(1, Math.max(0, liveLoudness)) : 0.35;

  const headerIn = spring({ frame, fps, config: { damping: 16, stiffness: 185 } });
  const phoneIn = spring({ frame: Math.max(0, frame - 4), fps, config: { damping: 15, stiffness: 180 } });
  const cardThreeStart = Math.round(0.08 * durationInFrames);
  const alertIn = spring({ frame: Math.max(0, frame - cardThreeStart), fps, config: { damping: 14, stiffness: 210, mass: 0.65 } });

  const rawDigits = data.amountLost.replace(/[^0-9]/g, '');
  const isNumericLoss = rawDigits.length >= 4;
  const isUnmask = data.mode ? data.mode === 'suspect_unmask' : !isNumericLoss;
  const baseAmount = isNumericLoss ? parseInt(rawDigits, 10) : 1000000;
  const formattedTotal = formatIndianNumber(baseAmount);

  const [cut1, cut2] = data.cutRatios ?? (isUnmask ? [0.66, 0.82] : [0.24, 0.64]);
  const shotIdx = (localProgress < cut1 ? 0 : localProgress < cut2 ? 1 : 2) as 0 | 1 | 2;

  const isSafePhase = localProgress < 0.36;
  const isDrainingPhase = !isUnmask && isNumericLoss && localProgress >= 0.36 && localProgress < 0.68;
  const drainT = interpolate(localProgress, [0.36, 0.65], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const remainingAmount = Math.round(baseAmount * (1 - drainT));
  const flashBlink = Math.sin(frame * 1.15) > 0;
  const rawUnmaskShakeX =
    isUnmask && localProgress >= cut2 && localProgress < cut2 + 0.09
      ? Math.sin(frame * 1.8) * 4 * (1 - (localProgress - cut2) / 0.09)
      : 0;
  const rawDrainShakeX = isDrainingPhase
    ? Math.sin(frame * 1.55) * 3.5 * (1 - drainT)
    : rawUnmaskShakeX;
  const drainShakeX = Math.max(-4, Math.min(4, rawDrainShakeX));
  const sirenSweepX = ((frame * 5.6) % 220) - 110;

  const sirenPulse = (Math.sin(frame * 0.16) + 1) / 2;
  const floatY = Math.sin(frame * 0.11) * 2.5;
  const pills = (data.shockPills.length > 0 ? data.shockPills : ['CLUE 01', 'CLUE 02', 'CLUE 03']).slice(0, 3);
  const pillThresholds = !isUnmask ? [0.48, 0.59, 0.70] : [0.08, 0.68, 0.83];
  const activePillIdx = Math.floor(frame / 20) % Math.max(1, pills.length);
  const clockShort = data.timeLabel.replace(/\s*(AM|PM)/i, '').trim() || '00:00';

  const displayAmount = isUnmask
    ? data.shotValues?.[shotIdx] ?? data.amountLost
    : data.shotValues?.[shotIdx] ??
      (isSafePhase
        ? `Rs ${formattedTotal}`
        : isDrainingPhase
          ? `Rs ${formatIndianNumber(remainingAmount)}`
          : 'Rs 0');
  const amountFontSize = displayAmount.length > 15 ? 46 : 56;

  if (isNoirCinema && data.heroImage) {
    // 3-Angle Data-Driven Cinema Choreography governed by mode ('loss_drain' | 'suspect_unmask') and cutRatios
    const activeHero =
      shotIdx === 0 && data.tertiaryImage
        ? data.tertiaryImage
        : shotIdx === 1 && data.secondaryImage
          ? data.secondaryImage
          : data.heroImage;
    const camScale =
      shotIdx === 0
        ? interpolate(localProgress, [0, cut1], [1.05, 1.12], { extrapolateRight: 'clamp' })
        : shotIdx === 1
          ? interpolate(localProgress, [cut1, cut2], [1.06, 1.15], { extrapolateRight: 'clamp' })
          : interpolate(localProgress, [cut2, 1], [1.06, 1.14], { extrapolateRight: 'clamp' });
    const camOrigin = isUnmask
      ? '50% 36.5%'
      : shotIdx === 1
        ? '50% 34%'
        : '50% 36.5%';
    const imgObjectPosition = isUnmask
      ? '50% 50%'
      : shotIdx === 1
        ? '50% 26%'
        : '50% 50%';
    const handheldX = Math.sin(frame * 0.075) * 4.5 + Math.cos(frame * 0.041) * 2.5 + drainShakeX;
    const handheldY = Math.cos(frame * 0.062) * 3.5;
    const handheldRot = Math.sin(frame * 0.048) * 0.24;
    const cutFlash =
      Math.abs(localProgress - cut1) < 0.026 || Math.abs(localProgress - cut2) < 0.026 ? 0.38 : 0;
    const radialTint = isUnmask
      ? shotIdx === 2
        ? `rgba(225, 29, 72, ${0.22 + safeLoudness * 0.14})`
        : 'rgba(16, 185, 129, 0.1)'
      : `rgba(225, 29, 72, ${shotIdx >= 1 ? 0.18 + safeLoudness * 0.14 : 0.04})`;

    const shotProgress =
      shotIdx === 0
        ? interpolate(localProgress, [0, cut1], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })
        : shotIdx === 1
          ? interpolate(localProgress, [cut1, cut2], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })
          : interpolate(localProgress, [cut2, 1], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
    const scrollStopperOpacity = interpolate(frame, [38, 50], [1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    const isCameoVoice = Boolean(activeSpeaker && !PRIMARY_SPEAKERS.has(activeSpeaker));
    const cameoLabel =
      (activeSpeaker && speakerLabels?.[activeSpeaker]) || 'VOICE AUDIO';
    const cameoColor = isUnmask || /call|phone/i.test(cameoLabel) ? '#34D399' : '#FBBF24';
    const stopperEmerald =
      data.scrollStopper?.tone === 'emerald' || (!data.scrollStopper?.tone && isUnmask);
    const shotTitle =
      data.shotTitles?.[shotIdx] ??
      (isUnmask
        ? shotIdx < 2
          ? `SUSPECT REVIEW · SHOT ${shotIdx + 1}`
          : `▲ ${data.bankAlertTitle}`
        : isSafePhase
          ? `● ${data.phoneStatus.toUpperCase()}`
          : `▲ ${data.bankAlertTitle}`);
    const shotTag =
      data.shotTags?.[shotIdx] ??
      (isUnmask
        ? shotIdx < 2
          ? 'VERIFIED CLUE'
          : 'UNMASKED!'
        : isSafePhase
          ? 'SAVINGS LOCKED'
          : isDrainingPhase
            ? 'DRAINING LIVE!'
            : 'ACCOUNT EMPTY!');

    return (
      <>
        <div
          data-ambient="true"
          style={{
            position: 'absolute',
            inset: 0,
            overflow: 'hidden',
            backgroundColor: '#04070F',
            pointerEvents: 'none',
          }}
        >
          <NoirParallaxStage
            key={activeHero}
            imagePath={activeHero}
            shotProgress={shotProgress}
            camScale={camScale}
            camOrigin={camOrigin}
            objectPosition={imgObjectPosition}
            handheldX={handheldX}
            handheldY={handheldY}
            handheldRot={handheldRot}
            contrast={shotIdx >= 1 ? 1.1 : 1.06}
            brightness={shotIdx >= 1 ? 0.93 + safeLoudness * 0.1 : 0.92}
            lockedParallax={data.lockedParallax}
            parallaxMode={
              shotIdx === 1
                ? (data.secondaryParallaxMode ?? 'macro')
                : data.lockedParallax
                  ? 'locked'
                  : 'standard'
            }
            accentColor={
              isUnmask && shotIdx < 2
                ? 'rgba(52, 211, 153, 0.34)'
                : shotIdx >= 1
                  ? 'rgba(255, 46, 84, 0.36)'
                  : 'rgba(250, 204, 21, 0.34)'
            }
          />
          {/* Top & Bottom Noir Vignettes Keeping Center Character Face 100% Clear */}
          <div
            data-ambient="true"
            style={{
              position: 'absolute',
              inset: 0,
              background: `
                linear-gradient(180deg, rgba(4, 7, 15, 0.84) 0%, rgba(4, 7, 15, 0.18) 24%, rgba(4, 7, 15, 0.06) 54%, rgba(4, 7, 15, 0.86) 78%, rgba(4, 7, 15, 0.96) 100%),
                radial-gradient(circle at 50% 42%, ${radialTint} 0%, transparent 58%)
              `,
            }}
          />
          {isDrainingPhase ? (
            <div
              data-ambient="true"
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: '-30%',
                width: '160%',
                background:
                  'linear-gradient(115deg, transparent 20%, rgba(255, 46, 84, 0.28) 50%, transparent 80%)',
                transform: `translate3d(${sirenSweepX}%, 0, 0)`,
                mixBlendMode: 'screen',
                pointerEvents: 'none',
              }}
            />
          ) : null}
          {cutFlash > 0 ? (
            <div
              data-ambient="true"
              style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: isUnmask
                  ? shotIdx === 2
                    ? '#FF2E54'
                    : '#10B981'
                  : shotIdx === 1
                    ? '#FF2E54'
                    : '#FACC15',
                opacity: cutFlash,
                mixBlendMode: 'screen',
              }}
            />
          ) : null}
        </div>

        <div
          data-role="stage-card"
          style={{
            position: 'absolute',
            left: NOIR_GRID.left,
            top: NOIR_GRID.stageTop,
            width: NOIR_GRID.width,
            height: NOIR_GRID.stageHeight,
            boxSizing: 'border-box',
            padding: '10px 0 12px 0',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          {/* Unified Top Header Card (2-line strip when scrollStopper active at Frame 0 -> strictly 2 cards on screen) */}
          <div
            style={{
              width: '100%',
              boxSizing: 'border-box',
              backgroundColor: 'rgba(7, 11, 22, 0.9)',
              borderRadius: 22,
              border:
                frame < 50 && data.scrollStopper
                  ? stopperEmerald
                    ? '1.5px solid rgba(16, 185, 129, 0.78)'
                    : '1.5px solid rgba(255, 46, 84, 0.78)'
                  : '1.5px solid rgba(250, 204, 21, 0.5)',
              padding: '11px 20px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.72)',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              opacity: interpolate(headerIn, [0, 1], [0, 1]),
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 12,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  backgroundColor: 'rgba(225, 29, 72, 0.92)',
                  border: '1.5px solid rgba(250, 204, 21, 0.65)',
                  color: '#FFFFFF',
                  padding: '6px 14px',
                  borderRadius: 999,
                  fontFamily: FONTS.mono,
                  fontSize: 20,
                  fontWeight: 900,
                  letterSpacing: 0.4,
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                }}
              >
                <span
                  style={{
                    width: 9,
                    height: 9,
                    borderRadius: '50%',
                    backgroundColor: '#FACC15',
                    opacity: 0.6 + sirenPulse * 0.4,
                  }}
                />
                {data.caseBadge}
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  minWidth: 0,
                  color: '#F8FAFC',
                  fontFamily: FONTS.mono,
                  fontSize: 20,
                  fontWeight: 800,
                  letterSpacing: 0.2,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                <span style={{ color: '#FACC15', flexShrink: 0 }}>{data.timeLabel}</span>
                <span style={{ color: '#94A3B8', flexShrink: 0 }}>·</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {data.locationLabel}
                </span>
              </div>
            </div>

            {frame < 50 && data.scrollStopper ? (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 12,
                  paddingTop: 8,
                  borderTop: '1px solid rgba(148, 163, 184, 0.22)',
                  opacity: scrollStopperOpacity,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 10px',
                    borderRadius: 999,
                    backgroundColor: stopperEmerald
                      ? 'rgba(16, 185, 129, 0.22)'
                      : 'rgba(255, 46, 84, 0.22)',
                    border: stopperEmerald
                      ? '1px solid rgba(16, 185, 129, 0.65)'
                      : '1px solid rgba(255, 46, 84, 0.65)',
                    flexShrink: 0,
                  }}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: stopperEmerald ? '#34D399' : '#FF2E54',
                    }}
                  />
                  {data.scrollStopper.currencyBadge ? (
                    <span
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        backgroundColor: stopperEmerald ? '#10B981' : '#FF2E54',
                        color: '#FFFFFF',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontFamily: FONTS.display,
                        fontSize: 20,
                        fontWeight: 900,
                      }}
                    >
                      {data.scrollStopper.currencyBadge}
                    </span>
                  ) : null}
                  <span
                    style={{
                      fontFamily: FONTS.mono,
                      fontSize: 20,
                      fontWeight: 900,
                      letterSpacing: 0.3,
                      color: stopperEmerald ? '#6EE7B7' : '#FECDD3',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {data.scrollStopper.badge}
                  </span>
                </div>

                <span
                  style={{
                    fontFamily: FONTS.body,
                    fontSize: 20,
                    fontWeight: 800,
                    color: '#F8FAFC',
                    minWidth: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {data.scrollStopper.text}
                </span>
              </div>
            ) : null}
          </div>

          {/* Lower Diegetic Bank Alert + Shock Pills (x: 132..948 symmetric, >= 4px right-rail immunity even mid-shake) */}
          <div
            style={{
              width: 816,
              margin: '0 auto',
              boxSizing: 'border-box',
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
            }}
          >
            {isCameoVoice ? (
              <div
                style={{
                  alignSelf: 'center',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '6px 16px',
                  borderRadius: 999,
                  backgroundColor: 'rgba(6, 10, 20, 0.92)',
                  border: `1.5px solid ${cameoColor}`,
                  boxShadow: '0 10px 24px rgba(0, 0, 0, 0.72)',
                }}
              >
                <div
                  data-ambient="true"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 3,
                    height: 18,
                  }}
                >
                  {[0.55, 0.9, 1.0, 0.8, 0.6].map((w, bIdx) => {
                    const wave =
                      0.35 + 0.65 * ((Math.sin(frame * 0.55 + bIdx * 1.15) + 1) / 2);
                    const barH = Math.round(
                      4 + 13 * Math.min(1, (0.25 + safeLoudness * 0.85) * w * wave)
                    );
                    return (
                      <span
                        key={bIdx}
                        data-ambient="true"
                        style={{
                          width: 3.5,
                          height: barH,
                          borderRadius: 999,
                          backgroundColor: cameoColor,
                        }}
                      />
                    );
                  })}
                </div>
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 20,
                    fontWeight: 900,
                    letterSpacing: 0.5,
                    color: cameoColor,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {cameoLabel}
                </span>
              </div>
            ) : null}

            <div
              style={{
                width: '100%',
                boxSizing: 'border-box',
                backgroundColor: 'rgba(7, 11, 22, 0.88)',
                borderRadius: 24,
                border: `2.5px solid ${
                  isUnmask
                    ? shotIdx < 2
                      ? '#10B981'
                      : '#FF2E54'
                    : !isSafePhase
                      ? '#FF2E54'
                      : '#FACC15'
                }`,
                padding: '16px 24px',
                boxShadow: '0 18px 42px rgba(0, 0, 0, 0.78)',
                opacity: interpolate(alertIn, [0, 1], [0, 1]),
                transform: `translateX(${drainShakeX}px)`,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 12,
                  marginBottom: 8,
                }}
              >
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 20,
                    fontWeight: 900,
                    letterSpacing: 0.6,
                    minWidth: 0,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    color: isUnmask
                      ? shotIdx === 0
                        ? '#FACC15'
                        : shotIdx === 1
                          ? '#38BDF8'
                          : '#FB7185'
                      : !isSafePhase
                        ? '#FB7185'
                        : '#FDE68A',
                  }}
                >
                  {shotTitle}
                </span>
                <span
                  style={{
                    fontFamily: FONTS.mono,
                    fontSize: 20,
                    fontWeight: 900,
                    letterSpacing: 0.3,
                    flexShrink: 0,
                    whiteSpace: 'nowrap',
                    backgroundColor: isUnmask
                      ? shotIdx < 2
                        ? 'rgba(16, 185, 129, 0.22)'
                        : 'rgba(255, 46, 84, 0.28)'
                      : isDrainingPhase && flashBlink
                        ? '#FACC15'
                        : 'rgba(255, 46, 84, 0.24)',
                    color: isUnmask
                      ? shotIdx === 0
                        ? '#FEF08A'
                        : shotIdx === 1
                          ? '#BAE6FD'
                          : '#FECDD3'
                      : isDrainingPhase && flashBlink
                        ? '#0F172A'
                        : '#FECDD3',
                    border: isUnmask
                      ? shotIdx === 0
                        ? '1px solid rgba(250, 204, 21, 0.6)'
                        : shotIdx === 1
                          ? '1px solid rgba(56, 189, 248, 0.6)'
                          : '1px solid rgba(255, 46, 84, 0.65)'
                      : '1px solid rgba(255, 46, 84, 0.5)',
                    padding: '4px 11px',
                    borderRadius: 999,
                  }}
                >
                  {shotTag}
                </span>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  justifyContent: 'space-between',
                  gap: 16,
                }}
              >
                <div
                  style={{
                    fontFamily: FONTS.display,
                    fontSize: amountFontSize,
                    fontWeight: 900,
                    lineHeight: 1.04,
                    color: isUnmask
                      ? shotIdx < 2
                        ? '#10B981'
                        : '#FF2E54'
                      : isSafePhase
                        ? '#FACC15'
                        : '#FF2E54',
                    textShadow:
                      isUnmask && shotIdx < 2
                        ? '0 2px 18px rgba(16, 185, 129, 0.42)'
                        : '0 2px 18px rgba(255, 46, 84, 0.45)',
                  }}
                >
                  {displayAmount}
                </div>
                {!isUnmask && isNumericLoss ? (
                  <div style={{ flex: 1, maxWidth: 260 }}>
                    <div
                      style={{
                        height: 10,
                        borderRadius: 999,
                        backgroundColor: 'rgba(148, 163, 184, 0.22)',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        data-ambient="true"
                        style={{
                          width: `${
                            isSafePhase ? 100 : Math.max(3, Math.round((1 - drainT) * 100))
                          }%`,
                          height: '100%',
                          borderRadius: 999,
                          backgroundColor: isSafePhase ? '#FACC15' : '#FF2E54',
                        }}
                      />
                    </div>
                  </div>
                ) : null}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              {pills.map((pill, idx) => {
                const startFrame = Math.round((pillThresholds[idx] ?? 0.54) * durationInFrames);
                const pillIn = spring({
                  frame: Math.max(0, frame - startFrame),
                  fps,
                  config: { damping: 14, stiffness: 260, mass: 0.55 },
                });
                const isHot = idx === activePillIdx && localProgress >= (!isUnmask ? 0.72 : 0.75);
                return (
                  <div
                    key={`${pill}-${idx}`}
                    style={{
                      flex: 1,
                      minWidth: 0,
                      backgroundColor: isHot
                        ? 'rgba(225, 29, 72, 0.92)'
                        : 'rgba(10, 15, 28, 0.86)',
                      border: `1.5px solid ${
                        isHot ? '#FACC15' : 'rgba(248, 250, 252, 0.28)'
                      }`,
                      borderRadius: 16,
                      padding: '11px 8px',
                      textAlign: 'center',
                      boxShadow: '0 10px 24px rgba(0, 0, 0, 0.65)',
                      opacity: interpolate(pillIn, [0, 1], [0, 1]),
                      transform: `scale(${interpolate(pillIn, [0, 1], [0.9, 1], {
                        extrapolateLeft: 'clamp',
                        extrapolateRight: 'clamp',
                      })})`,
                    }}
                  >
                    <span
                      style={{
                        fontFamily: FONTS.display,
                        fontSize: pill.length > 16 ? 20 : pill.length > 13 ? 21 : 22,
                        fontWeight: 900,
                        letterSpacing: pill.length > 16 ? 0.2 : 0.4,
                        color: isHot ? '#FFFFFF' : '#F8FAFC',
                      }}
                    >
                      {pill}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div
        data-ambient="true"
        style={{
          position: 'absolute', inset: -44, pointerEvents: 'none',
          background: isSafePhase
            ? `radial-gradient(circle at 50% 18%, rgba(245, 158, 11, 0.26) 0%, rgba(254, 243, 199, 0.78) 40%, ${BRIGHT_COLORS.creamWarm} 82%), linear-gradient(${BRIGHT_COLORS.gridLine} 1px, transparent 1px), linear-gradient(90deg, ${BRIGHT_COLORS.gridLine} 1px, transparent 1px)`
            : `radial-gradient(circle at 50% 20%, rgba(225, 29, 72, ${0.18 + safeLoudness * 0.14}) 0%, rgba(255, 228, 230, 0.74) 40%, ${BRIGHT_COLORS.creamWarm} 82%), linear-gradient(${BRIGHT_COLORS.gridLine} 1px, transparent 1px), linear-gradient(90deg, ${BRIGHT_COLORS.gridLine} 1px, transparent 1px)`,
          backgroundSize: '100% 100%, 44px 44px, 44px 44px',
        }}
      >
        <svg data-ambient="true" width="1168" height="2008" viewBox="0 0 1168 2008" style={{ position: 'absolute', inset: 0, opacity: 0.34 }}>
          <path d="M80 285 Q332 340 584 285 Q836 340 1088 285" fill="none" stroke={BRIGHT_COLORS.amberBright} strokeWidth="4" strokeDasharray="12 10" />
          {[180, 380, 584, 788, 988].map((cx) => (
            <circle key={cx} cx={cx} cy="306" r="9" fill={cx % 2 === 0 ? BRIGHT_COLORS.amberBright : BRIGHT_COLORS.crimson} />
          ))}
        </svg>
      </div>

      <div
        data-role="stage-card"
        style={{
          position: 'absolute', left: SAFE_ZONE.left, top: 298, width: SAFE_ZONE.usableWidth, height: 974,
          boxSizing: 'border-box', padding: '16px 56px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        }}
      >
        {/* Row 1: Case & Location Header */}
        <div
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
            opacity: interpolate(headerIn, [0, 1], [0, 1]),
          }}
        >
          <div
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              backgroundColor: BRIGHT_COLORS.crimson, color: '#FFFFFF',
              padding: '11px 20px', borderRadius: 999,
              fontFamily: FONTS.mono, fontSize: 19, fontWeight: 900, letterSpacing: 0.7,
              boxShadow: '0 10px 24px rgba(225, 29, 72, 0.26)',
            }}
          >
            <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: '#FACC15', opacity: 0.6 + sirenPulse * 0.4 }} />
            {data.caseBadge}
          </div>

          <div
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              background: 'linear-gradient(135deg, #7C2D12 0%, #991B1B 100%)', color: '#FFFFFF',
              border: `2px solid ${BRIGHT_COLORS.amberBright}`,
              padding: '9px 18px', borderRadius: 999,
              fontFamily: FONTS.mono, fontSize: 18, fontWeight: 800, letterSpacing: 0.5,
              boxShadow: '0 10px 22px rgba(180, 83, 9, 0.22)',
            }}
          >
            {/* Header Accent Motif */}
            <svg width="24" height="24" viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
              <path d="M8 9 L5 5 M16 9 L19 5" stroke="#4ADE80" strokeWidth="2.2" strokeLinecap="round" />
              <circle cx="12" cy="7" r="3" fill="#FACC15" />
              <path d="M7 10 H17 L19 16 C19 19.5 16 22 12 22 C8 22 5 19.5 5 16 Z" fill="#F59E0B" stroke="#FEF3C7" strokeWidth="1.4" />
              <path d="M8 15 H16" stroke="#DC2626" strokeWidth="2" />
            </svg>
            <span style={{ color: '#FDE68A' }}>{data.timeLabel}</span>
            <span style={{ color: '#FACC15' }}>·</span>
            <span>{data.locationLabel}</span>
          </div>
        </div>

        {/* Row 2: Smartphone Forensic Status Card */}
        <div
          style={{
            background: `linear-gradient(135deg, #FFFFFF 0%, ${BRIGHT_COLORS.creamWarm} 100%)`,
            borderRadius: 26, border: `2.5px solid ${BRIGHT_COLORS.amberBright}`,
            padding: '18px 24px', display: 'flex', alignItems: 'center', gap: 24,
            boxShadow: '0 16px 34px rgba(180, 83, 9, 0.1)',
            opacity: interpolate(phoneIn, [0, 1], [0, 1]),
            transform: `scale(${interpolate(phoneIn, [0, 1], [0.95, 1])})`,
          }}
        >
          <svg width="110" height="190" viewBox="0 0 110 190" style={{ flexShrink: 0, transform: `translateY(${floatY}px)` }}>
            <rect x="4" y="4" width="102" height="182" rx="22" fill="#0F172A" stroke="#F59E0B" strokeWidth="3.5" />
            <rect x="11" y="11" width="88" height="168" rx="16" fill="#1E293B" />
            <rect x="36" y="17" width="38" height="7" rx="3.5" fill="#020617" />
            {/* Lockscreen Accent */}
            <path d="M16 34 Q35 43 55 34 Q75 43 94 34" fill="none" stroke="#F59E0B" strokeWidth="2.4" />
            <path d="M45 66 V56 A10 10 0 0 1 65 56 V66" fill="none" stroke="#FACC15" strokeWidth="3.8" strokeLinecap="round" />
            <rect x="39" y="66" width="32" height="25" rx="6" fill="#FACC15" />
            <circle cx="55" cy="78.5" r="3.5" fill="#0F172A" />
            <rect x="20" y="106" width="70" height="22" rx="8" fill="rgba(245, 158, 11, 0.2)" stroke="#F59E0B" strokeWidth="1.2" />
            <circle cx="31" cy="117" r="4.5" fill="#10B981" />
            <rect x="41" y="113" width="40" height="8" rx="4" fill="#FDE68A" />
            <rect x="28" y="140" width="54" height="8" rx="4" fill="#94A3B8" opacity="0.65" />
            <rect x="34" y="166" width="42" height="5" rx="2.5" fill="#CBD5E1" opacity="0.7" />
          </svg>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span
                style={{
                  backgroundColor: BRIGHT_COLORS.emeraldSoft, color: BRIGHT_COLORS.emerald,
                  border: `1.5px solid ${BRIGHT_COLORS.emeraldBorder}`, borderRadius: 999,
                  padding: '5px 14px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900,
                }}
              >
                🔒 LOCKED @ {clockShort}
              </span>
              <span
                style={{
                  backgroundColor: BRIGHT_COLORS.amberSoft, color: BRIGHT_COLORS.amber,
                  border: `1.5px solid ${BRIGHT_COLORS.amberBright}`, borderRadius: 999,
                  padding: '5px 14px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900,
                }}
              >
                ★ SAVINGS PROTECTED
              </span>
            </div>

            <div style={{ fontFamily: FONTS.display, fontSize: 34, fontWeight: 900, lineHeight: 1.14, color: BRIGHT_COLORS.textPrimary }}>
              {data.phoneStatus}
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {['CLUE 01', 'CLUE 02', 'CLUE 03'].map((tag) => (
                <span
                  key={tag}
                  style={{
                    backgroundColor: '#FFFFFF', color: BRIGHT_COLORS.textSecondary,
                    border: `1.5px solid ${BRIGHT_COLORS.amberBorder}`,
                    borderRadius: 12, padding: '6px 13px', fontFamily: FONTS.body, fontSize: 18, fontWeight: 800,
                  }}
                >
                  ✓ {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Row 3: Voice-Synced Savings -> Rapid Live Balance Drain Card */}
        <div
          style={{
            backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 26,
            border: `3.5px solid ${isSafePhase ? BRIGHT_COLORS.emerald : BRIGHT_COLORS.crimson}`,
            padding: '18px 24px 20px', display: 'flex', flexDirection: 'column', gap: 12,
            boxShadow: isSafePhase
              ? '0 16px 36px rgba(5, 150, 105, 0.14)'
              : `0 18px ${Math.round(36 + safeLoudness * 18)}px rgba(225, 29, 72, ${(0.16 + safeLoudness * 0.24).toFixed(2)})`,
            opacity: interpolate(alertIn, [0, 1], [0, 1]),
            transform: `translateX(${drainShakeX}px) scale(${interpolate(alertIn, [0, 1], [0.92, 1])})`,
          }}
        >
          <div
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
              background: isSafePhase
                ? `linear-gradient(90deg, ${BRIGHT_COLORS.emerald} 0%, ${BRIGHT_COLORS.amber} 100%)`
                : BRIGHT_COLORS.crimson,
              color: '#FFFFFF', borderRadius: 16, padding: '10px 18px',
            }}
          >
            <span style={{ fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900, letterSpacing: 0.6 }}>
              {isSafePhase ? '★ ACCOUNT SAVINGS · SAFE' : `▲ ${data.bankAlertTitle}`}
            </span>
            <span
              style={{
                fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900,
                backgroundColor: isDrainingPhase && flashBlink ? '#FACC15' : 'rgba(255, 255, 255, 0.22)',
                color: isDrainingPhase && flashBlink ? '#0F172A' : '#FFFFFF',
                padding: '4px 12px', borderRadius: 999, whiteSpace: 'nowrap',
              }}
            >
              {isSafePhase
                ? 'FUNDS PROTECTED'
                : isDrainingPhase
                  ? `- Rs ${formattedTotal} DRAINED`
                  : 'BALANCE: Rs 0'}
            </span>
          </div>

          <div
            style={{
              background: isSafePhase
                ? 'linear-gradient(135deg, #ECFDF5 0%, #FEF3C7 100%)'
                : BRIGHT_COLORS.crimsonSoft,
              borderRadius: 18, padding: '14px 22px', textAlign: 'center',
              border: `1.5px solid ${isSafePhase ? BRIGHT_COLORS.emeraldBorder : BRIGHT_COLORS.crimsonBorder}`,
            }}
          >
            <div
              style={{
                fontFamily: FONTS.display, fontSize: amountFontSize, fontWeight: 900,
                lineHeight: 1.06, letterSpacing: -0.5,
                color: isSafePhase ? BRIGHT_COLORS.emerald : BRIGHT_COLORS.crimson,
              }}
            >
              {displayAmount}
            </div>
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14 }}>
              <div style={{ flex: 1, height: 8, borderRadius: 999, backgroundColor: 'rgba(15, 23, 42, 0.1)', overflow: 'hidden' }}>
                <div
                  data-ambient="true"
                  style={{
                    width: `${isSafePhase ? 100 : Math.max(2, Math.round((1 - drainT) * 100))}%`,
                    height: '100%', borderRadius: 999,
                    backgroundColor: isSafePhase ? BRIGHT_COLORS.emerald : BRIGHT_COLORS.crimson,
                  }}
                />
              </div>
              <span style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, color: isSafePhase ? BRIGHT_COLORS.amber : BRIGHT_COLORS.crimson, whiteSpace: 'nowrap' }}>
                {isSafePhase ? '100% PROTECTED' : `- Rs ${formattedTotal} DRAINED`}
              </span>
            </div>
          </div>
        </div>

        {/* Row 4: Voice-Synced Shock Pills (0.52, 0.61, 0.70) */}
        <div style={{ display: 'flex', gap: 14 }}>
          {pills.map((pill, idx) => {
            const startFrame = Math.round((pillThresholds[idx] ?? 0.52) * durationInFrames);
            const pillIn = spring({
              frame: Math.max(0, frame - startFrame),
              fps,
              config: { damping: 15, stiffness: 280, mass: 0.55 },
            });
            const isSpotlight = idx === activePillIdx && localProgress >= 0.72;
            return (
              <div
                key={`${pill}-${idx}`}
                style={{
                  flex: 1,
                  backgroundColor: isSpotlight ? BRIGHT_COLORS.crimson : BRIGHT_COLORS.bgCard,
                  border: `2.5px solid ${isSpotlight ? BRIGHT_COLORS.crimson : BRIGHT_COLORS.textPrimary}`,
                  borderRadius: 20, padding: '16px 12px', textAlign: 'center',
                  boxShadow: isSpotlight
                    ? `0 12px ${Math.round(22 + safeLoudness * 12)}px rgba(225, 29, 72, 0.3)`
                    : '0 8px 18px rgba(15, 23, 42, 0.08)',
                  opacity: interpolate(pillIn, [0, 1], [0, 1]),
                  transform: `scale(${interpolate(pillIn, [0, 1], [0.88, 1])})`,
                }}
              >
                <span
                  style={{
                    fontFamily: FONTS.display, fontSize: pill.length > 13 ? 23 : pill.length > 10 ? 26 : 29,
                    fontWeight: 900, letterSpacing: 0.3,
                    color: isSpotlight ? '#FFFFFF' : BRIGHT_COLORS.textPrimary,
                  }}
                >
                  {pill}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};
