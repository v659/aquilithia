from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
import bcrypt
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
import os
import uuid
import re
import requests
import json
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ADMIN_CREDENTIALS = json.loads(os.getenv("ADMIN_CREDENTIALS", "{}"))
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)          # for public/read operations
supabase_server: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) # for inserts, updates
# Simple in-memory session store for demo
sessions = {}
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "supersecret"))
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
                • Taxation: 0% + 5% VAT
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
from datetime import datetime

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    greeting = None
    user = request.session.get("user")
    timestamp = int(datetime.utcnow().timestamp())  # generate timestamp

    if user:
        if user.get("is_admin", False):
            greeting = f"Hello {user['name']} (admin)!"
        else:
            greeting = f"Hello {user['name']}!"

    # pass timestamp to template
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "greeting": greeting,
            "timestamp": timestamp
        }
    )





@app.post("/ask_ai", response_class=JSONResponse)
async def ask_ai_endpoint(message: str = Form(...)):
    answer = ask_ai(message, is_chat=True)
    return {"answer": answer}




@app.get("/apply", response_class=HTMLResponse)
async def apply_get(request: Request):
    return templates.TemplateResponse("apply.html", {"request": request})

@app.post("/apply", response_class=HTMLResponse)
async def apply_post(request: Request, name: str = Form(...), password: str = Form(...)):
    print(f"\n=== Apply/Register attempt ===")
    print(f"Login/Registration attempt for username: {name}")

    # Admin check
    is_admin = False
    if name in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[name] == password:
        is_admin = True
        print(f"Admin credentials detected for {name}")

    # --- Fetch all users for debug ---
    try:
        all_users = supabase.table("users").select("*").execute()
        print(f"All users in table: {all_users.data}")
    except Exception as e:
        print(f"Error fetching all users: {e}")
        all_users = {"data": []}

    # Check if user exists
    try:
        result = supabase.table("users").select("*").ilike("username", name).execute()

        print(f"Supabase query result for username '{name}': {result.data}")
    except Exception as e:
        print(f"Error querying user: {e}")
        return templates.TemplateResponse("apply.html", {"request": request, "error": f"Database error: {e}"})

    if result.data and len(result.data) > 0:
        # ✅ User already exists → check password
        user = result.data[0]
        stored_hash = user["password"]
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            print(f"Password correct. Logging in user {name}")
            request.session["user"] = {"name": name, "is_admin": user.get("is_admin", False)}
            return RedirectResponse("/", status_code=303)
        else:
            print(f"Incorrect password attempt for {name}")
            return templates.TemplateResponse("apply.html", {"request": request, "error": "Incorrect password!"})
    else:
        # 🆕 New user → register
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        data = {"username": name, "password": hashed_password, "is_admin": is_admin}

        print(f"Registering new user: {name}, admin={is_admin}")
        try:
            supabase_server.table("users").insert(data).execute()
            print(f"User {name} successfully registered")
        except Exception as e:
            print(f"Error registering user {name}: {e}")
            return templates.TemplateResponse("apply.html", {"request": request, "error": f"Failed to register: {e}"})

        # Log in new user
        request.session["user"] = {"name": name, "is_admin": is_admin}
        return RedirectResponse("/", status_code=303)




@app.get("/logout")
async def logout(request: Request):
    # Clear session stored in middleware
    request.session.clear()

    # Redirect back to homepage
    response = RedirectResponse(url="/", status_code=303)
    return response



@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("apply.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    print("Login attempt:", username)
    all_users = supabase.table("users").select("*").execute()
    print("All users in table:", all_users.data)
    result = supabase_server.table("users").select("*").eq("username", username).execute()
    print("Supabase result:", result.data)
    if not result.data:
        return templates.TemplateResponse("apply.html", {"request": request, "error": "Invalid username or password"})

    user = result.data[0]
    stored_hash = user["password"]
    print("Stored hash:", stored_hash)

    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        print("Password mismatch")
        return templates.TemplateResponse("apply.html", {"request": request, "error": "Invalid username or password"})

    request.session["user"] = {"name": user["username"], "is_admin": user.get("is_admin", False)}
    return RedirectResponse("/", status_code=303)




