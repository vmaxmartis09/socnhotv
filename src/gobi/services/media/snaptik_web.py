"""SnapTik Web Interface & Local API Server.

Provides a web dashboard mirroring snaptik.vn for one-click video downloading into the project,
integrated with the TikTok Shop Product Warehouse.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from gobi.services.media.snaptik_service import SnaptikService
from gobi.adapters.platforms.tiktok.product_extractor import extract_tiktok_shop_products
from gobi.services.product.ingestion import ingest_tiktok_product

app = FastAPI(title="Gobi SnapTik Downloader", description="Tải video TikTok không logo & đóng gói sản phẩm vào project")
service = SnaptikService()


class ExtractRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    download_audio: bool = False
    download_cover: bool = False
    watermark: bool = False
    hd: bool = True
    output_dir: str = "output/videos"


class IngestProductRequest(BaseModel):
    url: str
    base_dir: str = "data/products"
    download_cover: bool = True
    download_video: bool = True
    download_audio: bool = True


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SnapTik Gobi - Tải Video TikTok & Kho Sản Phẩm</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #fe2c55;
      --secondary: #25f4ee;
      --accent: #f59e0b;
      --bg: #0c0f17;
      --card: #161b26;
      --border: #283042;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at top, #1e1b4b 0%, var(--bg) 60%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
    }
    .container {
      width: 100%;
      max-width: 860px;
    }
    .header {
      text-align: center;
      margin-bottom: 36px;
    }
    .badge {
      display: inline-block;
      padding: 6px 14px;
      background: rgba(254, 44, 85, 0.15);
      color: var(--primary);
      border: 1px solid rgba(254, 44, 85, 0.3);
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 14px;
      letter-spacing: 0.5px;
    }
    h1 {
      font-size: 36px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin-bottom: 12px;
      background: linear-gradient(135deg, #ffffff 40%, var(--secondary) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .subtitle {
      color: var(--text-muted);
      font-size: 16px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.5);
      margin-bottom: 24px;
    }
    .input-group {
      display: flex;
      gap: 12px;
    }
    input[type="text"] {
      flex: 1;
      background: #0f131c;
      border: 1px solid var(--border);
      color: #fff;
      padding: 16px 20px;
      border-radius: 14px;
      font-size: 16px;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    input[type="text"]:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(254, 44, 85, 0.25);
    }
    button.btn-primary {
      background: linear-gradient(135deg, var(--primary) 0%, #e11d48 100%);
      color: #fff;
      border: none;
      padding: 16px 28px;
      font-size: 16px;
      font-weight: 700;
      border-radius: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: transform 0.15s, opacity 0.15s;
    }
    button.btn-primary:hover {
      opacity: 0.95;
      transform: translateY(-1px);
    }
    button.btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }
    .spinner {
      display: inline-block;
      width: 18px;
      height: 18px;
      border: 3px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .options {
      display: flex;
      gap: 20px;
      margin-top: 16px;
      font-size: 14px;
      color: var(--text-muted);
    }
    .options label {
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
    }
    .result-card {
      display: none;
      animation: fadeIn 0.3s ease;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .video-preview {
      display: flex;
      gap: 24px;
      margin-bottom: 24px;
      align-items: flex-start;
    }
    .cover-wrap {
      width: 160px;
      height: 230px;
      border-radius: 14px;
      overflow: hidden;
      flex-shrink: 0;
      background: #000;
      box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    .cover-wrap img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .video-meta {
      flex: 1;
    }
    .video-title {
      font-size: 18px;
      font-weight: 700;
      line-height: 1.4;
      margin-bottom: 12px;
      color: #fff;
    }
    .author-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
    }
    .author-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      border: 1px solid var(--border);
    }
    .author-name {
      font-weight: 700;
      font-size: 15px;
    }
    .author-handle {
      color: var(--text-muted);
      font-size: 13px;
    }
    .stats-row {
      display: flex;
      gap: 12px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }
    .stat-pill {
      background: #0f131c;
      padding: 6px 14px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      border: 1px solid var(--border);
    }
    .product-box {
      margin-bottom: 20px;
      padding: 18px 20px;
      border-radius: 14px;
      background: rgba(245, 158, 11, 0.08);
      border: 1px solid rgba(245, 158, 11, 0.25);
    }
    .product-tag {
      color: #fbbf24;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .product-title {
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
    }
    .product-links {
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 12px;
    }
    .product-links a {
      color: var(--secondary);
      text-decoration: none;
      margin-right: 14px;
    }
    .product-links a:hover { text-decoration: underline; }
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }
    .btn-action {
      background: #202738;
      border: 1px solid var(--border);
      color: #fff;
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      text-decoration: none;
      transition: background 0.15s, border-color 0.15s;
    }
    .btn-action:hover {
      background: #2a3449;
      border-color: var(--secondary);
    }
    .btn-action.ingest-btn {
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      border: none;
      grid-column: 1 / -1;
      font-size: 15px;
    }
    .btn-action.download-proj {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      border: none;
      grid-column: 1 / -1;
    }
    .status-msg {
      margin-top: 14px;
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 600;
      display: none;
      line-height: 1.6;
    }
    .status-msg.success { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status-msg.error { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">🚀 GOBI SOCIAL INTEGRATED PIPELINE</div>
      <h1>SnapTik Video & Kho Sản Phẩm</h1>
      <p class="subtitle">Trích xuất video TikTok không logo + Tự động bóc tách link TikTok Shop đóng gói vào folder sản phẩm</p>
    </div>

    <div class="card">
      <div class="input-group">
        <input type="text" id="urlInput" placeholder="Dán link video TikTok (https://www.tiktok.com/... hoặc https://vt.tiktok.com/...)" />
        <button class="btn-primary" id="btnExtract" onclick="extractVideo()">
          <span id="btnText">Lấy Video & Shop</span>
          <span class="spinner" id="spinner" style="display: none;"></span>
        </button>
      </div>
      <div class="options">
        <label><input type="checkbox" id="optAudio" checked /> Tải kèm Audio MP3</label>
        <label><input type="checkbox" id="optCover" checked /> Tải ảnh bìa (Cover)</label>
        <label><input type="checkbox" id="optHd" checked /> Ưu tiên HD</label>
      </div>
    </div>

    <div class="card result-card" id="resultCard">
      <div class="video-preview">
        <div class="cover-wrap">
          <img id="resCover" src="" alt="Cover" />
        </div>
        <div class="video-meta">
          <div class="video-title" id="resTitle"></div>
          <div class="author-bar">
            <img class="author-avatar" id="resAvatar" src="" alt="Avatar" />
            <div>
              <div class="author-name" id="resAuthorName"></div>
              <div class="author-handle" id="resAuthorHandle"></div>
            </div>
          </div>
          <div class="stats-row">
            <div class="stat-pill" id="statPlays">👀 0 views</div>
            <div class="stat-pill" id="statLikes">❤️ 0 likes</div>
            <div class="stat-pill" id="statComments">💬 0 cmt</div>
            <div class="stat-pill" id="statDuration">⏱️ 0s</div>
          </div>
        </div>
      </div>

      <!-- TikTok Shop Product Integration Box -->
      <div class="product-box" id="productBox" style="display: none;">
        <div class="product-tag">🛒 PHÁT HIỆN GIỎ HÀNG TIKTOK SHOP ĐÍNH KÈM</div>
        <div class="product-title" id="prodTitle"></div>
        <div class="product-links">
          <span><b>Product ID:</b> <code id="prodId"></code></span> | 
          <a id="linkPdp" href="#" target="_blank">🔗 Link TikTok Shop PDP</a> |
          <a id="linkAff" href="#" target="_blank">💰 Link Affiliate Gốc</a>
        </div>
        <button class="btn-action ingest-btn" id="btnIngest" onclick="ingestProductToWarehouse()">
          📦 Tải & Đóng Gói Toàn Diện Vào Kho Sản Phẩm (data/products)
        </button>
      </div>

      <div class="actions-grid">
        <button class="btn-action download-proj" id="btnSaveProj" onclick="downloadIntoProject()">
          📥 Lưu Trực Tiếp Vào output/videos
        </button>
        <a class="btn-action" id="btnDownloadNoWm" href="#" target="_blank" download>
          ⬇️ Tải MP4 (Không Logo)
        </a>
        <a class="btn-action" id="btnDownloadHd" href="#" target="_blank" download style="display:none;">
          ✨ Tải MP4 HD
        </a>
        <a class="btn-action" id="btnDownloadAudio" href="#" target="_blank" download>
          🎵 Tải Audio MP3
        </a>
      </div>

      <div class="status-msg" id="statusMsg"></div>
    </div>
  </div>

  <script>
    let currentData = null;

    function formatNumber(num) {
      if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
      if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
      return num || 0;
    }

    async function extractVideo() {
      const url = document.getElementById('urlInput').value.trim();
      if (!url) {
        alert('Vui lòng dán liên kết video TikTok!');
        return;
      }

      const btn = document.getElementById('btnExtract');
      const btnText = document.getElementById('btnText');
      const spinner = document.getElementById('spinner');
      const resultCard = document.getElementById('resultCard');
      const statusMsg = document.getElementById('statusMsg');

      btn.disabled = true;
      btnText.textContent = 'Đang phân tích...';
      spinner.style.display = 'inline-block';
      statusMsg.style.display = 'none';

      try {
        const resp = await fetch('/api/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url })
        });
        const res = await resp.json();
        if (!resp.ok || !res.success) {
          throw new Error(res.detail || res.error || 'Trích xuất thất bại');
        }

        currentData = res.data;
        displayResult(res.data, res.shop_product);
      } catch (err) {
        alert('Lỗi: ' + err.message);
      } finally {
        btn.disabled = false;
        btnText.textContent = 'Lấy Video & Shop';
        spinner.style.display = 'none';
      }
    }

    function displayResult(data, shopProduct) {
      const resultCard = document.getElementById('resultCard');
      document.getElementById('resCover').src = data.media.cover_url || '';
      document.getElementById('resTitle').textContent = data.title || '(Không có tiêu đề)';
      document.getElementById('resAvatar').src = data.author.avatar || '';
      document.getElementById('resAuthorName').textContent = data.author.nickname || 'Tác giả';
      document.getElementById('resAuthorHandle').textContent = '@' + (data.author.unique_id || 'tiktok');

      document.getElementById('statPlays').textContent = '👀 ' + formatNumber(data.stats.plays) + ' views';
      document.getElementById('statLikes').textContent = '❤️ ' + formatNumber(data.stats.likes) + ' likes';
      document.getElementById('statComments').textContent = '💬 ' + formatNumber(data.stats.comments) + ' cmt';
      document.getElementById('statDuration').textContent = '⏱️ ' + data.duration + 's';

      const btnNoWm = document.getElementById('btnDownloadNoWm');
      btnNoWm.href = data.media.video_url || '#';

      const btnHd = document.getElementById('btnDownloadHd');
      if (data.media.video_hd_url) {
        btnHd.href = data.media.video_hd_url;
        btnHd.style.display = 'flex';
      } else {
        btnHd.style.display = 'none';
      }

      const btnAudio = document.getElementById('btnDownloadAudio');
      if (data.media.audio_url) {
        btnAudio.href = data.media.audio_url;
        btnAudio.style.display = 'flex';
      } else {
        btnAudio.style.display = 'none';
      }

      // Handle shop product display
      const productBox = document.getElementById('productBox');
      if (shopProduct && shopProduct.has_shop_anchor && shopProduct.products && shopProduct.products.length > 0) {
        const p = shopProduct.products[0];
        document.getElementById('prodTitle').textContent = p.title || p.keyword || 'Sản phẩm TikTok Shop';
        document.getElementById('prodId').textContent = p.product_id;
        document.getElementById('linkPdp').href = p.pdp_url || '#';
        document.getElementById('linkAff').href = p.affiliate_pdp_url || '#';
        productBox.style.display = 'block';
      } else {
        productBox.style.display = 'none';
      }

      resultCard.style.display = 'block';
    }

    async function ingestProductToWarehouse() {
      if (!currentData) return;
      const btn = document.getElementById('btnIngest');
      const statusMsg = document.getElementById('statusMsg');
      const url = currentData.original_url;

      btn.disabled = true;
      btn.textContent = '⏳ Đang trích xuất link Shop & tạo hệ thống folder...';
      statusMsg.style.display = 'none';

      try {
        const resp = await fetch('/api/ingest-product', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: url,
            base_dir: 'data/products',
            download_cover: true,
            download_video: true,
            download_audio: true
          })
        });
        const res = await resp.json();
        if (!resp.ok || !res.success) {
          throw new Error(res.detail || res.error || 'Đóng gói sản phẩm thất bại');
        }

        const p = res.products[0];
        statusMsg.className = 'status-msg success';
        statusMsg.innerHTML = '🎉 <b>ĐÃ ĐÓNG GÓI THÀNH CÔNG VÀO HỆ THỐNG FOLDER SẢN PHẨM!</b><br>' +
          '📦 Tên sản phẩm: <b>' + p.title + '</b><br>' +
          '📁 Thư mục lưu trữ: <code>' + p.folder + '</code><br>' +
          '🎬 Video sạch: <code>' + p.folder + '/video_clean.mp4</code><br>' +
          '🎵 Audio MP3: <code>' + p.folder + '/video_clean_audio.mp3</code><br>' +
          '🖼️ Ảnh bìa: <code>' + p.folder + '/cover.jpg</code><br>' +
          '📋 Metadata: <code>' + p.metadata_file + '</code> & <code>README.md</code><br>' +
          '📚 Đã ghi sổ cái Catalog: <code>' + res.catalog_file + '</code>';
        statusMsg.style.display = 'block';
      } catch (err) {
        statusMsg.className = 'status-msg error';
        statusMsg.textContent = '❌ Lỗi: ' + err.message;
        statusMsg.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = '📦 Tải & Đóng Gói Toàn Diện Vào Kho Sản Phẩm (data/products)';
      }
    }

    async function downloadIntoProject() {
      if (!currentData) return;
      const btn = document.getElementById('btnSaveProj');
      const statusMsg = document.getElementById('statusMsg');
      const url = currentData.original_url;

      btn.disabled = true;
      btn.textContent = '⏳ Đang tải và lưu vào output/videos...';
      statusMsg.style.display = 'none';

      try {
        const resp = await fetch('/api/download', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            url: url,
            download_audio: document.getElementById('optAudio').checked,
            download_cover: document.getElementById('optCover').checked,
            hd: document.getElementById('optHd').checked,
            output_dir: 'output/videos'
          })
        });
        const res = await resp.json();
        if (!resp.ok || !res.success) {
          throw new Error(res.error || 'Lưu thất bại');
        }

        statusMsg.className = 'status-msg success';
        statusMsg.innerHTML = '✅ <b>Đã lưu thành công vào output/videos!</b><br>' +
          '🎬 Video: <code>' + (res.video_path || '') + '</code><br>' +
          (res.audio_path ? '🎵 Audio: <code>' + res.audio_path + '</code><br>' : '') +
          '📋 Metadata: <code>' + (res.metadata_path || '') + '</code>';
        statusMsg.style.display = 'block';
      } catch (err) {
        statusMsg.className = 'status-msg error';
        statusMsg.textContent = '❌ Lỗi: ' + err.message;
        statusMsg.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = '📥 Lưu Trực Tiếp Vào output/videos';
      }
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index_page():
    return HTML_TEMPLATE


@app.post("/api/extract")
def extract_endpoint(payload: ExtractRequest):
    try:
        info = service.get_info(payload.url)
        # Check if video has attached TikTok Shop products
        shop_res = None
        try:
            shop_res = extract_tiktok_shop_products(payload.url)
        except Exception:
            shop_res = None

        return {
            "success": True,
            "data": info.model_dump(),
            "shop_product": shop_res
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download")
def download_endpoint(payload: DownloadRequest):
    res = service.download(
        url=payload.url,
        output_dir=payload.output_dir,
        watermark=payload.watermark,
        hd=payload.hd,
        download_audio=payload.download_audio,
        download_cover=payload.download_cover,
        save_metadata=True,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.error or "Download failed")
    return res.model_dump()


@app.post("/api/ingest-product")
def ingest_product_endpoint(payload: IngestProductRequest):
    try:
        res = ingest_tiktok_product(
            video_url=payload.url,
            base_dir=payload.base_dir,
            download_cover=payload.download_cover,
            download_video=payload.download_video,
            download_audio=payload.download_audio,
        )
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error", "Ingestion failed"))
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def run_web_server(host: str = "0.0.0.0", port: int = 8088):
    """Start local web server."""
    import uvicorn
    print(f"\n[+] Khởi chạy Gobi SnapTik & Product Web UI tại: http://localhost:{port}")
    print("[*] Mở trình duyệt để dán link, tải source video và đóng gói sản phẩm vào project.")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_web_server()
