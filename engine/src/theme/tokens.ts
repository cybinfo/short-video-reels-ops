export const VIDEO_SPECS = {
  width: 1080,
  height: 1920,
  fps: 30,
} as const;

/**
 * Instagram Reels First Priority 9:16 Safe Zone (1080x1920, centered at x = 540px):
 * - Top 0..185px: OS status bar + Instagram Reels header chrome
 * - HUD 196..282px: Live CISO Avatar Comms Bar (clear of Reels top UI)
 * - Stage 296..1276px: 940x980px stage safely inside Instagram 4:5 profile grid (y: 285..1635)
 * - Captions 1296..1468px (x: 140..940): Centered at x = 540px, clear of Reels right rail (948..1080)
 * - Bottom 1490..1920px: Account handle, caption drawer, audio ticker, progress scrubber
 */
export const SAFE_ZONE = {
  left: 70,
  right: 1010,
  top: 192,
  bottom: 1475,
  hudTop: 192,
  hudHeight: 96,
  stageTop: 296,
  stageBottom: 1276,
  captionLeft: 140,
  captionWidth: 800,
  captionTop: 1296,
  captionBottom: 1468,
  usableWidth: 940,
} as const;

export const NOIR_GRID = {
  left: 84,
  right: 996,
  width: 912,
  centerX: 540,
  hudTop: 198,
  progressTop: 274,
  stageTop: 298,
  stageHeight: 974,
} as const;

export const COLORS = {
  bgCanvas: '#060A12',
  bgPanel: '#0D1526',
  bgPanelElevated: '#131F38',
  gridLine: 'rgba(0, 240, 255, 0.065)',
  borderSubtle: 'rgba(148, 163, 184, 0.22)',
  cyan: '#00F0FF',
  cyanMuted: 'rgba(0, 240, 255, 0.16)',
  crimson: '#FF2E54',
  crimsonMuted: 'rgba(255, 46, 84, 0.18)',
  amber: '#FFB020',
  amberMuted: 'rgba(255, 176, 32, 0.18)',
  emerald: '#10B981',
  emeraldMuted: 'rgba(16, 185, 129, 0.18)',
  textPrimary: '#F8FAFC',
  textSecondary: '#CBD5E1',
  textMuted: '#7C8BA1',
} as const;

export const BRIGHT_COLORS = {
  bgCanvas: '#F8FAFC',
  bgCard: '#FFFFFF',
  bgSubtle: '#F1F5F9',
  cobalt: '#1D4ED8',
  cobaltSoft: '#DBEAFE',
  cobaltBorder: 'rgba(29, 78, 216, 0.28)',
  crimson: '#E11D48',
  crimsonSoft: '#FFE4E6',
  crimsonBorder: 'rgba(225, 29, 72, 0.32)',
  amber: '#D97706',
  amberBright: '#F59E0B',
  amberSoft: '#FEF3C7',
  amberBorder: 'rgba(217, 119, 6, 0.32)',
  saffron: '#EA580C',
  saffronSoft: '#FFEDD5',
  creamWarm: '#FFFBEB',
  emerald: '#059669',
  emeraldSoft: '#D1FAE5',
  emeraldBorder: 'rgba(5, 150, 105, 0.28)',
  textPrimary: '#0F172A',
  textSecondary: '#334155',
  textMuted: '#64748B',
  borderSubtle: '#CBD5E1',
  gridLine: 'rgba(15, 23, 42, 0.05)',
  captionBg: '#0F172A',
  captionActiveYellow: '#FACC15',
  captionEmphasisCoral: '#FB7185',
} as const;

export const FONTS = {
  display: '"SF Pro Display", "Inter", -apple-system, BlinkMacSystemFont, sans-serif',
  body: '"SF Pro Text", "Inter", -apple-system, BlinkMacSystemFont, sans-serif',
  mono: '"SF Mono", "JetBrains Mono", "Menlo", monospace',
} as const;
