// src/entities/index.ts
import { makeEntity } from './_factory';

/** Core */
export const VideoProject = makeEntity<{
  title: string;
  topic: string;
  script?: string;
  scenes?: string; // JSON
  status?:
    | 'idea'
    | 'scripting'
    | 'storyboard'
    | 'production'
    | 'rendering'
    | 'post_production'
    | 'completed'
    | 'published';
  channel_id?: string;
  target_length?: number;
  video_url?: string;
  thumbnail_url?: string;
  thumbnail_preview_url?: string;
  storage_location?: 'local' | 'cloud' | 'archived';
  file_size_mb?: number;
  avatar_generation_id?: string;
  audio_tracks?: string; // JSON
  visual_assets?: string; // JSON
  rendering_settings?: string; // JSON
  seo_metadata?: string; // JSON
  performance_metrics?: string; // JSON
  revision_history?: string; // JSON
}>('VideoProject');

export const Job = makeEntity<{
  title: string;
  started_at: number;
  total_steps: number;
  step?: number;
  status?: 'queued' | 'running' | 'paused' | 'stuck' | 'done' | 'stopped' | 'error';
  eta_seconds?: number;
  last_heartbeat: number;
  preview_video_url?: string;
  error_message?: string;
}>('Job');

export const Channel = makeEntity<{
  name: string;
  youtube_channel_id: string;
  handle: string;
  focus?: string;
  style?: string;
  voice?: string;
  upload_schedule?: string;
  target_length?: string;
  status?: 'active' | 'paused' | 'maintenance' | 'testing' | 'archived';
  political_stance?: 'neutral' | 'conservative';
  content_personality_id?: string;
  testing_approved?: boolean;
  upload_prevention?: boolean;
}>('Channel');

/** Research */
export const ResearchResult = makeEntity<{
  channel_name: string;
  niche: string;
  research_type:
    | 'niche_opportunity'
    | 'competitor_analysis'
    | 'viral_patterns'
    | 'monetization_strategy'
    | 'audience_insights'
    | 'trend_forecasting'
    | 'brand_positioning'
    | 'content_gap_analysis'
    | 'platform_optimization'
    | 'thumbnail_title_research';
  research_depth?: 'quick' | 'standard' | 'deep';
  target_audience?: string;
  content_goals?: string;
  competitor_target?: string;
  result_data: string; // JSON
  generated_at: string; // ISO
}>('ResearchResult');

export const YouTubeIntelligence = makeEntity<{
  intelligence_summary: string;
  opportunity_level: 'low' | 'medium' | 'high' | 'critical';
  discovery_date: string; // ISO
  implementation_urgency?: 'low' | 'medium' | 'high';
  impact_timeline?: string;
}>('YouTubeIntelligence');

export const MarketOpportunity = makeEntity<{
  opportunity_name: string;
  created_date: string; // ISO
  revenue_potential: number;
  success_probability: number;
}>('MarketOpportunity');

export const StrategicDecision = makeEntity<{
  decision_title: string;
  created_date: string; // ISO
  decision_category: string;
  approval_status: 'pending_review' | 'approved' | 'rejected';
}>('StrategicDecision');

/** Viral */
export const ViralThumbnailStrategy = makeEntity<{
  strategy_name: string;
  description?: string;
  psychological_trigger?: string;
  visual_elements?: string; // JSON []
  copywriting_formula?: string;
  created_date?: string;
}>('ViralThumbnailStrategy');

export const ViralCopywritingStrategy = makeEntity<{
  strategy_name: string;
  description?: string;
  script_hook_formula?: string;
  best_for_niche?: string; // JSON []
  created_date?: string;
}>('ViralCopywritingStrategy');

export const ViralResearchEngine = makeEntity<{
  research_date: string;
  research_type: 'viral_hooks' | 'thumbnail_patterns' | 'format_discovery';
  key_findings?: string; // JSON []
  new_strategies_discovered?: string; // JSON []
  trend_predictions?: string; // JSON []
  confidence_score?: number;
}>('ViralResearchEngine');

export const ViralTrendTracker = makeEntity<{
  trend_name: string;
  trend_category: 'format' | 'topic' | 'style' | 'platform';
  first_detected: string;
  current_adoption_rate: number;
  trend_lifecycle_stage: 'emerging' | 'growing' | 'mature' | 'declining';
  effectiveness_score: number;
}>('ViralTrendTracker');

/** Style & Persona */
export const StyleAnalysis = makeEntity<{
  analysis_name: string;
  subject_analyzed: string;
  linguistic_patterns?: string; // JSON
  humor_mechanics?: string; // JSON
  differentiation_factors?: string; // JSON []
  created_date?: string;
}>('StyleAnalysis');

export const ContentPersonality = makeEntity<{
  personality_name: string;
  inspiration_source?: string;
  core_characteristics?: string; // JSON
  communication_style?: string; // JSON
  signature_phrases?: string; // JSON []
  created_date?: string;
}>('ContentPersonality');

export const ConservativeStyleGuide = makeEntity<{
  guide_name: string;
  target_personality: 'gutfeld_like' | 'watters_like' | 'generic_conservative';
  humor_techniques?: string; // JSON []
  rhetorical_strategies?: string; // JSON []
  created_date?: string;
}>('ConservativeStyleGuide');

/** TRP Databases */
export const ConservativeContentDatabase = makeEntity<{
  title: string;
  source: string;
  content_type: 'successful_format' | 'talking_point' | 'case_study';
  content_text?: string;
  key_talking_points?: string; // JSON []
  effectiveness_score?: number;
  viral_potential?: number;
  created_date?: string;
}>('ConservativeContentDatabase');

export const ConservativeFactDatabase = makeEntity<{
  fact_category: 'policy_outcome' | 'economics' | 'culture' | 'law';
  fact_statement: string;
  verification_sources?: string; // JSON []
  conservative_interpretation?: string;
  credibility_score?: number;
  created_date?: string;
}>('ConservativeFactDatabase');

export const PoliticalSafetyDatabase = makeEntity<{
  topic: string;
  safety_level: 'safe' | 'proceed_with_caution' | 'unsafe';
  approved_angles?: string; // JSON []
  forbidden_approaches?: string; // JSON []
  brand_alignment_score?: number;
  created_date?: string;
}>('PoliticalSafetyDatabase');

export const MediaBiasDatabase = makeEntity<{
  media_outlet: string;
  bias_examples?: string; // JSON []
  framing_patterns?: string;
  created_date?: string;
}>('MediaBiasDatabase');

/** Business & AB Testing */
export const ABTestCampaign = makeEntity<{
  campaign_name: string;
  test_type:
    | 'thumbnail'
    | 'title'
    | 'description'
    | 'posting_time'
    | 'content_format'
    | 'call_to_action'
    | 'affiliate_placement';
  variant_a: string; // JSON
  variant_b: string; // JSON
  success_metric:
    | 'click_through_rate'
    | 'conversion_rate'
    | 'engagement_rate'
    | 'revenue_per_view'
    | 'watch_time'
    | 'subscriber_conversion';
  test_duration_days?: number;
  sample_size?: number;
  current_results?: string; // JSON
  statistical_significance?: number;
  confidence_interval?: number;
  test_status?: 'planning' | 'running' | 'completed' | 'inconclusive' | 'stopped';
  winner_variant?: 'A' | 'B' | 'inconclusive';
  improvement_percentage?: number;
  channel_id?: string;
  video_project_id?: string;
  automated_implementation?: boolean;
}>('ABTestCampaign');

export const AdCampaignOptimizer = makeEntity<{
  optimizer_name: string;
  campaign_objectives: string; // JSON []
  optimization_algorithms: string; // JSON []
  budget_allocation?: string; // JSON
}>('AdCampaignOptimizer');

export const AdCreativeGenerator = makeEntity<{
  generator_name: string;
  target_audience: string; // JSON
  creative_type:
    | 'display_banner'
    | 'video_ad'
    | 'social_post'
    | 'native_ad'
    | 'email_creative'
    | 'landing_page'
    | 'sales_copy';
  brand_guidelines?: string; // JSON
}>('AdCreativeGenerator');

export const AdMarketResearch = makeEntity<{
  target_market: string;
  research_depth: 'surface' | 'standard' | 'deep' | 'comprehensive';
  opportunity_score: number;
  market_size_data?: string; // JSON
}>('AdMarketResearch');

export const AdSalesAutomation = makeEntity<{
  automation_name: string;
  target_market: string;
  sales_process_stages: string; // JSON []
  conversion_rate?: number;
}>('AdSalesAutomation');

export const AdaptationRule = makeEntity<{
  rule_name: string;
  trigger_conditions: string; // JSON
  adaptation_actions: string; // JSON []
  rule_priority?: number;
  rule_status?: 'active' | 'testing' | 'paused' | 'deprecated';
}>('AdaptationRule');

export const AffiliateProgram = makeEntity<{
  program_name: string;
  signup_url: string;
  commission_rate?: string;
  niche_category?: string;
  application_status?: 'not_applied' | 'pending' | 'approved' | 'rejected';
  affiliate_id?: string;
  api_credentials?: string; // JSON
  auto_signup_enabled?: boolean;
}>('AffiliateProgram');
