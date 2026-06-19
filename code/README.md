# Multi-Modal Evidence Review System

Verifies damage claims (car/laptop/package) using images + conversation + user history.

## Setup
pip install google-generativeai pandas Pillow python-dotenv

## API Key
Create .env in repo ROOT (not inside code/):
GEMINI_API_KEY=your_key_here
Get free key: aistudio.google.com

## Run evaluation (20 labeled samples — see accuracy)
cd code
python evaluation/evaluate.py

## Run full predictions (46 claims → output.csv)
cd code
python main.py

## Resume after crash
Just run python main.py again — resumes automatically from progress.json
