#!/usr/bin/env python3
"""CLI & library entrypoint for Instagram Reels UI safe-zone & multi-shot grid mockups."""

from render_instagram_ui_mockup import (
    CAPTION_SCALE,
    CAPTION_X,
    DEFAULT_CAPTION_1,
    DEFAULT_CAPTION_2,
    MAX_CAPTION_CHARS,
    RIGHT_RAIL_X,
    build_mockup_array,
    extract_instagram_caption_lines,
    main,
    render_mockup,
    render_multi_shot_grid,
    resolve_episode_manifest,
)

__all__ = [
    "CAPTION_SCALE",
    "CAPTION_X",
    "DEFAULT_CAPTION_1",
    "DEFAULT_CAPTION_2",
    "MAX_CAPTION_CHARS",
    "RIGHT_RAIL_X",
    "build_mockup_array",
    "extract_instagram_caption_lines",
    "main",
    "render_mockup",
    "render_multi_shot_grid",
    "resolve_episode_manifest",
]

if __name__ == "__main__":
    main()
