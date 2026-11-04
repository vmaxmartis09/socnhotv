"""Intelligence & Products API routes plugin."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from socnhotv.intelligence.analyzer import analyze_video
from socnhotv.intelligence.contracts import (
    VideoBlueprint,
    list_video_blueprints,
    load_video_blueprint,
)
from socnhotv.intelligence.patterns import aggregate_patterns
from socnhotv.intelligence.products import (
    Product,
    delete_product,
    get_product,
    import_product_from_url,
    list_products,
    save_product,
)
from socnhotv.intelligence.script_gen import GeneratorType, generate_complete_script
from socnhotv.video.contracts import Platform

router = APIRouter(tags=["intel"])


@router.get("/intel/_ping")
async def ping_intel():
    return {"status": "ok", "module": "intel"}


# --- Products CRUD ---

@router.get("/projects/{project_id}/products")
async def list_products_api(project_id: str):
    return [p.model_dump() for p in list_products(project_id)]


@router.post("/projects/{project_id}/products")
async def create_product_api(project_id: str, product: Product):
    saved = save_product(project_id, product)
    return saved.model_dump()


@router.get("/projects/{project_id}/products/{product_id}")
async def get_product_api(project_id: str, product_id: str):
    p = get_product(project_id, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")
    return p.model_dump()


@router.put("/projects/{project_id}/products/{product_id}")
async def update_product_api(project_id: str, product_id: str, product: Product):
    if product.id != product_id:
        product.id = product_id
    saved = save_product(project_id, product)
    return saved.model_dump()


@router.delete("/projects/{project_id}/products/{product_id}")
async def delete_product_api(project_id: str, product_id: str):
    ok = delete_product(project_id, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm để xoá.")
    return {"status": "ok", "message": f"Sản phẩm {product_id} đã chuyển vào thùng rác."}


class ImportUrlRequest(BaseModel):
    url: str


@router.post("/projects/{project_id}/products/import-url")
async def import_product_url_api(project_id: str, req: ImportUrlRequest):
    return import_product_from_url(req.url)


# --- Video Blueprints & Patterns ---

@router.post("/projects/{project_id}/intel/analyze/{source_id}")
async def analyze_video_api(project_id: str, source_id: str):
    try:
        bp = analyze_video(project_id, source_id)
        return bp.model_dump()
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích blueprint: {e}")


@router.get("/projects/{project_id}/intel/blueprints")
async def list_blueprints_api(project_id: str):
    items = list_video_blueprints(project_id)
    return [b.model_dump() for b in items]


@router.get("/projects/{project_id}/intel/blueprints/{blueprint_id}")
async def get_blueprint_api(project_id: str, blueprint_id: str):
    bp = load_video_blueprint(project_id, blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Không tìm thấy blueprint.")
    return bp.model_dump()


@router.get("/projects/{project_id}/intel/patterns")
async def get_patterns_api(project_id: str, niche: Optional[str] = Query(None)):
    return aggregate_patterns(project_id, niche=niche)


# --- Script Generation ---

class GenerateScriptRequest(BaseModel):
    product_id: str
    blueprint_id: Optional[str] = None
    generator_type: GeneratorType = "koc_review"
    character_name: str = "LyLy"
    voice_id: str = "soc-nho"
    platforms: List[Platform] = ["tiktok", "reels", "shorts"]


@router.post("/projects/{project_id}/intel/generate-script")
async def generate_script_api(project_id: str, req: GenerateScriptRequest):
    product = get_product(project_id, req.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm.")

    blueprint = None
    if req.blueprint_id:
        blueprint = load_video_blueprint(project_id, req.blueprint_id)

    res = generate_complete_script(
        project_id=project_id,
        product=product,
        generator_type=req.generator_type,
        blueprint=blueprint,
        character_name=req.character_name,
        voice_id=req.voice_id,
        platforms=req.platforms,
    )
    return res
