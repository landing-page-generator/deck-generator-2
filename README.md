# Deck Generator

Backend for AI deck generator

Deployed as [Deck Generator](https://deck-generator.onrender.com/)

Hacked on [Agents Hackathon @ MIT](https://app.agihouse.org/events/Agents-Hackathon-Powered-by-Jamba-20240928), Sep 28, 2024

# Installation

```bash
cp .env.example .env
nano .env
# then add your GitHub and Gemini secret keys to the .env file
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Run

## Local server

```bash
python main.py
```

or 

```bash
uvicorn main:app --reload
```

or 
```bash
uvicorn main:app --host 0.0.0.0 --port 80 --workers 4
```

# Production deployment  

Auto deployed to Render [https://deck-generator.onrender.com](https://deck-generator.onrender.com/) at each commit to `main` branch.
