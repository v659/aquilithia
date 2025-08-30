from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import re

app = FastAPI()

# Mount static folder for CSS

app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# --- AI Function ---
CLEANR = re.compile('<.*?>')
def cleanhtml(raw_html):
    return re.sub(CLEANR, '', raw_html)

def ask_ai(message, is_chat=False):
    url = "https://ai.hackclub.com/chat/completions"
    headers = {"Content-Type": "application/json"}

    system_prompt = "Answer the question directly."
    if is_chat:
        system_prompt = (
            "Give direct responses only, no thoughts. If a user is asking a specific questions, give a specific"
            "answer from the system prompts you have been given. for example, if the user asks what are the cultures and "
            "rituals, respond with a summary of the section 📜 Culture & Rituals"
    
            

            """Here is some information about aqualithya: 🏛️ General Overview

                • Name: The Sovereign Ceremonial Republic of Aqualithia
                • Type: Micronation with symbolic sovereignty, rooted in creative governance and ceremonial bureaucracy
                • Founded: 26th May 2025 as Communist puffer empire later became the republic of aqualithia
                • Purpose: To celebrate imaginative statecraft, ritualized administration, and playful diplomacy
                • Recognition: Operates within legal boundaries of its host nation; sovereignty is symbolic and respectful
                
                
                ---
                
                📍 Location
                
                • Territory: Privately owned residence within a gated community in the USA
                • Status: Non-contiguous, ceremonial territory
                • Map: Optional stylized map showing ministries, embassies (digital or symbolic), and borders of imagination
                • Access: Virtual citizenship and diplomatic engagement encouraged
                
                
                ---
                
                💬 Motto & Identity
                
                • Motto: Examples:• “Precision in Whimsy, Sovereignty in Spirit”
                • “Where Ceremony Meets Reality”
                • “Aqualithia: Governed by Imagination”
                
                
                ---
                
                💰 Economy
                
                • Currency: PUFB (Pufferbucks)
                • Peg System: Describe how PUFB is pegged (e.g., to USD, ceremonial value, or internal GDP metrics)
                • GDP: 570000 Puffer bucks, 350000 dollars 
                • Taxation: 80%
                • Institutions: Aqualithian Central Bank, Puffer mail 
                • Digital Infrastructure: E-banking platforms, ceremonial checks, budget dashboards
                
                
                ---
                
                🧑‍⚖️ Government & Roles
                
                • Structure: Democracy
                • Key Roles:• Sovereign: Head of state (active)
                • Ministers: Economy, Culture, Diplomacy, Rituals, etc.
                • Citizens: Rights, duties, and ceremonial titles
                
                • Election or Appointment:By vote
                
                
                ---
                
                📜 Culture & Rituals
                
                • Ceremonies: Budget Day, Treaty Signing, Citizen Induction
                • Documents: Official checks, proclamations, ID cards
                
                • Holidays: Founding Day, Sovereignty Week, etc.
                
                
                ---
                
                🌐 Digital Citizenship
                
                • Join Aqualithia: Application form, oath of imagination, digital ID
                • Citizen Portal: Access to banking, ministries, document generators
                • Embassies: Virtual embassies or forums for intermicronational diplomacy"""
            "If asked about Aqualithia, mention our football, basketball, swimming, cricket, and hockey teams, "
            "and link to our YouTube channel: https://www.youtube.com/@AQUALITHIA-Republic"
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]

    data = {"messages": messages}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()
        return cleanhtml(content)
    except Exception as e:
        return f"Could not connect to AI service: {e}"

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask_ai", response_class=JSONResponse)
async def ask_ai_endpoint(message: str = Form(...)):
    answer = ask_ai(message, is_chat=True)
    return {"answer": answer}
