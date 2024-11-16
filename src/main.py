import json
import uuid

from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from src.database import get_async_session
from src.exams.router import router as exams_router
from src.quizzes.query import get_random_word_for_translate, get_random_words
from src.quizzes.service import QuizService
from src.quizzes.utils import add_word_for_translate_to_other_words, shuffle_random_words
from src.users.query import get_user
from src.users.router import router as users_router
from src.quizzes.router import router as words_router
from src.competitions.router import router as competitions_router
from fastapi.websockets import WebSocket

app = FastAPI(docs_url=None, title='Learn API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(words_router)
app.include_router(exams_router)
app.include_router(competitions_router)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )
