# Deck Generator

Backend for AI deck generator

Deployed at xxx

Hacked on [Agents Hackathon @ MIT](https://app.agihouse.org/events/Agents-Hackathon-Powered-by-Jamba-20240928), Sep 28, 2024

# Installation

```bash
cp .env.example .env
nano .env
# then add your GitHub and Gemini secret keys to the .env file
virtualenv venv
source venv/bin/activate
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

# Production deployment  

Auto deployed to Vercel xxx at each commit to `main` branch.
