from fastapi import FastAPI, Request,Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.oauth2.id_token;
from google.auth.transport import requests
from google.cloud import firestore
import starlette.status as status
import datetime


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
    
     # Check if an EV with the same name already exists
    existing_ev_query = firestore_db.collection('evs').where("name", "==", name).limit(1).stream()
    existing_ev = list(existing_ev_query)

    if existing_ev:
        # EV with the same name exists, so do not add a new one.
        return RedirectResponse(url="/add_ev?error=EV name already exists", status_code=status.HTTP_302_FOUND)
    
    
    
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
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

@app.get("/search_ev", response_class=HTMLResponse)
async def search_ev(request: Request):
    # Display form for querying an EV
    return templates.TemplateResponse("search_ev.html", {"request": request})

@app.post("/query_ev", response_class=HTMLResponse)
async def query_ev(request: Request, name: str = Form(""), manufacturer: str = Form(""), year: str = Form(""),
                   battery_size: str = Form(""), wltp_range: str = Form(""), cost: str = Form(""), power: str = Form("")):
    ev_query = firestore_db.collection('evs')
    
    # Construct query based on provided input fields
    if name:
        ev_query = ev_query.where("name", '==', name)
    if manufacturer:
        ev_query = ev_query.where("manufacturer", '==', manufacturer)
    if year:
        ev_query = ev_query.where("year", '==', int(year))
    if battery_size:
        ev_query = ev_query.where("battery_size", '==', float(battery_size))
    if wltp_range:
        ev_query = ev_query.where("wltp_range", '==', int(wltp_range))
    if cost:
        ev_query = ev_query.where("cost", '==', float(cost))
    if power:
        ev_query = ev_query.where("power", '==', float(power))

    # Fetch and stream the query results
    evs = ev_query.stream()
    ev_list = [{"id": ev.id, **ev.to_dict()} for ev in evs]
    
    return templates.TemplateResponse("ev_results.html", {"request": request, "evs": ev_list})


@app.post("/ev/{ev_id}/review", response_class=RedirectResponse)
async def submit_review(request: Request, ev_id: str, comment: str = Form(...), rating: int = Form(...)):
    # Construct the review data
    review = {
        'comment': comment,
        'rating': rating,
        'datetime': datetime.datetime.now()
    }
    
    # Add the review to sub-doc of the EV document
    ev_reviews_ref = firestore_db.collection('evs').document(ev_id).collection('reviews')
    ev_reviews_ref.add(review)

    return RedirectResponse(url=f"/ev/{ev_id}", status_code=status.HTTP_302_FOUND)



@app.get("/ev/{ev_id}", response_class=HTMLResponse)
async def ev_detail(request: Request, ev_id: str):
    user_token = validateFirebaseIdToken(request.cookies.get("token"))
    ev_document = firestore_db.collection('evs').document(ev_id).get()

    if ev_document.exists:
        ev_data = ev_document.to_dict()
        ev_data['id'] = ev_id

        # Fetch reviews for the EV and calculate the average score
        reviews_query = firestore_db.collection('evs').document(ev_id).collection('reviews').order_by('datetime', direction=firestore.Query.DESCENDING)
        reviews = reviews_query.stream()
        review_list = [review.to_dict() for review in reviews]

        # Calculate average score
        total_score = sum(review['rating'] for review in review_list)
        average_score = total_score / len(review_list) if review_list else 0

        return templates.TemplateResponse("ev_detail.html", {
            "request": request,
            "ev": ev_data,
            "ev_id": ev_id,
            "reviews": review_list,
            "average_score": average_score,
            "user_token": user_token
        })
    else:
        return RedirectResponse(url="/search_ev", status_code=status.HTTP_302_FOUND)



@app.get("/ev/{ev_id}/edit", response_class=HTMLResponse)
async def edit_ev_form(request: Request, ev_id: str):
    # Verify user token
    user_token = validateFirebaseIdToken(request.cookies.get("token"))
    if not user_token:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    ev_document = firestore_db.collection('evs').document(ev_id).get()
    if ev_document.exists:
        return templates.TemplateResponse("edit_ev.html", {
            "request": request,
            "ev": ev_document.to_dict(),
            "ev_id": ev_id
        })
    else:
        return RedirectResponse(url="/search_ev", status_code=status.HTTP_302_FOUND)

@app.post("/ev/{ev_id}/update", response_class=RedirectResponse)
async def update_ev(request: Request, ev_id: str, name: str = Form(...), manufacturer: str = Form(...), 
                    year: int = Form(...), battery_size: str = Form(...), wltp_range: str = Form(...), 
                    cost: str = Form(...), power: str = Form(...)):
    # Verify user token
    user_token = validateFirebaseIdToken(request.cookies.get("token"))
    if not user_token:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Prepare the updated data
    updated_data = {
        'name': name,
        'manufacturer': manufacturer,
        'year': int(year),
        'battery_size': float(battery_size),
        'wltp_range': int(wltp_range),
        'cost': float(cost),
        'power': float(power)
    }

    # Update EV document
    firestore_db.collection('evs').document(ev_id).update(updated_data)
    
    return RedirectResponse(url=f"/ev/{ev_id}", status_code=status.HTTP_302_FOUND)



# delete ev
@app.post("/ev/{ev_id}/delete", response_class=RedirectResponse)
async def delete_ev(request: Request, ev_id: str):
    # Verify user token
    user_token = validateFirebaseIdToken(request.cookies.get("token"))
    if not user_token:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Delete the EV document
    firestore_db.collection('evs').document(ev_id).delete()
    
    return RedirectResponse(url="/search_ev", status_code=status.HTTP_302_FOUND)

# compare ev
@app.get("/compare_ev", response_class=HTMLResponse)
async def compare_ev_form(request: Request):
    evs = firestore_db.collection('evs').stream()
    ev_list = [{"id": ev.id, **ev.to_dict()} for ev in evs]
    return templates.TemplateResponse("compare_ev.html", {"request": request, "evs": ev_list})

@app.get("/perform_comparison", response_class=HTMLResponse)
async def perform_comparison(request: Request, ev1_id: str, ev2_id: str):
    ev_document_1 = firestore_db.collection('evs').document(ev1_id).get()
    ev_document_2 = firestore_db.collection('evs').document(ev2_id).get()

    if ev_document_1.exists and ev_document_2.exists:
        ev1_data = ev_document_1.to_dict()
        ev1_data['id'] = ev1_id  # Include the ID in the data for hyperlinking
        ev2_data = ev_document_2.to_dict()
        ev2_data['id'] = ev2_id  # Include the ID in the data for hyperlinking
        # Pass the EV data to the comparison template
        return templates.TemplateResponse("comparison_result.html", {
            "request": request,
            "ev1": ev1_data,
            "ev2": ev2_data
        })
    else:
        # If one of the EVs doesn't exist, redirect back to the comparison selection page
        return RedirectResponse(url="/compare_ev", status_code=status.HTTP_302_FOUND)


