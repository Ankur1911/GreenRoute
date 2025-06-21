from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

# Enums
class VehicleType(str, Enum):
    TRUCK = "truck"
    VAN = "van"
    PICKUP = "pickup"
    HEAVY_TRUCK = "heavy_truck"

class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL_B7 = "diesel_b7"
    ELECTRIC = "electric"
    HYBRID = "hybrid"

class TerrainType(str, Enum):
    FLAT = "flat"
    HILLY = "hilly"
    MOUNTAINOUS = "mountainous"

class RoadType(str, Enum):
    HIGHWAY = "highway"
    URBAN = "urban"
    RURAL = "rural"

# Pydantic Models
class LocationModel(BaseModel):
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TripRequest(BaseModel):
    start_location: LocationModel
    end_location: LocationModel
    vehicle_type: VehicleType
    fuel_type: FuelType
    load_weight: float = Field(gt=0, description="Load weight in kg")
    terrain: TerrainType = TerrainType.FLAT
    road_type: RoadType = RoadType.HIGHWAY

class CityEmission(BaseModel):
    city: str
    distance_km: float
    co2_emission_kg: float
    terrain: TerrainType
    road_type: RoadType

class EmissionBreakdown(BaseModel):
    ttw_kg: float  # Tank-to-Wheel
    wtt_kg: float  # Well-to-Tank
    wtw_kg: float  # Well-to-Wheel (TTW + WTT)

class FuelComparison(BaseModel):
    fuel_type: FuelType
    emission_kg: float
    percentage_difference: float

class TripResponse(BaseModel):
    trip_id: str
    total_distance_km: float
    total_fuel_consumption: float
    total_co2_emission: EmissionBreakdown
    city_emissions: List[CityEmission]
    fuel_comparisons: List[FuelComparison]
    route_coordinates: List[List[float]]
    reasoning: str
    calculation_time_ms: int

# Constants based on ISO 14083 and GLEC Framework
EMISSION_FACTORS = {
    # gCO2/km base emissions for different vehicle types and fuels
    VehicleType.TRUCK: {
        FuelType.DIESEL_B7: {"ttw": 850, "wtt": 220},
        FuelType.PETROL: {"ttw": 920, "wtt": 250},
        FuelType.ELECTRIC: {"ttw": 0, "wtt": 180},
        FuelType.HYBRID: {"ttw": 450, "wtt": 190}
    },
    VehicleType.VAN: {
        FuelType.DIESEL_B7: {"ttw": 650, "wtt": 170},
        FuelType.PETROL: {"ttw": 720, "wtt": 190},
        FuelType.ELECTRIC: {"ttw": 0, "wtt": 140},
        FuelType.HYBRID: {"ttw": 350, "wtt": 150}
    },
    VehicleType.PICKUP: {
        FuelType.DIESEL_B7: {"ttw": 450, "wtt": 120},
        FuelType.PETROL: {"ttw": 520, "wtt": 140},
        FuelType.ELECTRIC: {"ttw": 0, "wtt": 100},
        FuelType.HYBRID: {"ttw": 250, "wtt": 110}
    },
    VehicleType.HEAVY_TRUCK: {
        FuelType.DIESEL_B7: {"ttw": 1200, "wtt": 310},
        FuelType.PETROL: {"ttw": 1350, "wtt": 360},
        FuelType.ELECTRIC: {"ttw": 0, "wtt": 250},
        FuelType.HYBRID: {"ttw": 650, "wtt": 280}
    }
}

