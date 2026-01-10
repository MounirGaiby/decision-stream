# Guide de Présentation en Classe

**Durée recommandée:** 15-20 minutes
**Approche:** Dagster UI (interface visuelle professionnelle)

---

## Préparation Avant la Présentation

### La Veille

```bash
# 1. Vérifier Docker Desktop est lancé
docker ps

# 2. Vérifier Python et Dagster
python3 --version  # 3.9+
source venv/bin/activate
dagster --version

# 3. Test Dagster UI
just dagster
# → Ouvrir http://localhost:3000
# → Vérifier que l'interface charge avec 8 assets

# 4. Test pipeline complet (optionnel - prend 25 min)
# Dans Dagster UI: Jobs → full_pipeline → Launch Run
# Vérifier que tout fonctionne

# 5. Nettoyer pour démo fraîche
just clean
```

### Le Jour Même (Juste avant)

```bash
# 1. Clean start (supprime tout)
just clean

# 2. Lancer Dagster UI
just dagster
# → http://localhost:3000 doit être accessible

# 3. Ne lancez PAS le pipeline encore!
# Vous le ferez en live pendant la présentation
```

---

## Scénario de Présentation (15 minutes)

### 1. Introduction (2 minutes)

**Ce que vous dites:**

> "Bonjour. Je vais vous présenter notre système de détection de fraude bancaire en temps réel. Ce système utilise les technologies Big Data étudiées en cours: Kafka pour le streaming, Spark pour le traitement distribué, MongoDB pour le stockage, et Machine Learning avec 3 modèles en ensemble pour la détection."

**Montrez le schéma d'architecture (README.md):**

```
Dataset Kaggle → Producer → Kafka → Spark → MongoDB → Tableau
                               ↓
                          SparkML (3 modèles)
```

**Points clés à mentionner:**
- 284K transactions Kaggle
- Détection en temps réel (<2 secondes)
- 3 modèles ML en ensemble (>99% accuracy)
- 4 collections MongoDB pour traçabilité

---

### 2. Démonstration Dagster UI (8 minutes)

#### A. Montrer l'Interface (1 min)

**Navigation:**
1. Ouvrez http://localhost:3000
2. Montrez l'interface principale

**Ce que vous dites:**

> "Nous utilisons Dagster, une plateforme d'orchestration moderne, pour gérer tout notre pipeline. Au lieu d'exécuter des scripts manuellement, tout est orchestré visuellement avec des dépendances automatiques."

#### B. Expliquer les Assets (2 min)

**Navigation:**
1. Cliquez sur **"Assets"** (menu gauche)
2. Montrez le graphe de dépendances

**Ce que vous montrez:**

```
start_docker_services  →  install_dependencies  →  check_services  →
accumulate_data  →  train_models  →  run_ml_predictions  →
validate_data  →  export_to_excel
```

**Ce que vous dites:**

> "Le pipeline se compose de 8 étapes entièrement automatisées:
> 1. **start_docker_services**: Lance Kafka, MongoDB, Spark avec docker-compose
> 2. **install_dependencies**: Installe NumPy, Pandas, Scikit-learn dans Spark (3-5 min)
> 3. **check_services**: Vérifie que tous les services sont prêts
> 4. **accumulate_data**: Collecte 2 minutes de transactions depuis Kafka
> 5. **train_models**: Entraîne nos 3 modèles ML en parallèle (Random Forest, Gradient Boosting, Logistic Regression)
> 6. **run_ml_predictions**: Applique les modèles et fait du vote majoritaire
> 7. **validate_data**: Vérifie la qualité (accuracy >99%, précision, recall)
> 8. **export_to_excel**: Exporte tout vers Excel pour analyse Tableau
>
> Dagster gère automatiquement les dépendances: impossible d'entraîner sans données, impossible de prédire sans modèles. Tout est reproductible."

#### C. Lancer le Pipeline (5 min)

**Navigation:**
1. Cliquez sur **"Jobs"** (menu gauche)
2. Cliquez sur **"full_pipeline"**
3. Cliquez sur **"Launchpad"** (bouton en haut à droite)
4. Cliquez sur **"Launch Run"**

**Ce que vous dites:**

> "Je vais maintenant lancer le pipeline complet avec un seul clic. Normalement ça prend 15-20 minutes, mais pour la démo, chaque étape est accélérée."

**Pendant l'exécution:**

**~30 secondes:** start_docker_services
> "Dagster lance automatiquement docker-compose. Tous les services démarrent: Kafka, MongoDB, Spark, monitoring."

**~3-5 minutes:** install_dependencies
> "Installation de NumPy, Pandas, Scikit-learn dans le container Spark. C'est fait une seule fois - les prochains runs seront plus rapides."

**~10 secondes:** check_services
> "Vérification que tous les services sont opérationnels avant de continuer."

**~2 minutes:** accumulate_data
> "Collecte de transactions depuis Kafka, traitement avec Spark, stockage MongoDB. En production, on accumulerait plus longtemps."

**~10-15 minutes:** train_models (partie la plus longue)
> "Entraînement des 3 modèles ML en parallèle. Chaque modèle apprend sur ~1000-2000 transactions."

**~2 minutes:** run_ml_predictions
> "Application des 3 modèles, vote majoritaire, auto-flagging des cas à haut risque."

**~30 secondes:** validate_data + export_to_excel
> "Validation qualité et export Excel. Système maintenant prêt pour Tableau."

**(Optionnel) Si le training prend trop de temps:**
- Montrez les logs en temps réel
- Expliquez les métriques (accuracy, precision, recall)
- Ou utilisez le job "validate_data" seul pour démo rapide

---

### 3. Machine Learning - Approche Ensemble (2 minutes)

**Pendant que le training tourne ou après:**

**Ce que vous dites:**

> "Notre approche ML utilise 3 modèles complémentaires:
>
> **1. Random Forest**: Robuste, capture les interactions non-linéaires
> **2. Gradient Boosting**: Excellent sur données déséquilibrées (0.17% de fraudes)
> **3. Logistic Regression**: Baseline interprétable
>
> **Vote Majoritaire**: Pour chaque transaction, on fait voter les 3 modèles. La décision finale est le consensus (2/3 ou 3/3). Ça nous donne plus de 99% d'accuracy.
>
> **Auto-Flagging**: Si les 3 modèles sont unanimes OU si la probabilité moyenne dépasse 80%, on flag automatiquement la transaction pour action immédiate."

**Montrez le README.md - section ensemble code:**

```python
# Décision finale
final_prediction = majority_vote(vote_rf, vote_gb, vote_lr)
confidence = average(prob_rf, prob_gb, prob_lr)

# Auto-flagging
if confidence > 0.80 or (vote_rf == vote_gb == vote_lr == 1):
    flag_transaction(transaction)
```

---

### 4. Base de Données et Résultats (2 minutes)

#### A. MongoDB - 4 Collections (1 min)

**Navigation:**
- Ouvrez http://localhost:8081 (Mongo Express)
- Naviguez dans les 4 collections

**Ce que vous montrez:**

1. **transactions**: Données brutes (Time, V1-V28, Amount, Class)
2. **model_predictions**: Prédiction de chaque modèle individuellement
3. **ensemble_results**: Décision finale + vote + confiance
4. **flagged_transactions**: Cas critiques auto-flaggés

**Ce que vous dites:**

> "On utilise 4 collections MongoDB pour la traçabilité complète:
> - **transactions**: Toutes les données brutes
> - **model_predictions**: Chaque modèle garde sa prédiction (audit)
> - **ensemble_results**: La décision finale avec le vote et la confiance
> - **flagged_transactions**: Les cas à haut risque isolés pour action immédiate
>
> Cette structure permet l'audit complet et l'analyse de performance de chaque modèle."

#### B. Export Excel pour Tableau (1 min)

**Navigation:**
- Retournez à Dagster UI
- Montrez l'asset "export_to_excel" complété
- Ouvrez le dossier `exports/` dans Finder/Explorer

**Ce que vous montrez:**
- `transactions.xlsx`
- `model_predictions.xlsx`
- `ensemble_results.xlsx`
- `flagged_transactions.xlsx`

**Ce que vous dites:**

> "Tout est automatiquement exporté en Excel pour Tableau. Quatre fichiers pour créer des dashboards: analyse temporelle, comparaison des modèles, distribution des fraudes, transactions flaggées. Voir le document CHARTS.md pour les visualisations recommandées."

---

### 5. Décisions Business (1 minute)

**Ce que vous dites:**

> "Ce système supporte plusieurs décisions business:
>
> **1. Blocage Temps Réel**: Transaction flaggée → carte bloquée immédiatement → réduction des pertes
>
> **2. Analyse des Patterns**: Identifier nouvelles techniques de fraude, heures/montants à risque
>
> **3. Optimisation Continue**: Comparer les 3 modèles, ajuster les seuils, réentraîner avec nouvelles données
>
> **4. Conformité**: Historique complet dans MongoDB pour audit, chaque décision est traçable
>
> Latence bout-en-bout: moins de 2 secondes. Scalable horizontalement via Kafka et Spark."

---

### 6. Questions & Réponses

**Questions fréquentes:**

**Q: Pourquoi 3 modèles au lieu d'un seul?**
> R: Robustesse. Un modèle peut se tromper. Trois modèles d'accord = haute confiance. Ça réduit les faux positifs qui coûtent cher (blocage carte client légitime).

**Q: Pourquoi Kafka et pas directement fichier CSV?**
> R: Kafka permet le streaming temps réel. En production, les transactions arrivent en continu. On veut détecter immédiatement, pas attendre un batch.

**Q: Pourquoi MongoDB et pas SQL?**
> R: NoSQL est flexible (schéma peut évoluer), performant sur requêtes fraud spécifiques, et excellent pour agrégations analytics.

**Q: Comment vous gérez le déséquilibre (0.17% fraudes)?**
> R: Gradient Boosting est spécialisé pour ça. On utilise aussi AUC-ROC (pas juste accuracy) et on peut ajuster les class weights.

**Q: Dagster vs scripts?**
> R: Scripts = manuel, erreur-prone, pas de visibilité. Dagster = reproductible, dépendances auto, logs centralisés, métadonnées riches.

---

## Dépannage Express

### Dagster ne démarre pas

```bash
# Tuer processus sur port 3000
lsof -i :3000
kill -9 <PID>

# Relancer
just dagster
```

### Services Docker ne démarrent pas

```bash
just stop
just start
just health
```

### Pipeline bloqué

```bash
# Dans Dagster UI: Terminer le run
# Puis:
just clean-checkpoint
# Relancer le job
```

### Pas de données dans MongoDB

```bash
# Vérifier producer
docker logs producer --tail 20

# Redémarrer si nécessaire
just restart
```

---

## Plan B (Si Tout Échoue)

**Avoir préparé avant:**
1. Screenshots de Dagster UI avec pipeline complet
2. Fichiers Excel dans exports/ (pré-générés)
3. Captures MongoDB avec les 4 collections
4. Screenshots de métriques (accuracy >99%)

**Présentation alternative:**
- Montrez les captures d'écran
- Expliquez l'architecture avec le schéma
- Ouvrez le code source (producer.py, train_model.py) pour montrer la technique
- Expliquez comment ça fonctionne conceptuellement

---

## Checklist Finale

**Avant de commencer:**
- [ ] Docker Desktop est lancé
- [ ] `just health` → tout est vert
- [ ] Dagster UI accessible (http://localhost:3000)
- [ ] Mongo Express accessible (http://localhost:8081)
- [ ] README.md ouvert pour schéma architecture
- [ ] CHARTS.md disponible si questions sur Tableau
- [ ] Écran partagé / projeté correctement

**Timing:**
- [ ] Introduction: 2 min
- [ ] Dagster démo: 8 min (dont 5 min exécution)
- [ ] ML ensemble: 2 min
- [ ] MongoDB + Export: 2 min
- [ ] Business decisions: 1 min
- [ ] Questions: reste du temps

**Talking points mémorisés:**
- [ ] 284K transactions, 0.17% fraudes
- [ ] 3 modèles, vote majoritaire, >99% accuracy
- [ ] 4 collections MongoDB pour traçabilité
- [ ] <2 secondes latence bout-en-bout
- [ ] Scalable (Kafka partitions, Spark cluster)

---

**🎓 Bonne présentation!**
