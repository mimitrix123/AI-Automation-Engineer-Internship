"""Rule-constrained energy optimizer; replace scoring with a trained model when data is available."""
from dataclasses import dataclass

@dataclass
class EnergyAction:
    light_level: int
    hvac_enabled: bool
    reason: str


def optimize(*, occupied: bool, ambient_light: float, temperature: float,
             comfort_min: float = 20.0, comfort_max: float = 26.0) -> EnergyAction:
    light_level = 0 if not occupied else max(0, min(100, int(100 - ambient_light)))
    hvac = occupied and (temperature < comfort_min or temperature > comfort_max)
    reason = "occupied comfort optimization" if occupied else "unoccupied energy saving"
    return EnergyAction(light_level=light_level, hvac_enabled=hvac, reason=reason)
