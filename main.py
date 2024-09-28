import uvicorn
import os
import uuid
import json

from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr

from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

from gemini import gemini

app = FastAPI()

_ = load_dotenv(Path(__file__).parent / '.env')

class InputData(BaseModel):
    lead: dict
    persona: dict
    company: dict

@app.get('/', response_class=HTMLResponse)
async def read_index():
    return HTMLResponse('Hello, world!')


def generate_deck(input: InputData):
    # TODO: Implement this
    prompt = Path('prompts/master.txt').read_text() + f'\n{input.dict()}\n'
    response = gemini(prompt)
    print(response)
    deck = json.loads(response)
    return deck


@app.post('/api/generate-decks', response_class=JSONResponse)
async def api_generate_deck(request: Request, input: InputData):
    supabase_url: str = os.environ.get("SUPABASE_URL")
    supabase_key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    supabase.table('api-requests').insert({
        "data": input.dict(),
    }).execute()
    deck = generate_deck(input)
    deck_uuid = str(uuid.uuid4())
    supabase.table('decks').insert({
        "data": deck,
        "uuid": deck_uuid
    }).execute()
    return JSONResponse(content={"uuid": deck_uuid, "message": "Data received and is being processed... <3"})



if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)