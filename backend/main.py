"""
楽天ROOMアイテムマネージャー - FastAPIメインアプリケーション
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import API_TITLE, API_VERSION, API_DESCRIPTION, API_PREFIX, CORS_ORIGINS, BASE_DIR
from backend.api import profile, items, export, ai

# FastAPIアプリケーション
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(profile.router, prefix=API_PREFIX)
app.include_router(items.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(ai.router, prefix=API_PREFIX)

# 静的ファイル配信（フロントエンド）
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    # CSS, JSファイルなどの静的ファイルをマウント
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

# 画像ファイル配信
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


@app.get("/")
def root():
    """
    ルートエンドポイント - フロントエンドのindex.htmlを返す
    """
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    # フロントエンドがない場合はAPI情報を返す
    return {
        "message": "楽天ROOMアイテムマネージャー API",
        "version": API_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
def health_check():
    """
    ヘルスチェック
    """
    return {"status": "ok"}
