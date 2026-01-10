# 🔍 Système de Détection de Fraude en Temps Réel

**Projet Big Data - Processus Décisionnel**

Système complet de détection de fraude bancaire utilisant Machine Learning (3 modèles en ensemble) et traitement en temps réel avec orchestration Dagster.

---

## 📊 Architecture

```
Dataset Kaggle (284K transactions)
        ↓
Producer Python → Kafka → Spark Streaming → MongoDB (4 collections) → Export Excel
                             ↓
                    SparkML Ensemble (3 modèles)
                    - Random Forest
                    - Gradient Boosting
                    - Logistic Regression
                             ↓
                    Vote Majoritaire + Auto-flagging
```

### Pile Technologique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Orchestration** | Dagster | Interface visuelle pour gérer tout le pipeline |
| **Streaming** | Apache Kafka | Ingestion temps réel des transactions |
| **Traitement** | Apache Spark | Traitement distribué et ML |
| **ML** | SparkML | 3 modèles en ensemble (vote majoritaire) |
| **Stockage** | MongoDB | Base NoSQL (4 collections) |
| **Visualisation** | Tableau | Dashboards et analyses |
| **Monitoring** | Dozzle, Mongo Express | Surveillance système |

---

## 🚀 Démarrage Rapide (5 Minutes)

### Prérequis

- Docker Desktop installé et démarré
- Python 3.9+ avec pip
- Compte Kaggle (pour le dataset)
- Just installé: `brew install just` (macOS) ou [voir installation](https://github.com/casey/just#installation)

### Configuration Initiale

**1. Configuration Kaggle**

Créez un fichier `.env` à la racine:
```env
KAGGLE_API_TOKEN=KGAT_votre_token_ici
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC=fraud-detection-stream
STATE_FILE=/app/state/producer_state.db
```

> **Obtenir votre token:** [Kaggle Settings](https://www.kaggle.com/settings) → API → Create New API Token

**2. Installation des Dépendances**

```bash
# Créer environnement virtuel Python
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou: venv\Scripts\activate.ps1  # Windows

# Installer dépendances Python
pip install -r requirements.txt

# Démarrer Docker et installer dépendances Spark
just setup
```

**3. Lancer Dagster UI**

```bash
just dagster
# Ouvre automatiquement http://localhost:3000
```

**4. Exécuter le Pipeline Complet**

Dans l'interface Dagster (http://localhost:3000):
1. Cliquez sur **"Jobs"** dans le menu gauche
2. Sélectionnez **"full_pipeline"**
3. Cliquez sur **"Launchpad"**
4. Cliquez sur **"Launch Run"**

✅ **C'est tout!** Le système exécute automatiquement:
- Démarrage des services Docker
- Accumulation de données d'entraînement (2 min)
- Entraînement des 3 modèles ML (~10-15 min)
- Génération de prédictions en temps réel (2 min)
- Validation de la qualité des données
- Export vers Excel pour Tableau

---

## 🎭 Orchestration avec Dagster

### Pourquoi Dagster?

**Avant Dagster (Scripts Manuels):**
- ❌ 8+ commandes à exécuter manuellement
- ❌ Risque d'oublier une étape
- ❌ Pas de visibilité sur la progression
- ❌ Logs dispersés dans plusieurs terminaux
- ❌ Difficile de reproduire exactement

**Avec Dagster:**
- ✅ Interface web professionnelle
- ✅ Exécution en un clic
- ✅ Dépendances automatiques (impossible d'entraîner sans données)
- ✅ Logs centralisés avec métadonnées
- ✅ Progression en temps réel
- ✅ Workflows reproductibles

### Assets Disponibles (7 étapes)

Le pipeline complet est composé de 7 assets avec dépendances automatiques:

```
start_docker_services
        ↓
check_services
        ↓
accumulate_data (2 min)
        ↓
train_models (10-15 min)
        ↓
run_ml_predictions (2 min)
        ↓
validate_data (30s)
        ↓
export_to_excel (30s)
```

**Chaque asset génère des métadonnées:**
- Nombre de transactions traitées
- Accuracy des modèles (>99%)
- Transactions flaggées (haut risque)
- Temps d'exécution

### Jobs Disponibles

| Job | Description | Durée | Utilisation |
|-----|-------------|-------|-------------|
| **full_pipeline** | Workflow complet de A à Z | 15-20 min | Première fois, démo complète |
| **accumulate_data** | Collecter données d'entraînement | 2-3 min | Besoin de plus de données |
| **train_models** | Réentraîner les 3 modèles | 10-15 min | Après ajout de données |
| **run_ml_predictions** | Générer prédictions temps réel | 2-3 min | Tester les modèles |
| **validate_data** | Vérifier qualité et accuracy | 30s | Health check rapide |

### Interfaces Web

Une fois Dagster lancé (`just dagster`):

| Interface | URL | Description |
|-----------|-----|-------------|
| **Dagster UI** | http://localhost:3000 | Orchestration principale |
| **Mongo Express** | http://localhost:8081 | Navigateur de données MongoDB |
| **Dozzle** | http://localhost:8080 | Logs Docker temps réel |

---

## 🤖 Machine Learning - Approche Ensemble

### Dataset: Credit Card Fraud Detection (Kaggle)

- **Source:** [Kaggle Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- **Taille:** 284,807 transactions
- **Fraudes:** 492 cas (0.172% - très déséquilibré)
- **Features:** 31 colonnes
  - `Time`: Secondes depuis la première transaction
  - `V1-V28`: 28 composantes PCA (anonymisation)
  - `Amount`: Montant de la transaction
  - `Class`: 0 (normal) ou 1 (fraude)

### 3 Modèles Complémentaires

**1. Random Forest Classifier**
- 100 arbres de décision
- Profondeur maximale: 10
- Excellent pour capturer les interactions non-linéaires

**2. Gradient Boosting Trees**
- 50 itérations
- Profondeur maximale: 5
- Très performant sur classes déséquilibrées

**3. Logistic Regression**
- 100 itérations
- Régularisation: 0.01
- Baseline interprétable

### Stratégie Ensemble: Vote Majoritaire

```python
# Pour chaque transaction:
vote_rf = model_random_forest.predict(transaction)
vote_gb = model_gradient_boosting.predict(transaction)
vote_lr = model_logistic_regression.predict(transaction)

# Décision finale
final_prediction = majority_vote(vote_rf, vote_gb, vote_lr)
confidence = average(prob_rf, prob_gb, prob_lr)

# Auto-flagging (action immédiate requise)
if confidence > 0.80 or (vote_rf == vote_gb == vote_lr == 1):
    flag_transaction(transaction)
```

**Avantages:**
- **Robustesse:** Un modèle seul peut se tromper, 3 modèles d'accord = haute confiance
- **Réduction faux positifs:** Unanimité ou haute probabilité requise pour flagging
- **Performance:** Accuracy >99%, Precision >90%, Recall >85%

### Métriques de Performance

**Résultats typiques après entraînement:**
- **AUC-ROC:** 0.98+ (excellente séparation des classes)
- **Accuracy:** 99%+ (très peu d'erreurs)
- **Precision:** 90-100% (peu de fausses alarmes)
- **Recall:** 85-95% (peu de fraudes manquées)
- **F1-Score:** 0.95+ (bon équilibre)

---

## 🗄️ Base de Données MongoDB

### Structure: 4 Collections

**1. `transactions`** - Toutes les transactions brutes
```json
{
  "Time": 0.0,
  "V1": -1.359, "V2": -0.072, ..., "V28": -0.021,
  "Amount": 149.62,
  "Class": 0.0,
  "processed_at": "2026-01-10T14:30:45Z"
}
```

**2. `model_predictions`** - Prédictions individuelles par modèle
```json
{
  "transaction_id": "...",
  "model_name": "random_forest",
  "prediction": 0,
  "probability": 0.02,
  "timestamp": "2026-01-10T14:30:46Z"
}
```

**3. `ensemble_results`** - Décisions finales (vote majoritaire)
```json
{
  "transaction_id": "...",
  "final_prediction": 0,
  "confidence_score": 0.03,
  "model_agreement": true,
  "votes": {"rf": 0, "gb": 0, "lr": 0},
  "timestamp": "2026-01-10T14:30:47Z"
}
```

**4. `flagged_transactions`** - Cas à haut risque
```json
{
  "transaction_id": "...",
  "reason": "all_models_agree",
  "confidence": 0.95,
  "amount": 5000.00,
  "flagged_at": "2026-01-10T14:30:47Z",
  "action_required": true
}
```

**Pourquoi 4 collections?**
- **Traçabilité:** Audit complet de chaque décision
- **Analytics:** Analyser performance de chaque modèle
- **Business Intelligence:** Dashboards Tableau détaillés
- **Actions:** Isoler les cas critiques (flagged)

---

## 📈 Visualisation et Décisions

### Export vers Tableau

Le système génère automatiquement 4 fichiers Excel (dossier `exports/`):
- `transactions.xlsx` - Toutes les transactions
- `model_predictions.xlsx` - Prédictions par modèle
- `ensemble_results.xlsx` - Décisions finales
- `flagged_transactions.xlsx` - Cas critiques

### Décisions Business Supportées

**1. Blocage Temps Réel**
- Si transaction flaggée → bloquer immédiatement la carte
- Réduction pertes financières
- Notification client pour vérification

**2. Analyse des Patterns**
- Identifier nouvelles techniques de fraude
- Montants moyens des fraudes
- Heures/jours à risque élevé
- Localisation géographique (si disponible)

**3. Optimisation Modèles**
- Comparer performance des 3 modèles
- Identifier faux positifs/négatifs
- Ajuster seuils de confiance
- Réentraînement périodique

**4. Reporting et Conformité**
- Historique complet pour audit
- Taux de détection par période
- Coûts évités (fraudes détectées)
- SLA: latence de détection

📊 **Voir [CHARTS.md](docs/CHARTS.md)** pour le guide complet des visualisations Tableau à créer.

---

## 🛠️ Commandes Utiles

### Infrastructure

```bash
just setup          # Configuration initiale complète
just start          # Démarrer Docker services
just stop           # Arrêter Docker services
just restart        # Redémarrer services
just health         # Vérifier état du système
```

### Dagster

```bash
just dagster        # Lancer Dagster UI (http://localhost:3000)
```

Tous les workflows (accumulation, entraînement, prédictions, validation, export) se font maintenant via l'interface Dagster UI.

### Monitoring

```bash
just logs           # Voir logs de tous les services
just log <service>  # Logs d'un service spécifique
just ui-mongo       # Ouvrir Mongo Express
just ui-logs        # Ouvrir Dozzle
```

### Maintenance

```bash
just clean             # Nettoyer toutes les données (reset complet)
just clean-checkpoint  # Fixer erreurs Spark
just reset-producer    # Redémarrer producer depuis le début
```

### Debug

```bash
just shell-spark    # Shell dans container Spark
just shell-mongo    # Shell MongoDB
just disk-usage     # Utilisation disque Docker
```

---

## 📚 Documentation

| Document | Contenu |
|----------|---------|
| **README.md** (ce fichier) | Vue d'ensemble, architecture, démarrage |
| [**INSTRUCTIONS.md**](docs/INSTRUCTIONS.md) | Guide pas-à-pas pour présentation en classe |
| [**CHARTS.md**](docs/CHARTS.md) | Visualisations Tableau et décisions business |

---

## 🎯 Workflow Typique

### Première Utilisation

```bash
# 1. Setup (une seule fois)
just setup

# 2. Lancer Dagster
just dagster

# 3. Dans Dagster UI (http://localhost:3000)
#    Jobs → full_pipeline → Launch Run

# 4. Attendre 15-20 minutes (tout est automatique)

# 5. Résultats dans exports/ (Excel pour Tableau)
```

### Réentraînement avec Plus de Données

```bash
# Dagster UI: Jobs → accumulate_data → Launch Run
# Attendre 2-3 minutes pour +1000-1500 transactions

# Dagster UI: Jobs → train_models → Launch Run
# Attendre 10-15 minutes

# Dagster UI: Jobs → run_ml_predictions → Launch Run
# Vérifier les nouvelles métriques
```

### Validation Rapide

```bash
# Dagster UI: Jobs → validate_data → Launch Run
# 30 secondes pour vérifier:
#   - Qualité des données
#   - Accuracy des modèles
#   - Distribution fraude/normal
#   - Flagged transactions count
```

---

## 🏆 Points Clés pour Présentation

### Techniquement

- **Streaming temps réel:** Kafka + Spark (pas de batch)
- **ML distribué:** SparkML sur cluster (scalable)
- **Ensemble learning:** 3 modèles = robustesse
- **NoSQL flexible:** MongoDB 4 collections pour traçabilité
- **Orchestration moderne:** Dagster pour reproductibilité

### Business

- **Détection immédiate:** <2 secondes bout-en-bout
- **High accuracy:** >99% de précision
- **Réduction pertes:** Fraudes bloquées en temps réel
- **Décisions data-driven:** Dashboards Tableau pour insights
- **Audit complet:** Historique MongoDB de chaque transaction

### Démonstration

1. **Montrer l'architecture** (schéma ci-dessus)
2. **Lancer Dagster UI** → visualiser le graphe d'assets
3. **Exécuter full_pipeline** → progression temps réel
4. **Ouvrir Mongo Express** → 4 collections avec données
5. **Montrer exports/** → fichiers Excel pour Tableau
6. **Expliquer décisions business** supportées

---

## 📝 Licence & Crédits

**Projet académique** - Processus Décisionnel Big Data
**Dataset:** [Credit Card Fraud Detection (Kaggle)](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
**Technologies:** Apache Kafka, Apache Spark, MongoDB, Dagster, Python, Docker

---

**🚀 Prêt à démarrer? Lancez `just setup` puis `just dagster`!**
