# 🔍 Système de Détection de Fraude en Temps Réel

Projet réalisé dans le cadre du module **Processus Décisionnel Big Data**.

Système complet de détection de fraude bancaire utilisant Machine Learning et traitement en temps réel.

## 🖥️ Support Multi-Plateforme

Ce projet fonctionne sur **Windows**, **macOS** et **Linux** :
- Scripts PowerShell (`.ps1`) pour Windows
- Scripts Bash (`.sh`) pour macOS et Linux
- Tous les scripts Docker et Python fonctionnent de manière identique sur toutes les plateformes

## 🚀 Task Runners - Méthode Recommandée

Pour une utilisation plus simple et reproductible, utilisez les task runners :

**Recommandé - `just` (moderne, simple):**
```bash
brew install just           # Installation (macOS)
just --list                 # Voir toutes les commandes
just setup                  # Configuration complète
just run-basic              # Démarrer sans ML
just train                  # Entraîner le modèle
just run-ml                 # Démarrer avec ML
just health                 # Vérifier l'état du système
```

**Alternative - `make` (traditionnel, universel):**
```bash
make help                   # Voir toutes les commandes
make setup                  # Configuration complète
make run-basic              # Démarrer sans ML
make train                  # Entraîner le modèle
make run-ml                 # Démarrer avec ML
make health                 # Vérifier l'état du système
```

📖 **Guide complet:** Voir [TASK_RUNNERS.md](TASK_RUNNERS.md)

---

## 📊 Architecture Complète

```
Dataset Kaggle
    ↓
Producer (Python) → Kafka → Spark Streaming → MongoDB → Tableau
                                ↓
                         SparkML (Random Forest)
                                ↓
                    Prédictions temps réel
```

### Composants du Système

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Ingestion** | Kafka | Streaming des transactions en temps réel |
| **Traitement** | Spark Streaming | Traitement et transformation des données |
| **ML** | SparkML (Random Forest) | Détection de fraude par Machine Learning |
| **Stockage** | MongoDB | Base de données NoSQL pour persistance |
| **Visualisation** | Tableau | Dashboards et analyses visuelles |
| **Monitoring** | Dozzle, Mongo Express | Surveillance système et données |

---

## 🚀 Installation et Démarrage

### Prérequis

- Docker Desktop installé et démarré
- Python 3.9+ installé
- Compte Kaggle (pour le dataset)
- **Recommandé**: `just` ou `make` (task runners)
- **Alternative**:
  - **Windows**: PowerShell
  - **macOS/Linux**: Bash (inclus par défaut)

### Installation de `just` (Recommandé)

```bash
# macOS
brew install just

# Linux
cargo install just

# Windows
cargo install just
# ou
scoop install just
```

> **Note**: Si vous préférez ne pas installer `just`, vous pouvez utiliser `make` (pré-installé sur macOS/Linux) ou les scripts directs (`.sh`/`.ps1`)

### Étape 1 : Configuration Kaggle

1. Créez un compte sur [Kaggle](https://www.kaggle.com)
2. Allez dans Settings → API → Create New API Token
3. Notez votre token (format : `KGAT_xxxxx...`)
4. Créez un fichier `.env` à la racine :

```env
KAGGLE_API_TOKEN=KGAT_votre_token_ici
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC=fraud-detection-stream
STATE_FILE=/app/state/producer_state.db
```

### Étape 2 : Démarrage de l'Infrastructure

**Méthode recommandée (avec task runner):**
```bash
# Avec just (recommandé)
just start

# Avec make (alternative)
make start
```

**Méthode manuelle (avec Docker):**
```bash
# Démarrer tous les services Docker
docker-compose up -d

# Vérifier que tous les containers sont UP (6 containers)
docker ps
```

**Services disponibles :**
- Kafka : `localhost:9092`
- MongoDB : `localhost:27017`
- Mongo Express : `http://localhost:8081`
- Dozzle (logs) : `http://localhost:8080`

### Étape 3 : Installation des Dépendances Python (Spark)

**Méthode recommandée (task runner):**
```bash
# Avec just (recommandé)
just install-deps

# Avec make (alternative)
make install-deps
```

**Méthode manuelle (scripts directs):**
```powershell
# Windows (PowerShell)
.\setup-spark-dependencies.ps1
```
```bash
# macOS/Linux (Bash)
./setup-spark-dependencies.sh
```

**Durée :** 3-5 minutes


## 🔄 Workflow Complet

### 🎯 Workflow Rapide (avec Task Runners)

```bash
# Configuration initiale (une seule fois)
just setup                  # ou: make setup

# Phase 1: Accumuler des données (5-10 minutes)
just run-basic              # ou: make run-basic

# Vérifier les données (autre terminal)
just check                  # ou: make check

# Phase 2: Entraîner le modèle (arrêter run-basic avec Ctrl+C d'abord)
just train                  # ou: make train

# Phase 3: Exécuter avec ML
just run-ml                 # ou: make run-ml

# Vérifier les prédictions
just check-ml               # ou: make check-ml

# État du système
just health                 # ou: make health
```

### 📝 Workflow Détaillé (méthode manuelle)

### Phase 1 : Traitement Sans ML (Accumulation de données)

**Avec task runners (recommandé):**
```bash
just run-basic              # ou: make run-basic
```

**Avec scripts (alternative):**
```powershell
# Windows (PowerShell)
.\start-spark-processor.ps1
```
```bash
# macOS/Linux (Bash)
./start-spark-processor.sh
```

**Laisser tourner 5-10 minutes** pour accumuler ~5000 transactions.

**Vérification:**
```bash
# Avec task runner
just check                  # ou: make check

# Avec Python direct
python check-mongodb.py
```

### Phase 2 : Entraînement du Modèle ML

**Avec task runners (recommandé):**
```bash
# 1. Arrêter le processeur Spark (Ctrl+C dans le terminal)

# 2. Entraîner le modèle Random Forest
just train                  # ou: make train
```

**Avec scripts (alternative):**
```powershell
# Windows (PowerShell)
.\train-model.ps1
```
```bash
# macOS/Linux (Bash)
./train-model.sh
```

**Durée :** 5-10 minutes

**Résultat attendu :**
```
📈 Dataset Statistics:
   Total transactions: 5000+
   Normal transactions: 4990+ (99.X%)
   Fraudulent transactions: 10+ (0.X%)

🌲 Training Random Forest...
   ✅ Model trained successfully!

📈 MODEL PERFORMANCE METRICS
   AUC-ROC:   0.98+
   Accuracy:  0.99+
   Precision: 0.99+
   Recall:    0.99+
   F1-Score:  0.99+

💾 Model saved to: /app/models/fraud_detection_model
```

### Phase 3 : Prédictions en Temps Réel

**Avec task runners (recommandé):**
```bash
just run-ml                 # ou: make run-ml
```

**Avec scripts (alternative):**
```powershell
# Windows (PowerShell)
.\start-spark-ml.ps1
```
```bash
# macOS/Linux (Bash)
./start-spark-ml.sh
```

**Le système va maintenant :**
- Lire les transactions depuis Kafka
- Faire des prédictions en temps réel
- Ajouter `fraud_prediction` et `fraud_probability` dans MongoDB

**Vérification des prédictions:**
```bash
# Avec task runner
just check-ml               # ou: make check-ml

# Avec Python direct
python check_ml_predictions.py
```

**Résultat attendu :**
```
🤖 ML PREDICTIONS - MongoDB Statistics
================================
📈 Total transactions: 7000+
🤖 Transactions with ML predictions: 3500+

📈 Model Performance:
   Accuracy: 99.X%
   Precision: 100.00%
   Recall: 100.00%

📊 Confusion Matrix:
   True Positives (Fraud detected): X
   False Positives (False alarm): X
   True Negatives (Normal detected): X
   False Negatives (Fraud missed): X
```


## 📊 Dataset

**Credit Card Fraud Detection** (Kaggle)
- Source : [Kaggle Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- 284,807 transactions
- 492 fraudes (0.172%)
- 31 features : Time, V1-V28 (PCA), Amount, Class

### Schéma des Données

**Dans Kafka/MongoDB :**
```json
{
  "Time": 0.0,
  "V1": -1.359807,
  "V2": -0.072781,
  ...
  "V28": -0.021053,
  "Amount": 149.62,
  "Class": 0.0,
  "processed_at": "2026-01-09T14:30:45.123Z"
}
```

**Avec Prédictions ML :**
```json
{
  "Time": 0.0,
  "V1": -1.359807,
  ...
  "Amount": 149.62,
  "Class": 0.0,
  "fraud_prediction": 0,
  "fraud_probability": 0.02,
  "processed_at": "2026-01-09T14:30:45.123Z"
}
```

---

## 🤖 Machine Learning

### Algorithme : Random Forest Classifier

**Configuration :**
- Nombre d'arbres : 100
- Profondeur maximale : 10
- Features : V1-V28 + Amount (29 features)
- Normalisation : StandardScaler
- Split : 80% train / 20% test

### Métriques de Performance

**Résultats typiques :**
- **AUC-ROC :** 0.98+ (excellente séparation des classes)
- **Accuracy :** 99%+ (très peu d'erreurs)
- **Precision :** 80-100% (peu de fausses alertes)
- **Recall :** 80-100% (peu de fraudes manquées)
- **F1-Score :** 0.99+ (bon équilibre)

### Feature Importance

Les 10 features les plus importantes (typiquement) :
1. V14, V12, V10 (composantes PCA liées au comportement)
2. Amount (montant de la transaction)
3. V17, V16, V18
4. Time (moment de la transaction)

---

## 📈 Monitoring et Vérification

### Interfaces Web

| Interface | URL | Description |
|-----------|-----|-------------|
| Dozzle | `http://localhost:8080` | Logs Docker en temps réel |
| Mongo Express | `http://localhost:8081` | Interface MongoDB |

### Scripts de Vérification

```bash
# Vérifier les données dans MongoDB
python check-mongodb.py

# Vérifier les prédictions ML
python check_ml_predictions.py

# Voir les logs
docker logs producer --tail 50
docker logs spark --tail 50
docker logs mongodb --tail 50
```

### 📋 Commandes Rapides par Plateforme

**Windows (PowerShell):**
```powershell
.\setup-spark-dependencies.ps1    # Installer dépendances
.\start-spark-processor.ps1        # Démarrer sans ML
.\train-model.ps1                  # Entraîner modèle
.\start-spark-ml.ps1               # Démarrer avec ML
```

**macOS/Linux (Bash):**
```bash
./setup-spark-dependencies.sh     # Installer dépendances
./start-spark-processor.sh         # Démarrer sans ML
./train-model.sh                   # Entraîner modèle
./start-spark-ml.sh                # Démarrer avec ML
```

---

## 🎯 État du Projet

| Composant | État | Notes |
|-----------|------|-------|
| ✅ Ingestion (Kafka) | **Complet** | Producer avec état persistant |
| ✅ Stockage (MongoDB) | **Complet** | Base NoSQL + interface web |
| ✅ Traitement (Spark Streaming) | **Complet** | Traitement temps réel |
| ✅ Machine Learning (SparkML) | **Complet** | Random Forest 99%+ accuracy |
| ⏳ Visualisation (Tableau) | **À faire** | Prochaine étape |

---