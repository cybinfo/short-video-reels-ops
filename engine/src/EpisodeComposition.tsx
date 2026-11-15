import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {AssetTierMatrix} from './components/AssetTierMatrix';
import {BreachAlertTerminal} from './components/BreachAlertTerminal';
import {CinemaAtmosphere} from './components/CinemaAtmosphere';
import {CommentSpotlightCard} from './components/CommentSpotlightCard';
import {CyberSoundscape} from './components/CyberSoundscape';
import {DetectiveCrimeHookScene} from './components/DetectiveCrimeHookScene';
import {DetectiveEvidenceTwistScene} from './components/DetectiveEvidenceTwistScene';
import {DetectiveSuspectBoardScene} from './components/DetectiveSuspectBoardScene';
import {DetectiveWifiClueScene} from './components/DetectiveWifiClueScene';
import {NetworkAttackGraph} from './components/NetworkAttackGraph';
import {PayoffProofCard} from './components/PayoffProofCard';
import {RiskAssessmentGrid} from './components/RiskAssessmentGrid';
import {SafeZoneOverlay} from './components/SafeZoneOverlay';
import {SeasonHudHeader} from './components/SeasonHudHeader';
import {VoteCliffhangerCard} from './components/VoteCliffhangerCard';
import {WordCaptions} from './components/WordCaptions';
import {BRIGHT_COLORS, COLORS, NOIR_GRID, SAFE_ZONE} from './theme/tokens';
import {EpisodeManifest, EpisodeScene, SpeakerId, WordTimestamp} from './types';

export interface EpisodeCompositionProps {
  manifest: EpisodeManifest;
  words?: WordTimestamp[];
  audioPublicPath?: string;
  showSafeZone?: boolean;
  enableSfx?: boolean;
}

interface VoiceMotionContext {
  liveLoudness: number;
  activeSpeaker: SpeakerId;
  sceneWords: WordTimestamp[];
  isNoirCinema: boolean;
  speakerLabels?: Partial<Record<SpeakerId, string>>;
  companyName?: string;
}

const computeLiveLoudness = (words: WordTimestamp[], currentSec: number): number => {
  const exactWord = words.find((w) => currentSec >= w.startSec && currentSec <= w.endSec);
  if (!exactWord) {
    return 0.04;
  }
  const t = Math.min(
    1,
    Math.max(
      0,
      (currentSec - exactWord.startSec) / Math.max(0.02, exactWord.endSec - exactWord.startSec)
    )
  );
  if (exactWord.peak && exactWord.peak.length > 0) {
    if (exactWord.peak.length === 1) {
      return Math.min(1, Math.max(0, exactWord.peak[0]));
    }
    const scaled = t * (exactWord.peak.length - 1);
    const idx = Math.min(exactWord.peak.length - 2, Math.floor(scaled));
    const frac = scaled - idx;
    const raw = exactWord.peak[idx] * (1 - frac) + exactWord.peak[idx + 1] * frac;
    return Number.isFinite(raw) ? Math.min(1, Math.max(0, raw)) : 0.45;
  }
  return 0.45 + 0.4 * Math.sin(Math.PI * t);
};

const renderScene = (
  scene: EpisodeScene,
  voiceCtx: VoiceMotionContext
): React.ReactNode => {
  switch (scene.kind) {
    case 'comment_spotlight':
      return <CommentSpotlightCard data={scene.props} />;
    case 'breach_terminal':
      return <BreachAlertTerminal data={scene.props} />;
    case 'network_attack_graph':
      return <NetworkAttackGraph data={scene.props} />;
    case 'asset_tier_matrix':
      return <AssetTierMatrix data={scene.props} />;
    case 'risk_heatmap':
      return <RiskAssessmentGrid data={scene.props} />;
    case 'payoff_proof_card':
      return <PayoffProofCard data={scene.props} />;
    case 'vote_cliffhanger':
      return <VoteCliffhangerCard data={scene.props} />;
    case 'detective_crime_hook':
      return (
        <DetectiveCrimeHookScene
          data={scene.props}
          liveLoudness={voiceCtx.liveLoudness}
          activeSpeaker={voiceCtx.activeSpeaker}
          sceneWords={voiceCtx.sceneWords}
          isNoirCinema={voiceCtx.isNoirCinema}
          speakerLabels={voiceCtx.speakerLabels}
        />
      );
    case 'detective_wifi_clue':
      return (
        <DetectiveWifiClueScene
          data={scene.props}
          liveLoudness={voiceCtx.liveLoudness}
          activeSpeaker={voiceCtx.activeSpeaker}
          sceneWords={voiceCtx.sceneWords}
          isNoirCinema={voiceCtx.isNoirCinema}
        />
      );
    case 'detective_evidence_twist':
      return (
        <DetectiveEvidenceTwistScene
          data={scene.props}
          liveLoudness={voiceCtx.liveLoudness}
          activeSpeaker={voiceCtx.activeSpeaker}
          sceneWords={voiceCtx.sceneWords}
          isNoirCinema={voiceCtx.isNoirCinema}
        />
      );
    case 'detective_suspect_board':
      return (
        <DetectiveSuspectBoardScene
          data={scene.props}
          sceneStartSec={scene.startSec}
          liveLoudness={voiceCtx.liveLoudness}
          activeSpeaker={voiceCtx.activeSpeaker}
          sceneWords={voiceCtx.sceneWords}
          isNoirCinema={voiceCtx.isNoirCinema}
          companyName={voiceCtx.companyName}
        />
      );
    default:
      return null;
  }
};

export const EpisodeComposition: React.FC<EpisodeCompositionProps> = ({
  manifest,
  words = [],
  audioPublicPath,
  showSafeZone = false,
  enableSfx = true,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const currentSec = frame / fps;
  const progress = Math.min(1, Math.max(0, frame / Math.max(1, durationInFrames - 1)));
  const isBrightTheme = manifest.visualTheme === 'bright_detective';
  const isNoirCinema = manifest.visualTheme === 'noir_cinema';

  const activeSegment = manifest.scriptSegments.find(
    (seg) => currentSec >= seg.startSec && currentSec < seg.endSec
  );

  // Resolve live active speaker ("jyoti" | "rajat") down to exact spoken clause/word timestamp
  const hasDualSpeakers =
    words.some((w) => w.speaker === 'rajat') ||
    manifest.scriptSegments.some((s) => s.speaker === 'rajat');
  let activeSpeaker: SpeakerId = activeSegment?.speaker ?? 'jyoti';
  if (words.length > 0) {
    const curWord =
      words.find(
        (w) => currentSec >= w.startSec - 0.05 && currentSec <= w.endSec + 0.16
      ) ??
      [...words]
        .reverse()
        .find((w) => w.startSec <= currentSec && currentSec - w.endSec <= 0.45);
    if (curWord?.speaker) {
      activeSpeaker = curWord.speaker;
    }
  }
  const isAlertPhase =
    !activeSegment ||
    activeSegment.phase === 'hook' ||
    activeSegment.phase === 'escalation' ||
    activeSegment.phase === 'cliffhanger_vote';

  const glowColor = isAlertPhase
    ? 'rgba(255, 46, 84, 0.16)'
    : 'rgba(0, 240, 255, 0.13)';

  const activeSceneIdx = Math.max(
    0,
    manifest.scenes.findIndex(
      (sc) => currentSec >= sc.startSec && currentSec < sc.endSec
    )
  );
  const activeScene = manifest.scenes[activeSceneIdx] ?? manifest.scenes[0];
  const liveLoudness = computeLiveLoudness(words, currentSec);
  const activeSceneWords = activeScene
    ? words.filter((w) => w.endSec > activeScene.startSec && w.startSec < activeScene.endSec)
    : [];
  const sceneStartFrame = activeScene
    ? Math.max(0, Math.round(activeScene.startSec * fps))
    : 0;
  const sceneDurFrames = activeScene
    ? Math.max(1, Math.round((activeScene.endSec - activeScene.startSec) * fps))
    : durationInFrames;
  const sceneLocalFrame = Math.max(0, frame - sceneStartFrame);
  const sceneProgress = Math.min(1, sceneLocalFrame / Math.max(1, sceneDurFrames - 1));

  // Continuous Reels camera push-in: background 1.0 -> 1.028, stage 0.976 -> 1.000 (noir_cinema uses full 1.0 stage + internal multicam zooms)
  const bgPushScale = interpolate(sceneProgress, [0, 1], [1.0, 1.028]);
  const stagePushScale = isNoirCinema ? 1.0 : interpolate(sceneProgress, [0, 1], [0.976, 1.0]);

  // 8-frame digital cyan/crimson flash transition on scene cuts
  const isSceneCutFlash = activeSceneIdx > 0 && sceneLocalFrame < 8;
  const cutFlashOpacity = isSceneCutFlash
    ? interpolate(sceneLocalFrame, [0, 1, 7], [0.2, 0.26, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;
  const cutFlashColor = isBrightTheme
    ? activeSceneIdx % 2 === 1
      ? BRIGHT_COLORS.crimson
      : BRIGHT_COLORS.cobalt
    : activeSceneIdx % 2 === 1
      ? COLORS.crimson
      : COLORS.cyan;

  const brightGlowColor = isAlertPhase
    ? 'rgba(225, 29, 72, 0.16)'
    : 'rgba(29, 78, 216, 0.14)';

  return (
    <AbsoluteFill
      style={{
        backgroundColor: isBrightTheme ? BRIGHT_COLORS.bgCanvas : COLORS.bgCanvas,
        overflow: 'hidden',
      }}
    >
      {/* Parallax Full-Bleed Base Backdrop */}
      <div
        data-ambient="true"
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 1,
          backgroundImage: isBrightTheme
            ? `
              radial-gradient(circle at 50% 26%, ${brightGlowColor} 0%, transparent 62%),
              linear-gradient(${BRIGHT_COLORS.gridLine} 1px, transparent 1px),
              linear-gradient(90deg, ${BRIGHT_COLORS.gridLine} 1px, transparent 1px)
            `
            : `
              radial-gradient(circle at 50% 28%, ${glowColor} 0%, transparent 60%),
              linear-gradient(${COLORS.gridLine} 1px, transparent 1px),
              linear-gradient(90deg, ${COLORS.gridLine} 1px, transparent 1px)
            `,
          backgroundSize: isBrightTheme
            ? '100% 100%, 44px 44px, 44px 44px'
            : '100% 100%, 48px 48px, 48px 48px',
          transform: `scale(${bgPushScale})`,
          transformOrigin: '540px 786px',
          pointerEvents: 'none',
        }}
      />

      {/* Full-Bleed Top Detective Header Wash (y: 0..290) so top chrome has zero void */}
      {isBrightTheme ? (
        <div
          data-ambient="true"
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: 1080,
            height: 290,
            zIndex: 3,
            background: isAlertPhase
              ? 'linear-gradient(180deg, rgba(225, 29, 72, 0.22) 0%, rgba(254, 226, 226, 0.55) 58%, rgba(248, 250, 252, 0) 100%)'
              : 'linear-gradient(180deg, rgba(29, 78, 216, 0.2) 0%, rgba(219, 234, 254, 0.52) 58%, rgba(248, 250, 252, 0) 100%)',
            pointerEvents: 'none',
          }}
        >
          <div
            data-ambient="true"
            style={{
              width: '100%',
              height: 12,
              background:
                'repeating-linear-gradient(135deg, #E11D48 0px, #E11D48 18px, #F59E0B 18px, #F59E0B 36px, #1D4ED8 36px, #1D4ED8 54px)',
              opacity: 0.85,
            }}
          />
        </div>
      ) : null}

      {audioPublicPath ? <Audio src={staticFile(audioPublicPath)} /> : null}
      <CyberSoundscape
        manifest={manifest}
        enabled={enableSfx}
        liveLoudness={liveLoudness}
      />

      {isNoirCinema ? (
        <CinemaAtmosphere
          liveLoudness={liveLoudness}
          loopHeroImage={
            manifest.scenes[0]?.kind === 'detective_crime_hook'
              ? manifest.scenes[0].props.tertiaryImage ??
                manifest.scenes[0].props.heroImage
              : undefined
          }
          coldOpenTag={manifest.coldOpenTag}
          seriesLabel={manifest.companyName}
          hasHookSceneCard={activeScene?.kind === 'detective_crime_hook'}
        />
      ) : null}

      {isNoirCinema ? (
        <div
          data-role="hud-header"
          style={{
            position: 'absolute',
            left: NOIR_GRID.left,
            top: NOIR_GRID.hudTop,
            width: NOIR_GRID.width,
            height: 66,
            zIndex: 10,
            boxSizing: 'border-box',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            padding: 0,
            pointerEvents: 'none',
          }}
        >
          {/* Sleek Minimal Noir Case Pill with Detective Kabir Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              minWidth: 0,
              backgroundColor: 'rgba(6, 10, 18, 0.78)',
              border: '1.5px solid rgba(250, 204, 21, 0.42)',
              borderRadius: 999,
              padding: '6px 20px 6px 8px',
              boxShadow: '0 10px 28px rgba(0, 0, 0, 0.65)',
            }}
          >
            <Img
              src={staticFile('brand/kabir-avatar.png')}
              alt=""
              style={{
                width: 42,
                height: 42,
                flexShrink: 0,
                borderRadius: '50%',
                objectFit: 'cover',
                border: '2px solid #FACC15',
                boxShadow:
                  '0 0 0 2px rgba(225, 29, 72, 0.65), 0 0 14px rgba(250, 204, 21, 0.35)',
                filter: 'sepia(0.22) contrast(1.08) saturate(1.12) brightness(0.96)',
              }}
            />
            <span
              style={{
                fontFamily: '"SF Mono", "JetBrains Mono", monospace',
                fontSize: 20,
                fontWeight: 900,
                letterSpacing: 0.5,
                color: '#F8FAFC',
                textTransform: 'uppercase',
                maxWidth: 590,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {manifest.securityDomain}
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              flexShrink: 0,
              backgroundColor: 'rgba(225, 29, 72, 0.86)',
              border: '1.5px solid rgba(255, 255, 255, 0.34)',
              borderRadius: 999,
              padding: '8px 16px',
              boxShadow: '0 8px 22px rgba(225, 29, 72, 0.42)',
            }}
          >
            <span
              style={{
                width: 9,
                height: 9,
                borderRadius: '50%',
                backgroundColor: '#FACC15',
                opacity: 0.55 + liveLoudness * 0.45,
              }}
            />
            <span
              style={{
                fontFamily: '"SF Mono", "JetBrains Mono", monospace',
                fontSize: 20,
                fontWeight: 900,
                letterSpacing: 0.5,
                color: '#FFFFFF',
                whiteSpace: 'nowrap',
              }}
            >
              {manifest.hudPartBadge ?? `PART ${manifest.episode}/${manifest.totalEpisodesInSeason}`}
            </span>
          </div>
        </div>
      ) : (
        <SeasonHudHeader
          companyName={manifest.companyName}
          season={manifest.season}
          episode={manifest.episode}
          totalEpisodes={manifest.totalEpisodesInSeason}
          domain={manifest.securityDomain}
          progress={progress}
          spoilerFlipSec={
            manifest.scriptSegments.find((s) => s.phase === 'framework')?.startSec ?? 14
          }
          cliffhangerStartSec={
            manifest.scriptSegments.find((s) => s.phase === 'cliffhanger_vote')?.startSec
          }
          activeSpeaker={activeSpeaker}
          hasDualSpeakers={hasDualSpeakers}
          isBrightTheme={isBrightTheme}
          liveLoudness={liveLoudness}
          sceneWords={activeSceneWords}
        />
      )}

      {/* Sleek Live Episode Tension Progress Bar */}
      <div
        data-ambient="true"
        style={{
          position: 'absolute',
          left: isNoirCinema ? NOIR_GRID.left : SAFE_ZONE.left,
          top: isNoirCinema ? NOIR_GRID.progressTop : 288,
          width: isNoirCinema ? NOIR_GRID.width : SAFE_ZONE.usableWidth,
          height: isNoirCinema ? 3 : 5,
          zIndex: 10,
          borderRadius: 999,
          backgroundColor: isBrightTheme
            ? 'rgba(15, 23, 42, 0.12)'
            : 'rgba(148, 163, 184, 0.22)',
          overflow: 'hidden',
          pointerEvents: 'none',
        }}
      >
        <div
          data-ambient="true"
          style={{
            width: `${progress * 100}%`,
            height: '100%',
            borderRadius: 999,
            background: isBrightTheme
              ? `linear-gradient(90deg, ${BRIGHT_COLORS.cobalt} 0%, ${BRIGHT_COLORS.amberBright} 52%, ${BRIGHT_COLORS.crimson} 100%)`
              : `linear-gradient(90deg, #FACC15 0%, #F59E0B 50%, ${COLORS.crimson} 100%)`,
            boxShadow: isBrightTheme
              ? 'none'
              : `0 0 12px ${isAlertPhase ? COLORS.crimson : '#FACC15'}`,
          }}
        />
      </div>

      {/* Stage Wrapper */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 2,
          transform: `scale(${stagePushScale})`,
          transformOrigin: '540px 786px',
        }}
      >
        {manifest.scenes.map((scene) => {
          const fromFrame = Math.max(0, Math.round(scene.startSec * fps));
          const durationFrames = Math.max(
            1,
            Math.round((scene.endSec - scene.startSec) * fps)
          );
          const sceneWords = words.filter(
            (w) => w.endSec > scene.startSec && w.startSec < scene.endSec
          );
          return (
            <Sequence
              key={scene.id}
              from={fromFrame}
              durationInFrames={durationFrames}
              layout="none"
            >
              {renderScene(scene, {
                liveLoudness,
                activeSpeaker,
                sceneWords,
                isNoirCinema,
                speakerLabels: manifest.speakerLabels,
                companyName: manifest.companyName,
              })}
            </Sequence>
          );
        })}
      </div>

      {/* 8-Frame Scene Cut Flash */}
      {cutFlashOpacity > 0 ? (
        <div
          data-ambient="true"
          style={{
            position: 'absolute',
            inset: isNoirCinema ? 0 : undefined,
            left: isNoirCinema ? undefined : SAFE_ZONE.left,
            top: isNoirCinema ? undefined : SAFE_ZONE.stageTop,
            width: isNoirCinema ? undefined : SAFE_ZONE.usableWidth,
            height: isNoirCinema ? undefined : SAFE_ZONE.stageBottom - SAFE_ZONE.stageTop,
            zIndex: 12,
            borderRadius: isNoirCinema ? 0 : 24,
            background: `linear-gradient(180deg, transparent 0%, ${cutFlashColor} 48%, transparent 100%)`,
            opacity: isBrightTheme ? cutFlashOpacity * 0.55 : cutFlashOpacity * 0.75,
            mixBlendMode: isBrightTheme ? 'normal' : 'screen',
            pointerEvents: 'none',
          }}
        />
      ) : null}

      {/* Cinema Lower Vignette for Boxless Caption Readability */}
      {isNoirCinema ? (
        <div
          data-ambient="true"
          style={{
            position: 'absolute',
            left: 0,
            top: 1180,
            width: 1080,
            height: 740,
            zIndex: 8,
            background:
              'linear-gradient(180deg, rgba(4, 7, 15, 0) 0%, rgba(4, 7, 15, 0.72) 26%, rgba(4, 7, 15, 0.92) 64%, rgba(2, 5, 12, 0.98) 100%)',
            pointerEvents: 'none',
          }}
        />
      ) : null}

      <WordCaptions
        words={words}
        segments={manifest.scriptSegments}
        isBrightTheme={isBrightTheme}
        isNoirCinema={isNoirCinema}
        liveLoudness={liveLoudness}
        activeSpeaker={activeSpeaker}
        sceneWords={activeSceneWords}
        speakerLabels={manifest.speakerLabels}
        hideSpeakerPill={activeScene?.kind === 'detective_crime_hook'}
        companyName={manifest.companyName}
      />

      {/* Full-Bleed Lower Case-File Footer Band (y: 1475..1920) or Dark Cyber Waveform (omitted in noir_cinema) */}
      {isNoirCinema ? null : isBrightTheme ? (
        <div
          data-ambient="true"
          style={{
            position: 'absolute',
            left: 0,
            top: 1475,
            width: 1080,
            height: 445,
            zIndex: 6,
            background: isAlertPhase
              ? 'linear-gradient(180deg, rgba(248, 250, 252, 0) 0%, rgba(254, 226, 226, 0.72) 28%, rgba(254, 243, 199, 0.88) 68%, rgba(226, 232, 240, 0.95) 100%)'
              : 'linear-gradient(180deg, rgba(248, 250, 252, 0) 0%, rgba(219, 234, 254, 0.72) 28%, rgba(254, 243, 199, 0.85) 68%, rgba(226, 232, 240, 0.95) 100%)',
            pointerEvents: 'none',
          }}
        >
          {/* Detective Tape Accent Strip */}
          <div
            data-ambient="true"
            style={{
              position: 'absolute',
              left: 0,
              top: 22,
              width: 1080,
              height: 14,
              background:
                'repeating-linear-gradient(135deg, rgba(245, 158, 11, 0.42) 0px, rgba(245, 158, 11, 0.42) 20px, rgba(15, 23, 42, 0.22) 20px, rgba(15, 23, 42, 0.22) 40px)',
              borderTop: '1.5px solid rgba(225, 29, 72, 0.28)',
              borderBottom: '1.5px solid rgba(29, 78, 216, 0.24)',
            }}
          />

          {/* Voice-Reactive Bright Equalizer Bars */}
          <div
            data-ambient="true"
            style={{
              position: 'absolute',
              left: 90,
              top: 62,
              width: 900,
              height: 76,
              opacity: 0.34 + liveLoudness * 0.42,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            {Array.from({length: 36}).map((_, i) => {
              const centerDist = Math.abs(i - 17.5) / 17.5;
              const envelope = 1 - centerDist * 0.46;
              const harmonic = (Math.sin(frame * 0.34 + i * 0.62) + 1) / 2;
              const barH = Math.round(
                8 + liveLoudness * (20 + 46 * envelope * (0.55 + 0.45 * harmonic))
              );
              const isRajatSpeaking = hasDualSpeakers && activeSpeaker === 'rajat';
              const col = isRajatSpeaking
                ? i % 3 === 0
                  ? BRIGHT_COLORS.cobalt
                  : i % 3 === 1
                    ? BRIGHT_COLORS.emerald
                    : BRIGHT_COLORS.amberBright
                : i % 3 === 0
                  ? BRIGHT_COLORS.crimson
                  : i % 3 === 1
                    ? BRIGHT_COLORS.amberBright
                    : BRIGHT_COLORS.cobalt;
              return (
                <span
                  key={i}
                  data-ambient="true"
                  style={{
                    width: 8,
                    height: barH,
                    borderRadius: 999,
                    backgroundColor: col,
                  }}
                />
              );
            })}
          </div>
        </div>
      ) : (
        <div
          data-ambient="true"
          style={{
            position: 'absolute',
            left: 140,
            top: 1560,
            width: 800,
            height: 60,
            opacity: 0.22,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            pointerEvents: 'none',
          }}
        >
          {Array.from({length: 32}).map((_, i) => {
            const w = (Math.sin(frame * 0.22 + i * 0.48) + 1) / 2;
            const barH = Math.round(8 + w * 44);
            return (
              <span
                key={i}
                data-ambient="true"
                style={{
                  width: 6,
                  height: barH,
                  borderRadius: 999,
                  backgroundColor: i % 3 === 0 ? COLORS.crimson : COLORS.cyan,
                }}
              />
            );
          })}
        </div>
      )}

      <SafeZoneOverlay visible={showSafeZone} />
    </AbsoluteFill>
  );
};
