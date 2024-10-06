import uvicorn
import os
import uuid
import json

from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse

from pptx_generator_v2 import create_pptx_from_json

from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

from img import get_image_from_pexels

from ai import gemini, ai21

app = FastAPI()

_ = load_dotenv(Path(__file__).parent / ".env")

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


@app.get("/", response_class=HTMLResponse)
async def read_index():
    # return HTMLResponse("Hello, world!")
    placeholder = """
{
    "lead": { "name": "John Smith", "email": "john.smith@gmail.com"},
    "persona": { "name": "Firefighter" },
    "company": { "name": "Sundai" }
}"""

    return HTMLResponse(
        f"""
    <html>
    <body>
    <h1>Deck Generation Form</h1>
    <form action="/generate-deck" method="post">
        <label for="lead">Data: (you can put here whatever you want in any format)</label><br>
        <textarea id="data" name="data" rows="10" cols="100">{placeholder}</textarea><br>
        <input type="submit" value="Generate Deck" onclick="this.form.submit(); this.disabled=true;">
    </form>
    </body>
    </html>
    """
    )


@app.post("/generate-deck", response_class=HTMLResponse)
async def generate_deck_form(request: Request):
    form_data = await request.form()
    data = form_data.get("data")
    try:
        data = json.loads(data)
    except:
        data = data
    deck_uuid, deck_content = generate_deck(data)
    deck_content_html = json.dumps(deck_content, indent=4)
    return HTMLResponse(
        "Deck generated successfully!<br><br>"
        f"URL: <a href='https://sales-six-theta.vercel.app/{deck_uuid}'><b>https://sales-six-theta.vercel.app/{deck_uuid}</b></a><br><br>"
        f"<hr><br><br>"
        f"UUID: {deck_uuid}<br><br>"
        f"DECK:<br><pre>{deck_content_html}</pre>"
        '<a href="/">← Back</a>'
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    decks = (
        supabase.table("decks")
        .select("uuid, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    deck_uuids_html = "".join(
        f'<li>[{datetime.fromisoformat(deck["created_at"]).strftime("%Y-%m-%d %H:%M")}] <a href="https://sales-six-theta.vercel.app/{deck["uuid"]}">html</a>, <a href="https://deck-generator.onrender.com/pptx/{deck["uuid"]}">pptx</a></li>'
        for deck in decks.data
    )
    return HTMLResponse(
        f'<html><body><h1>Admin Page</h1><h2>All Decks:</h2><ul>{deck_uuids_html}</ul><a href="/">← Back</a></body></html>'
    )


def generate_deck(input: dict):
    deck_uuid = str(uuid.uuid4())

    master = Path("prompts/master.txt").read_text() + f"\n\n{input}\n"
    try:
        master_response = gemini(master)
        master_response = master_response.replace("```json", "").replace("```", "")
        deck_content = json.loads(master_response)
    except:
        master_response = gemini(master)
        master_response = master_response.replace("```json", "").replace("```", "")
        deck_content = json.loads(master_response)

    image = Path("prompts/image.txt").read_text() + f"\n\n{deck_content}\n"
    image_response = gemini(image)
    image_url = get_image_from_pexels(image_response)
    deck_content["list"][0]["imageURL"] = image_url

    # pptx = Path("prompts/pptx.txt").read_text() + f"\n\n{deck_content}\n"
    # pptx_response = gemini(pptx)
    pptx_response = None

    supabase.table("decks").insert(
        {"data": deck_content, "input": input, "uuid": deck_uuid, "pptx": pptx_response}
    ).execute()

    return deck_uuid, deck_content


@app.post("/api/generate-decks", response_class=JSONResponse)
async def api_generate_deck(request: Request, input: dict):
    supabase.table("api-requests").insert(
        {
            "data": input,
        }
    ).execute()
    deck_uuid, deck_content = generate_deck(input)
    return JSONResponse(
        content={
            "uuid": deck_uuid,
            "url": f"https://sales-six-theta.vercel.app/{deck_uuid}",
            "status": "success",
            "debug_data": deck_content,
        }
    )


@app.get("/pptx/{uuid}")
async def generate_pptx(uuid: str):
    # Create a presentation object

    data = supabase.table("decks").select("data").eq("uuid", uuid).execute()

    pptx_filename = create_pptx_from_json(data, uuid)

    # Return the file as a downloadable response
    return FileResponse(
        pptx_filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=pptx_filename,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
