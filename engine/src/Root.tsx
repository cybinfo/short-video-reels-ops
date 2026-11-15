import React from 'react';
import {Composition, Folder} from 'remotion';
import {EpisodeComposition, EpisodeCompositionProps} from './EpisodeComposition';
import {CAPTIONS_BY_ID, EPISODES} from './generated/episodeRegistry';
import {VIDEO_SPECS} from './theme/tokens';
import type {EpisodeManifest} from './types';

const FALLBACK_MANIFEST: EpisodeManifest = {
  id: 's00e00-dynamic-placeholder',
  season: 0,
  episode: 0,
  totalEpisodesInSeason: 1,
  seasonTitle: 'Dynamic Builder',
  episodeTitle: 'Dynamic Episode Placeholder',
  companyName: 'Cyber Jasoos',
  securityDomain: 'Cyber Investigation',
  realBreachParallel: {
    incident: 'Dynamic CLI composition placeholder',
    year: 2026,
    impact: 'Preview only',
    lesson: 'Verify runtime props',
  },
  visualTheme: 'noir_cinema',
  coldOpenTag: 'DYNAMIC BUILDER',
  hudPartBadge: 'PREVIEW',
  voiceConfig: {
    mode: 'draft_say',
    engineLicense: 'MACOS_DRAFT',
    targetWpm: 165,
  },
  durationSeconds: 50,
  fps: 30,
  hook: {
    openingLine: 'Dynamic episode placeholder hook line.',
    hookPattern: 'mid_breach_timestamp',
  },
  scriptSegments: [],
  scenes: [],
  postCopy: {
    instagramCaption: '',
    youtubeShortsTitle: 'Dynamic Placeholder',
    linkedinPost: '',
    pinnedCommentVote: 'A / B / C',
    hashtags: ['#CyberJasoos', '#CyberSecurity', '#StaySafe', '#DigitalSafety'],
  },
};

const EpisodeWrapper: React.FC<Record<string, unknown>> = (props) => {
  return <EpisodeComposition {...(props as unknown as EpisodeCompositionProps)} />;
};

export const RemotionRoot: React.FC = () => {
  const seasons = Array.from(new Set(EPISODES.map((ep) => ep.season))).sort((a, b) => a - b);
  const defaultDynamicManifest = EPISODES[0] ?? FALLBACK_MANIFEST;

  return (
    <>
      {seasons.map((season) => {
        const folderName = `Season-${String(season).padStart(2, '0')}`;
        const seasonEpisodes = EPISODES.filter((ep) => ep.season === season);
        return (
          <Folder key={folderName} name={folderName}>
            {seasonEpisodes.map((ep) => (
              <Composition
                key={ep.id}
                id={ep.id}
                component={EpisodeWrapper}
                durationInFrames={Math.round(ep.durationSeconds * VIDEO_SPECS.fps)}
                fps={VIDEO_SPECS.fps}
                width={VIDEO_SPECS.width}
                height={VIDEO_SPECS.height}
                defaultProps={{
                  manifest: ep,
                  words: CAPTIONS_BY_ID[ep.id] ?? [],
                  audioPublicPath: `audio/${ep.id}.wav`,
                  showSafeZone: false,
                }}
              />
            ))}
          </Folder>
        );
      })}

      <Folder name="Dynamic-Builder">
        <Composition
          id="dynamic-episode"
          component={EpisodeWrapper}
          durationInFrames={1500}
          fps={VIDEO_SPECS.fps}
          width={VIDEO_SPECS.width}
          height={VIDEO_SPECS.height}
          defaultProps={{
            manifest: defaultDynamicManifest,
            words: EPISODES[0] ? (CAPTIONS_BY_ID[EPISODES[0].id] ?? []) : [],
            audioPublicPath: EPISODES[0]
              ? (EPISODES[0].voiceConfig?.audioFile ?? `audio/${EPISODES[0].id}.wav`)
              : '',
            showSafeZone: false,
          }}
          calculateMetadata={({props}) => {
            const typed = props as unknown as Partial<EpisodeCompositionProps>;
            const durSec = Number(typed?.manifest?.durationSeconds ?? EPISODES[0]?.durationSeconds ?? 50);
            return {
              durationInFrames: Math.max(1, Math.round(durSec * VIDEO_SPECS.fps)),
              fps: VIDEO_SPECS.fps,
              width: VIDEO_SPECS.width,
              height: VIDEO_SPECS.height,
            };
          }}
        />
      </Folder>

      {EPISODES.length > 0 ? (
        <Folder name="QA-Safe-Zone-Check">
          <Composition
            id="qa-safezone-s01e01"
            component={EpisodeWrapper}
            durationInFrames={Math.round(EPISODES[0].durationSeconds * VIDEO_SPECS.fps)}
            fps={VIDEO_SPECS.fps}
            width={VIDEO_SPECS.width}
            height={VIDEO_SPECS.height}
            defaultProps={{
              manifest: EPISODES[0],
              words: CAPTIONS_BY_ID[EPISODES[0].id] ?? [],
              audioPublicPath: `audio/${EPISODES[0].id}.wav`,
              showSafeZone: true,
            }}
          />
        </Folder>
      ) : null}
    </>
  );
};
