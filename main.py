from fastapi import FastAPI, Request,Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token;
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status


app = FastAPI()


firestore_db = firestore.Client()


firebase_request_adapter = requests.Request()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")




def getUser(user_token):
    
    
    user = firestore_db.collection('users').document(user_token['user_id'])
    if not user.get().exists:
        user_data={
            
            'name': 'no name yet',
            'age': 0
        }
        firestore_db.collection('users').document(user_token['user_id']).set(user_data)
        
        
    return user


def validateFirebaseIdToken(id_token):
    
    if not id_token:
        return None
    
    
    
    user_token = None
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
    except ValueError as e:
        
        
        print(str(e))
        
    return user_token



@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    
    
    
    id_token = request.cookies.get("token")
    error_message = "no error here"
    user_token = None
    user = None
    
    
    user_token = validateFirebaseIdToken(id_token)
    if not user_token:
        return templates.TemplateResponse("main.html", {"request": request,'user_token':None,'user_email': None,'error_message':"Please log in!",'user_info':None})
    
    
    user = getUser(user_token)
    return templates.TemplateResponse("main.html", {"request": request,'user_token':user_token,'error_message':error_message,'user_info':user.get()})
        
        
@app.get("/update_user",response_class=HTMLResponse)
async def updateForm(request: Request):
    
    id_token = request.cookies.get("token")
    
    
    user_token = validateFirebaseIdToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    
    
    user = getUser(user_token)
    return templates.TemplateResponse("update.html", {"request": request,'user_token':user_token,'error_message':None,'user_info':user.get()})


@app.get("/add_ev", response_class=HTMLResponse)
async def add_ev_form(request: Request):
    return templates.TemplateResponse("add_ev.html", {"request": request})

@app.post("/add_ev", response_class=RedirectResponse)
async def add_ev(request: Request, name: str = Form(...), manufacturer: str = Form(...), year: int = Form(...), 
                 battery_size: float = Form(...), wltp_range: int = Form(...), cost: float = Form(...), 
                 power: float = Form(...)):
    ev_data = {
        'name': name,
        'manufacturer': manufacturer,
        'year': year,
        'battery_size': battery_size,
        'wltp_range': wltp_range,
        'cost': cost,
        'power': power
    }
    firestore_db.collection('evs').add(ev_data)
    return RedirectResponse('/add_ev', status_code=status.HTTP_302_FOUND)

@app.get("/search_ev", response_class=HTMLResponse)
async def search_ev(request: Request):
    # Display form for querying an EV
    return templates.TemplateResponse("search_ev.html", {"request": request})

@app.post("/query_ev", response_class=HTMLResponse)
async def query_ev(request: Request, attribute: str = Form(...), query_value: str = Form(...)):
    # Handle different attribute types and search accordingly
    # For simplicity, we're showing string-based querying here
    evs = firestore_db.collection('evs').where(attribute, '==', query_value).stream()
    ev_list = [ev.to_dict() for ev in evs]
    return templates.TemplateResponse("ev_results.html", {"request": request, "evs": ev_list})


    
    