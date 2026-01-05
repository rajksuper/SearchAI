export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { query, results } = req.body;
    const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

    if (!OPENAI_API_KEY) {
        return res.status(500).json({ error: 'OpenAI API key not configured' });
    }

    const systemPrompt = `You are a search result analyzer for SearchZ.ai. You classify queries and rank results intelligently. Always respond with valid JSON only.`;

    const userPrompt = `Query: "${query}"

Search Results:
${results.map((r, i) => `[${i}] ${r.title}
Domain: ${extractDomain(r.url)}
Content: ${(r.content || r.summary || '').substring(0, 300)}`).join('\n---\n')}

Classify this query and provide a response:

Query Types:
- SIMPLE: Math, definitions, conversions → Direct answer only
- BRAND: Company/service search → Brief description, official site first
- FACTUAL: "What/Who/When/Where" → Answer + all ranked results
- COMPLEX: Comparisons, "best", how-to → Summary + ranked results

Respond in this exact JSON format:
{
  "queryType": "SIMPLE|BRAND|FACTUAL|COMPLEX",
  "intent": "what user wants",
  "answer": "6-8 sentence response",
  "ranking": [array of ALL result indices 0-19 in ranked order],
  "reasoning": "why you classified this way"
}

IMPORTANT Rules:
- ALWAYS include ALL 20 results in ranking array (no exclusions)
- Brand searches: Put official domain first in ranking
- Prioritize .gov, .edu, Wikipedia higher in ranking
- Just reorder by quality - do NOT exclude any results`;

    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'gpt-5-mini',
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