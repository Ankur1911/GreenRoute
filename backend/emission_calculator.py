from models import FuelType, VehicleType, EMISSION_FACTORS, EmissionBreakdown, TerrainType, RoadType


# Terrain and road type multipliers
TERRAIN_MULTIPLIERS = {
    TerrainType.FLAT: 1.0,
    TerrainType.HILLY: 1.15,
    TerrainType.MOUNTAINOUS: 1.35
}

ROAD_TYPE_MULTIPLIERS = {
    RoadType.HIGHWAY: 1.0,
    RoadType.URBAN: 1.25,
    RoadType.RURAL: 1.1
}

# Load weight impact (additional gCO2/km per kg of load)
LOAD_WEIGHT_FACTOR = 0.05
class EmissionCalculator:
    """Service for CO2 emission calculations based on ISO 14083 and GLEC Framework"""
    
    @staticmethod
    def calculate_base_emission(vehicle_type: VehicleType, fuel_type: FuelType, 
                              distance_km: float) -> EmissionBreakdown:
        """Calculate base emissions for given parameters"""
        factors = EMISSION_FACTORS[vehicle_type][fuel_type]
        
        ttw_g = factors["ttw"] * distance_km
        wtt_g = factors["wtt"] * distance_km
        
        return EmissionBreakdown(
            ttw_kg=ttw_g / 1000,
            wtt_kg=wtt_g / 1000,
            wtw_kg=(ttw_g + wtt_g) / 1000
        )
    
    @staticmethod
    def apply_modifiers(base_emission: EmissionBreakdown, terrain: TerrainType, 
                       road_type: RoadType, load_weight: float, distance_km: float) -> EmissionBreakdown:
        """Apply terrain, road type, and load weight modifiers"""
        terrain_mult = TERRAIN_MULTIPLIERS[terrain]
        road_mult = ROAD_TYPE_MULTIPLIERS[road_type]
        load_addition_kg = (load_weight * LOAD_WEIGHT_FACTOR * distance_km) / 1000
        
        multiplier = terrain_mult * road_mult
        
        return EmissionBreakdown(
            ttw_kg=base_emission.ttw_kg * multiplier + load_addition_kg,
            wtt_kg=base_emission.wtt_kg * multiplier,
            wtw_kg=(base_emission.ttw_kg + base_emission.wtt_kg) * multiplier + load_addition_kg
        )
