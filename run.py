from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn,os
from app import customer,models,dashboard
from app.database import Base,engine
from fastapi.templating import Jinja2Templates

models.Base.metadata.create_all(bind=engine)

app = FastAPI(redoc_url=None)

# origins = ["https://pawn.youngstorage.in","http://localhost:3000","http://localhost:8000"]

origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customer.router,prefix="/api")
app.include_router(dashboard.router,prefix="/api")

app.mount("/images", StaticFiles(directory="images"), name="images")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=FileResponse)
async def serve_vite():
    index_path = os.path.join("static", "index.html")
    return FileResponse(index_path)

# Catch-all route to serve index.html for any undefined route (for frontend routing)
# @app.get("/{full_path:path}", response_class=FileResponse)
# async def serve_spa(full_path: str):
#     index_path = os.path.join("static", "index.html")
#     return FileResponse(index_path)

if __name__ == "__main__":
    uvicorn.run("run:app",host="0.0.0.0",port=8000,reload=True)
