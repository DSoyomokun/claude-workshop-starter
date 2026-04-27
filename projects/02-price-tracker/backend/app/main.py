from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.models import AddItemRequest, BulkAddRequest, ItemResponse, PricePoint, AuthStatusResponse, RefreshResult
from app.service import PriceService
from app.scheduler import start_scheduler, stop_scheduler
import app.auth as auth_module

service = PriceService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler(service)
    yield
    stop_scheduler()


app = FastAPI(title="Grailed Price Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/items", response_model=ItemResponse)
async def add_item(body: AddItemRequest):
    try:
        return await service.add_item(body.url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/items/bulk", response_model=list[ItemResponse])
async def add_bulk(body: BulkAddRequest):
    return await service.add_bulk(body.urls)


@app.get("/items", response_model=list[ItemResponse])
def get_items():
    return service.get_items()


@app.get("/items/{item_id}/history", response_model=list[PricePoint])
def get_history(item_id: int):
    return service.get_history(item_id)


@app.post("/items/{item_id}/refresh", response_model=RefreshResult)
async def refresh_item(item_id: int):
    return await service.refresh_item(item_id)


@app.post("/refresh-all", response_model=list[RefreshResult])
async def refresh_all():
    return await service.refresh_all()


@app.post("/items/import/brand-page", response_model=list[ItemResponse])
async def import_brand_page(body: AddItemRequest):
    try:
        return await service.add_from_brand_page(body.url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/items/import/saved", response_model=list[ItemResponse])
async def import_saved_items():
    try:
        return await service.add_from_saved_items()
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status():
    username = await auth_module.get_logged_in_username()
    return AuthStatusResponse(logged_in=username is not None, username=username)


@app.post("/auth/login")
async def trigger_login():
    await auth_module.login_and_save_session()
    username = await auth_module.get_logged_in_username()
    return AuthStatusResponse(logged_in=username is not None, username=username)
