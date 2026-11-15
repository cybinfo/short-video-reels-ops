import React from 'react';
import {Composition, Folder} from 'remotion';
import {EpisodeComposition, EpisodeCompositionProps} from './EpisodeComposition';
import {CAPTIONS_BY_ID, EPISODES} from './generated/episodeRegistry';
import {VIDEO_SPECS} from './theme/tokens';

const EpisodeWrapper: React.FC<Record<string, unknown>> = (props) => {
  return <EpisodeComposition {...(props as unknown as EpisodeCompositionProps)} />;
};

export const RemotionRoot: React.FC = () => {
  const seasons = Array.from(new Set(EPISODES.map((ep) => ep.season))).sort((a, b) => a - b);

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
