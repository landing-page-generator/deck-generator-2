import uvicorn
import os
import uuid
import json

from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    FileResponse,
    StreamingResponse,
)

from pptx_generator_v2 import create_pptx_from_json

from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

from img import get_image_from_pexels

from ai import gemini

app = FastAPI()

_ = load_dotenv(Path(__file__).parent / ".env")

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


@app.get("/", response_class=HTMLResponse)
async def read_index():
    # return HTMLResponse("Hello, world!")
    placeholder = """COMPANY: Acme Inc.
PRODUCT: Firefighter Suit
LEAD: John Smith"""

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
    except Exception as _:
        data = data
    deck_uuid, deck_content = generate_deck(data)
    deck_content_html = json.dumps(deck_content, indent=4)
    return HTMLResponse(
        '<a href="/">← Back</a><br><br>'
        f"Deck generated successfully!<br>"
        f"<a href='/pptx/{deck_uuid}.pptx'>Download PPTX</a>"
        f"<hr>"
        f"DECK {deck_uuid}:<br><pre><code class='language-json'>{deck_content_html}</code></pre>"
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/styles/default.min.css">'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.6.0/highlight.min.js"></script>'
        "<script>hljs.highlightAll();</script>"
        '<a href="/">← Back</a><br><br>'
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    decks = (
        supabase.table("decks2")
        .select("uuid, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    deck_uuids_html = "".join(
        f'<li>[{datetime.fromisoformat(deck["created_at"]).strftime("%Y-%m-%d %H:%M")}] <a href="/pptx/{deck["uuid"]}.pptx">PPTX</a></li>'
        for deck in decks.data
    )
    return HTMLResponse(
        f'<html><body><a href="/">← Back</a><br><br><h1>Admin Page: All Decks</h1><ul>{deck_uuids_html}</ul><a href="/">← Back</a></body></html>'
    )


def generate_deck(input: dict):
    master = Path("prompts/master.txt").read_text() + f"\n\n{input}\n"
    master_response = gemini(master)
    master_response = master_response.replace("```json", "").replace("```", "")
    deck_content = json.loads(master_response)

    image = Path("prompts/image.txt").read_text() + f"\n\n{deck_content}\n"
    image_response = gemini(image)
    image_url = get_image_from_pexels(image_response)
    deck_content["list"][0]["imageURL"] = image_url

    # pptx = Path("prompts/pptx.txt").read_text() + f"\n\n{deck_content}\n"
    # pptx_response = gemini(pptx)
    deck_uuid = str(uuid.uuid4())
    pptx_filename = create_pptx_from_json(deck_content, deck_uuid)
    # download_filename = f"deck-{uuid}.pptx"

    # Save the PPTX to Supabase bucket
    with open(pptx_filename, "rb") as file:
        pptx_content = file.read()

    pptx_filename = pptx_filename.split("/")[-1]
    supabase.storage.from_("decks2").upload(pptx_filename, pptx_content)

    supabase.table("decks2").insert(
        {
            "json_content": deck_content,
            "input": input,
            "uuid": deck_uuid,
            "pptx_filename": pptx_filename,
        }
    ).execute()

    return deck_uuid, deck_content


@app.get("/pptx/{uuid}.pptx")
async def generate_pptx(uuid: str):
    data = supabase.table("decks2").select("pptx_filename").eq("uuid", uuid).execute()
    print(data)

    if data:
        pptx_filename = data.data[0]["pptx_filename"]
        pptx_content = supabase.storage.from_("decks2").download(pptx_filename)
        pptx_filename_local = f"decks/{pptx_filename}"
        with open(pptx_filename_local, "wb") as file:
            file.write(pptx_content)

        return FileResponse(
            pptx_filename_local,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=pptx_filename,
        )
    else:
        return {"error": "PPTX file not found"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
