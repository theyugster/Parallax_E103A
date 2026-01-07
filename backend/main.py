from fastapi import FastAPI
from routes import router  # Import the router we just made
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins (good for dev),should be changed in the future
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Plug it in!
@app.get("/")
async def root():
    return {"message": "EV App Backend Running"}
app.include_router(router)