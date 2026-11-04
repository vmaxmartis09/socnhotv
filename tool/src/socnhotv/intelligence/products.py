from __future__ import annotations

import json
import logging
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field
from socnhotv.workspace import project_path

logger = logging.getLogger(__name__)


class AffiliateLinks(BaseModel):
    tiktok_shop: str = ""
    shopee: str = ""
    lazada: str = ""
    other: str = ""


class Product(BaseModel):
    id: str
    name: str
    brand: str = ""
    category: str = "general"
    price: float = 0.0
    sale_price: Optional[float] = None
    currency: str = "VND"
    affiliate_links: AffiliateLinks = Field(default_factory=AffiliateLinks)
    usp: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    specs: Dict[str, str] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    target_audience: str = ""
    compliance_notes: str = ""


def list_products(project_id: str) -> List[Product]:
    products_dir = project_path(project_id, "products")
    if not products_dir.exists():
        return []

    items: List[Product] = []
    for p_dir in products_dir.iterdir():
        if p_dir.is_dir() and not p_dir.name.startswith((".", "_")):
            p_json = p_dir / "product.json"
            if p_json.exists():
                try:
                    with open(p_json, "r", encoding="utf-8") as f:
                        items.append(Product(**json.load(f)))
                except Exception as e:
                    logger.warning("Error loading product %s: %s", p_json, e)
    return items


def get_product(project_id: str, product_id: str) -> Optional[Product]:
    p_json = project_path(project_id, "products", product_id, "product.json")
    if not p_json.exists():
        return None
    try:
        with open(p_json, "r", encoding="utf-8") as f:
            return Product(**json.load(f))
    except Exception as e:
        logger.warning("Error reading product %s: %s", product_id, e)
        return None


def save_product(project_id: str, product: Product) -> Product:
    target_dir = project_path(project_id, "products", product.id)
    target_dir.mkdir(parents=True, exist_ok=True)
    p_json = target_dir / "product.json"
    with open(p_json, "w", encoding="utf-8") as f:
        f.write(product.model_dump_json(indent=2))
    return product


def delete_product(project_id: str, product_id: str) -> bool:
    target_dir = project_path(project_id, "products", product_id)
    if not target_dir.exists():
        return False
    trash_dir = project_path(project_id, "products", "_trash")
    trash_dir.mkdir(parents=True, exist_ok=True)
    trash_target = trash_dir / product_id
    if trash_target.exists():
        shutil.rmtree(trash_target)
    shutil.move(str(target_dir), str(trash_target))
    return True


def import_product_from_url(url: str) -> Dict[str, Any]:
    """Extract public OpenGraph metadata without requiring login or cookies."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    title = ""
    image = ""
    description = ""
    price = 0.0

    try:
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                html = resp.text
                
                # Title
                m_og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', html, re.I)
                if m_og_title:
                    title = m_og_title.group(1).strip()
                else:
                    m_title = re.search(r'<title>(.*?)</title>', html, re.I)
                    if m_title:
                        title = m_title.group(1).strip()

                # Image
                m_og_img = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', html, re.I)
                if m_og_img:
                    image = m_og_img.group(1).strip()

                # Description
                m_og_desc = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html, re.I)
                if m_og_desc:
                    description = m_og_desc.group(1).strip()

                # Price heuristic
                m_price = re.search(r'([0-9]{2,3}(?:\.[0-9]{3})+)\s*(?:đ|VND|d)', html, re.I)
                if m_price:
                    raw_p = m_price.group(1).replace(".", "")
                    try:
                        price = float(raw_p)
                    except ValueError:
                        pass
    except Exception as e:
        logger.warning("Failed to fetch product metadata from %s: %s", url, e)

    return {
        "title": title or "Sản phẩm mới",
        "description": description,
        "image": image,
        "price": price,
        "url": url,
    }
