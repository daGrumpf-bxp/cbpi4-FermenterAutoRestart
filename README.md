# cbpi4-FermenterAutoRestart

Plugin pour **CraftBeerPi4** qui reprend automatiquement le mode **Auto** des fermenteurs après un reboot ou un redémarrage de cbpi4.

## Fonctionnement

- Toutes les 10 secondes, le plugin surveille l'état auto (on/off) de chaque fermenteur et le sauvegarde dans un fichier `fermenter_auto_state.json` dans le dossier config de cbpi4.
- Au démarrage, le plugin attend 20 secondes que cbpi4 ait chargé tous ses composants, puis relit ce fichier et **relance le mode auto** pour chaque fermenteur qui :
  1. avait le mode auto actif avant le reboot **ET**
  2. a la propriété **AutoResumeStateAfterReboot = Yes** configurée dans ses paramètres hardware.

## Installation

```bash
pipx runpip cbpi4 install cbpi4-FermenterAutoRestart.zip
```

Redémarrer cbpi4 après l'installation.

## Configuration par fermenteur

Dans la page **Hardware** de cbpi4, éditer chaque fermenteur et changer son type de `Fermenter Hysteresis` vers `Fermenter Hysteresis + AutoRestart`. Le paramètre suivant apparaît alors dans le formulaire :

| Paramètre | Valeur | Effet |
|-----------|--------|-------|
| AutoResumeStateAfterReboot | **Yes** | Le mode auto reprend automatiquement après reboot |
| AutoResumeStateAfterReboot | **No** | Comportement par défaut cbpi4 (pas de reprise auto) |

Les fermenteurs sans ce paramètre (type `Fermenter Hysteresis` standard) ne sont pas affectés.

## Fichier d'état

`~/.cbpi/config/fermenter_auto_state.json`

```json
{
  "abc123": true,
  "def456": false
}
```

Les clés sont les IDs internes des fermenteurs, les valeurs sont `true` (auto était actif) ou `false`.

## Compatibilité

- CraftBeerPi4 >= 4.7.x
- Python 3.11+

## Auteur

Pierre Grasswill

## Homepage

https://github.com/daGrumpf-bxp/cbpi4-FermenterAutoRestart
