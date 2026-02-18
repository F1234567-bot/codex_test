from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import Base, engine, get_db
from app.db.models import ActionItem, Article, Briefing, ModelConfig
from app.services.collector import collect_articles
from app.services.llm import build_briefing
from app.services.scoring import classify_category, compute_impact_score, confidence_from_score

Base.metadata.create_all(bind=engine)

# Light schema backfill for local SQLite when upgrading existing DB.
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE model_configs ADD COLUMN base_url VARCHAR(250) DEFAULT ''"))
        conn.commit()
    except Exception:
        pass

app = FastAPI(title="Veille Énergie Québec")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def run_daily_pipeline(db: Session) -> Briefing:
    raw_articles = collect_articles(limit_per_source=8)
    for raw in raw_articles:
        exists = db.query(Article).filter(Article.url == raw["url"]).first()
        if exists:
            continue
        merged_text = f"{raw['title']}\n{raw['summary']}"
        score = compute_impact_score(merged_text)
        category = classify_category(merged_text)
        confidence = confidence_from_score(score)
        db.add(
            Article(
                title=raw["title"],
                url=raw["url"],
                source=raw["source"],
                published_at=raw["published_at"],
                summary=raw["summary"],
                impact_score=score,
                category=category,
                confidence=confidence,
            )
        )
    db.commit()

    today_key = datetime.utcnow().strftime("%Y-%m-%d")
    existing = db.query(Briefing).filter(Briefing.date_key == today_key).first()
    if existing:
        return existing

    latest_articles = (
        db.query(Article)
        .order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
        .limit(30)
        .all()
    )
    article_payload = [
        {
            "title": a.title,
            "source": a.source,
            "summary": a.summary,
            "impact_score": a.impact_score,
            "confidence": a.confidence,
            "category": a.category,
        }
        for a in latest_articles
    ]

    sections = build_briefing(db, article_payload)
    briefing = Briefing(
        date_key=today_key,
        executive_summary=sections.executive_summary,
        opportunity_radar=sections.opportunity_radar,
        critical_alerts=sections.critical_alerts,
        recommendations=sections.recommendations,
        used_fallback=sections.used_fallback,
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)

    default_actions = [
        "Valider les 3 infos les plus critiques et envoyer un mémo client.",
        "Identifier 2 prospects industriels à fort potentiel selon la veille.",
        "Planifier un appel interne pour ajuster les offres IA énergie.",
    ]
    for item in default_actions:
        db.add(ActionItem(briefing_id=briefing.id, title=item))
    db.commit()
    return briefing


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    latest_briefing = db.query(Briefing).order_by(Briefing.created_at.desc()).first()
    articles = db.query(Article).order_by(Article.created_at.desc()).limit(50).all()
    actions = latest_briefing.actions if latest_briefing else []
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "briefing": latest_briefing,
            "articles": articles,
            "actions": actions,
        },
    )


@app.post("/api/run-daily")
def run_daily(db: Session = Depends(get_db)):
    briefing = run_daily_pipeline(db)
    return {"status": "ok", "briefing_id": briefing.id, "date": briefing.date_key}


@app.post("/actions/{action_id}/status")
def update_action_status(action_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    action = db.query(ActionItem).filter(ActionItem.id == action_id).first()
    if action:
        action.status = status
        db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request, db: Session = Depends(get_db)):
    configs = db.query(ModelConfig).all()
    by_provider = {cfg.provider: cfg for cfg in configs}
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "configs": by_provider},
    )


@app.post("/settings")
def save_settings(
    anthropic_key: str = Form(""),
    anthropic_model: str = Form("claude-sonnet-4-6"),
    anthropic_base_url: str = Form("https://api.anthropic.com"),
    mistral_key: str = Form(""),
    mistral_model: str = Form("mistral-large-latest"),
    mistral_base_url: str = Form("https://api.mistral.ai/v1"),
    kimi_key: str = Form(""),
    kimi_model: str = Form("kimi-2.5"),
    kimi_base_url: str = Form("https://api.moonshot.ai/v1"),
    synthesis_provider: str = Form("anthropic"),
    classification_provider: str = Form("mistral"),
    db: Session = Depends(get_db),
):
    incoming = {
        "anthropic": (anthropic_key, anthropic_model, anthropic_base_url),
        "mistral": (mistral_key, mistral_model, mistral_base_url),
        "kimi": (kimi_key, kimi_model, kimi_base_url),
    }

    for provider, (key, model, base_url) in incoming.items():
        cfg = db.query(ModelConfig).filter(ModelConfig.provider == provider).first()
        if not cfg:
            cfg = ModelConfig(provider=provider)
            db.add(cfg)
        cfg.api_key = key.strip()
        cfg.model_name = model.strip()
        cfg.base_url = base_url.strip()
        cfg.role = "available"
    db.commit()

    synth = db.query(ModelConfig).filter(ModelConfig.provider == synthesis_provider).first()
    if synth:
        synth.role = "synthesis"

    clf = db.query(ModelConfig).filter(ModelConfig.provider == classification_provider).first()
    if clf:
        clf.role = "classification"

    db.commit()
    return RedirectResponse(url="/settings", status_code=303)
