// src/entities/seed.ts
import {
  ResearchResult,
  MarketOpportunity,
  Channel,
  VideoProject,
  Job,
  ViralThumbnailStrategy,
  ConservativeContentDatabase,
  PoliticalSafetyDatabase,
  ViralTrendTracker,
  YouTubeIntelligence,
  StrategicDecision,
  ViralCopywritingStrategy,
  ContentPersonality,
  ConservativeStyleGuide,
  ABTestCampaign,
  AffiliateProgram,
} from './index';

export async function seedIfEmpty() {
  // Seed ResearchResult
  const existingResearch = await ResearchResult.list();
  if (existingResearch.length === 0) {
    await ResearchResult.create({
      channel_name: 'The Right Perspective',
      niche: 'Political Commentary',
      research_type: 'niche_opportunity',
      research_depth: 'deep',
      target_audience: 'Conservative viewers aged 25-55',
      content_goals: 'Provide fact-based political analysis with conservative perspective',
      result_data: JSON.stringify({
        opportunity_score: 8.5,
        competition_level: 'medium',
        monetization_potential: 'high',
        growth_trajectory: 'strong',
        key_insights: [
          'High engagement on political content',
          'Strong affiliate marketing opportunities',
          'Consistent viewership during election cycles',
        ],
      }),
      generated_at: new Date().toISOString(),
    });

    await ResearchResult.create({
      channel_name: 'Next Gen Tech Today',
      niche: 'Technology Reviews',
      research_type: 'competitor_analysis',
      research_depth: 'standard',
      target_audience: 'Tech enthusiasts aged 18-45',
      content_goals: 'Provide honest tech reviews and tutorials',
      result_data: JSON.stringify({
        opportunity_score: 7.2,
        competition_level: 'high',
        monetization_potential: 'medium',
        growth_trajectory: 'steady',
        key_insights: [
          'High competition in tech review space',
          'Strong affiliate potential with tech products',
          'Consistent demand for product reviews',
        ],
      }),
      generated_at: new Date().toISOString(),
    });
  }

  // Seed MarketOpportunity
  const existingOpportunities = await MarketOpportunity.list();
  if (existingOpportunities.length === 0) {
    await MarketOpportunity.create({
      opportunity_name: 'Conservative Political Commentary Expansion',
      created_date: new Date().toISOString(),
      revenue_potential: 85000,
      success_probability: 0.75,
    });

    await MarketOpportunity.create({
      opportunity_name: 'Tech Review Affiliate Marketing',
      created_date: new Date().toISOString(),
      revenue_potential: 45000,
      success_probability: 0.65,
    });
  }

  // Seed Channel
  const existingChannels = await Channel.list();
  if (existingChannels.length === 0) {
    await Channel.create({
      name: 'The Right Perspective',
      youtube_channel_id: 'UC_TRP_CHANNEL_ID',
      handle: '@therightperspective',
      focus: 'Political commentary and conservative analysis',
      style: 'Fact-based, engaging, professional',
      voice: 'Authoritative yet approachable conservative voice',
      upload_schedule: 'Monday, Wednesday, Friday at 6 PM EST',
      target_length: '8-12 minutes',
      status: 'active',
      political_stance: 'conservative',
      content_personality_id: 'gutfeld_inspired',
      testing_approved: true,
      upload_prevention: false,
    });

    await Channel.create({
      name: 'Next Gen Tech Today',
      youtube_channel_id: 'UC_NGTT_CHANNEL_ID',
      handle: '@nextgentechtoday',
      focus: 'Technology reviews and tutorials',
      style: 'Informative, detailed, honest',
      voice: 'Expert but accessible tech reviewer',
      upload_schedule: 'Tuesday, Thursday at 3 PM EST',
      target_length: '10-15 minutes',
      status: 'active',
      political_stance: 'neutral',
      testing_approved: true,
      upload_prevention: false,
    });
  }

  // Seed VideoProject
  const existingProjects = await VideoProject.list();
  if (existingProjects.length === 0) {
    await VideoProject.create({
      title: 'Breaking Down the Latest Political Developments',
      topic: 'Current political analysis',
      status: 'scripting',
      channel_id: 'trp_channel',
      target_length: 600,
      storage_location: 'local',
    });

    await VideoProject.create({
      title: 'iPhone 15 Pro Max: Complete Review',
      topic: 'Technology review',
      status: 'production',
      channel_id: 'ngtt_channel',
      target_length: 900,
      storage_location: 'local',
    });
  }

  // Seed Job
  const existingJobs = await Job.list();
  if (existingJobs.length === 0) {
    await Job.create({
      title: 'Video Rendering: Political Analysis',
      started_at: Date.now(),
      total_steps: 5,
      step: 3,
      status: 'running',
      eta_seconds: 300,
      last_heartbeat: Date.now(),
    });
  }

  // Seed ViralThumbnailStrategy
  const existingThumbnailStrategies = await ViralThumbnailStrategy.list();
  if (existingThumbnailStrategies.length === 0) {
    await ViralThumbnailStrategy.create({
      strategy_name: 'Shocked Face + Bold Text',
      description: 'High-contrast shocked expression with bold, contrasting text overlay',
      psychological_trigger: 'Curiosity and urgency',
      visual_elements: JSON.stringify([
        'Shocked facial expression',
        'Bold contrasting colors',
        'Large readable text',
        'High contrast',
      ]),
      copywriting_formula: '[SHOCKING FACT] + [EMOTIONAL TRIGGER]',
      created_date: new Date().toISOString(),
    });

    await ViralThumbnailStrategy.create({
      strategy_name: 'Before/After Split',
      description: 'Split screen showing dramatic before and after comparison',
      psychological_trigger: 'Transformation curiosity',
      visual_elements: JSON.stringify([
        'Split screen layout',
        'Clear before/after labels',
        'Dramatic difference',
        'Arrow pointing to change',
      ]),
      copywriting_formula: '[BEFORE STATE] vs [AFTER STATE]',
      created_date: new Date().toISOString(),
    });
  }

  // Seed ConservativeContentDatabase
  const existingConservativeContent = await ConservativeContentDatabase.list();
  if (existingConservativeContent.length === 0) {
    await ConservativeContentDatabase.create({
      title: 'Economic Policy Success Stories',
      source: 'Conservative policy research',
      content_type: 'talking_point',
      content_text: 'Data-driven analysis of successful conservative economic policies',
      key_talking_points: JSON.stringify([
        'Tax reduction impact on job creation',
        'Deregulation success stories',
        'Free market solutions',
      ]),
      effectiveness_score: 8.5,
      viral_potential: 7.2,
      created_date: new Date().toISOString(),
    });
  }

  // Seed PoliticalSafetyDatabase
  const existingPoliticalSafety = await PoliticalSafetyDatabase.list();
  if (existingPoliticalSafety.length === 0) {
    await PoliticalSafetyDatabase.create({
      topic: 'Economic Policy',
      safety_level: 'safe',
      approved_angles: JSON.stringify([
        'Data-driven analysis',
        'Historical comparisons',
        'Policy outcome focus',
      ]),
      forbidden_approaches: JSON.stringify([
        'Personal attacks',
        'Unsubstantiated claims',
        'Inflammatory language',
      ]),
      brand_alignment_score: 9.0,
      created_date: new Date().toISOString(),
    });
  }

  // Seed ViralTrendTracker
  const existingTrends = await ViralTrendTracker.list();
  if (existingTrends.length === 0) {
    await ViralTrendTracker.create({
      trend_name: 'Political Reaction Videos',
      trend_category: 'format',
      first_detected: new Date().toISOString(),
      current_adoption_rate: 0.65,
      trend_lifecycle_stage: 'growing',
      effectiveness_score: 8.2,
    });
  }

  // Seed YouTubeIntelligence
  const existingIntelligence = await YouTubeIntelligence.list();
  if (existingIntelligence.length === 0) {
    await YouTubeIntelligence.create({
      intelligence_summary:
        'Conservative political content showing 25% higher engagement during election periods',
      opportunity_level: 'high',
      discovery_date: new Date().toISOString(),
      implementation_urgency: 'medium',
      impact_timeline: '3-6 months',
    });
  }

  // Seed StrategicDecision
  const existingDecisions = await StrategicDecision.list();
  if (existingDecisions.length === 0) {
    await StrategicDecision.create({
      decision_title: 'Expand Conservative Commentary Content',
      created_date: new Date().toISOString(),
      decision_category: 'Content Strategy',
      approval_status: 'approved',
    });
  }

  // Seed ViralCopywritingStrategy
  const existingCopyStrategies = await ViralCopywritingStrategy.list();
  if (existingCopyStrategies.length === 0) {
    await ViralCopywritingStrategy.create({
      strategy_name: 'Problem-Agitation-Solution Hook',
      description:
        'Start with a relatable problem, agitate the pain point, then tease the solution',
      script_hook_formula:
        "[PROBLEM] is destroying [TARGET AUDIENCE]. Here's what [AUTHORITY FIGURE] doesn't want you to know...",
      best_for_niche: JSON.stringify(['Political commentary', 'Self-help', 'Business advice']),
      created_date: new Date().toISOString(),
    });
  }

  // Seed ContentPersonality
  const existingPersonalities = await ContentPersonality.list();
  if (existingPersonalities.length === 0) {
    await ContentPersonality.create({
      personality_name: 'Gutfeld-Inspired Conservative Host',
      inspiration_source: "Greg Gutfeld's communication style",
      core_characteristics: JSON.stringify([
        'Witty and sharp',
        'Fact-based arguments',
        'Confident delivery',
        'Relatable humor',
      ]),
      communication_style: JSON.stringify({
        tone: 'Authoritative yet approachable',
        humor_type: 'Observational and satirical',
        pacing: 'Dynamic with strategic pauses',
      }),
      signature_phrases: JSON.stringify([
        "Let's break this down",
        "Here's what they don't tell you",
        'The facts speak for themselves',
      ]),
      created_date: new Date().toISOString(),
    });
  }

  // Seed ConservativeStyleGuide
  const existingStyleGuides = await ConservativeStyleGuide.list();
  if (existingStyleGuides.length === 0) {
    await ConservativeStyleGuide.create({
      guide_name: 'TRP Conservative Commentary Style',
      target_personality: 'gutfeld_like',
      humor_techniques: JSON.stringify([
        'Observational comedy',
        'Satirical commentary',
        'Witty one-liners',
        'Relatable analogies',
      ]),
      rhetorical_strategies: JSON.stringify([
        'Fact-based arguments',
        'Historical comparisons',
        'Logical progression',
        'Common sense appeals',
      ]),
      created_date: new Date().toISOString(),
    });
  }

  // Seed ABTestCampaign
  const existingABTests = await ABTestCampaign.list();
  if (existingABTests.length === 0) {
    await ABTestCampaign.create({
      campaign_name: 'Thumbnail Style A/B Test',
      test_type: 'thumbnail',
      variant_a: JSON.stringify({
        style: 'Shocked face with bold text',
        colors: 'High contrast red/white',
        text_size: 'Large',
      }),
      variant_b: JSON.stringify({
        style: 'Professional headshot with subtle text',
        colors: 'Blue/white professional',
        text_size: 'Medium',
      }),
      success_metric: 'click_through_rate',
      test_duration_days: 14,
      test_status: 'running',
      channel_id: 'trp_channel',
    });
  }

  // Seed AffiliateProgram
  const existingAffiliatePrograms = await AffiliateProgram.list();
  if (existingAffiliatePrograms.length === 0) {
    await AffiliateProgram.create({
      program_name: 'Amazon Associates',
      signup_url: 'https://affiliate-program.amazon.com',
      commission_rate: '1-10% depending on category',
      niche_category: 'Books, Electronics, Home & Garden',
      application_status: 'approved',
      affiliate_id: 'therightperspective-20',
      auto_signup_enabled: false,
    });

    await AffiliateProgram.create({
      program_name: 'Best Buy Affiliate Program',
      signup_url: 'https://www.bestbuy.com/site/affiliate-program',
      commission_rate: '1-4%',
      niche_category: 'Electronics, Tech Products',
      application_status: 'pending',
      auto_signup_enabled: true,
    });
  }

  console.log('✅ Seed data initialized successfully');
}

// Utility function to enforce TRP rules
export function enforceTRPRules(channelId: string, content: any) {
  if (channelId === 'trp_channel' || content.political_stance === 'conservative') {
    // Ensure conservative stance is maintained
    if (content.political_stance && content.political_stance !== 'conservative') {
      content.political_stance = 'conservative';
    }

    // Ensure content personality aligns with conservative values
    if (!content.content_personality_id) {
      content.content_personality_id = 'gutfeld_inspired';
    }

    // Ensure upload prevention is properly managed
    if (content.upload_prevention === undefined) {
      content.upload_prevention = false;
    }
  }

  return content;
}
