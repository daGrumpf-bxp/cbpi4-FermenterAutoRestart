# cbpi4-FermenterAutoRestart

Plugin pour **CraftBeerPi4** qui reprend automatiquement le mode **Auto** des fermenteurs après un reboot ou un redémarrage de cbpi4.

## Fonctionnement

- Toutes les 10 secondes, le plugin surveille l'état auto (on/off) de chaque fermenteur et le sauvegarde dans un fichier `fermenter_auto_state.json` dans le dossier config de cbpi4.
- Au démarrage (après un reboot), le plugin attend 5 secondes que cbpi4 ait chargé tous ses composants, puis relit ce fichier et **relance le mode auto** pour chaque fermenteur qui :
  1. avait le mode auto actif avant le reboot **ET**
  2. a la propriété **AutoRestart = Yes** configurée dans ses paramètres hardware.

## Installation

```bash
# Depuis le dossier du plugin
pip install -e . --break-system-packages

# Ou directement depuis une archive zip
pip install cbpi4-FermenterAutoRestart.zip --break-system-packages
```

Puis ajouter `cbpi4-FermenterAutoRestart` à la liste des plugins dans `config.yaml` :

```yaml
plugins:
  - cbpi4ui
  - cbpi4-FermenterHysteresis
  - cbpi4-FermenterAutoRestart   # ← ajouter cette ligne
```

## Configuration par fermenteur

Dans la page **Hardware** de cbpi4, éditer chaque fermenteur et régler le paramètre :

| Paramètre | Valeur | Effet |
|-----------|--------|-------|
| AutoRestart | **Yes** | Le mode auto reprend automatiquement après reboot |
| AutoRestart | **No** | Comportement par défaut cbpi4 (pas de reprise auto) |

## Fichier d'état

`~/.cbpi/fermenter_auto_state.json` (ou dans le dossier config de cbpi4)

```json
{
  "abc123": true,
  "def456": false
}
```

Les clés sont les IDs internes des fermenteurs, les valeurs sont `true` (auto était actif) ou `false`.

## Notes

- Le délai de 5 secondes au démarrage est intentionnel pour laisser le temps à cbpi4 de charger sensors, actors et fermenters avant de tenter de basculer le mode auto.
- Si le mode auto échoue à se relancer (ex. capteur absent), une erreur est loguée mais cbpi4 continue de fonctionner normalement.
- Compatible cbpi4 >= 4.0.0
