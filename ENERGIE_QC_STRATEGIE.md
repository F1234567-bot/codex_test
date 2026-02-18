# Plan d’application IA: veille approfondie du marché de l’énergie au Québec

## 1) Objectif produit
Construire une application qui:
- fait une recherche approfondie du marché de l’énergie au Québec (réglementation, prix, programmes, appels d’offres, nouvelles techno);
- filtre l’information pour votre niche (efficacité énergétique pour industries lourdes);
- envoie chaque matin un briefing actionnable pour votre agence IA.

## 2) Architecture recommandée (MVP en 4 blocs)

### A. Collecte de données (sources fiables)
- Sources publiques à intégrer en priorité:
  - Gouvernement du Québec (ministères, MELCCFP, transitions énergétique);
  - Régie de l’énergie;
  - Hydro-Québec (tarifs, programmes, communiqués);
  - IESO/NEB/CER, StatCan, Institut de la statistique du Québec;
  - Médias économiques spécialisés et communiqués industriels.
- Mécanismes:
  - RSS/API quand disponible;
  - scraping légal et respectueux (fréquence limitée, robots.txt);
  - stockage brut horodaté (JSON + URL source).

### B. Enrichissement IA
- Pipeline suggéré:
  1. Déduplication des articles;
  2. Classification thématique (tarifs, réglementation, subventions, technologies, risques);
  3. Extraction d’entités (organisations, régions, secteurs, montants, dates);
  4. Scoring d’impact pour « industries lourdes »;
  5. Résumé exécutif en français.

### C. Base de connaissance + recherche
- Vector store (pgvector, Weaviate ou Qdrant) pour retrouver rapidement les éléments pertinents.
- Métadonnées structurées (date, source, crédibilité, secteur ciblé, type d’impact).
- Requête hybride (keyword + vecteur) pour améliorer précision.

### D. Orchestration quotidienne
- Job planifié (cron à 5h30):
  - collecte -> enrichissement -> ranking -> génération briefing;
- livraison à 7h00:
  - email, Slack, Notion, ou dashboard interne.

## 3) Quel LLM/API choisir pour votre cas (recherche + tri)

### Option pragmatique (recommandée)
Adopter une architecture « multi-modèles »:
- **Modèle A (raisonnement/synthèse)**: pour produire un briefing fiable et actionnable;
- **Modèle B (coût réduit)**: pour classification/tri à grand volume;
- **Moteur non-LLM**: règles + scoring + recherche hybride pour fiabiliser.

Pourquoi: un seul modèle n’est pas toujours optimal entre coût, vitesse et qualité.

### Critères de sélection (ordre de priorité)
1. Qualité sur documents FR/EN (Québec = bilingue);
2. Coût par 1M tokens (ingestion quotidienne peut grossir vite);
3. Latence (briefing matinal sous contrainte de temps);
4. Support « tool calling » / function calling;
5. Fenêtre de contexte + qualité des résumés longs;
6. Gouvernance données (rétention, conformité, options entreprise).

### MCP vs API classique
- **API classique**: stable, simple à industrialiser, meilleure observabilité.
- **MCP**: très bon pour brancher des outils et sources de contexte de façon modulaire.

Recommandation pratique:
- Démarrer avec API classique pour le pipeline critique de production;
- Ajouter MCP pour les modules exploratoires et connecteurs de recherche.

## 4) Sources de données prioritaires (Québec énergie)
1. Régie de l’énergie (décisions, audiences, documents tarifaires);
2. Hydro-Québec (tarifs industriels, programmes d’efficacité, plans réseau);
3. Programmes gouvernementaux (subventions, appels à projets);
4. Données macro: prix combustibles, inflation énergétique, carbone;
5. Actualités industrielles (acier, aluminium, ciment, mines, pâtes et papiers).

## 5) Format de briefing matinal recommandé

### Résumé exécutif (5 points max)
- 3 à 5 faits majeurs des dernières 24h;
- niveau de confiance par item (Élevé/Moyen/Faible);
- impact attendu (coût énergétique, conformité, opportunité).

### Radar opportunités
- Opportunités commerciales pour votre agence IA;
- secteurs industriels les plus touchés;
- valeur potentielle estimée (ordre de grandeur).

### Alertes critiques
- Risques réglementaires;
- changements tarifaires;
- échéances de dépôt/appel d’offres.

### Recommandations opérationnelles
- 3 actions concrètes à lancer aujourd’hui;
- message type à envoyer à vos prospects cibles.

## 6) Roadmap 30 jours (concrète)

### Semaine 1
- Définir 15–20 sources prioritaires;
- Mettre en place ingestion + stockage brut;
- Créer taxonomie métier (10–15 catégories).

### Semaine 2
- Ajouter classification + résumé automatique;
- Mettre un score d’impact « industrie lourde »;
- Créer dashboard interne minimal.

### Semaine 3
- Ajouter moteur de recherche hybride;
- Déployer briefing quotidien automatique;
- Ajuster scoring avec feedback humain.

### Semaine 4
- Mettre A/B test de modèles LLM;
- Calculer KPI (précision, coût/briefing, temps de génération);
- Stabiliser version v1 pour production.

## 7) KPI à suivre dès le départ
- Précision du tri (pertinent vs bruit);
- Taux d’hallucination détectée;
- Temps total pipeline;
- Coût quotidien LLM;
- Taux d’ouverture/lecture du briefing;
- Nombre d’opportunités commerciales générées.

## 8) Stack technique suggérée (simple et robuste)
- Backend: Python (FastAPI) + workers (Celery/Temporal);
- Data: PostgreSQL + pgvector;
- ETL: Airbyte/custom scrapers;
- LLM orchestration: LangGraph/LlamaIndex;
- Monitoring: OpenTelemetry + logs structurés;
- Livraison briefing: email + Slack.

## 9) Première décision à prendre maintenant
Choisir 2 modèles à comparer sur vos vraies données pendant 7 jours:
- un modèle premium pour la synthèse stratégique;
- un modèle économique pour tri/classification;
- benchmarker qualité/coût/latence avant engagement long terme.

---
Ce document sert de blueprint initial. Prochaine étape recommandée: implémenter un POC d’ingestion + briefing quotidien sur 10 sources, puis itérer rapidement avec vos retours métier.
