# Commandes de Gestion - Confirmations Décalées

Ce dossier contient les commandes Django pour gérer le système de confirmations décalées automatiques.

## 📋 Vue d'ensemble

Le système de **confirmations décalées** permet aux opérateurs de planifier une confirmation automatique à une date/heure future, évitant ainsi de devoir traiter manuellement chaque commande en temps réel.

## 🛠️ Commandes disponibles

### 1. `process_delayed_confirmations.py`

**Fonction** : Traite automatiquement les confirmations décalées qui ont atteint leur date d'expiration.

**Usage** :
```bash
python manage.py process_delayed_confirmations
```

**Fonctionnement** :
- Recherche toutes les commandes avec l'état "Confirmation décalée" actif
- Vérifie si leur `date_fin_delayed` est dépassée
- Ferme automatiquement l'état "Confirmation décalée"
- Crée un nouvel état "Confirmée" avec transition automatique

**Sortie exemple** :
```
Début du traitement des confirmations décalées...
OK: Commande 211998 : Confirmation décalée -> Confirmée
=== RÉSUMÉ DU TRAITEMENT ===
Confirmations décalées traitées: 1
Heure de traitement: 08/09/2025 10:30:15
Traitement terminé avec succès !
```

### 2. `test_delayed_confirmations.py`

**Fonction** : Commande de test et diagnostic pour les confirmations décalées.

**Usage** :
```bash
# Mode normal (seulement les expirées)
python manage.py test_delayed_confirmations

# Mode force (traite toutes les confirmations décalées actives)
python manage.py test_delayed_confirmations --force
```

**Fonctionnalités** :
- Affiche les confirmations décalées et leur statut
- Mode `--force` pour traiter même les non-expirées
- Demande confirmation avant traitement
- Diagnostic détaillé

### 3. `setup_delayed_confirmation_cron.py`

**Fonction** : Affiche les instructions pour configurer l'exécution automatique périodique.

**Usage** :
```bash
python manage.py setup_delayed_confirmation_cron
```

**Sortie** : Instructions détaillées pour :
- Configuration manuelle via Planificateur de tâches Windows
- Script PowerShell automatique
- Configuration crontab (Linux/Mac)

## ⚙️ Configuration automatique

### Windows (Recommandé)

Exécutez ce script PowerShell **en tant qu'administrateur** :

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\Users\ASUS\Desktop\STAGE2025\YZ-CMD\manage.py process_delayed_confirmations" -WorkingDirectory "C:\Users\ASUS\Desktop\STAGE2025\YZ-CMD"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -TaskName "YZ-CMD-Confirmations-Delayed" -Description "Traite les confirmations décalées automatiquement"
```

### Vérification

```bash
# Vérifier si la tâche est créée
schtasks /query /tn "YZ-CMD-Confirmations-Delayed"

# Tester manuellement
python manage.py process_delayed_confirmations
```

## 🔧 Fonctionnement technique

### Modèle de données

Le champ `date_fin_delayed` dans `EtatCommande` stocke la date/heure limite :

```python
date_fin_delayed = models.DateTimeField(blank=True, null=True)
```

### Logique de traitement

1. **Recherche** : `date_fin_delayed <= now()` ET `date_fin IS NULL`
2. **Transition** : 
   - Fermer l'état actuel (`date_fin = now()`)
   - Créer nouvel état "Confirmée"
   - Commentaire automatique avec traçabilité

### Gestion des erreurs

- Vérification de l'existence de l'état "Confirmée"
- Gestion des erreurs par commande individuellement
- Logging détaillé pour le débogage

## 📊 Monitoring

### Vérifier les confirmations en attente

```python
from commande.models import EtatCommande
from django.utils import timezone

# Commandes en confirmation décalée
etats_delayed = EtatCommande.objects.filter(
    enum_etat__libelle='Confirmation décalée',
    date_fin__isnull=True
)

print(f"Confirmations décalées actives: {etats_delayed.count()}")

# Expirées
now = timezone.now()
expiries = etats_delayed.filter(date_fin_delayed__lte=now)
print(f"Expirées à traiter: {expiries.count()}")
```

### Logs

Les transitions sont enregistrées dans les logs Django :

```python
logger.info(f'Transition automatique: Commande {commande.id_yz} de "Confirmation décalée" vers "Confirmée"')
```

## ⚠️ Notes importantes

1. **Fréquence** : La tâche s'exécute toutes les 5 minutes
2. **Encodage** : Tous les emojis ont été supprimés pour compatibilité Windows CP1252
3. **Sécurité** : Pas de suppression de données, seulement des transitions d'état
4. **Performance** : Utilise `select_related()` pour optimiser les requêtes DB

## 🐛 Dépannage

### Problème d'encodage Unicode
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Solution** : Utiliser `chcp 65001` avant d'exécuter les commandes ou utiliser PowerShell.

### Aucune confirmation détectée
```
Aucune confirmation décalée à traiter
```
**Vérification** : Les dates `date_fin_delayed` sont-elles dans le futur ?

### Tâche planifiée ne s'exécute pas
1. Vérifier les permissions (Exécuter en tant qu'administrateur)
2. Vérifier le chemin Python dans PATH système
3. Tester manuellement la commande

## 📝 Développement

Pour modifier le comportement :

1. **Fréquence** : Modifier l'intervalle dans la tâche planifiée
2. **États cibles** : Modifier `libelle='Confirmée'` dans le code
3. **Logique métier** : Ajouter des conditions dans `process_delayed_confirmations.py`