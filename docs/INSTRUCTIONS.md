# Instructions pour la Présentation en Classe

Ce guide fournit des instructions détaillées pour présenter le système de détection de fraude en classe.

---

## 📋 Table des Matières

1. [Préparation Avant la Présentation](#préparation-avant-la-présentation)
2. [Méthode Recommandée: Dagster UI](#méthode-recommandée-dagster-ui)
3. [Méthode Alternative: Scripts Manuels](#méthode-alternative-scripts-manuels)
4. [Scénario de Présentation (20 minutes)](#scénario-de-présentation-20-minutes)
5. [Points Clés à Mentionner](#points-clés-à-mentionner)
6. [Dépannage Pendant la Présentation](#dépannage-pendant-la-présentation)

---

## Préparation Avant la Présentation

### Vérifications Préalables (À Faire 1 Jour Avant)

```bash
# 1. Vérifier Docker
docker ps

# 2. Vérifier l'environnement virtuel Python
source venv/bin/activate
python --version  # Doit être Python 3.9+

# 3. Vérifier just est installé
just --version

# 4. Vérifier Dagster
source venv/bin/activate
dagster --version

# 5. Configuration initiale (si première fois)
just setup
```

### Nettoyage et Reset (Le Jour de la Présentation)

```bash
# Nettoyer toutes les données pour repartir de zéro
just clean

# Redémarrer les services
just start

# Vérifier que tout fonctionne
just health
```

---

## Méthode Recommandée: Dagster UI

### Pourquoi Dagster?

**Avantages pour la présentation:**
- ✅ Interface visuelle professionnelle
- ✅ Progression en temps réel visible par l'audience
- ✅ Logs centralisés et organisés
- ✅ Exécution simplifiée (un clic)
- ✅ Métriques et métadonnées automatiques
- ✅ Gestion des dépendances automatique

### Workflow avec Dagster

#### 1. Démarrer Dagster UI

```bash
# Terminal 1: Lancer Dagster
just dagster

# Ouvrir dans le navigateur
# http://localhost:3000
```

**Ce que vous verrez:**
- Interface Dagster avec menu de gauche
- Tabs: Assets, Jobs, Runs, Overview

#### 2. Montrer l'Architecture (Assets)

1. Cliquez sur **"Assets"** dans le menu gauche
2. Montrez le graphe de dépendances:
   ```
   check_services → accumulate_data → train_models →
   run_ml_predictions → validate_data → export_to_excel
   ```
3. Expliquez chaque asset brièvement (voir section "Points Clés")

#### 3. Exécuter le Pipeline Complet

1. Cliquez sur **"Jobs"** dans le menu gauche
2. Sélectionnez **"full_pipeline"**
3. Cliquez sur **"Launchpad"** (bouton en haut à droite)
4. Cliquez sur **"Launch Run"**

**Pendant l'exécution:**
- Montrez la progression en temps réel
- Cliquez sur chaque asset pour voir les logs
- Expliquez ce qui se passe à chaque étape
- Montrez les métadonnées (nombre de transactions, accuracy, etc.)

#### 4. Voir les Résultats

Une fois le pipeline terminé:
1. Cliquez sur **"validate_data"** asset
2. Montrez les métriques de qualité
3. Expliquez les résultats (accuracy, precision, recall)

#### 5. Ouvrir les Données Exportées

```bash
# Les fichiers Excel sont dans exports/
ls -lh exports/

# Montrer un fichier
open exports/ensemble_results.xlsx  # macOS
```

### Jobs Individuels (Si Besoin)

Si vous voulez montrer des étapes individuelles:

```bash
# Via commandes
just dagster-accumulate   # Accumulation seulement
just dagster-train        # Entraînement seulement
just dagster-predict      # Prédictions seulement

# Ou via UI:
# Jobs → Sélectionner le job → Launch Run
```

---

## Méthode Alternative: Scripts Manuels

Si Dagster ne fonctionne pas ou si vous préférez montrer le processus manuel.

### Workflow Manuel (Pas à Pas)

#### 1. Setup Initial

```bash
# Démarrer tous les services
just start

# Vérifier l'état
just status
```

#### 2. Accumulation de Données (5-10 minutes)

```bash
# Terminal 1: Démarrer l'accumulation
just run-basic

# Terminal 2: Surveiller la progression
just check
```

**Pendant l'accumulation:**
- Montrez les logs Spark qui défilent
- Exécutez `just check` régulièrement pour voir les compteurs augmenter
- Expliquez: "On collecte des transactions depuis Kafka, on les traite avec Spark, et on les stocke dans MongoDB"
- Objectif: Accumuler ~5000+ transactions (minimum 100)

**Arrêt:**
- Pressez `Ctrl+C` dans le terminal qui exécute `just run-basic`

#### 3. Entraînement des Modèles (10-15 minutes)

```bash
# Entraîner les 3 modèles
just train
```

**Pendant l'entraînement:**
- Montrez les logs de progression
- Expliquez les 3 modèles: Random Forest, Gradient Boosting, Logistic Regression
- Montrez les métriques finales (AUC-ROC, Accuracy, Precision, Recall)

**Vérification:**
```bash
just check-model  # Confirme que les 3 modèles existent
```

#### 4. Prédictions avec ML (2-5 minutes)

```bash
# Terminal 1: Démarrer les prédictions
just run-ml

# Terminal 2: Vérifier les prédictions
just check-ml
```

**Pendant les prédictions:**
- Montrez les logs avec les prédictions en temps réel
- Exécutez `just check-ml` pour voir les statistiques
- Expliquez l'ensemble voting (vote majoritaire des 3 modèles)
- Montrez les transactions flaggées (high-risk)

#### 5. Export pour Tableau

```bash
just export-excel
```

Montrez les fichiers Excel créés dans `exports/`:
- `transactions.xlsx`
- `model_predictions.xlsx`
- `ensemble_results.xlsx`
- `flagged_transactions.xlsx`

---

## Scénario de Présentation (20 minutes)

### Introduction (2 minutes)

"Bonjour, je vais vous présenter notre système de détection de fraude bancaire en temps réel. Ce système utilise les technologies Big Data que nous avons étudiées: Kafka pour le streaming, Spark pour le traitement, MongoDB pour le stockage, et Machine Learning pour la détection."

**Montrez le schéma d'architecture:**
```
Dataset Kaggle → Producer → Kafka → Spark Streaming → MongoDB → Tableau
                                        ↓
                                   SparkML (3 Models)
```

### Démonstration de l'Architecture (3 minutes)

**Montrez les services Docker:**
```bash
just status
```

Expliquez chaque service:
- **Kafka**: Message broker pour le streaming temps réel
- **MongoDB**: Base de données NoSQL pour persistance
- **Spark**: Moteur de traitement distribué
- **Producer**: Génère des transactions depuis le dataset Kaggle
- **Monitoring**: Mongo Express (visualiser les données), Dozzle (logs)

**Ouvrez les interfaces web:**
```bash
# Mongo Express (données)
open http://localhost:8081

# Dozzle (logs)
open http://localhost:8080
```

### Option A: Démonstration avec Dagster (10 minutes)

**1. Lancer Dagster (1 min)**
```bash
just dagster
# Ouvrir http://localhost:3000
```

**2. Montrer les Assets (2 min)**
- Cliquez sur "Assets"
- Expliquez le graphe de dépendances
- Décrivez brièvement chaque asset

**3. Lancer le Pipeline (5 min)**
- Jobs → full_pipeline → Launch Run
- Montrez la progression en temps réel
- Cliquez sur les assets pour voir les logs
- Expliquez ce qui se passe à chaque étape

**4. Voir les Résultats (2 min)**
- Montrez les métriques finales
- Ouvrez les fichiers Excel exportés
- Expliquez comment les utiliser dans Tableau

### Option B: Démonstration Manuelle (10 minutes)

**1. Accumulation (3 min)**
```bash
just run-basic
# Dans un autre terminal: just check
```
- Montrez les logs
- Expliquez le flux: Kafka → Spark → MongoDB
- Montrez les compteurs qui augmentent

**2. Entraînement (3 min)**
```bash
just train
```
- Expliquez les 3 modèles
- Montrez les métriques (accuracy >99%)
- Expliquez l'ensemble approach

**3. Prédictions (3 min)**
```bash
just run-ml
# Dans un autre terminal: just check-ml
```
- Montrez les prédictions en temps réel
- Expliquez le vote majoritaire
- Montrez les transactions flaggées

**4. Export (1 min)**
```bash
just export-excel
open exports/
```

### Machine Learning en Détail (3 minutes)

Expliquez l'approche ensemble:

**3 Modèles Complémentaires:**
1. **Random Forest**: Robuste, gère bien les features non-linéaires
2. **Gradient Boosting**: Excellent pour les déséquilibres de classes
3. **Logistic Regression**: Baseline, interprétable

**Vote Majoritaire:**
- Chaque modèle vote: fraude ou normal
- Décision finale: majorité (2/3 ou 3/3)
- Confiance: moyenne des probabilités

**Auto-flagging:**
- Transaction flaggée si:
  - Tous les modèles sont d'accord (unanimité), OU
  - Probabilité moyenne > 80%
- Permet l'action immédiate sur les cas évidents

### Structure de la Base de Données (2 minutes)

Montrez MongoDB avec Mongo Express:

**4 Collections:**
1. **transactions**: Toutes les transactions brutes
2. **model_predictions**: Prédictions individuelles de chaque modèle
3. **ensemble_results**: Décisions finales (vote majoritaire)
4. **flagged_transactions**: Cas à haut risque (auto-flagged)

Montrez des exemples de documents dans chaque collection.

### Questions et Réponses (variable)

---

## Points Clés à Mentionner

### Architecture Big Data

**Pourquoi Kafka?**
- Streaming en temps réel (pas de batch)
- Haute disponibilité et scalabilité
- Découplage producer/consumer

**Pourquoi Spark?**
- Traitement distribué (scale horizontalement)
- Micro-batches (optimise latence vs throughput)
- SparkML intégré (pas besoin d'exporter les données)

**Pourquoi MongoDB?**
- NoSQL: schéma flexible pour évolution future
- Performance: index optimisés pour requêtes fraud
- Agrégations puissantes pour analytics

### Machine Learning

**Dataset:**
- 284,807 transactions Kaggle
- 492 fraudes (0.172% - très déséquilibré!)
- 28 features PCA (V1-V28) + Amount + Time

**Défis:**
- Classe très déséquilibrée (99.8% normal, 0.2% fraude)
- Temps réel requis (<100ms par transaction)
- Faux positifs coûteux (blocage carte client)
- Faux négatifs catastrophiques (perte financière)

**Solution: Ensemble de 3 modèles**
- Meilleure robustesse que modèle unique
- Réduit les faux positifs (unanimité requise)
- Haute accuracy (>99%) avec recall élevé

### Performance

**Throughput:**
- Producer: ~10 transactions/seconde
- Spark: traite microbatch de 50-100 trans en <1s
- MongoDB: écrit ~1000+ trans/minute

**Latence:**
- Bout en bout: <2 secondes (Kafka → Spark → MongoDB)
- Prédiction ML: ~50ms par microbatch

**Scalabilité:**
- Kafka: partitionnement horizontal
- Spark: cluster multi-nœuds (actuellement 1 nœud local)
- MongoDB: sharding possible

### Décisions Business

**Ce système permet de:**
1. **Bloquer transactions suspectes en temps réel**
   - Si flagged=true: bloquer immédiatement
   - Réduire pertes financières

2. **Analyser patterns de fraude**
   - Tableau dashboards pour trends
   - Identifier nouvelles techniques de fraude

3. **Optimiser règles métier**
   - Ajuster seuils de probabilité
   - Balance faux positifs vs faux négatifs

4. **Audit et conformité**
   - Historique complet dans MongoDB
   - Traçabilité de chaque décision

---

## Dépannage Pendant la Présentation

### Problème: Services Docker ne démarrent pas

```bash
# Vérifier Docker Desktop est lancé
docker ps

# Si rien, redémarrer tout
just restart

# Si erreur persistante
just clean
just start
```

### Problème: Pas de données dans MongoDB

```bash
# Vérifier le producer tourne
docker logs producer --tail 20

# Vérifier Spark tourne
docker logs spark --tail 20

# Redémarrer l'accumulation
just clean-checkpoint
just run-basic
```

### Problème: Modèles ne se chargent pas

```bash
# Vérifier les modèles existent
just check-model

# Si manquants, réentraîner
just clean-model
just train
```

### Problème: Dagster ne démarre pas

```bash
# Vérifier port 3000 libre
lsof -i :3000

# Si occupé, tuer le processus
kill -9 <PID>

# Ou utiliser un autre port
export DAGSTER_PORT=3001
dagster-webserver -h 0.0.0.0 -p 3001 -w workspace.yaml
```

### Problème: Performances lentes

```bash
# Vérifier ressources système
docker stats

# Augmenter mémoire Spark (dans docker-compose.yml)
# SPARK_WORKER_MEMORY=4g

# Redémarrer
just restart
```

### Plan B: Si Tout Échoue

**Montrer des résultats pré-générés:**
1. Ouvrez les fichiers Excel dans `exports/`
2. Montrez des captures d'écran de Dagster UI
3. Expliquez l'architecture avec le schéma
4. Montrez le code source des composants clés

**Fichiers à préparer à l'avance:**
- Screenshots de Dagster UI avec pipeline complet
- Excel avec données réelles exportées
- Logs exemple de Spark avec prédictions
- Captures MongoDB avec les 4 collections

---

## Commandes de Référence Rapide

```bash
# Setup et démarrage
just setup              # Configuration complète initiale
just start              # Démarrer services
just status             # Vérifier état services

# Dagster (Recommandé)
just dagster            # Lancer UI Dagster
just dagster-full       # Pipeline complet via CLI
just dagster-accumulate # Accumulation seulement
just dagster-train      # Entraînement seulement
just dagster-predict    # Prédictions seulement

# Méthode manuelle (Alternative)
just run-basic          # Accumulation données
just train              # Entraîner modèles
just run-ml             # Prédictions ML
just export-excel       # Export pour Tableau

# Monitoring
just check              # Statistiques MongoDB
just check-ml           # Statistiques ML
just check-model        # Vérifier modèles
just health             # Santé système complète
just logs               # Logs tous services

# Nettoyage
just clean              # Tout nettoyer (reset complet)
just clean-model        # Supprimer modèles seulement
just clean-checkpoint   # Fixer streams bloqués
just stop               # Arrêter services

# Interfaces web
open http://localhost:3000  # Dagster UI
open http://localhost:8081  # Mongo Express (données)
open http://localhost:8080  # Dozzle (logs)
```

---

## Documentation Additionnelle

Pour plus de détails pendant la préparation:

| Document | Utilité |
|----------|---------|
| [DAGSTER.md](DAGSTER.md) | Guide complet Dagster (assets, jobs, troubleshooting) |
| [DATABASE_STRUCTURE.md](DATABASE_STRUCTURE.md) | Schéma MongoDB, exemples de documents |
| [TABLEAU_GUIDE.md](TABLEAU_GUIDE.md) | Créer visualisations Tableau |
| [BENCHMARK.md](BENCHMARK.md) | Métriques de performance détaillées |
| [COMMANDS.md](COMMANDS.md) | Référence complète des commandes |
| [README.md](../README.md) | Vue d'ensemble du projet |

---

**Bonne présentation! 🎓**
