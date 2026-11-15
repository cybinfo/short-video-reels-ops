import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRIGHT_COLORS, FONTS, NOIR_GRID, SAFE_ZONE } from '../theme/tokens';
import { DetectiveWifiClueDevice, DetectiveWifiClueProps, SpeakerId, WordTimestamp } from '../types';
import { NoirParallaxStage } from './NoirParallaxStage';

const DeviceVectorIcon: React.FC<{
  name: string;
  icon?: DetectiveWifiClueDevice['icon'];
  index: number;
  suspicious: boolean;
}> = ({ name, icon, index, suspicious }) => {
  const stroke = suspicious ? '#FFFFFF' : BRIGHT_COLORS.emerald;
  if (icon === 'alert' || (!icon && suspicious)) {
    return (
      <svg width="32" height="32" viewBox="0 0 32 32" style={{ display: 'block' }}>
        <rect x="4" y="4" width="14" height="24" rx="3.5" fill="none" stroke={stroke} strokeWidth="2.4" />
        <circle cx="11" cy="23.5" r="1.4" fill={stroke} />
        <path d="M16 14 C21 14, 24 11, 27 8" fill="none" stroke="#FACC15" strokeWidth="2.8" strokeLinecap="round" />
        <path d="M22 7 H27.5 V12.5" fill="none" stroke="#FACC15" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M19 21 L28 21 M25 18 L28 21 L25 24" fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (icon === 'wifi' || (!icon && /wifi|router|net|hotspot/i.test(name))) {
    return (
      <svg width="30" height="30" viewBox="0 0 30 30" style={{ display: 'block' }}>
        <path d="M4 11 C10 5.5, 20 5.5, 26 11" fill="none" stroke={stroke} strokeWidth="2.4" strokeLinecap="round" />
        <path d="M8.5 15.5 C12.2 12.2, 17.8 12.2, 21.5 15.5" fill="none" stroke={stroke} strokeWidth="2.4" strokeLinecap="round" />
        <circle cx="15" cy="21" r="2.2" fill={stroke} />
      </svg>
    );
  }
  if (icon === 'phone' || (!icon && /phone|mobile|sim|device|handset/i.test(name))) {
    return (
      <svg width="30" height="30" viewBox="0 0 30 30" style={{ display: 'block' }}>
        <rect x="8" y="3" width="14" height="24" rx="3.5" fill="none" stroke={stroke} strokeWidth="2.4" />
        <path d="M12 7 H18" stroke={stroke} strokeWidth="2" strokeLinecap="round" />
        <circle cx="15" cy="22.5" r="1.5" fill={stroke} />
      </svg>
    );
  }
  if (icon === 'shield' || (!icon && /shield|link/i.test(name))) {
    return (
      <svg width="30" height="30" viewBox="0 0 30 30" style={{ display: 'block' }}>
        <path d="M15 3 L25 7 V14.5 C25 20.5 20.5 25 15 27 C9.5 25 5 20.5 5 14.5 V7 Z" fill="none" stroke={stroke} strokeWidth="2.3" strokeLinejoin="round" />
        <path d="M11 11 L19 19 M19 11 L11 19" stroke={stroke} strokeWidth="2.4" strokeLinecap="round" />
      </svg>
    );
  }
  if (icon === 'call' || (!icon && (/call|otp|phone|clock|alert/i.test(name) || index === 2))) {
    return (
      <svg width="30" height="30" viewBox="0 0 30 30" style={{ display: 'block' }}>
        <circle cx="13.5" cy="15.5" r="9.5" fill="none" stroke={stroke} strokeWidth="2.3" />
        <path d="M13.5 10.5 V15.5 L17 17.5" fill="none" stroke={stroke} strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round" />
        <rect x="19" y="4" width="8" height="7" rx="2" fill={stroke} />
      </svg>
    );
  }
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" style={{ display: 'block' }}>
      <circle cx="13" cy="13" r="8" fill="none" stroke={stroke} strokeWidth="2.4" />
      <path d="M19 19 L26 26" stroke={stroke} strokeWidth="2.8" strokeLinecap="round" />
    </svg>
  );
};

export const DetectiveWifiClueScene: React.FC<{
  data: DetectiveWifiClueProps;
  liveLoudness?: number;
  activeSpeaker?: SpeakerId;
  sceneWords?: WordTimestamp[];
  isNoirCinema?: boolean;
}> = ({ data, liveLoudness = 0.35, isNoirCinema = false }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const safeDur = Math.max(1, durationInFrames - 1);
  const localProgress = Math.min(1, Math.max(0, frame / safeDur));
  const safeLoudness = Number.isFinite(liveLoudness) ? Math.min(1, Math.max(0, liveLoudness)) : 0.35;

  const bannerIn = spring({ frame, fps, config: { damping: 16, stiffness: 185 } });
  const cardIn = spring({
    frame: Math.max(0, frame - 4),
    fps,
    config: { damping: 16, stiffness: 175 },
  });
  const radarPulse = (Math.sin(frame * 0.18) + 1) / 2;
  const rows = data.devices.slice(0, 4);
  const rowRevealRatios = [0.06, 0.24, 0.42, 0.60];

  if (isNoirCinema && data.heroImage) {
    // 2-Angle Forensic Clue Cinema: Shot 1 Establishing Clue (0-46%) -> Shot 2 Live Signal Intercept (46-100%)
    const isMacroCut = localProgress >= 0.46;
    const activeHero = isMacroCut && data.secondaryImage ? data.secondaryImage : data.heroImage;
    const camScale = !isMacroCut
      ? interpolate(localProgress, [0, 0.46], [1.05, 1.13], { extrapolateRight: 'clamp' })
      : interpolate(localProgress, [0.46, 1], [1.06, 1.15], { extrapolateRight: 'clamp' });
    const camOrigin = isMacroCut ? '54% 46%' : '50% 44%';
    const buzzX =
      localProgress >= 0.46 && localProgress < 0.52 ? Math.sin(frame * 2.7) * 3.2 : 0;
    const handheldX = Math.sin(frame * 0.068 + 1.2) * 4 + buzzX;
    const handheldY = Math.cos(frame * 0.054 + 0.7) * 3;
    const handheldRot = Math.sin(frame * 0.044) * 0.2;
    const cutFlash = Math.abs(localProgress - 0.46) < 0.026 ? 0.34 : 0;
    const ambientFlicker =
      0.52 +
      0.24 * Math.sin(frame * 0.49) +
      0.15 * Math.sin(frame * 0.93 + 0.8) +
      0.09 * Math.cos(frame * 1.47);

    const shotProgress = !isMacroCut
      ? interpolate(localProgress, [0, 0.46], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : interpolate(localProgress, [0.46, 1], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
    const isAmberIntercept = data.interceptBanner?.tone === 'amber';
    const interceptStartFrame = Math.round(0.46 * durationInFrames);
    const interceptIn = spring({
      frame: Math.max(0, frame - interceptStartFrame),
      fps,
      config: { damping: 14, stiffness: 230, mass: 0.55 },
    });
    const pulseBarPct = Math.round(52 + radarPulse * 34 + safeLoudness * 14);

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
            objectPosition={
              isMacroCut ? (data.secondaryObjectPosition ?? '50% 38%') : '50% 38%'
            }
            handheldX={handheldX}
            handheldY={handheldY}
            handheldRot={handheldRot}
            contrast={isMacroCut ? 1.12 : 1.06}
            brightness={isMacroCut ? 0.93 + safeLoudness * 0.1 : 0.95}
            lockedParallax={data.lockedParallax}
            accentColor={
              isAmberIntercept
                ? 'rgba(56, 189, 248, 0.34)'
                : isMacroCut
                  ? 'rgba(255, 46, 84, 0.36)'
                  : 'rgba(251, 191, 36, 0.34)'
            }
          />
          <div
            data-ambient="true"
            style={{
              position: 'absolute',
              inset: 0,
              pointerEvents: 'none',
              mixBlendMode: 'screen',
              background: isAmberIntercept
                ? `radial-gradient(circle at 20% 48%, rgba(186, 230, 253, ${0.18 * ambientFlicker}) 0%, rgba(56, 189, 248, ${0.07 * ambientFlicker}) 28%, transparent 54%)`
                : `radial-gradient(circle at 28% 46%, rgba(251, 191, 36, ${0.22 * ambientFlicker}) 0%, rgba(245, 158, 11, ${0.08 * ambientFlicker}) 26%, transparent 52%)`,
            }}
          />
          {isMacroCut && Boolean(data.interceptBanner) ? (
            <svg
              data-ambient="true"
              width="1080"
              height="1920"
              viewBox="0 0 1080 1920"
              style={{ position: 'absolute', inset: 0, opacity: 0.46 }}
            >
              <circle
                cx="580"
                cy="690"
                r={95 + radarPulse * 45}
                fill="none"
                stroke="#FF2E54"
                strokeWidth="3"
              />
              <circle
                cx="580"
                cy="690"
                r={150 + radarPulse * 55}
                fill="none"
                stroke="#FACC15"
                strokeWidth="2"
                strokeDasharray="10 8"
              />
            </svg>
          ) : null}
          <div
            data-ambient="true"
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'linear-gradient(180deg, rgba(4, 7, 15, 0.86) 0%, rgba(4, 7, 15, 0.22) 24%, rgba(4, 7, 15, 0.08) 52%, rgba(4, 7, 15, 0.88) 76%, rgba(4, 7, 15, 0.97) 100%)',
            }}
          />
          {cutFlash > 0 ? (
            <div
              data-ambient="true"
              style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: '#FF2E54',
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
          {/* Top Compact Forensic Mystery Header + Live Phone Intercept Notification Pill (y ~ 308..480, keeping center y: 560..880 100% clear!) */}
          <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
            <div
              style={{
                backgroundColor: 'rgba(7, 11, 22, 0.86)',
                border: '1.5px solid rgba(56, 189, 248, 0.45)',
                borderRadius: 22,
                padding: '14px 22px',
                boxShadow: '0 14px 34px rgba(0, 0, 0, 0.72)',
                opacity: interpolate(bannerIn, [0, 1], [0, 1]),
              }}
            >
              <div
                style={{
                  fontFamily: FONTS.mono,
                  fontSize: 20,
                  fontWeight: 900,
                  letterSpacing: 0.4,
                  color: '#38BDF8',
                  marginBottom: 4,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                ● FORENSIC TRACE · {data.subline.toUpperCase()}
              </div>
              <div
                style={{
                  fontFamily: FONTS.display,
                  fontSize: data.headline.length > 32 ? 29 : 33,
                  fontWeight: 900,
                  lineHeight: 1.12,
                  color: '#F8FAFC',
                }}
              >
                {data.headline}
              </div>
            </div>

            {isMacroCut && data.interceptBanner ? (
              <div
                style={{
                  marginTop: 10,
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: 'rgba(8, 12, 24, 0.92)',
                  border: `1.5px solid ${
                    isAmberIntercept ? 'rgba(250, 204, 21, 0.78)' : 'rgba(255, 46, 84, 0.84)'
                  }`,
                  borderRadius: 18,
                  padding: '10px 18px 11px',
                  boxShadow: '0 14px 32px rgba(0, 0, 0, 0.76)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 7,
                  opacity: interpolate(interceptIn, [0, 1], [0, 1]),
                  transform: `translateY(${interpolate(interceptIn, [0, 1], [-8, 0]).toFixed(1)}px)`,
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
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 7,
                      padding: '4px 10px',
                      borderRadius: 999,
                      backgroundColor: isAmberIntercept
                        ? 'rgba(250, 204, 21, 0.2)'
                        : 'rgba(255, 46, 84, 0.24)',
                      border: isAmberIntercept
                        ? '1px solid rgba(250, 204, 21, 0.65)'
                        : '1px solid rgba(255, 46, 84, 0.68)',
                      fontFamily: FONTS.mono,
                      fontSize: 20,
                      fontWeight: 900,
                      letterSpacing: 0.3,
                      color: isAmberIntercept ? '#FDE047' : '#FECDD3',
                      whiteSpace: 'nowrap',
                      flexShrink: 0,
                    }}
                  >
                    <span
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        backgroundColor: isAmberIntercept ? '#FACC15' : '#FF2E54',
                        opacity: 0.55 + radarPulse * 0.45,
                      }}
                    />
                    {data.interceptBanner.badge}
                  </span>
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
                    {data.interceptBanner.text}
                  </span>
                </div>
                <div
                  data-ambient="true"
                  style={{
                    width: '100%',
                    height: 5,
                    borderRadius: 999,
                    backgroundColor: 'rgba(148, 163, 184, 0.2)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    data-ambient="true"
                    style={{
                      width: `${Math.min(100, pulseBarPct)}%`,
                      height: '100%',
                      borderRadius: 999,
                      background: isAmberIntercept
                        ? 'linear-gradient(90deg, #FACC15 0%, #FF2E54 100%)'
                        : 'linear-gradient(90deg, #FF2E54 0%, #FB7185 65%, #FACC15 100%)',
                    }}
                  />
                </div>
              </div>
            ) : null}
          </div>

          {/* Lower Compact Dark-Glass Clue Strips (x: 132..948 symmetric, >= 8px clear of iPhone right rail) */}
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
            {rows.map((dev, idx) => {
              const startFrame = Math.round((rowRevealRatios[idx] ?? 0.48) * durationInFrames);
              const rowIn = spring({
                frame: Math.max(0, frame - startFrame),
                fps,
                config: { damping: dev.suspicious ? 12 : 16, stiffness: 230, mass: 0.58 },
              });
              return (
                <div
                  key={`${dev.name}-${idx}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 14,
                    padding: '12px 18px',
                    borderRadius: 18,
                    backgroundColor: dev.suspicious
                      ? 'rgba(136, 19, 55, 0.9)'
                      : 'rgba(8, 13, 26, 0.86)',
                    border: dev.suspicious
                      ? '2px solid #FF2E54'
                      : '1.5px solid rgba(148, 163, 184, 0.28)',
                    boxShadow: '0 12px 28px rgba(0, 0, 0, 0.7)',
                    opacity: interpolate(rowIn, [0, 1], [0, 1]),
                    transform: `translateX(${interpolate(rowIn, [0, 1], [-5, 0], {
                      extrapolateLeft: 'clamp',
                      extrapolateRight: 'clamp',
                    })}px)`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14, flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        width: 46,
                        height: 46,
                        borderRadius: 13,
                        flexShrink: 0,
                        backgroundColor: dev.suspicious
                          ? '#E11D48'
                          : 'rgba(16, 185, 129, 0.18)',
                        border: dev.suspicious
                          ? '1.5px solid #FACC15'
                          : '1.5px solid rgba(16, 185, 129, 0.45)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <DeviceVectorIcon
                        name={dev.name}
                        icon={dev.icon}
                        index={idx}
                        suspicious={dev.suspicious}
                      />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
                      <span
                        style={{
                          fontFamily: FONTS.display,
                          fontSize: 23,
                          fontWeight: 900,
                          color: '#F8FAFC',
                          lineHeight: 1.14,
                        }}
                      >
                        {dev.name}
                      </span>
                      <span
                        style={{
                          fontFamily: FONTS.body,
                          fontSize: 20,
                          fontWeight: 800,
                          color: dev.suspicious ? '#FACC15' : '#CBD5E1',
                          lineHeight: 1.18,
                        }}
                      >
                        {dev.status}
                      </span>
                    </div>
                  </div>
                  <span
                    style={{
                      backgroundColor: dev.suspicious
                        ? '#FACC15'
                        : 'rgba(16, 185, 129, 0.2)',
                      color: dev.suspicious ? '#0F172A' : '#34D399',
                      borderRadius: 999,
                      padding: '6px 12px',
                      fontFamily: FONTS.mono,
                      fontSize: 20,
                      fontWeight: 900,
                      letterSpacing: 0.3,
                      whiteSpace: 'nowrap',
                      flexShrink: 0,
                    }}
                  >
                    {dev.suspicious ? '▲ ALERT' : '✓ CLEAR'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      {/* 100% Full-Bleed Royal-Cobalt-to-Warm-White Detective Backdrop */}
      <div
        data-ambient="true"
        style={{
          position: 'absolute',
          inset: -44,
          background: `
            radial-gradient(circle at 50% 22%, rgba(29, 78, 216, ${0.16 + safeLoudness * 0.1}) 0%, rgba(219, 234, 254, 0.76) 42%, ${BRIGHT_COLORS.bgCanvas} 82%),
            linear-gradient(${BRIGHT_COLORS.gridLine} 1px, transparent 1px),
            linear-gradient(90deg, ${BRIGHT_COLORS.gridLine} 1px, transparent 1px)
          `,
          backgroundSize: '100% 100%, 44px 44px, 44px 44px',
          pointerEvents: 'none',
        }}
      >
        <svg
          data-ambient="true"
          width="1168"
          height="2008"
          viewBox="0 0 1168 2008"
          style={{ position: 'absolute', inset: 0, opacity: 0.2 }}
        >
          <circle cx="584" cy="430" r={190 + radarPulse * 35} fill="none" stroke={BRIGHT_COLORS.cobalt} strokeWidth="2" />
          <circle cx="584" cy="430" r={330 + radarPulse * 45} fill="none" stroke={BRIGHT_COLORS.cobalt} strokeWidth="1.5" strokeDasharray="8 8" />
        </svg>
      </div>

      {/* Stage Safe-Zone Container */}
      <div
        data-role="stage-card"
        style={{
          position: 'absolute',
          left: SAFE_ZONE.left,
          top: 298,
          width: SAFE_ZONE.usableWidth,
          height: 974,
          boxSizing: 'border-box',
          padding: '16px 56px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: 16,
        }}
      >
        {/* Top Cobalt Detective Stamp Banner */}
        <div
          style={{
            background: `linear-gradient(135deg, ${BRIGHT_COLORS.cobalt} 0%, #1E3A8A 100%)`,
            borderRadius: 26, padding: '18px 26px', color: '#FFFFFF',
            boxShadow: '0 16px 36px rgba(29, 78, 216, 0.24)',
            opacity: interpolate(bannerIn, [0, 1], [0, 1]),
          }}
        >
          <div style={{ fontFamily: FONTS.mono, fontSize: 18, fontWeight: 800, letterSpacing: 1.0, color: '#FDE68A', marginBottom: 6 }}>
            ● FORENSIC AUDIT · {rows.length} KEY CLUES
          </div>
          <div style={{ fontFamily: FONTS.display, fontSize: data.headline.length > 30 ? 33 : 37, fontWeight: 900, lineHeight: 1.12, marginBottom: 6 }}>
            {data.headline}
          </div>
          <div style={{ fontFamily: FONTS.body, fontSize: 21, fontWeight: 700, color: '#DBEAFE', lineHeight: 1.22 }}>
            {data.subline}
          </div>
        </div>

        {/* Clean Step-by-Step Live Clue Timeline Card */}
        <div
          style={{
            flex: 1, backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 28,
            border: '2px solid #BFDBFE', padding: '18px 24px',
            display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            boxShadow: '0 20px 44px rgba(15, 23, 42, 0.08)',
            opacity: interpolate(cardIn, [0, 1], [0, 1]),
          }}
        >
          <div
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              paddingBottom: 10, borderBottom: `1.5px solid ${BRIGHT_COLORS.bgSubtle}`,
            }}
          >
            <span style={{ fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900, color: BRIGHT_COLORS.textPrimary, letterSpacing: 0.6 }}>
              LIVE CLUE TIMELINE
            </span>
            <span
              style={{
                backgroundColor: BRIGHT_COLORS.cobaltSoft, color: BRIGHT_COLORS.cobalt,
                borderRadius: 999, padding: '6px 16px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900,
              }}
            >
              STEP 1 → {rows.length}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 13, flex: 1, justifyContent: 'center' }}>
            {rows.map((dev, idx) => {
              const startFrame = Math.round((rowRevealRatios[idx] ?? 0.56) * durationInFrames);
              const rowIn = spring({
                frame: Math.max(0, frame - startFrame),
                fps,
                config: {
                  damping: dev.suspicious ? 12 : 16,
                  stiffness: dev.suspicious ? 240 : 195,
                  mass: 0.6,
                },
              });

              return (
                <div
                  key={`${dev.name}-${idx}`}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
                    padding: dev.suspicious ? '17px 20px' : '14px 20px', borderRadius: 22,
                    backgroundColor: dev.suspicious ? BRIGHT_COLORS.crimsonSoft : BRIGHT_COLORS.bgCanvas,
                    border: dev.suspicious ? `3px solid ${BRIGHT_COLORS.crimson}` : `1.5px solid ${BRIGHT_COLORS.borderSubtle}`,
                    boxShadow: dev.suspicious
                      ? `0 14px ${Math.round(28 + safeLoudness * 18)}px rgba(225, 29, 72, ${(0.18 + safeLoudness * 0.28).toFixed(2)})`
                      : 'none',
                    opacity: interpolate(rowIn, [0, 1], [0, 1]),
                    transform: `translateX(${interpolate(rowIn, [0, 1], [dev.suspicious ? -18 : -10, 0])}px) scale(${interpolate(rowIn, [0, 1], [0.92, 1])})`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1 }}>
                    <div
                      style={{
                        width: 56, height: 56, borderRadius: 16, flexShrink: 0,
                        backgroundColor: dev.suspicious ? BRIGHT_COLORS.crimson : BRIGHT_COLORS.emeraldSoft,
                        border: dev.suspicious ? '2px solid #FACC15' : `1.5px solid ${BRIGHT_COLORS.emeraldBorder}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}
                    >
                      <DeviceVectorIcon name={dev.name} icon={dev.icon} index={idx} suspicious={dev.suspicious} />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      <span style={{ fontFamily: FONTS.display, fontSize: dev.suspicious ? 28 : 25, fontWeight: 900, color: BRIGHT_COLORS.textPrimary, lineHeight: 1.15 }}>
                        {dev.name}
                      </span>
                      <span
                        style={{
                          fontFamily: FONTS.body, fontSize: 19, fontWeight: dev.suspicious ? 800 : 700,
                          color: dev.suspicious ? BRIGHT_COLORS.crimson : BRIGHT_COLORS.textSecondary, lineHeight: 1.2,
                        }}
                      >
                        {dev.status}
                      </span>
                    </div>
                  </div>

                  <div
                    style={{
                      backgroundColor: dev.suspicious ? BRIGHT_COLORS.crimson : BRIGHT_COLORS.emeraldSoft,
                      color: dev.suspicious ? '#FFFFFF' : BRIGHT_COLORS.emerald,
                      borderRadius: 999, padding: dev.suspicious ? '8px 16px' : '6px 14px',
                      fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, whiteSpace: 'nowrap', flexShrink: 0,
                    }}
                  >
                    {dev.suspicious ? '● ALERT' : `✓ CLUE #${idx + 1}`}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
};
