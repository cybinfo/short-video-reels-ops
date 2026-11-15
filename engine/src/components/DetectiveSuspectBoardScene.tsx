import React from 'react';
import { Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { BRIGHT_COLORS, FONTS, NOIR_GRID, SAFE_ZONE } from '../theme/tokens';
import { DetectiveSuspectBoardProps, SpeakerId, WordTimestamp } from '../types';

const SUSPECT_ACCENTS = {
  A: { solid: BRIGHT_COLORS.crimson, soft: BRIGHT_COLORS.crimsonSoft, glow: 'rgba(225, 29, 72, 0.28)' },
  B: { solid: BRIGHT_COLORS.cobalt, soft: BRIGHT_COLORS.cobaltSoft, glow: 'rgba(29, 78, 216, 0.28)' },
  C: { solid: BRIGHT_COLORS.amber, soft: BRIGHT_COLORS.amberSoft, glow: 'rgba(217, 119, 6, 0.28)' },
} as const;

const SuspectRoleIcon: React.FC<{
  suspectKey: 'A' | 'B' | 'C';
  color: string;
  revealed: boolean;
  waveAlpha: number;
}> = ({ suspectKey, color, revealed, waveAlpha }) => {
  const mainTone = revealed ? color : '#64748B';
  const skinTone = revealed ? '#FDE68A' : '#CBD5E1';
  const hairTone = revealed ? '#0F172A' : '#475569';

  if (suspectKey === 'A') {
    // Suspect Option A: Youthful Silhouette + Pulsing Hotspot Waves
    return (
      <svg width="44" height="44" viewBox="0 0 44 44" style={{ display: 'block' }}>
        <path d="M7 40 C8.5 30.5, 13.5 27.5, 20 27.5 C26.5 27.5, 31.5 30.5, 33 40 Z" fill={mainTone} />
        <path d="M16 28 L20 33 L24 28" fill="none" stroke="#FFFFFF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="20" cy="18.5" r="7.5" fill={skinTone} stroke={hairTone} strokeWidth="1.6" />
        {/* Spiky Youthful Hair */}
        <path d="M12 16 L13.5 9.5 L17 12 L20 7.5 L23 11.5 L26.5 9 L27.8 15.5 C25 13, 15 13, 12 16 Z" fill={hairTone} />
        <circle cx="17.5" cy="18.5" r="1.2" fill={hairTone} />
        <circle cx="22.5" cy="18.5" r="1.2" fill={hairTone} />
        {/* Pulsing Hotspot / Wi-Fi Waves */}
        <path d="M31 14 A6 6 0 0 1 37 8" fill="none" stroke={mainTone} strokeWidth="2.2" strokeLinecap="round" opacity={0.45 + waveAlpha * 0.55} />
        <path d="M33.5 17 A10 10 0 0 1 41 9.5" fill="none" stroke={mainTone} strokeWidth="2" strokeLinecap="round" opacity={0.3 + waveAlpha * 0.65} />
        <circle cx="32" cy="16.5" r="1.8" fill={mainTone} />
      </svg>
    );
  }
  if (suspectKey === 'B') {
    // Suspect Option B: Traditional Kurta Collar + Curved Moustache
    return (
      <svg width="44" height="44" viewBox="0 0 44 44" style={{ display: 'block' }}>
        <path d="M8 40 C9.5 30, 15 27.5, 22 27.5 C29 27.5, 34.5 30, 36 40 Z" fill={mainTone} />
        <path d="M22 28 V38" stroke="#FFFFFF" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="22" cy="18" r="8" fill={skinTone} stroke={hairTone} strokeWidth="1.6" />
        {/* Classic Side-Swept Hair */}
        <path d="M14 15.5 C15 10, 29 10, 30 15.5 C26 13.5, 18 13.5, 14 15.5 Z" fill={hairTone} />
        <circle cx="19" cy="17.5" r="1.2" fill={hairTone} />
        <circle cx="25" cy="17.5" r="1.2" fill={hairTone} />
        {/* Curved Moustache */}
        <path
          d="M15.5 21.5 C17.5 23.2, 20.5 22.5, 22 21.2 C23.5 22.5, 26.5 23.2, 28.5 21.5"
          fill="none"
          stroke={hairTone}
          strokeWidth="2.4"
          strokeLinecap="round"
        />
      </svg>
    );
  }
  // Suspect Option C: Round Spectacles + Golden Currency Badge
  return (
    <svg width="44" height="44" viewBox="0 0 44 44" style={{ display: 'block' }}>
      <path d="M7 40 C8.5 30.5, 14 27.5, 20.5 27.5 C27 27.5, 32 30.5, 33.5 40 Z" fill={mainTone} />
      <circle cx="20.5" cy="18" r="8" fill={skinTone} stroke={hairTone} strokeWidth="1.6" />
      <path d="M13 15 C14.5 9.5, 26.5 9.5, 28 15 C24 13, 17 13, 13 15 Z" fill={hairTone} />
      {/* Round Spectacles */}
      <circle cx="17.2" cy="18" r="2.7" fill="#FFFFFF" stroke={hairTone} strokeWidth="1.6" />
      <circle cx="23.8" cy="18" r="2.7" fill="#FFFFFF" stroke={hairTone} strokeWidth="1.6" />
      <line x1="19.9" y1="18" x2="21.1" y2="18" stroke={hairTone} strokeWidth="1.6" />
      {/* Rupee Coin Badge */}
      <circle cx="35" cy="13" r="6.5" fill={revealed ? '#FACC15' : '#CBD5E1'} stroke={hairTone} strokeWidth="1.4" />
      <path
        d="M32.5 10 H37.5 M32.5 12.2 H37.2 M34.5 10 C36.2 10, 36.2 13.8, 33.2 13.8 L36.8 16.5"
        fill="none"
        stroke={hairTone}
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const preventOrphanWrap = (text: string): string => text.trim().replace(/\s+(\S+)$/, '\u00A0$1');

export const DetectiveSuspectBoardScene: React.FC<{
  data: DetectiveSuspectBoardProps;
  sceneStartSec?: number;
  liveLoudness?: number;
  activeSpeaker?: SpeakerId;
  sceneWords?: WordTimestamp[];
  isNoirCinema?: boolean;
  companyName?: string;
}> = ({
  data,
  sceneStartSec = 0,
  liveLoudness = 0.35,
  sceneWords = [],
  isNoirCinema = false,
  companyName = 'SERIES',
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const localSec = frame / fps;
  const durationSec = Math.max(1, durationInFrames / fps);
  const safeLoudness = Number.isFinite(liveLoudness) ? Math.min(1, Math.max(0, liveLoudness)) : 0.35;

  const cards = data.suspects.slice(0, 3);
  const rawTimings = data.optionTimingsSec;
  let [tA, tB, tC] = [durationSec * 0.16, durationSec * 0.36, durationSec * 0.56];

  if (rawTimings && rawTimings.length === 3) {
    const isAbsolute = rawTimings[0] > durationSec || (sceneStartSec > 0 && rawTimings[0] >= sceneStartSec);
    tA = Math.max(0, isAbsolute ? rawTimings[0] - sceneStartSec : rawTimings[0]);
    tB = Math.max(tA + 0.25, isAbsolute ? rawTimings[1] - sceneStartSec : rawTimings[1]);
    tC = Math.max(tB + 0.25, isAbsolute ? rawTimings[2] - sceneStartSec : rawTimings[2]);
  } else if (sceneWords.length > 0 && cards.length === 3) {
    const matched = cards.map((s) => {
      const firstToken = s.name.split(/[\s(]+/)[0]?.toLowerCase().replace(/[^a-z0-9]/g, '') ?? '';
      if (firstToken.length < 3) return undefined;
      const hit = sceneWords.find((w) => w.word.toLowerCase().replace(/[^a-z0-9]/g, '').includes(firstToken));
      return hit ? Math.max(0, hit.startSec - sceneStartSec) : undefined;
    });
    if (matched[0] !== undefined && matched[1] !== undefined && matched[2] !== undefined) {
      tA = matched[0];
      tB = Math.max(tA + 0.25, matched[1]);
      tC = Math.max(tB + 0.25, matched[2]);
    }
  }
  const cHoldSec = Math.max(1.68, Math.min(2.45, tC - tB));
  const allVoteSec = Math.min(durationSec * 0.88, tC + cHoldSec);

  const headerIn = spring({ frame, fps, config: { damping: 16, stiffness: 185 } });
  const ctaIn = spring({ frame: Math.max(0, frame - 14), fps, config: { damping: 15, stiffness: 195 } });
  const pulse = (Math.sin(frame * 0.2) + 1) / 2;
  const balancedCta = preventOrphanWrap(data.ctaLine);
  const ctaFontSize = data.ctaLine.length > 46 ? 22 : data.ctaLine.length > 36 ? 25 : 28;
  const revealTimes = [tA, tB, tC];

  if (isNoirCinema && cards.some((c) => Boolean(c.image))) {
    const isNextCaseVote = data.boardMode === 'next_case_vote';
    const noirAccents = {
      A: { border: '#FF2E54', badge: '#E11D48', glow: 'rgba(255, 46, 84, 0.55)' },
      B: { border: '#38BDF8', badge: '#0284C7', glow: 'rgba(56, 189, 248, 0.5)' },
      C: { border: '#FACC15', badge: '#D97706', glow: 'rgba(250, 204, 21, 0.55)' },
    } as const;

    // Full-screen single-suspect shutter spotlight while each suspect is introduced (tA .. allVoteSec)
    const spotlightIdx =
      localSec >= tA && localSec < allVoteSec
        ? localSec < tB
          ? 0
          : localSec < tC
            ? 1
            : 2
        : -1;
    const activeSpotCard = spotlightIdx >= 0 ? cards[spotlightIdx] : undefined;
    const spotStartSec = spotlightIdx >= 0 ? (revealTimes[spotlightIdx] ?? tA) : 0;
    const spotAgeSec = Math.max(0, localSec - spotStartSec);
    const shutterFlash =
      (spotlightIdx >= 0 && spotAgeSec < 0.14) || Math.abs(localSec - allVoteSec) < 0.07
        ? interpolate(spotAgeSec, [0, 0.14], [0.46, 0], { extrapolateRight: 'clamp' }) || 0.34
        : 0;

    if (activeSpotCard && activeSpotCard.image) {
      const spAcc = noirAccents[activeSpotCard.key] ?? noirAccents.A;
      const spZoom = interpolate(spotAgeSec, [0, 2.2], [1.04, 1.14], { extrapolateRight: 'clamp' });
      return (
        <>
          <div data-ambient="true" style={{ position: 'absolute', inset: 0, overflow: 'hidden', backgroundColor: '#040710', pointerEvents: 'none' }}>
            <Img
              key={activeSpotCard.image}
              data-ambient="true"
              src={staticFile(activeSpotCard.image)}
              alt=""
              style={{
                position: 'absolute', inset: 0, width: '100%', height: '100%',
                objectFit: 'cover', objectPosition: '50% 50%',
                transform: `scale(${spZoom})`, transformOrigin: '50% 36.5%',
                filter: `contrast(1.1) brightness(${0.96 + safeLoudness * 0.08})`,
              }}
            />
            <div
              data-ambient="true"
              style={{
                position: 'absolute', inset: 0,
                background: 'linear-gradient(180deg, rgba(4, 7, 15, 0.82) 0%, rgba(4, 7, 15, 0.12) 26%, rgba(4, 7, 15, 0.08) 56%, rgba(4, 7, 15, 0.9) 78%, rgba(4, 7, 15, 0.98) 100%)',
              }}
            />
            {shutterFlash > 0 ? (
              <div data-ambient="true" style={{ position: 'absolute', inset: 0, backgroundColor: '#FFFFFF', opacity: shutterFlash, mixBlendMode: 'screen' }} />
            ) : null}
          </div>

          <div
            data-role="stage-card"
            style={{
              position: 'absolute', left: NOIR_GRID.left, top: NOIR_GRID.stageTop, width: NOIR_GRID.width, height: NOIR_GRID.stageHeight,
              boxSizing: 'border-box', padding: '10px 0 12px 0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <span style={{ backgroundColor: spAcc.badge, border: '2px solid #FFFFFF', color: '#FFFFFF', borderRadius: 14, padding: '8px 18px', fontFamily: FONTS.display, fontSize: 24, fontWeight: 900, whiteSpace: 'nowrap' }}>
                {isNextCaseVote
                  ? `${activeSpotCard.timestampBadge ?? `CASE ${activeSpotCard.key}`} · NEXT MYSTERY`
                  : `${data.forensicClueBar ? 'SUSPECT' : 'OPTION'} ${activeSpotCard.key} · ${activeSpotCard.timestampBadge ?? activeSpotCard.role}`}
              </span>
              <span style={{ backgroundColor: 'rgba(6, 10, 20, 0.88)', border: '1.5px solid #FACC15', color: '#FACC15', borderRadius: 999, padding: '7px 15px', fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900, letterSpacing: 0.4, whiteSpace: 'nowrap', flexShrink: 0 }}>
                {data.spotlightRightBadge ?? data.partBadge}
              </span>
            </div>

            <div
              style={{
                width: 816,
                margin: '0 auto',
                boxSizing: 'border-box',
                backgroundColor: 'rgba(8, 13, 26, 0.92)',
                borderRadius: 24,
                border: `2.5px solid ${spAcc.border}`,
                padding: '18px 24px',
                boxShadow: `0 18px 42px ${spAcc.glow}`,
              }}
            >
              <div style={{ fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900, letterSpacing: 0.4, color: spAcc.border, marginBottom: 4 }}>
                {`● ${activeSpotCard.role.toUpperCase()}`}
              </div>
              <div style={{ fontFamily: FONTS.display, fontSize: 40, fontWeight: 900, lineHeight: 1.08, color: '#FFFFFF', marginBottom: 6 }}>
                {activeSpotCard.name}
              </div>
              <div style={{ fontFamily: FONTS.display, fontSize: 24, fontWeight: 800, color: '#FEF08A' }}>
                {activeSpotCard.clue}
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
            position: 'absolute', inset: 0, overflow: 'hidden', backgroundColor: '#040710', pointerEvents: 'none',
            backgroundImage: 'radial-gradient(circle at 50% 35%, rgba(225, 29, 72, 0.24) 0%, rgba(7, 11, 24, 0.95) 62%, #03050C 100%)',
          }}
        >
          {shutterFlash > 0 ? (
            <div data-ambient="true" style={{ position: 'absolute', inset: 0, backgroundColor: '#FACC15', opacity: shutterFlash, mixBlendMode: 'screen' }} />
          ) : null}
        </div>

        <div
          data-role="stage-card"
          style={{
            position: 'absolute', left: NOIR_GRID.left, top: NOIR_GRID.stageTop, width: NOIR_GRID.width, height: NOIR_GRID.stageHeight,
            boxSizing: 'border-box', padding: '8px 0 10px 0', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', gap: 12,
          }}
        >
          {/* Top Suspect Lineup Header + Solvable Forensic Clue */}
          <div
            style={{
              backgroundColor: 'rgba(8, 13, 26, 0.92)', borderRadius: 20, border: '1.5px solid rgba(255, 46, 84, 0.62)',
              padding: '10px 18px', display: 'flex', flexDirection: 'column', gap: 6,
              opacity: interpolate(headerIn, [0, 1], [0, 1]),
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div style={{ fontFamily: FONTS.display, fontSize: data.prompt.length > 23 ? 25 : 28, fontWeight: 900, lineHeight: 1.08, color: '#FFFFFF', minWidth: 0 }}>
                {data.prompt}
              </div>
              <div
                style={{
                  backgroundColor: '#E11D48',
                  border: '1.5px solid #FACC15',
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
                {`${data.followHandleLine?.match(/@[A-Za-z0-9_.]+/)?.[0]?.toUpperCase() ?? companyName.toUpperCase()} · ${data.partBadge}`}
              </div>
            </div>
            {data.forensicClueBar ? (
              <div style={{ backgroundColor: 'rgba(250, 204, 21, 0.14)', border: '1px solid rgba(250, 204, 21, 0.55)', borderRadius: 10, padding: '5px 10px', fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900, letterSpacing: 0.3, lineHeight: 1.15, color: '#FACC15' }}>
                {`▲ ${data.forensicClueBar}`}
              </div>
            ) : null}
          </div>

          {/* 3 Vertical Character Portrait Cards Side-by-Side (strictly above y = 1000 right-rail boundary) */}
          <div style={{ display: 'flex', gap: 15, height: 540 }}>
            {cards.map((s, idx) => {
              const acc = noirAccents[s.key] ?? noirAccents.A;
              const revSec = revealTimes[idx] ?? 0;
              const revealed = localSec >= revSec;
              const revSpring = spring({
                frame: revealed ? Math.max(0, frame - Math.round(revSec * fps)) : 0,
                fps,
                config: { damping: 14, stiffness: 260, mass: 0.55 },
              });
              const allActive = localSec >= allVoteSec;
              const seqActive =
                !allActive &&
                ((idx === 0 && localSec >= tA && localSec < tB) ||
                  (idx === 1 && localSec >= tB && localSec < tC) ||
                  (idx === 2 && localSec >= tC && localSec < allVoteSec));
              const active = seqActive || allActive;

              return (
                <div
                  key={s.key}
                  style={{
                    flex: 1, position: 'relative', borderRadius: 22, overflow: 'hidden',
                    backgroundColor: '#0B1222',
                    border: `${active ? 3 : 2}px solid ${revealed ? acc.border : 'rgba(148, 163, 184, 0.25)'}`,
                    boxShadow: active ? `0 16px 34px ${acc.glow}` : '0 10px 24px rgba(0, 0, 0, 0.7)',
                    transform: `scale(${revealed ? interpolate(revSpring, [0, 1], [0.95, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) : 0.96})`,
                  }}
                >
                  {s.image ? (
                    <Img
                      src={staticFile(s.image)}
                      alt=""
                      style={{
                        position: 'absolute', inset: 0, width: '100%', height: '100%',
                        objectFit: 'cover', objectPosition: '50% 50%',
                        filter: revealed
                          ? 'brightness(1.06) contrast(1.08)'
                          : 'brightness(0.44) contrast(1.14) saturate(0.38)',
                      }}
                    />
                  ) : null}
                  <div
                    data-ambient="true"
                    style={{
                      position: 'absolute', inset: 0,
                      background: 'linear-gradient(180deg, rgba(4, 7, 15, 0.35) 0%, rgba(4, 7, 15, 0) 32%, rgba(4, 7, 15, 0.88) 64%, rgba(4, 7, 15, 0.98) 100%)',
                    }}
                  />
                  {/* Top Letter + Timestamp Pill */}
                  <div
                    style={{
                      position: 'absolute', left: 8, top: 8,
                      boxSizing: 'border-box',
                      backgroundColor: revealed ? acc.badge : 'rgba(15, 23, 42, 0.88)',
                      border: `2px solid ${revealed ? '#FFFFFF' : 'rgba(148, 163, 184, 0.45)'}`,
                      color: '#FFFFFF', borderRadius: 12, padding: '3px 8px',
                      fontFamily: FONTS.display, fontSize: 20, fontWeight: 900,
                      letterSpacing: 0.2, lineHeight: 1.12,
                      maxWidth: 'calc(100% - 16px)',
                    }}
                  >
                    {revealed
                      ? isNextCaseVote && s.timestampBadge
                        ? s.timestampBadge
                        : `${s.key} · ${s.timestampBadge ?? s.role}`
                      : `${s.key} · ?`}
                  </div>

                  {/* Normalized Bottom Character Block (minHeight alignment so A, B, C titles share exact baseline) */}
                  <div
                    style={{
                      position: 'absolute',
                      left: 8,
                      right: 8,
                      bottom: 10,
                      minHeight: 162,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'flex-start',
                      gap: 6,
                    }}
                  >
                    <span
                      style={{
                        alignSelf: 'flex-start',
                        maxWidth: '100%',
                        minHeight: 30,
                        boxSizing: 'border-box',
                        display: 'inline-flex',
                        alignItems: 'center',
                        backgroundColor: 'rgba(15, 23, 42, 0.94)',
                        border: `1.5px solid ${acc.border}`,
                        color: acc.border,
                        borderRadius: 14,
                        padding: '3px 8px',
                        fontFamily: FONTS.mono,
                        fontSize: 20,
                        fontWeight: 900,
                        letterSpacing: 0.4,
                        lineHeight: 1.15,
                      }}
                    >
                      {s.role}
                    </span>
                    <div
                      style={{
                        minHeight: 54,
                        fontFamily: FONTS.display,
                        fontSize: 24,
                        fontWeight: 900,
                        lineHeight: 1.08,
                        color: '#FFFFFF',
                      }}
                    >
                      {s.name}
                    </div>
                    <div
                      style={{
                        minHeight: 62,
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        backgroundColor: 'rgba(15, 23, 42, 0.92)',
                        borderLeft: `3px solid ${acc.border}`,
                        borderRadius: 8,
                        padding: '5px 8px',
                        fontFamily: FONTS.display,
                        fontSize: 20,
                        fontWeight: 800,
                        lineHeight: 1.14,
                        color: '#FEF08A',
                      }}
                    >
                      {s.clue}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Clean 3-Equal-Third Accent Divider + Comment CTA (x: 132..948 symmetric, >= 8px clear of right rail) */}
          <div
            style={{
              width: 816,
              margin: '4px auto 0 auto',
              boxSizing: 'border-box',
              backgroundColor: 'rgba(8, 13, 26, 0.92)',
              borderRadius: 20,
              border: `2px solid ${pulse > 0.5 ? '#FACC15' : '#FF2E54'}`,
              padding: '12px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              opacity: interpolate(ctaIn, [0, 1], [0, 1]),
            }}
          >
            <div style={{ display: 'flex', height: 8, borderRadius: 999, overflow: 'hidden', gap: 6 }}>
              <div data-ambient="true" style={{ flex: 1, backgroundColor: '#FF2E54', borderRadius: 999 }} />
              <div data-ambient="true" style={{ flex: 1, backgroundColor: '#38BDF8', borderRadius: 999 }} />
              <div data-ambient="true" style={{ flex: 1, backgroundColor: '#FACC15', borderRadius: 999 }} />
            </div>
            <div style={{ fontFamily: FONTS.display, fontSize: 24, fontWeight: 900, lineHeight: 1.16, color: '#FFFFFF', textAlign: 'center' }}>
              {balancedCta}
            </div>
            <div style={{ fontFamily: FONTS.mono, fontSize: 20, fontWeight: 900, color: '#FACC15', letterSpacing: 0.4, lineHeight: 1.15, textAlign: 'center' }}>
              {data.followHandleLine ??
                (isNextCaseVote
                  ? `NEXT CASE KE LIYE FOLLOW ${companyName.toUpperCase()}`
                  : `NEXT PART KE LIYE FOLLOW ${companyName.toUpperCase()}`)}
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
          background: `radial-gradient(circle at 50% 22%, rgba(254, 243, 199, 0.92) 0%, #FFFBEB 48%, ${BRIGHT_COLORS.bgCanvas} 90%), linear-gradient(${BRIGHT_COLORS.gridLine} 1px, transparent 1px), linear-gradient(90deg, ${BRIGHT_COLORS.gridLine} 1px, transparent 1px)`,
          backgroundSize: '100% 100%, 44px 44px, 44px 44px',
        }}
      >
        <svg data-ambient="true" width="1168" height="2008" viewBox="0 0 1168 2008" style={{ position: 'absolute', inset: 0, opacity: 0.3 }}>
          <line x1="120" y1="240" x2="584" y2="540" stroke={BRIGHT_COLORS.crimson} strokeWidth="2.5" />
          <line x1="1048" y1="260" x2="584" y2="540" stroke={BRIGHT_COLORS.crimson} strokeWidth="2.5" />
          <line x1="584" y1="540" x2="210" y2="1560" stroke={BRIGHT_COLORS.crimson} strokeWidth="2" strokeDasharray="8 6" />
          <line x1="584" y1="540" x2="960" y2="1560" stroke={BRIGHT_COLORS.crimson} strokeWidth="2" strokeDasharray="8 6" />
          <circle cx="584" cy="540" r="8" fill={BRIGHT_COLORS.crimson} />
        </svg>
      </div>

      <div
        data-role="stage-card"
        style={{
          position: 'absolute', left: SAFE_ZONE.left, top: 298, width: SAFE_ZONE.usableWidth, height: 974,
          boxSizing: 'border-box', padding: '16px 56px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        }}
      >
        {/* Top Detective Pinboard Header */}
        <div
          style={{
            backgroundColor: BRIGHT_COLORS.bgCard, borderRadius: 24,
            border: `2.5px solid ${BRIGHT_COLORS.crimson}`, padding: '16px 24px',
            boxShadow: '0 14px 32px rgba(15, 23, 42, 0.08)',
            opacity: interpolate(headerIn, [0, 1], [0, 1]),
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <span
              style={{
                backgroundColor: BRIGHT_COLORS.crimson, color: '#FFFFFF', borderRadius: 999,
                padding: '5px 15px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, letterSpacing: 0.7,
              }}
            >
              ● 3 SUSPECTS · CASE LINEUP
            </span>
            <span
              style={{
                backgroundColor: BRIGHT_COLORS.cobalt, color: '#FFFFFF', borderRadius: 999,
                padding: '5px 15px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900, letterSpacing: 0.6,
              }}
            >
              {data.partBadge}
            </span>
          </div>
          <div style={{ fontFamily: FONTS.display, fontSize: data.prompt.length > 26 ? 34 : 39, fontWeight: 900, lineHeight: 1.12, color: BRIGHT_COLORS.textPrimary }}>
            {data.prompt}
          </div>
        </div>

        {/* 3 Voice-Revealed Suspect Dossier Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {cards.map((s, idx) => {
            const accent = SUSPECT_ACCENTS[s.key] ?? SUSPECT_ACCENTS.A;
            const revealSec = revealTimes[idx] ?? 0;
            const isRevealed = localSec >= revealSec;
            const revealFrame = Math.round(revealSec * fps);
            const revealSpring = spring({
              frame: isRevealed ? Math.max(0, frame - revealFrame) : 0,
              fps,
              config: { damping: 13, stiffness: 240, mass: 0.6 },
            });

            const allActive = localSec >= allVoteSec;
            const isSequentialActive =
              !allActive &&
              ((idx === 0 && localSec >= tA && localSec < tB) ||
                (idx === 1 && localSec >= tB && localSec < tC) ||
                (idx === 2 && localSec >= tC && localSec < allVoteSec));
            const isHighlighted = isSequentialActive || allActive;

            const cardOpacity = isRevealed ? interpolate(revealSpring, [0, 1], [0.34, 1]) : 0.34;
            const cardScale = isRevealed ? interpolate(revealSpring, [0, 0.55, 1], [0.95, 1.01, 1]) : 0.98;
            const glowBlur = Math.round(26 + safeLoudness * 18);

            return (
              <div
                key={s.key}
                style={{
                  backgroundColor: isRevealed ? BRIGHT_COLORS.bgCard : '#F1F5F9',
                  borderRadius: 24,
                  border: isHighlighted
                    ? `3px solid ${accent.solid}`
                    : isRevealed
                      ? `2px solid ${accent.solid}`
                      : '2px dashed #CBD5E1',
                  padding: '15px 20px', display: 'flex', alignItems: 'center', gap: 16,
                  boxShadow: isHighlighted
                    ? `0 14px ${glowBlur}px ${accent.glow}`
                    : isRevealed
                       ? '0 10px 22px rgba(15, 23, 42, 0.08)'
                      : 'none',
                  opacity: cardOpacity,
                  transform: `scale(${cardScale})`,
                }}
              >
                {/* 64x64 Illustrated Character Avatar Badge + Option Letter Pill */}
                <div style={{ position: 'relative', width: 64, height: 64, flexShrink: 0 }}>
                  <div
                    style={{
                      width: 64, height: 64, borderRadius: 18,
                      backgroundColor: isRevealed ? accent.soft : '#E2E8F0',
                      border: `2.5px solid ${isRevealed ? accent.solid : '#94A3B8'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      boxSizing: 'border-box',
                    }}
                  >
                    <SuspectRoleIcon suspectKey={s.key} color={accent.solid} revealed={isRevealed} waveAlpha={safeLoudness} />
                  </div>
                  <div
                    style={{
                      position: 'absolute', left: -6, top: -6, width: 30, height: 30, borderRadius: 9,
                      backgroundColor: isRevealed ? accent.solid : '#64748B', color: '#FFFFFF',
                      border: '2px solid #FFFFFF',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: FONTS.display, fontSize: 18, fontWeight: 900,
                    }}
                  >
                    {s.key}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 5, flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontFamily: FONTS.display, fontSize: 28, fontWeight: 900, color: BRIGHT_COLORS.textPrimary, lineHeight: 1.14 }}>
                        {s.name}
                      </span>
                      {isSequentialActive ? (
                        <span
                          style={{
                            backgroundColor: accent.solid, color: '#FFFFFF', borderRadius: 999,
                            padding: '3px 10px', fontFamily: FONTS.mono, fontSize: 18, fontWeight: 900,
                          }}
                        >
                          ● ACTIVE
                        </span>
                      ) : null}
                    </div>
                    <span
                      style={{
                        backgroundColor: isRevealed ? accent.soft : '#E2E8F0',
                        color: isRevealed ? accent.solid : '#64748B',
                        borderRadius: 999, padding: '5px 14px',
                        fontFamily: FONTS.mono, fontSize: 18, fontWeight: 800, whiteSpace: 'nowrap',
                      }}
                    >
                      {s.role}
                    </span>
                  </div>

                  <div style={{ fontFamily: FONTS.body, fontSize: 20, fontWeight: 700, color: BRIGHT_COLORS.textSecondary, lineHeight: 1.22 }}>
                    {s.clue}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Balanced Single/Even-Line CTA Banner */}
        <div
          style={{
            background: `linear-gradient(90deg, ${BRIGHT_COLORS.crimson} 0%, ${BRIGHT_COLORS.saffron} 100%)`,
            borderRadius: 22, padding: '16px 24px', textAlign: 'center',
            border: `2.5px solid ${pulse > 0.5 ? '#FACC15' : '#FFFFFF'}`,
            boxShadow: `0 14px ${Math.round(28 + safeLoudness * 14)}px rgba(225, 29, 72, 0.28)`,
            opacity: interpolate(ctaIn, [0, 1], [0, 1]),
          }}
        >
          <div style={{ fontFamily: FONTS.display, fontSize: ctaFontSize, fontWeight: 900, lineHeight: 1.2, color: '#FFFFFF', textWrap: 'balance' }}>
            {balancedCta}
          </div>
        </div>
      </div>
    </>
  );
};
