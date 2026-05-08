# cbpi4-FermenterAutoRestart — v1.0.13 (stable)
# Plugin CraftBeerPi4 — Fermenter Hysteresis avec reprise d'état auto après reboot

import asyncio
import json
import logging
from pathlib import Path

from cbpi.api import *
from cbpi.api.base import CBPiBase

logger = logging.getLogger(__name__)

PROP_KEY      = "AutoResumeStateAfterReboot"
STATE_FILENAME = "fermenter_auto_state.json"


def _state_file(cbpi) -> Path:
    try:
        return Path(cbpi.config_folder.get_file_path(STATE_FILENAME))
    except Exception:
        return Path("./config") / STATE_FILENAME


def _load_saved_states(cbpi) -> dict:
    p = _state_file(cbpi)
    if p.exists():
        try:
            with open(p) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[AutoRestart] Lecture {p} échouée : {e}")
    return {}


def _save_states(cbpi, states: dict):
    p = _state_file(cbpi)
    try:
        with open(p, "w") as f:
            json.dump(states, f, indent=2)
    except Exception as e:
        logger.warning(f"[AutoRestart] Écriture {p} échouée : {e}")


def _resume_enabled(props: dict) -> bool:
    return str(props.get(PROP_KEY, "No")).strip().lower() == "yes"


@parameters([
    Property.Select(
        label="AutoResumeStateAfterReboot",
        options=["Yes", "No"],
        description="Reprendre le mode Auto après un redémarrage du système",
    ),
    Property.Number(
        label="HeaterOffsetOn",
        configurable=True,
        description="Offset as decimal number when the heater is switched on. Should be greater then 'HeaterOffsetOff'. For example a value of 2 switches on the heater if the current temperature is 2 degrees below the target temperature",
    ),
    Property.Number(
        label="HeaterOffsetOff",
        configurable=True,
        description="Offset as decimal number when the heater is switched off. Should be smaller then 'HeaterOffsetOn'. For example a value of 1 switches off the heater if the current temperature is 1 degree below the target temperature",
    ),
    Property.Number(
        label="CoolerOffsetOn",
        configurable=True,
        description="Offset as decimal number when the cooler is switched on. Should be greater then 'CoolerOffsetOff'. For example a value of 2 switches on the cooler if the current temperature is 2 degrees above the target temperature",
    ),
    Property.Number(
        label="CoolerOffsetOff",
        configurable=True,
        description="Offset as decimal number when the cooler is switched off. Should be smaller then 'CoolerOffsetOn'. For example a value of 1 switches off the cooler if the current temperature is 1 degree above the target temperature",
    ),
    Property.Number(
        label="HeaterMaxPower",
        configurable=True,
        description="Max Power [%] for Heater (default: 100)",
    ),
    Property.Number(
        label="CoolerMaxPower",
        configurable=True,
        description="Max Power [%] for Cooler (default: 100)",
    ),
    Property.Select(
        label="AutoStart",
        options=["Yes", "No"],
        description="Autostart Fermenter on cbpi start",
    ),
    Property.Sensor(
        label="sensor2",
        description="Optional Sensor for LCDisplay (e.g. iSpindle)",
    ),
])
class FermenterHysteresisAutoRestart(CBPiFermenterLogic):
    """
    Fermenter Hysteresis avec reprise d'état auto après reboot.
    Logique identique au FermenterHysteresis du core cbpi4.
    Paramètre supplémentaire : AutoResumeStateAfterReboot (Yes/No).
    """

    async def run(self):
        try:
            self.heater_offset_min = float(self.props.get("HeaterOffsetOn", 0.2))
            self.heater_offset_max = float(self.props.get("HeaterOffsetOff", 0))
            self.cooler_offset_min = float(self.props.get("CoolerOffsetOn", 0.2))
            self.cooler_offset_max = float(self.props.get("CoolerOffsetOff", 0))
            self.heater_max_power  = int(self.props.get("HeaterMaxPower", 100))
            self.cooler_max_power  = int(self.props.get("CoolerMaxPower", 100))
            self.heater_max_output = self.heater_max_power
            self.cooler_max_output = self.cooler_max_power

            self.fermenter = self.get_fermenter(self.id)
            self.heater    = self.fermenter.heater
            self.cooler    = self.fermenter.cooler

            heater = self.cbpi.actor.find_by_id(self.heater)
            cooler = self.cbpi.actor.find_by_id(self.cooler)

            while self.running == True:
                sensor_value = float(self.get_sensor_value(self.fermenter.sensor).get("value"))
                target_temp  = float(self.get_fermenter_target_temp(self.id))
                try:
                    heater_state = heater.instance.state
                except:
                    heater_state = False
                try:
                    cooler_state = cooler.instance.state
                except:
                    cooler_state = False

                if sensor_value + self.heater_offset_min <= target_temp:
                    if self.heater and (heater_state == False):
                        await self.actor_on(self.heater, self.heater_max_power, self.heater_max_output)
                if sensor_value + self.heater_offset_max >= target_temp:
                    if self.heater and (heater_state == True):
                        await self.actor_off(self.heater)
                if sensor_value >= self.cooler_offset_min + target_temp:
                    if self.cooler and (cooler_state == False):
                        await self.actor_on(self.cooler, self.cooler_max_power, self.cooler_max_output)
                if sensor_value <= self.cooler_offset_max + target_temp:
                    if self.cooler and (cooler_state == True):
                        await self.actor_off(self.cooler)

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.error("FermenterHysteresisAutoRestart Error {}".format(e))
        finally:
            self.running = False
            if self.heater:
                await self.actor_off(self.heater)
            if self.cooler:
                await self.actor_off(self.cooler)


class FermenterAutoRestartExtension(CBPiExtension):

    def __init__(self, cbpi):
        self.cbpi = cbpi
        self._known_states: dict = {}
        self._task = asyncio.create_task(self.run())

    async def run(self):
        try:
            logger.warning("[AutoRestart] Démarrage — attente init cbpi4 (20s)...")
            await asyncio.sleep(20)
            await self._restore()
            await self._watch_loop()
        except Exception as e:
            logger.error(f"[AutoRestart] Erreur fatale : {e}", exc_info=True)

    async def _restore(self):
        saved = _load_saved_states(self.cbpi)
        logger.warning(f"[AutoRestart] États sauvegardés : {saved}")
        for item in self._get_items():
            fid      = item.get("id", "")
            name     = item.get("name", fid)
            props    = item.get("props", {})
            resume   = _resume_enabled(props)
            was_auto = saved.get(fid, False)
            logger.warning(f"[AutoRestart] {name} | {PROP_KEY}={resume} | état précédent={was_auto}")
            if resume and was_auto:
                try:
                    await self.cbpi.fermenter.toggle(fid)
                    logger.warning(f"[AutoRestart] {name} → Auto RELANCÉ ✓")
                    self._known_states[fid] = True
                except Exception as e:
                    logger.error(f"[AutoRestart] {name} → échec : {e}")
                    self._known_states[fid] = False
            else:
                self._known_states[fid] = False

    async def _watch_loop(self):
        while True:
            try:
                await asyncio.sleep(10)
                changed = False
                for item in self._get_items():
                    fid          = item.get("id", "")
                    name         = item.get("name", fid)
                    current_auto = bool(item.get("state", False))
                    if self._known_states.get(fid) != current_auto:
                        logger.warning(f"[AutoRestart] {name} état : {self._known_states.get(fid)} → {current_auto}")
                        self._known_states[fid] = current_auto
                        changed = True
                if changed:
                    _save_states(self.cbpi, self._known_states)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[AutoRestart] Erreur surveillance : {e}")

    def _get_items(self) -> list:
        try:
            return self.cbpi.fermenter.get_state().get("data", [])
        except Exception as e:
            logger.warning(f"[AutoRestart] get_state() échoué : {e}")
            return []


def setup(cbpi):
    cbpi.plugin.register("Fermenter Hysteresis + AutoRestart", FermenterHysteresisAutoRestart)
    cbpi.plugin.register("FermenterAutoRestartExtension", FermenterAutoRestartExtension)
    logger.warning("[AutoRestart] Plugin enregistré.")
