export const QUICK_TEST_TEMPLATES = [
  {
    id: 'product',
    icon: '\u{1F680}',
    titleKey: 'quickTest.templates.product.title',
    subtitleKey: 'quickTest.templates.product.subtitle',
    placeholderKey: 'quickTest.templates.product.placeholder',
    promptTemplate: (input) =>
      `Simulate the reactions of a representative sample of consumers to the following product: ${input}. Analyze acceptance, criticisms, perceived strengths and weaknesses, and demographic segments.`,
    evaluationPrompt: (input) =>
      `Considering the product "${input}", express your judgment. Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Market analysis for product: '
  },
  {
    id: 'policy',
    icon: '\u{1F3DB}',
    titleKey: 'quickTest.templates.policy.title',
    subtitleKey: 'quickTest.templates.policy.subtitle',
    placeholderKey: 'quickTest.templates.policy.placeholder',
    promptTemplate: (input) =>
      `Simulate the reactions of citizens to the following law/policy: ${input}. Analyze consent, opposition, concerns by social category, and potential unintended consequences.`,
    evaluationPrompt: (input) =>
      `Considering the law/policy "${input}", express your judgment. Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Policy impact analysis: '
  },
  {
    id: 'marketing',
    icon: '\u{1F4E3}',
    titleKey: 'quickTest.templates.marketing.title',
    subtitleKey: 'quickTest.templates.marketing.subtitle',
    placeholderKey: 'quickTest.templates.marketing.placeholder',
    promptTemplate: (input) =>
      `Simulate the reactions of consumers to the following marketing campaign: ${input}. Analyze engagement, sentiment, virality potential, and criticisms.`,
    evaluationPrompt: (input) =>
      `Considering the marketing campaign "${input}", express your judgment. Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Marketing campaign analysis: '
  },
  {
    id: 'pricing',
    icon: '\u{1F4B0}',
    titleKey: 'quickTest.templates.pricing.title',
    subtitleKey: 'quickTest.templates.pricing.subtitle',
    placeholderKey: 'quickTest.templates.pricing.placeholder',
    promptTemplate: (input) =>
      `Simulate the reactions of consumers to the following pricing options: ${input}. Analyze acceptability, psychological thresholds, competitive comparison, and willingness to pay.`,
    evaluationPrompt: (input) =>
      `Considering the pricing "${input}", express your judgment. Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Pricing evaluation: '
  },
  {
    id: 'opinion',
    icon: '\u{1F5F3}',
    titleKey: 'quickTest.templates.opinion.title',
    subtitleKey: 'quickTest.templates.opinion.subtitle',
    placeholderKey: 'quickTest.templates.opinion.placeholder',
    promptTemplate: (input) =>
      `Simulate a public opinion poll on the following topic: ${input}. Analyze distribution of opinions, motivations, polarization, and demographic differences.`,
    evaluationPrompt: (input) =>
      `Considering the topic "${input}", express your opinion. Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Public opinion analysis: '
  },
  {
    id: 'business_scenario',
    icon: '📊',
    titleKey: 'businessPlan.templates.business_scenario.title',
    subtitleKey: 'businessPlan.templates.business_scenario.subtitle',
    placeholderKey: 'businessPlan.templates.business_scenario.placeholder',
    type: 'business_plan',
    promptTemplate: (metadata) =>
      "Simulate how " + (metadata.stakeholders || 'stakeholders') + " react to this business plan under three scenarios: optimistic, realistic, and pessimistic. Sector: " + (metadata.sector || 'N/A') + ", Phase: " + (metadata.phase || 'N/A') + ", Horizon: " + (metadata.time_horizon || 'N/A') + ". KPIs to track: " + (Array.isArray(metadata.kpis) ? metadata.kpis.join(', ') : metadata.kpis || 'N/A') + ".",
    evaluationPrompt: (metadata) =>
      `As a stakeholder in the ${metadata.sector || 'N/A'} sector, what is your reaction to this business plan under the optimistic, realistic, and pessimistic scenarios presented? Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Business Plan - Multi-Scenario Analysis:\n'
  },
  {
    id: 'business_evolution',
    icon: '📈',
    titleKey: 'businessPlan.templates.business_evolution.title',
    subtitleKey: 'businessPlan.templates.business_evolution.subtitle',
    placeholderKey: 'businessPlan.templates.business_evolution.placeholder',
    type: 'business_plan',
    promptTemplate: (metadata) =>
      "Simulate the evolution of stakeholder reactions to this business plan across three phases: launch, growth, and maturity. Sector: " + (metadata.sector || 'N/A') + ". Identify how sentiment shifts over " + (metadata.time_horizon || 'the forecast period') + " and what triggers change.",
    evaluationPrompt: (metadata) =>
      `Considering this business plan in the ${metadata.sector || 'N/A'} sector, how does your sentiment change across the launch, growth, and maturity phases? Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Business Plan - Evolution Analysis:\n'
  },
  {
    id: 'business_competitive',
    icon: '🎯',
    titleKey: 'businessPlan.templates.business_competitive.title',
    subtitleKey: 'businessPlan.templates.business_competitive.subtitle',
    placeholderKey: 'businessPlan.templates.business_competitive.placeholder',
    type: 'business_plan',
    promptTemplate: (metadata) =>
      "Simulate reactions of competitors, investors, and target customers to this business plan in the " + (metadata.sector || 'N/A') + " sector. Identify competitive threats, investment attractiveness, and customer adoption barriers. Main competitors: " + (Array.isArray(metadata.competitors) ? metadata.competitors.join(', ') : metadata.competitors || 'N/A') + ".",
    evaluationPrompt: (metadata) =>
      `From your perspective as a stakeholder in the ${metadata.sector || 'N/A'} sector, how do you assess the competitive positioning of this business plan? Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Business Plan - Competitive Analysis:\n'
  },
  {
    id: 'business_full',
    icon: '🏢',
    titleKey: 'businessPlan.templates.business_full.title',
    subtitleKey: 'businessPlan.templates.business_full.subtitle',
    placeholderKey: 'businessPlan.templates.business_full.placeholder',
    type: 'business_plan',
    promptTemplate: (metadata) =>
      "Perform a comprehensive business plan analysis for a " + (metadata.phase || 'N/A') + " company in the " + (metadata.sector || 'N/A') + " sector. Simulate multi-scenario outcomes, stakeholder reactions across time, competitive dynamics, and generate a risk matrix with strategic recommendations. Priority KPIs: " + (Array.isArray(metadata.kpis) ? metadata.kpis.join(', ') : metadata.kpis || 'N/A') + ". Risk areas: " + (Array.isArray(metadata.risk_areas) ? metadata.risk_areas.join(', ') : metadata.risk_areas || 'N/A') + ".",
    evaluationPrompt: (metadata) =>
      `Having reviewed this comprehensive business plan for a ${metadata.phase || 'N/A'} company in the ${metadata.sector || 'N/A'} sector, what is your overall assessment? Reply ONLY with JSON: {"sentiment":"favorable","score":7,"reason":"brief explanation"}\nPossible sentiment values: "favorable", "unfavorable", "neutral". Score from -10 to 10.`,
    seedPrefix: 'Business Plan - Full Analysis:\n'
  }
]
