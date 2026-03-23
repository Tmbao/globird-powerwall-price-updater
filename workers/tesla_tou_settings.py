from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class TouPeriod:
    fromDayOfWeek: int
    fromHour: int
    fromMinute: int
    toDayOfWeek: int
    toHour: int
    toMinute: int


@dataclass_json
@dataclass
class TouPeriodContainer:
    periods: List[TouPeriod]


@dataclass_json
@dataclass
class Season:
    fromMonth: int
    fromDay: int
    toMonth: int
    toDay: int
    tou_periods: Dict[str, TouPeriodContainer]


@dataclass_json
@dataclass
class EnergyChargesSeason:
    rates: Dict[str, float]


@dataclass_json
@dataclass
class DailyCharge:
    name: str
    amount: float


@dataclass_json
@dataclass
class DemandChargesSeason:
    rates: Dict[str, Any]


@dataclass_json
@dataclass
class SellTariff:
    min_applicable_demand: float
    monthly_minimum_bill: float
    monthly_charges: float
    max_applicable_demand: float
    utility: str
    demand_charges: Dict[str, DemandChargesSeason]
    daily_charges: List[DailyCharge]
    seasons: Dict[str, Season]
    code: str
    energy_charges: dict[str, EnergyChargesSeason]
    daily_demand_charges: Dict[str, Any]
    currency: str
    name: str


@dataclass_json
@dataclass
class TimeOfUseSettings:
    version: int
    monthly_minimum_bill: float
    min_applicable_demand: float
    max_applicable_demand: float
    monthly_charges: float
    utility: str
    code: str
    name: str
    currency: str
    daily_charges: List[DailyCharge]
    daily_demand_charges: Dict[str, Any]
    demand_charges: Dict[str, DemandChargesSeason]
    energy_charges: Dict[str, EnergyChargesSeason]
    seasons: Dict[str, Season]
    sell_tariff: SellTariff
