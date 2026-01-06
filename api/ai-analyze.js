export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { query, results } = req.body;
    const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

    if (!OPENAI_API_KEY) {
        return res.status(500).json({ error: 'OpenAI API key not configured' });
    }

    const systemPrompt = `You are a search result classifier and ranker for SearchZ.ai. You classify query types and rank results by quality and relevance. Always respond with valid JSON only.`;

    const userPrompt = `Query: "${query}"

Search Results:
${results.map((r, i) => `[${i}] ${r.title}
Domain: ${extractDomain(r.url)}
Content: ${(r.content || r.summary || '').substring(0, 300)}`).join('\n---\n')}

Your task: Classify the query type and rank ALL 20 results by quality and relevance.

Query Types:
- SIMPLE: Math, definitions, conversions
- BRAND: Company/service search
- FACTUAL: "What/Who/When/Where" questions
- COMPLEX: Comparisons, "best", how-to queries

Respond in this exact JSON format:
{
  "queryType": "SIMPLE|BRAND|FACTUAL|COMPLEX",
  "ranking": [array of ALL result indices 0-19 in ranked order],
  "reasoning": "brief explanation of classification and ranking"
}

Ranking Rules:
- Put most relevant results first
- Prioritize .gov, .edu, Wikipedia, major news outlets
- Brand searches: Put official domain first in ranking
- Consider authority, relevance, and quality
- IMPORTANT: Ensure source diversity - avoid ranking multiple results from same domain consecutively
- Spread out results from same source (e.g., if 10 results from yahoo.com, alternate with other sources)
- MUST include all 20 indices in ranking array`;

    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'gpt-4o-mini',
                messages: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: userPrompt }
                ],
                temperature: 0,
                response_format: { type: "json_object" }
            })
        });

        const data = await response.json();

        if (data.error) {
            return res.status(500).json({ error: data.error.message });
        }

        const aiResponse = JSON.parse(data.choices[0].message.content);
        res.json(aiResponse);

    } catch (error) {
        console.error('AI analysis error:', error);
        res.status(500).json({ error: 'AI analysis failed' });
    }
}

function extractDomain(url) {
    try {
        return new URL(url).hostname.replace('www.', '');
    } catch {
        return url;
    }
}