from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token 
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status

#define the app that will contain all of our routing for Fast APT
app = FastAPI()


firebase_request_adapter = requests.Request()


app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    
    
    
    id_token = request.cookies.get("token")
    error_message = "No error here"
    user_token = None


    if id_token:
        try:
           user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        except ValueError as err:
        
        
            print(str(err))
        
    return templates.TemplateResponse("main.html", {'request': request, 'user_token': user_token, 'error_message': error_message})
        
        