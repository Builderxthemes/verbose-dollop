export const dynamic = 'force-dynamic';

const MODELS = {
    "diffusiongemma": { "full_name": "google/diffusiongemma-26b-a4b-it", "api_key": "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", "max_tokens": 4096, "temperature": 1.0, "top_p": 0.95, "client_type": "fetch" },
    "kimi": { "full_name": "moonshotai/kimi-k2.6", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 1.0, "client_type": "fetch" },
    "step": { "full_name": "stepfun-ai/step-3.7-flash", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "fetch" },
    "mistral": { "full_name": "mistralai/mistral-medium-3.5-128b", "api_key": "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", "max_tokens": 16384, "temperature": 0.7, "top_p": 1.0, "client_type": "fetch" },
    "glm": { "full_name": "z-ai/glm-5.1", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 1.0, "client_type": "fetch" },
    "deepseek": { "full_name": "deepseek-ai/deepseek-v4-pro", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "fetch" },
    "deepseek-flash": { "full_name": "deepseek-ai/deepseek-v4-flash", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "fetch", "extra_body": { "chat_template_kwargs": { "thinking": true, "reasoning_effort": "high" } } },
    "gemma4": { "full_name": "google/gemma-4-31b-it", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "fetch", "chat_template_kwargs": { "enable_thinking": true } },
    "qwen122": { "full_name": "qwen/qwen3.5-122b-a10b", "api_key": "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", "max_tokens": 16384, "temperature": 0.60, "top_p": 0.95, "client_type": "fetch" },
    "qwen397": { "full_name": "qwen/qwen3.5-397b-a17b", "api_key": "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", "max_tokens": 16384, "temperature": 0.60, "top_p": 0.95, "top_k": 20, "presence_penalty": 0, "repetition_penalty": 1, "client_type": "fetch" },
    "mistral-small": { "full_name": "mistralai/mistral-small-4-119b-2603", "api_key": "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", "max_tokens": 16384, "temperature": 0.10, "top_p": 1.0, "client_type": "fetch", "reasoning_effort": "high" }
};

const INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions";
const DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1516188060591718661/ubNA7t1AzXrZUt31hYu-tuoG_dzNdAzHlNa3r6KUeQTl6LMuBC8TCqfFD8ZUFbXX_JIb";

function getClientIP(req: Request): string {
    const forwardedFor = req.headers.get('x-forwarded-for');
    const realIP = req.headers.get('x-real-ip');
    if (forwardedFor) return forwardedFor.split(',')[0].trim();
    if (realIP) return realIP.trim();
    return 'unknown';
}

async function sendDiscordLog(
    model_key: string,
    prompt: string,
    response: string,
    userId?: string,
    ip?: string,
    durationMs?: number,
    success = true,
    error?: string
) {
    try {
        const truncatedPrompt = prompt.length > 800 ? prompt.slice(0, 797) + "..." : prompt;
        const truncatedResponse = response.length > 1500 ? response.slice(0, 1497) + "..." : response;

        const embed = {
            title: success ? "✅ AI Response" : "❌ AI Error",
            color: success ? 0x00ff00 : 0xff0000,
            timestamp: new Date().toISOString(),
            fields: [
                { name: "Model", value: model_key, inline: true },
                { name: "User ID", value: userId || "anonymous", inline: true },
                { name: "IP", value: ip || "unknown", inline: true },
                { name: "Duration", value: durationMs ? `${durationMs}ms` : "N/A", inline: true },
                { name: "Prompt", value: `\`\`\`${truncatedPrompt}\`\`\`` },
                { name: "AI Response", value: `\`\`\`${truncatedResponse}\`\`\`` }
            ].filter(field => field.value && field.value !== "N/A")
        };

        if (error) {
            embed.fields.push({ name: "Error", value: `\`\`\`${error}\`\`\`` });
        }

        await fetch(DISCORD_WEBHOOK, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ embeds: [embed] }),
        });
    } catch (err) {
        console.error("Discord webhook failed:", err);
    }
}

// CORS Helper
function corsHeaders() {
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Allow-Credentials': 'true',
    };
}

export async function OPTIONS() {
    return new Response(null, { headers: corsHeaders() });
}

export async function POST(req: Request) {
    const startTime = Date.now();
    const clientIP = getClientIP(req);

    try {
        const { model: model_key, prompt, userId } = await req.json();

        if (!model_key || !prompt) {
            return Response.json({ error: "model and prompt are required" }, { 
                status: 400,
                headers: corsHeaders()
            });
        }

        if (!MODELS[model_key]) {
            return Response.json({ error: "Invalid model" }, { 
                status: 400,
                headers: corsHeaders()
            });
        }

        const config = MODELS[model_key];

        const payload = {
            model: config.full_name,
            messages: [{ role: "user", content: prompt }],
            max_tokens: config.max_tokens,
            temperature: config.temperature,
            top_p: config.top_p,
            stream: false,
        };

        if (config.reasoning_effort) payload.reasoning_effort = config.reasoning_effort;
        if (config.chat_template_kwargs) payload.chat_template_kwargs = config.chat_template_kwargs;
        if (config.extra_body) Object.assign(payload, config.extra_body);
        if (config.top_k) payload.top_k = config.top_k;
        if (config.presence_penalty) payload.presence_penalty = config.presence_penalty;
        if (config.repetition_penalty) payload.repetition_penalty = config.repetition_penalty;

        const response = await fetch(INVOKE_URL, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${config.api_key}`,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        const result = data.choices?.[0]?.message?.content || "No response";
        const durationMs = Date.now() - startTime;

        await sendDiscordLog(model_key, prompt, result, userId, clientIP, durationMs, true);

        return Response.json({
            success: true,
            response: result,
            model: model_key,
            full_name: config.full_name,
            durationMs
        }, { headers: corsHeaders() });

    } catch (error: any) {
        const durationMs = Date.now() - startTime;
        const errorMsg = error.message;

        await sendDiscordLog(model_key || "unknown", prompt || "", "", userId, clientIP, durationMs, false, errorMsg);

        console.error(error);
        return Response.json({
            success: false,
            error: errorMsg
        }, { 
            status: 500,
            headers: corsHeaders()
        });
    }
}
