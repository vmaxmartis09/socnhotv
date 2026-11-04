"""Intelligence & Products API routes plugin."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from socnhotv.intelligence.analyzer import analyze_video
from socnhotv.intelligence.channel_analyze import analyze_channel
from socnhotv.intelligence.channel_ingest import ingest_channel
from socnhotv.intelligence.contracts import (
    ChannelBlueprint,
    ContentIdea,
    VideoBlueprint,
    list_channel_blueprints,
    list_content_ideas,
    list_video_blueprints,
    load_channel_blueprint,
    load_content_idea,
    load_video_blueprint,
)
from socnhotv.intelligence.ideas import (
    generate_ideas_batch,
    promote_idea,
    schedule_idea_to_social,
    update_idea_status,
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
from socnhotv.intelligence.strategy import (
    generate_channel_strategy,
    load_channel_strategy,
)
from socnhotv.video.contracts import Platform
from socnhotv.workspace import project_path

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


# --- B4: Channel Intelligence ---

class IngestChannelRequest(BaseModel):
    url: str
    max_videos: int = 50


@router.post("/projects/{project_id}/intel/channels")
async def ingest_channel_api(project_id: str, req: IngestChannelRequest):
    try:
        meta = ingest_channel(project_id, req.url, max_videos=req.max_videos)
        analysis = analyze_channel(project_id, meta["id"])
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi nạp và phân tích kênh: {e}")


@router.get("/projects/{project_id}/intel/channels")
async def list_channels_api(project_id: str):
    channels_dir = project_path(project_id, "knowledge", "channels")
    if not channels_dir.exists():
        return []

    channels = []
    for d in channels_dir.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            cfg = d / "channel.json"
            if cfg.exists():
                try:
                    with open(cfg, "r", encoding="utf-8") as f:
                        channels.append(json.load(f))
                except Exception:
                    continue
    return channels


@router.get("/projects/{project_id}/intel/channels/{channel_id}")
async def get_channel_analysis_api(project_id: str, channel_id: str):
    try:
        return analyze_channel(project_id, channel_id)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích kênh: {e}")


# --- B4: Channel Strategy ---

class StrategyRequest(BaseModel):
    channel_ids: List[str] = Field(default_factory=list)


@router.post("/projects/{project_id}/intel/strategy")
async def generate_strategy_api(project_id: str, req: StrategyRequest):
    try:
        return generate_channel_strategy(project_id, req.channel_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo chiến lược: {e}")


@router.get("/projects/{project_id}/intel/strategy")
async def get_strategy_api(project_id: str):
    strat = load_channel_strategy(project_id)
    if not strat:
        # Generate default strategy if none exists
        strat = generate_channel_strategy(project_id, [])
    return strat


# --- B4: Content Ideas & Kanban ---

@router.post("/projects/{project_id}/intel/ideas/generate")
async def generate_ideas_api(project_id: str, count: int = Query(30)):
    ideas = generate_ideas_batch(project_id, count=count)
    return [i.model_dump() for i in ideas]


@router.get("/projects/{project_id}/intel/ideas")
async def list_ideas_api(
    project_id: str,
    status: Optional[str] = Query(None),
):
    all_ideas = list_content_ideas(project_id)
    if status:
        all_ideas = [i for i in all_ideas if i.status == status]
    return [i.model_dump() for i in all_ideas]


class UpdateIdeaRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None


@router.patch("/projects/{project_id}/intel/ideas/{idea_id}")
async def update_idea_api(project_id: str, idea_id: str, req: UpdateIdeaRequest):
    updated = update_idea_status(
        project_id, idea_id, status=req.status, priority=req.priority
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ý tưởng {idea_id}")
    return updated.model_dump()


class PromoteIdeaRequest(BaseModel):
    product_id: Optional[str] = None
    character_name: str = "LyLy"
    voice_id: str = "soc-nho"


@router.post("/projects/{project_id}/intel/ideas/{idea_id}/promote")
async def promote_idea_api(project_id: str, idea_id: str, req: PromoteIdeaRequest):
    try:
        return promote_idea(
            project_id=project_id,
            idea_id=idea_id,
            product_id=req.product_id,
            character_name=req.character_name,
            voice_id=req.voice_id,
        )
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi thăng hạng ý tưởng: {e}")


@router.post("/projects/{project_id}/intel/ideas/{idea_id}/schedule")
async def schedule_idea_api(project_id: str, idea_id: str):
    try:
        return schedule_idea_to_social(project_id, idea_id)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lên lịch ý tưởng: {e}")
