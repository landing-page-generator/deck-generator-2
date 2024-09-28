import uvicorn
import os

from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr

from supabase import create_client, Client

app = FastAPI()

# class InputData(BaseModel):
#     idea: str
#     existing_page_url: str | None = None
#     existing_page: str | None = None
#     email: str | None = None

@app.get('/', response_class=HTMLResponse)
async def read_index():
    return HTMLResponse('Hello, world!')


@app.post('/api/generate-decks', response_class=JSONResponse)
async def process_data(request: Request, data: dict = None):
    supabase_url: str = os.environ.get("SUPABASE_URL")
    supabase_key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    supabase.table('api-requests').insert({
        "data": data,
    }).execute()
    return JSONResponse(content={"message": "Data received and is being processed... <3"})

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)