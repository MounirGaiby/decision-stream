# Guide de Visualisation Tableau

**Objectif:** Créer des dashboards pour analyser les fraudes et prendre des décisions business.

**Source des données:** Fichiers Excel dans le dossier `exports/` (générés automatiquement par Dagster)

---

## 📊 Fichiers Excel Disponibles

Après avoir exécuté le job `full_pipeline` ou `export_to_excel` dans Dagster:

| Fichier | Collection MongoDB | Contenu |
|---------|-------------------|---------|
| `transactions.xlsx` | transactions | Toutes les transactions brutes (Time, V1-V28, Amount, Class) |
| `model_predictions.xlsx` | model_predictions | Prédictions individuelles par modèle (RF, GB, LR) |
| `ensemble_results.xlsx` | ensemble_results | Décisions finales (vote majoritaire, confiance) |
| `flagged_transactions.xlsx` | flagged_transactions | Transactions à haut risque (action requise) |

---

## 🎨 Dashboards Recommandés

### Dashboard 1: Vue d'Ensemble Fraude (Executive Summary)

**Audience:** Direction, managers
**Objectif:** Comprendre rapidement l'état de la fraude

#### Charts à Créer

**1.1 KPIs (Cartes de Métriques)**
- **Total Transactions**: `COUNT(transaction_id)`
- **Taux de Fraude**: `SUM(Class=1) / COUNT(*) * 100%`
- **Transactions Flaggées**: `COUNT(flagged_transactions)`
- **Accuracy ML**: `>99%` (depuis validate_data)

**Décisions Supportées:**
- Surveiller volume global (throughput système)
- Comparer taux de fraude vs objectifs (0.17% attendu)
- Prioriser actions sur transactions flaggées
- Valider performance ML acceptable

---

**1.2 Distribution Fraude vs Normal (Donut Chart)**
- **Source:** `transactions.xlsx`
- **Grouper par:** `Class` (0=Normal, 1=Fraude)
- **Valeur:** Nombre de transactions
- **Couleurs:** Vert (normal), Rouge (fraude)

**Décisions Supportées:**
- Vérifier déséquilibre des classes (normal: 99.83%, fraude: 0.17%)
- Confirmer présence de cas de fraude dans les données
- Évaluer si besoin de rebalancing pour entraînement

---

**1.3 Évolution Temporelle (Line Chart)**
- **Source:** `transactions.xlsx`
- **Axe X:** `Time` (converti en heures: Time/3600)
- **Axe Y:** Nombre de transactions
- **Couleur:** Séparer par `Class`

**Décisions Supportées:**
- **Patterns temporels:** Identifier heures à haut risque
- **Pics de fraude:** Détecter campagnes de fraude
- **Planification ressources:** Adapter staffing aux heures de pointe
- **Anomalies:** Spot suspicious spikes

---

### Dashboard 2: Performance ML (Data Science Team)

**Audience:** Data scientists, ML engineers
**Objectif:** Analyser et optimiser les modèles

#### Charts à Créer

**2.1 Matrice de Confusion (Heat Map)**
- **Source:** `ensemble_results.xlsx`
- **Lignes:** `Class` (Réel)
- **Colonnes:** `final_prediction` (Prédit)
- **Valeur:** Nombre de transactions
- **Couleur:** Gradient (vert → rouge)

```
                Prédit Normal | Prédit Fraude
Réel Normal         TN (99%)  |  FP (<1%)
Réel Fraude         FN (<1%)  |  TP (>85%)
```

**Décisions Supportées:**
- **True Positives (TP):** Fraudes correctement détectées → succès
- **False Positives (FP):** Fausses alarmes → coût support client
- **False Negatives (FN):** Fraudes manquées → pertes financières
- **True Negatives (TN):** Transactions normales → pas d'action

**Actions:**
- FP élevé → Augmenter seuil de confiance (80% → 85%)
- FN élevé → Diminuer seuil ou réentraîner avec plus de données
- TP/TN élevés → Système performant

---

**2.2 Comparaison des 3 Modèles (Bar Chart)**
- **Source:** `model_predictions.xlsx`
- **Axe X:** `model_name` (random_forest, gradient_boosting, logistic_regression)
- **Axe Y:** Accuracy (calculée: correct predictions / total)
- **Couleur:** Par modèle

**Décisions Supportées:**
- **Meilleur modèle:** Identifier le modèle le plus performant
- **Modèle faible:** Remplacer ou retirer du vote
- **Consensus:** Vérifier si les 3 modèles sont utiles ou redondants

---

**2.3 Distribution de Confiance (Histogram)**
- **Source:** `ensemble_results.xlsx`
- **Axe X:** `confidence_score` (bins: 0-20%, 20-40%, ..., 80-100%)
- **Axe Y:** Nombre de prédictions
- **Couleur:** Séparer par `final_prediction` (0=Normal, 1=Fraude)

**Décisions Supportées:**
- **Haute confiance (>80%):** Transactions à auto-bloquer
- **Moyenne confiance (50-80%):** Revue manuelle requise
- **Basse confiance (<50%):** Laisser passer, surveiller
- **Calibration:** Vérifier que confiance reflète accuracy réelle

---

### Dashboard 3: Transactions Flaggées (Équipe Opérationnelle)

**Audience:** Analystes fraude, support client
**Objectif:** Actions immédiates sur cas critiques

#### Charts à Créer

**3.1 Top 10 Transactions à Haut Risque (Table)**
- **Source:** `flagged_transactions.xlsx`
- **Colonnes affichées:**
  - `transaction_id`
  - `amount` (montant)
  - `confidence` (score de confiance)
  - `reason` (all_models_agree / high_confidence)
  - `flagged_at` (timestamp)
- **Tri:** Par `confidence` descendant

**Décisions Supportées:**
- **Action immédiate:** Bloquer carte, contacter client
- **Priorisation:** Traiter par ordre de confiance/montant
- **Investigation:** Analyser patterns communs

---

**3.2 Distribution des Montants Frauduleux (Box Plot)**
- **Source:** `flagged_transactions.xlsx`
- **Axe Y:** `amount`
- **Grouper par:** `reason`

**Décisions Supportées:**
- **Montants typiques:** Identifier la fourchette des fraudes
- **Outliers:** Fraudes exceptionnellement élevées → priorité
- **Stratégie:** Ajuster limites de cartes par profil client

---

**3.3 Raisons de Flagging (Pie Chart)**
- **Source:** `flagged_transactions.xlsx`
- **Grouper par:** `reason`
  - all_models_agree (unanimité)
  - high_confidence (>80%)
- **Valeur:** Nombre de transactions

**Décisions Supportées:**
- **Taux unanimité:** Si élevé (>60%) → système très confiant
- **Taux high_confidence:** Si élevé → peut-être trop agressif
- **Balance:** Ajuster seuil de 80% si nécessaire

---

### Dashboard 4: Analyse Temporelle Avancée (Stratégie)

**Audience:** Direction, risk management
**Objectif:** Trends long-terme et optimisation stratégie

#### Charts à Créer

**4.1 Taux de Détection par Jour (Line Chart with Trend)**
- **Source:** `ensemble_results.xlsx`
- **Axe X:** Date (grouper par jour)
- **Axe Y:** % de fraudes détectées (TP / (TP + FN))
- **Ligne de tendance:** Moyenne mobile 7 jours

**Décisions Supportées:**
- **Amélioration continue:** Tendance à la hausse = bon
- **Dégradation:** Tendance à la baisse → réentraîner modèles
- **Stabilité:** Variance élevée → investiguer causes

---

**4.2 Coût vs Bénéfice (Dual Axis Chart)**
- **Source:** `ensemble_results.xlsx` + calculs
- **Axe X:** Date
- **Axe Y1 (gauche):** Coût des faux positifs (FP * coût support)
- **Axe Y2 (droit):** Bénéfice des vrais positifs (TP * montant moyen fraude)

**Paramètres:**
- Coût support client: ~50€ par FP
- Montant moyen fraude: calculer depuis `flagged_transactions.amount`

**Décisions Supportées:**
- **ROI du système:** Bénéfice >> Coût = système rentable
- **Optimisation seuil:** Si Coût trop élevé → augmenter seuil
- **Business case:** Justifier investissement ML

---

**4.3 Accord des Modèles (Stacked Bar Chart)**
- **Source:** `ensemble_results.xlsx`
- **Axe X:** Date (ou batch)
- **Axe Y:** % de transactions
- **Empilement:** Par `model_agreement`
  - Unanimité (3/3)
  - Majorité (2/3)
  - Désaccord (1/2 - rare)

**Décisions Supportées:**
- **Consensus élevé:** Modèles convergent → prédictions fiables
- **Consensus faible:** Modèles divergent → données ambiguës ou drift
- **Action:** Si accord baisse → investiguer data drift, réentraîner

---

## 🎯 Décisions Business par Dashboard

### Opérationnelles (Court Terme)

**Dashboard 1 + 3:**
- Bloquer cartes flaggées immédiatement
- Contacter clients pour transactions douteuses
- Allouer analystes aux heures de pointe
- Ajuster limites de transaction temps réel

### Tactiques (Moyen Terme)

**Dashboard 2:**
- Réentraîner modèles avec nouvelles données (hebdomadaire/mensuel)
- Ajuster seuils de confiance (80% → 75% ou 85%)
- Retirer modèle sous-performant du vote
- Ajouter features si recall insuffisant

### Stratégiques (Long Terme)

**Dashboard 4:**
- Investir dans infrastructure si throughput insuffisant
- Développer nouveaux modèles (Deep Learning)
- Étendre à d'autres types de fraude (AML, identity theft)
- Intégrer données externes (géolocalisation, device fingerprinting)

---

## 💡 Conseils Tableau

### Connexion aux Données

**Option 1: Excel (Recommandé pour démo)**
1. Fichiers dans `exports/`
2. Data → Connect to File → Excel
3. Sélectionner le fichier
4. Glisser la feuille vers l'espace de travail

**Option 2: MongoDB (Production)**
1. Data → To a Server → MongoDB
2. Server: localhost, Port: 27017
3. Database: fraud_detection, Auth: admin/admin123
4. Collection: sélectionner (transactions, model_predictions, etc.)

### Calculs Utiles

**Accuracy:**
```
SUM(IF [Class] = [final_prediction] THEN 1 ELSE 0 END) / COUNT([transaction_id])
```

**Precision:**
```
[True Positives] / ([True Positives] + [False Positives])
```

**Recall:**
```
[True Positives] / ([True Positives] + [False Negatives])
```

**Taux de Fraude:**
```
SUM(IF [Class] = 1 THEN 1 ELSE 0 END) / COUNT([transaction_id]) * 100
```

### Bonnes Pratiques

1. **Couleurs cohérentes:**
   - Vert: Normal, OK, True Negatives
   - Rouge: Fraude, Alert, True/False Positives
   - Jaune: Attention, False Negatives

2. **Tooltips riches:**
   - Ajouter ID transaction pour drill-down
   - Afficher montant, confiance, raison flagging

3. **Filtres interactifs:**
   - Par date (range slider)
   - Par type de fraude détectée/manquée
   - Par modèle (dans dashboard 2)

4. **Actions:**
   - Click sur transaction → ouvrir détail dans Mongo Express
   - Export liste transactions flaggées vers CSV pour équipe ops

---

## 📈 Exemple de Workflow Décisionnel

### Scénario: Trop de Faux Positifs

**Observation** (Dashboard 2):
- Matrice de confusion montre FP = 5% des normaux
- 500 transactions normales flaggées par jour
- Coût support: 500 * 50€ = 25,000€/jour

**Analyse** (Dashboard 2 + 4):
- Accord des modèles: seulement 40% unanimité sur FP
- Distribution confiance: beaucoup de FP entre 80-85%

**Décision:**
- Augmenter seuil de flagging de 80% → 90%
- Réentraîner avec données des faux positifs (hard negatives)

**Validation** (après 1 semaine):
- Dashboard 1: FP réduits à 2%
- Dashboard 4: Coût baissé à 10,000€/jour
- Dashboard 2: Recall stable (pas de dégradation)

**Résultat:** 15,000€/jour économisés, clients moins perturbés

---

## 🔗 Ressources

- **Données sources:** Exécuter `just dagster` puis job `export_to_excel`
- **Documentation système:** [README.md](../README.md)
- **Guide présentation:** [INSTRUCTIONS.md](INSTRUCTIONS.md)

---

**💡 Astuce:** Créer un dashboard par semaine. Commencez par Dashboard 1 (vue d'ensemble), puis ajoutez les autres au fur et à mesure.
