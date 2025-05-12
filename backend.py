from fastapi import FastAPI, Request
import httpx
import redis

app = FastAPI()
redis_client = redis.Redis(host="localhost", port=6379)

# Model Endpoints & Pricing
MODELS = {
    "claude-3-haiku": {"endpoint": "anthropic-haiku-api", "cost": 0.25},
    "claude-3-opus": {"endpoint": "anthropic-opus-api", "cost": 15},
    "claude-3-5-sonnet": {"endpoint": "anthropic-sonnet-api", "cost": 3},
    "gpt-3.5-turbo": {"endpoint": "openai-api", "cost": 0.5},
}

@app.post("/query")
async def handle_query(request: Request):
    query = await request.json()
    query_text = query.get("text")
    
    # Check cache first
    cached_response = redis_client.get(query_text)
    if cached_response:
        return {"response": cached_response, "model": "cached"}
    
    # Select model based on logic
    selected_model = select_model(query_text, len(query_text))
    
    # Call API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            MODELS[selected_model]["endpoint"],
            json={"text": query_text}
        )
    
    # Cache response
    redis_client.setex(query_text, 3600, response.text)  # Cache for 1h
    
    return {"response": response.text, "model": selected_model}