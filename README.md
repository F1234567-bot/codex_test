# Veille Énergie Québec - MVP

Application FastAPI pour:
- collecter des nouvelles énergie pertinentes au Québec,
- trier/synthétiser pour industries lourdes,
- générer un briefing matinal,
- visualiser le contenu et piloter des actions via un dashboard.

## Démarrage

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Ouvrir: http://127.0.0.1:8000

## Configuration modèles (ta préférence)
Depuis **Settings** (`/settings`), configure:
- **Anthropic** pour la synthèse (`claude-sonnet-4-6`),
- **Mistral** ou **Kimi 2.5** pour classification/tri (`mistral-large-latest` ou `kimi-2.5`).

Tu peux entrer tes clés API directement via l'interface.

## Providers supportés
- Anthropic (`/v1/messages`)
- Mistral (chat completions OpenAI-compatible)
- Kimi/Moonshot (chat completions OpenAI-compatible)

> Si aucune clé n'est fournie, l'application fonctionne avec une synthèse heuristique (fallback).

## Exécution quotidienne
- Bouton "Lancer la veille maintenant" sur le dashboard
- Endpoint API: `POST /api/run-daily`

## Sources par défaut
- Hydro‑Québec (nouvelles)
- Gouvernement du Québec (fils d'actualité)
- Radio-Canada Énergie

Les URLs RSS sont modifiables dans `app/services/collector.py`.
