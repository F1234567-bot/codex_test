from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.db.models import ModelConfig


@dataclass
class BriefingSections:
    executive_summary: str
    opportunity_radar: str
    critical_alerts: str
    recommendations: str
    used_fallback: bool


def _get_provider_config(db: Session, role: str) -> ModelConfig | None:
    return db.query(ModelConfig).filter(ModelConfig.role == role).first()


def _format_article_bullets(articles: list[dict]) -> str:
    lines = []
    for a in articles[:10]:
        lines.append(
            f"- {a['title']} ({a['source']}) | catégorie={a.get('category', 'general')} | impact={a['impact_score']}"
        )
    return "\n".join(lines)


def _anthropic_messages(api_key: str, model_name: str, prompt: str) -> str:
    with httpx.Client(timeout=45.0) as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model_name,
                "max_tokens": 1200,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        payload = response.json()
    blocks = payload.get("content", [])
    texts = [block.get("text", "") for block in blocks if block.get("type") == "text"]
    return "\n".join([t for t in texts if t]).strip()


def _openai_compatible_messages(api_key: str, model_name: str, prompt: str, base_url: str) -> str:
    with httpx.Client(timeout=45.0) as client:
        response = client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
        )
        response.raise_for_status()
        payload = response.json()
    choices = payload.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "").strip()


def _call_provider(cfg: ModelConfig, prompt: str) -> str:
    if cfg.provider == "anthropic":
        return _anthropic_messages(cfg.api_key, cfg.model_name, prompt)

    if cfg.provider == "mistral":
        base = cfg.base_url.strip() or "https://api.mistral.ai/v1"
        return _openai_compatible_messages(cfg.api_key, cfg.model_name, prompt, base)

    if cfg.provider == "kimi":
        base = cfg.base_url.strip() or "https://api.moonshot.ai/v1"
        return _openai_compatible_messages(cfg.api_key, cfg.model_name, prompt, base)

    return ""


def build_briefing_with_fallback(articles: list[dict]) -> BriefingSections:
    top = sorted(articles, key=lambda a: a["impact_score"], reverse=True)[:5]
    executive = "\n".join([f"• {a['title']} — impact {a['impact_score']} ({a['confidence']})" for a in top])

    opportunities = "\n".join(
        [
            "• Cibler les comptes industriels mentionnés dans les nouvelles à fort impact.",
            "• Proposer un audit IA d'efficacité énergétique sur les postes de consommation critiques.",
            "• Automatiser la veille conformité/tarifs pour créer une offre de monitoring continu.",
        ]
    )
    alerts = "\n".join(
        [
            "• Vérifier les changements tarifaires publiés dans les dernières 24h.",
            "• Contrôler les échéances des programmes d'aide/subvention.",
            "• Revoir les annonces réglementaires pouvant impacter les industries lourdes.",
        ]
    )
    recos = "\n".join(
        [
            "1) Contacter 3 prospects prioritaires avec un angle coûts/tarifs.",
            "2) Préparer un mini diagnostic IA pour un secteur (aluminium, acier ou mines).",
            "3) Mettre à jour votre offre selon les opportunités/subventions détectées.",
        ]
    )

    return BriefingSections(executive, opportunities, alerts, recos, True)


def _classifier_signal(cfg: ModelConfig | None, articles: list[dict]) -> str:
    if not cfg or not cfg.api_key:
        return "• Classifieur fallback: utiliser le score heuristique impact > 2.0 pour prioriser."

    prompt = (
        "Tu es un analyste énergie Québec. À partir des titres ci-dessous, donne 3 opportunités business "
        "pour une agence IA d'efficacité énergétique industrielle. Réponds en 3 puces courtes.\n\n"
        f"{_format_article_bullets(articles)}"
    )
    try:
        response = _call_provider(cfg, prompt)
        if response:
            return response
    except Exception:
        pass
    return "• Le modèle de classification n'a pas répondu, utiliser les règles d'impact locales."


def build_briefing(db: Session, articles: list[dict]) -> BriefingSections:
    synthesis_cfg = _get_provider_config(db, "synthesis")
    classification_cfg = _get_provider_config(db, "classification")

    if not synthesis_cfg or not synthesis_cfg.api_key:
        return build_briefing_with_fallback(articles)

    bullets = _format_article_bullets(articles)
    prompt = (
        "Tu es un analyste senior du marché de l'énergie au Québec pour industries lourdes. "
        "Rédige en français avec sections exactes:\n"
        "[RESUME]\n[RADAR]\n[ALERTES]\n[RECOMMANDATIONS]\n"
        "Chaque section doit être concise et actionnable.\n\n"
        f"Articles:\n{bullets}"
    )

    try:
        raw = _call_provider(synthesis_cfg, prompt)
    except Exception:
        return build_briefing_with_fallback(articles)

    if not raw:
        return build_briefing_with_fallback(articles)

    radar_from_classifier = _classifier_signal(classification_cfg, articles)
    executive = raw
    opportunities = radar_from_classifier
    alerts = "• Vérifier la source primaire avant toute communication client."
    recos = "1) Prioriser comptes impact>2.0.\n2) Envoyer 1 campagne ciblée secteur.\n3) Revue KPI à 16h."

    return BriefingSections(executive, opportunities, alerts, recos, False)
