from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .observability import logger
from .store import load_data
from .api.routes_advise import router as advise_router
from .api.routes_courses import router as courses_router
from .api.routes_debug import router as debug_router

app = FastAPI(title="Upskill Advisor API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def tracing(request: Request, call_next):
    response = await call_next(request)
    logger.info("http", path=str(request.url), method=request.method, status_code=response.status_code)
    return response

load_data()

@app.on_event("startup")
def _startup():
    load_data()

@app.get("/")
def root():
    return {"ok": True, "service": "upskill-advisor", "version": app.version}

app.include_router(courses_router, prefix="/api", tags=["courses"])
app.include_router(advise_router,  prefix="/api", tags=["advise"])
app.include_router(debug_router,   prefix="/api", tags=["debug"])