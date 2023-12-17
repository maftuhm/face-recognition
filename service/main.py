from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .welcome import WELCOME_HTML
from .routes import router as api_router
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def welcome_page():
    return WELCOME_HTML


app.include_router(api_router, prefix="/v1")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
