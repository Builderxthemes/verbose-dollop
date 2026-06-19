import discord
from discord.ext import commands
import requests
import asyncio
from openai import AsyncOpenAI
import os
import json
from datetime import datetime, timedelta

# ==================== BOT CONFIG ====================
BOT_NAME = "RAM Bot"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Credit System Settings
CREDIT_FILE = "credits.json"
DAILY_REWARD = 1500
CHAT_COST = 25

# Load/Save Credits
def load_credits():
    if os.path.exists(CREDIT_FILE):
        try:
            with open(CREDIT_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_credits(credits_data):
    with open(CREDIT_FILE, "w") as f:
        json.dump(credits_data, f, indent=2)

credits_data = load_credits()
daily_cooldown = {}  # user_id: last_claim_time

# ==================== ALL MODELS ====================
MODELS = {
    "diffusiongemma": {"full_name": "google/diffusiongemma-26b-a4b-it", "api_key": "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", "max_tokens": 4096, "temperature": 1.0, "top_p": 0.95, "client_type": "requests"},
    "kimi": {"full_name": "moonshotai/kimi-k2.6", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 1.0, "client_type": "requests"},
    "step": {"full_name": "stepfun-ai/step-3.7-flash", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "requests"},
    "mistral": {"full_name": "mistralai/mistral-medium-3.5-128b", "api_key": "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", "max_tokens": 16384, "temperature": 0.7, "top_p": 1.0, "client_type": "requests"},
    "glm": {"full_name": "z-ai/glm-5.1", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 1.0, "client_type": "openai"},
    "deepseek": {"full_name": "deepseek-ai/deepseek-v4-pro", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "openai"},
    "deepseek-flash": {"full_name": "deepseek-ai/deepseek-v4-flash", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "openai", "extra_body": {"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}}},
    "gemma4": {"full_name": "google/gemma-4-31b-it", "api_key": "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", "max_tokens": 16384, "temperature": 1.0, "top_p": 0.95, "client_type": "requests", "chat_template_kwargs": {"enable_thinking": True}},
    "qwen122": {"full_name": "qwen/qwen3.5-122b-a10b", "api_key": "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", "max_tokens": 16384, "temperature": 0.60, "top_p": 0.95, "client_type": "requests"},
    "qwen397": {"full_name": "qwen/qwen3.5-397b-a17b", "api_key": "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", "max_tokens": 16384, "temperature": 0.60, "top_p": 0.95, "top_k": 20, "presence_penalty": 0, "repetition_penalty": 1, "client_type": "requests"},
    "mistral-small": {"full_name": "mistralai/mistral-small-4-119b-2603", "api_key": "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", "max_tokens": 16384, "temperature": 0.10, "top_p": 1.0, "client_type": "requests", "reasoning_effort": "high"}
}

INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# ==================== HELPER FUNCTIONS ====================
def get_credits(user_id):
    return credits_data.get(str(user_id), 100)  # New users start with 100 credits

def add_credits(user_id, amount):
    uid = str(user_id)
    credits_data[uid] = get_credits(user_id) + amount
    save_credits(credits_data)

def spend_credits(user_id, amount):
    uid = str(user_id)
    current = get_credits(user_id)
    if current < amount:
        return False
    credits_data[uid] = current - amount
    save_credits(credits_data)
    return True

# ==================== QUERY MODEL ====================
async def query_model(model_key: str, prompt: str):
    if model_key not in MODELS:
        return "❌ Unknown model."
    
    config = MODELS[model_key]
    model_name = config["full_name"]
    
    try:
        if config["client_type"] == "requests":
            headers = {"Authorization": f"Bearer {config['api_key']}", "Accept": "application/json"}
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
                "top_p": config["top_p"],
                "stream": False
            }
            if "reasoning_effort" in config: payload["reasoning_effort"] = config["reasoning_effort"]
            if "chat_template_kwargs" in config: payload["chat_template_kwargs"] = config["chat_template_kwargs"]
            if "top_k" in config: payload["top_k"] = config["top_k"]
            if "presence_penalty" in config: payload["presence_penalty"] = config["presence_penalty"]
            if "repetition_penalty" in config: payload["repetition_penalty"] = config["repetition_penalty"]

            response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=180)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        else:
            client = AsyncOpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=config["api_key"])
            completion = await client.chat.completions.create(
                model=model_name, messages=[{"role": "user", "content": prompt}],
                temperature=config["temperature"], top_p=config["top_p"],
                max_tokens=config["max_tokens"], extra_body=config.get("extra_body", {}), stream=False
            )
            return completion.choices[0].message.content

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ==================== EVENTS ====================
@bot.event
async def on_ready():
    print(f"✅ {BOT_NAME} is online! All models running with 8GB RAM.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!chat • Earn Credits"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Small reward for activity (max once every 5 minutes)
    uid = str(message.author.id)
    if uid not in daily_cooldown or datetime.now() - datetime.fromisoformat(daily_cooldown[uid]) > timedelta(minutes=5):
        add_credits(message.author.id, 5)
        daily_cooldown[uid] = datetime.now().isoformat()
    await bot.process_commands(message)

# ==================== COMMANDS ====================
@bot.command(name="models")
async def list_models(ctx):
    embed = discord.Embed(title=f"{BOT_NAME} - All Models", description="**All running locally with 8GB RAM**", color=0x00ff00)
    for key, config in MODELS.items():
        embed.add_field(name=f"`{key}`", value=f"`{config['full_name']}`", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="balance")
async def balance(ctx):
    creds = get_credits(ctx.author.id)
    embed = discord.Embed(title="💰 Your Credits", description=f"You have **{creds}** credits.", color=0x00ff00)
    embed.set_footer(text=f"Chat cost: {CHAT_COST} credits")
    await ctx.send(embed=embed)

@bot.command(name="daily")
async def daily(ctx):
    uid = str(ctx.author.id)
    now = datetime.now()
    last_claim = daily_cooldown.get(uid)
    
    if last_claim:
        last_time = datetime.fromisoformat(last_claim)
        if now - last_time < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_time)
            await ctx.send(f"⏳ You already claimed today. Next claim in **{str(remaining).split('.')[0]}**.")
            return
    
    add_credits(ctx.author.id, DAILY_REWARD)
    daily_cooldown[uid] = now.isoformat()
    await ctx.send(f"✅ **Daily Reward!** You received **{DAILY_REWARD}** credits! Come back tomorrow.")

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    sorted_users = sorted(credits_data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "\n".join([f"{i+1}. <@{uid}> — **{credits}** credits" for i, (uid, credits) in enumerate(sorted_users)])
    embed = discord.Embed(title="🏆 Credit Leaderboard", description=desc or "No credits yet!", color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command(name="chat")
async def chat(ctx, model_key: str, *, prompt: str):
    if model_key not in MODELS:
        await ctx.send("❌ Invalid model! Use `!models`")
        return
    
    if not spend_credits(ctx.author.id, CHAT_COST):
        await ctx.send(f"❌ Not enough credits! You need **{CHAT_COST}** credits to chat.\nUse `!daily` to earn more.")
        return
    
    config = MODELS[model_key]
    await ctx.send(f"🤖 **{model_key}** (`{config['full_name']}`) is thinking... (8GB RAM) | -{CHAT_COST} credits")

    response = await query_model(model_key, prompt)
    
    if len(response) > 1900:
        for i in range(0, len(response), 1900):
            await ctx.send(response[i:i+1900])
    else:
        await ctx.send(response)

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title=f"{BOT_NAME} Help", color=0x00ff00)
    embed.add_field(name="Credit System", value="Earn credits with `!daily`\nGet small rewards by chatting in the server\nSpend credits to use models", inline=False)
    embed.add_field(name="Commands", value="`!models` • `!balance` • `!daily` • `!leaderboard`\n`!chat <model> <prompt>`", inline=False)
    embed.set_footer(text="All models running locally with 8GB of RAM")
    await ctx.send(embed=embed)

# ==================== RUN ====================
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("❌ Set DISCORD_TOKEN environment variable!")
    else:
        bot.run(TOKEN)
