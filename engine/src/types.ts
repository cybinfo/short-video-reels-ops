export type ScriptPhase =
  | 'hook'
  | 'escalation'
  | 'framework'
  | 'micro_payoff'
  | 'cliffhanger_vote';

export type SpeakerId = 'jyoti' | 'rajat' | 'narrator' | 'kabir' | (string & {});

export interface SfxCueSpec {
  file: string;
  offsetRatio?: number;
  offsetFrames?: number;
  volume?: number;
}

export interface WordTimestamp {
  word: string;
  startSec: number;
  endSec: number;
  emphasis?: boolean;
  speaker?: SpeakerId;
  peak?: number[];
}

export interface ScriptSegment {
  id: string;
  startSec: number;
  endSec: number;
  phase: ScriptPhase;
  speaker?: SpeakerId;
  narration: string;
  highlightKeywords: string[];
  ttsHindi?: string;
  ttsClauses?: Array<{
    roman: string;
    hi: string;
    speaker?: SpeakerId;
    rate?: string;
    pitch?: string;
    pauseAfter?: number;
    emotion?: string;
  }>;
}

export interface CommentSpotlightProps {
  optionPicked: 'A' | 'B' | 'C';
  percentage: number;
  voterQuote: string;
  verdictLabel: string;
  verdictTone: 'danger' | 'success' | 'warning';
}

export interface TerminalLogLine {
  time: string;
  text: string;
  level: 'info' | 'warn' | 'alert';
}

export interface BreachTerminalProps {
  windowTitle: string;
  timestamp: string;
  severity: 'CRITICAL' | 'HIGH' | 'WARNING';
  metricBadge: string;
  logLines: TerminalLogLine[];
}

export interface NetworkNode {
  id: string;
  label: string;
  sublabel: string;
  tier: 'untracked' | 'public' | 'internal' | 'restricted' | 'crown_jewel';
  compromised?: boolean;
}

export interface NetworkEdge {
  from: string;
  to: string;
  label: string;
  attackPath?: boolean;
}

export interface NetworkAttackGraphProps {
  title: string;
  subtitle: string;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export interface AssetTierRow {
  rank: number;
  name: string;
  tag: string;
  examples: string;
  blastRadius: string;
  colorTone: 'crimson' | 'amber' | 'cyan' | 'emerald';
}

export interface AssetTierMatrixProps {
  title: string;
  activeTier?: string;
  tiers: AssetTierRow[];
}

export interface RiskItemRow {
  id: string;
  asset: string;
  likelihood: 1 | 2 | 3 | 4 | 5;
  impact: 1 | 2 | 3 | 4 | 5;
  annualLoss: string;
  fixCost: string;
  action: 'MITIGATE' | 'TRANSFER' | 'ACCEPT' | 'AVOID';
}

export interface RiskHeatmapProps {
  title: string;
  budgetAvailable: string;
  items: RiskItemRow[];
}

export interface PayoffProofCardProps {
  takeawayHeadline: string;
  coreRule: string;
  realBreachName: string;
  realBreachStat: string;
  realBreachCause: string;
}

export interface VoteOptionItem {
  key: 'A' | 'B' | 'C';
  label: string;
  detail: string;
}

export interface VoteCliffhangerProps {
  crisisPrompt: string;
  countdownLabel: string;
  options: [VoteOptionItem, VoteOptionItem, VoteOptionItem];
  ctaLine: string;
  loopBridgeText: string;
}

export interface DetectiveCrimeHookProps {
  caseBadge: string;
  timeLabel: string;
  locationLabel: string;
  phoneStatus: string;
  bankAlertTitle: string;
  amountLost: string;
  shockPills: string[];
  heroImage?: string;
  secondaryImage?: string;
  tertiaryImage?: string;
  mode?: 'loss_drain' | 'suspect_unmask';
  cutRatios?: [number, number];
  scrollStopper?: {
    badge: string;
    text: string;
    tone?: 'danger' | 'emerald';
    currencyBadge?: string;
  };
  shotTitles?: [string, string, string];
  shotTags?: [string, string, string];
  shotValues?: [string, string, string];
  lockedParallax?: boolean;
  secondaryParallaxMode?: 'standard' | 'macro' | 'locked';
}

export interface DetectiveWifiClueDevice {
  name: string;
  status: string;
  suspicious: boolean;
  icon?: 'wifi' | 'phone' | 'call' | 'alert' | 'shield';
}

export interface DetectiveWifiClueProps {
  headline: string;
  subline: string;
  devices: DetectiveWifiClueDevice[];
  heroImage?: string;
  secondaryImage?: string;
  interceptBanner?: {
    badge: string;
    text: string;
    tone?: 'danger' | 'amber';
  };
  secondaryObjectPosition?: string;
  lockedParallax?: boolean;
}

export interface DetectiveEvidenceTwistProps {
  variant: 'cctv_backdoor' | 'contact_match';
  badge: string;
  headline: string;
  stepOneTitle?: string;
  stepOneTag?: string;
  stepTwoTitle?: string;
  exposedItems?: string[];
  crossedOutLabel?: string;
  matchHeadline?: string;
  matchSubline?: string;
  heroImage?: string;
  secondaryImage?: string;
  tone?: 'crimson' | 'amber' | 'emerald';
  radarPinLabel?: string;
  stepTwoTag?: string;
  ussdTilesStepOne?: string[];
  ussdTilesStepTwo?: string[];
  verdictPillLeft?: string;
  verdictPillRight?: string;
  lockedParallax?: boolean;
}

export interface DetectiveSuspectItem {
  key: 'A' | 'B' | 'C';
  name: string;
  role: string;
  clue: string;
  image?: string;
  timestampBadge?: string;
}

export interface DetectiveSuspectBoardProps {
  prompt: string;
  partBadge: string;
  suspects: DetectiveSuspectItem[];
  ctaLine: string;
  loopBridgeText?: string;
  forensicClueBar?: string;
  optionTimingsSec?: [number, number, number];
  boardMode?: 'suspect_vote' | 'next_case_vote';
  spotlightRightBadge?: string;
  followHandleLine?: string;
}

export type EpisodeScene =
  | { id: string; startSec: number; endSec: number; kind: 'comment_spotlight'; props: CommentSpotlightProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'breach_terminal'; props: BreachTerminalProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'network_attack_graph'; props: NetworkAttackGraphProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'asset_tier_matrix'; props: AssetTierMatrixProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'risk_heatmap'; props: RiskHeatmapProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'payoff_proof_card'; props: PayoffProofCardProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'vote_cliffhanger'; props: VoteCliffhangerProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'detective_crime_hook'; props: DetectiveCrimeHookProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'detective_wifi_clue'; props: DetectiveWifiClueProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'detective_evidence_twist'; props: DetectiveEvidenceTwistProps; sfxCues?: SfxCueSpec[] }
  | { id: string; startSec: number; endSec: number; kind: 'detective_suspect_board'; props: DetectiveSuspectBoardProps; sfxCues?: SfxCueSpec[] };

export interface EpisodeManifest {
  id: string;
  season: number;
  episode: number;
  totalEpisodesInSeason: number;
  seasonTitle: string;
  episodeTitle: string;
  companyName: string;
  securityDomain: string;
  visualTheme?: 'bright_detective' | 'dark_cyber' | 'noir_cinema';
  coldOpenTag?: string;
  hudPartBadge?: string;
  introSfx?: { file: string; durationSec?: number; volume?: number };
  speakerLabels?: Partial<Record<SpeakerId, string>>;
  pollBranches?: Record<string, unknown>;
  realBreachParallel: {
    incident: string;
    year: number;
    impact: string;
    lesson: string;
  };
  voiceConfig: {
    mode: 'recorded' | 'commercial_clone' | 'draft_say' | 'kokoro_neural' | 'edge_neural';
    engineLicense:
      | 'OWN_VOICE'
      | 'COMMERCIAL_API'
      | 'APACHE_2_0'
      | 'MIT'
      | 'MACOS_DRAFT'
      | 'EDGE_READ_ALOUD_PREVIEW';
    audioFile?: string;
    captionsFile?: string;
    targetWpm: number;
    azureSpeechRegion?: string;
    kokoroVoice?: string;
    kokoroVoices?: Record<string, string>;
    kokoroLang?: string;
    kokoroSpeed?: number;
    kokoroSpeeds?: Record<string, number>;
    edgeVoices?: Record<string, string>;
    edgeRates?: Record<string, string>;
    edgePitches?: Record<string, string>;
    edgeFormants?: Record<string, number>;
  };
  durationSeconds: number;
  fps: 30;
  hook: {
    openingLine: string;
    hookPattern: 'comment_callout' | 'mid_breach_timestamp' | 'contradiction_shock';
    previousVoteResult?: {
      winningOption: 'A' | 'B' | 'C';
      percentage: number;
      outcomeVerdict: string;
    };
  };
  scriptSegments: ScriptSegment[];
  scenes: EpisodeScene[];
  postCopy: {
    instagramCaption: string;
    youtubeShortsTitle: string;
    linkedinPost: string;
    pinnedCommentVote: string;
    hashtags: string[];
  };
}
