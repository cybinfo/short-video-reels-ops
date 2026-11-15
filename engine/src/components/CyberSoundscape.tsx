import React from 'react';
import {Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import {EpisodeManifest, EpisodeScene} from '../types';

export interface CyberSoundscapeProps {
  manifest: EpisodeManifest;
  enabled?: boolean;
  liveLoudness?: number;
}

interface SceneSfxCue {
  file: string;
  volume: number;
  offsetFrames: number;
}

const resolveSceneCue = (
  scene: EpisodeScene,
  fromFrame: number
): SceneSfxCue | null => {
  switch (scene.kind) {
    case 'comment_spotlight':
      return {file: 'sfx/stamp-slam.wav', volume: 0.28, offsetFrames: 8};
    case 'breach_terminal':
    case 'network_attack_graph':
    case 'detective_crime_hook':
    case 'detective_wifi_clue':
      return {
        file: 'sfx/soc-alert-ping.wav',
        volume: 0.2,
        offsetFrames: fromFrame === 0 ? 6 : 0,
      };
    case 'asset_tier_matrix':
    case 'risk_heatmap':
      return {file: 'sfx/blueprint-whoosh.wav', volume: 0.22, offsetFrames: 0};
    case 'payoff_proof_card':
    case 'detective_evidence_twist':
      return {file: 'sfx/payoff-chime.wav', volume: 0.2, offsetFrames: 0};
    case 'vote_cliffhanger':
    case 'detective_suspect_board':
      return {file: 'sfx/cliffhanger-tick.wav', volume: 0.22, offsetFrames: 0};
    default:
      return null;
  }
};

export const CyberSoundscape: React.FC<CyberSoundscapeProps> = ({
  manifest,
  enabled = true,
  liveLoudness = 0.25,
}) => {
  const {fps, durationInFrames} = useVideoConfig();

  if (enabled === false) {
    return null;
  }

  const isNoir = manifest.visualTheme === 'noir_cinema';
  const safeLoud = Number.isFinite(liveLoudness)
    ? Math.min(1, Math.max(0, liveLoudness))
    : 0.25;
  const bedFile = isNoir ? 'sfx/noir-thriller-bed.wav' : 'sfx/dark-thriller-bed.wav';
  // Live voice-reactive sidechain ducking: cello bed swells in pauses (0.25) and ducks smoothly under speech (0.14)
  const bedVolume = isNoir
    ? 0.25 * (1 - safeLoud * 0.44)
    : manifest.visualTheme === 'bright_detective'
      ? 0.095
      : 0.13;
  const introDurationFrames = manifest.introSfx
    ? Math.min(
        durationInFrames,
        Math.max(1, Math.round((manifest.introSfx.durationSec ?? 3.6) * fps))
      )
    : 0;

  return (
    <>
      <Audio src={staticFile(bedFile)} loop volume={bedVolume} />

      {manifest.introSfx && introDurationFrames > 0 ? (
        <Sequence
          from={0}
          durationInFrames={introDurationFrames}
          layout="none"
        >
          <Audio
            src={staticFile(manifest.introSfx.file)}
            volume={manifest.introSfx.volume ?? 0.26}
          />
        </Sequence>
      ) : null}

      <Sequence
        from={0}
        durationInFrames={Math.min(
          durationInFrames,
          Math.max(1, Math.round(0.75 * fps))
        )}
        layout="none"
      >
        <Audio src={staticFile('sfx/cold-open-impact.wav')} volume={isNoir ? 0.28 : 0.16} />
      </Sequence>

      {manifest.scenes.map((scene) => {
        const fromFrame = Math.max(0, Math.round(scene.startSec * fps));
        const durationFrames = Math.max(
          1,
          Math.round((scene.endSec - scene.startSec) * fps)
        );
        const cue = resolveSceneCue(scene, fromFrame);

        const extraCues: Array<{key: string; file: string; offset: number; vol: number}> = [];
        if (scene.sfxCues && scene.sfxCues.length > 0) {
          scene.sfxCues.forEach((sc, idx) => {
            const rawOffset =
              sc.offsetFrames !== undefined
                ? sc.offsetFrames
                : Math.round((sc.offsetRatio ?? 0) * durationFrames);
            extraCues.push({
              key: `cue-${idx}-${sc.file}`,
              file: sc.file,
              offset: Math.max(0, rawOffset),
              vol: sc.volume ?? 0.4,
            });
          });
        } else if (isNoir && scene.kind === 'detective_suspect_board') {
          const rawOpts = scene.props.optionTimingsSec ?? [1.8, 3.0, 4.2];
          const durSec = durationFrames / fps;
          rawOpts.forEach((secVal, idx) => {
            const relSec =
              secVal > durSec || (scene.startSec > 0 && secVal >= scene.startSec)
                ? Math.max(0, secVal - scene.startSec)
                : Math.max(0, secVal);
            extraCues.push({
              key: `suspect-${idx}`,
              file: 'sfx/noir-suspect-slam.wav',
              offset: Math.max(2, Math.round(relSec * fps)),
              vol: 0.52,
            });
          });
        }

        return (
          <Sequence
            key={`sfx-${scene.id}`}
            from={fromFrame}
            durationInFrames={durationFrames}
            layout="none"
          >
            {cue && durationFrames > cue.offsetFrames ? (
              cue.offsetFrames > 0 ? (
                <Sequence
                  from={cue.offsetFrames}
                  durationInFrames={Math.max(1, durationFrames - cue.offsetFrames)}
                  layout="none"
                >
                  <Audio src={staticFile(cue.file)} volume={cue.volume} />
                </Sequence>
              ) : (
                <Audio src={staticFile(cue.file)} volume={cue.volume} />
              )
            ) : null}

            {extraCues.map((ec) =>
              durationFrames > ec.offset + 2 ? (
                ec.offset > 0 ? (
                  <Sequence
                    key={ec.key}
                    from={ec.offset}
                    durationInFrames={Math.max(1, durationFrames - ec.offset)}
                    layout="none"
                  >
                    <Audio src={staticFile(ec.file)} volume={ec.vol} />
                  </Sequence>
                ) : (
                  <Audio key={ec.key} src={staticFile(ec.file)} volume={ec.vol} />
                )
              ) : null
            )}
          </Sequence>
        );
      })}
    </>
  );
};
