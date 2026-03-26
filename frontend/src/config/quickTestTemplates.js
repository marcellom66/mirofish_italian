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
  }
]
