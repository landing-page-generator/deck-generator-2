import requests
import uvicorn
import os
import uuid
import json

from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
# from pydantic import BaseModel, EmailStr

from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

from img import get_image_from_pexels

from ai import gemini, ai21

app = FastAPI()

_ = load_dotenv(Path(__file__).parent / '.env')

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


@app.get('/', response_class=HTMLResponse)
async def read_index():
    # return HTMLResponse("Hello, world!")
    placeholder = """
    {
        "lead": { "name": "John Smith", "email": "john.smith@gmail.com"},
        "persona": { "name": "Firefighter" },
        "company": { "name": "Sundai" }
    }"""

    return HTMLResponse(f"""
    <html>
    <body>
    <h1>Deck Generation Form</h1>
    <form action="/generate-deck" method="post">
        <label for="lead">Data:</label><br>
        <textarea id="data" name="data" rows="10" cols="100">{placeholder}</textarea><br>
        <input type="submit" value="Generate Deck">
    </form>
    </body>
    </html>
    """)


@app.post('/generate-deck', response_class=HTMLResponse)
async def generate_deck_form(request: Request):
    form_data = await request.form()
    data = form_data.get('data')
    data = json.loads(data)
    deck_uuid, deck_content = generate_deck(data)
    deck_content_html = json.dumps(deck_content, indent=4)
    return HTMLResponse(
        "Deck generated successfully!<br><br>"
        f"UUID: <b>{deck_uuid}</b><br><br>"
        f"DECK:<br><pre>{deck_content_html}</pre>"
    )


def generate_deck(input: dict):
    deck_uuid = str(uuid.uuid4())
    
    master = Path('prompts/master.txt').read_text() + f'\n\n{input}\n'
    master_response = ai21(master)
    deck_content = json.loads(master_response)

    image = Path('prompts/image.txt').read_text() + f'\n\n{deck_content}\n'
    image_response = ai21(image)
    image_url = get_image_from_pexels(image_response)
    deck_content['list'][0]['imageURL'] = image_url

    supabase.table('decks').insert({
        "data": deck_content,
        "uuid": deck_uuid
    }).execute()

    return deck_uuid, deck_content


@app.post('/api/generate-decks', response_class=JSONResponse)
async def api_generate_deck(request: Request, input: dict):
    supabase.table('api-requests').insert({
        "data": input,
    }).execute()
    deck_uuid, deck_content = generate_deck(input)
    return JSONResponse(content={"uuid": deck_uuid, "status": "success", "debug_data": deck_content})

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
