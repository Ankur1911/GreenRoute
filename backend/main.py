from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import google.generativeai as genai
from functools import lru_cache

from models import VehicleType, FuelType, TerrainType, RoadType, LocationModel, TripRequest, CityEmission, EmissionBreakdown, TripResponse, FuelComparison, EMISSION_FACTORS
from route_service import RouteService
from emission_calculator import EmissionCalculator
from reasoning import ReasoningService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GreenRoute API",
    description="CO2 Emission Tracking and Route Optimization API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Cache for frequently accessed data
@lru_cache(maxsize=100)
def get_cached_emission_factors(vehicle_type: str, fuel_type: str):
    """Cache emission factors for better performance"""
    return EMISSION_FACTORS[VehicleType(vehicle_type)][FuelType(fuel_type)]

# API Endpoints
@app.get("/")
async def root():
    return {"message": "GreenRoute API - CO2 Emission Tracking and Route Optimization"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/calculate-trip", response_model=TripResponse)
async def calculate_trip(trip_request: TripRequest):
    """Calculate CO2 emissions and optimize route for a trip"""
    start_time = datetime.now()
    
    try:
        # Generate unique trip ID
        trip_id = f"trip_{int(datetime.now().timestamp())}"
        
        # Geocode addresses if coordinates not provided
        if not trip_request.start_location.latitude:
            start_coords = await route_service.geocode_address(trip_request.start_location.address)
        else:
            start_coords = (trip_request.start_location.latitude, trip_request.start_location.longitude)
            
        if not trip_request.end_location.latitude:
            end_coords = await route_service.geocode_address(trip_request.end_location.address)
        else:
            end_coords = (trip_request.end_location.latitude, trip_request.end_location.longitude)
        
        # Get optimized route with cities
        route_data = await route_service.get_route_with_cities(start_coords, end_coords)
        route_service.route = route_data
        # Calculate city-wise emissions
        city_emissions = []
        total_emission_sum = EmissionBreakdown(ttw_kg=0, wtt_kg=0, wtw_kg=0)
        
        for city_data in route_data["cities"]:
            # Use city-specific terrain and road type if available, otherwise use request defaults
            city_terrain = city_data.get("terrain", trip_request.terrain)
            city_road_type = city_data.get("road_type", trip_request.road_type)
            
            # Calculate base emission for this city segment
            city_base_emission = EmissionCalculator.calculate_base_emission(
                trip_request.vehicle_type,
                trip_request.fuel_type,
                city_data["segment_distance_km"]
            )
            
            # Apply modifiers for this city segment
            city_emission = EmissionCalculator.apply_modifiers(
                city_base_emission,
                city_terrain,
                city_road_type,
                trip_request.load_weight,
                city_data["segment_distance_km"]
            )
            
            # Add to city emissions list
            city_emissions.append(
                CityEmission(
                    city=city_data["name"],
                    distance_km=city_data["segment_distance_km"],
                    co2_emission_kg=city_emission.wtw_kg,
                    terrain=city_terrain,
                    road_type=city_road_type
                )
            )
            
            # Sum up total emissions
            total_emission_sum.ttw_kg += city_emission.ttw_kg
            total_emission_sum.wtt_kg += city_emission.wtt_kg
            total_emission_sum.wtw_kg += city_emission.wtw_kg
        
        # Use summed emissions as total
        total_emission = total_emission_sum
        
        # Calculate fuel consumption based on total distance
        fuel_consumption = route_data["distance_km"] * 0.08  # L/km estimate
        
        # Calculate fuel comparisons for each city and total
        fuel_comparisons = []
        baseline_total_emission = total_emission.wtw_kg
        
        for fuel in FuelType:
            if fuel == trip_request.fuel_type:
                fuel_comparisons.append(
                    FuelComparison(
                        fuel_type=fuel,
                        emission_kg=baseline_total_emission,
                        percentage_difference=0.0
                    )
                )
            else:
                # Calculate total emission for this fuel type across all cities
                fuel_total_emission = 0.0
                
                for city_data in route_data["cities"]:
                    city_terrain = city_data.get("terrain", trip_request.terrain)
                    city_road_type = city_data.get("road_type", trip_request.road_type)
                    
                    city_fuel_emission = EmissionCalculator.calculate_base_emission(
                        trip_request.vehicle_type, fuel, city_data["segment_distance_km"]
                    )
                    city_fuel_emission_modified = EmissionCalculator.apply_modifiers(
                        city_fuel_emission, city_terrain, city_road_type,
                        trip_request.load_weight, city_data["segment_distance_km"]
                    )
                    fuel_total_emission += city_fuel_emission_modified.wtw_kg
                
                percentage_diff = ((fuel_total_emission - baseline_total_emission) / baseline_total_emission) * 100
                
                fuel_comparisons.append(
                    FuelComparison(
                        fuel_type=fuel,
                        emission_kg=fuel_total_emission,
                        percentage_difference=percentage_diff
                    )
                )
        
        # Generate reasoning with city-specific information
        city_info = [{"name": city["name"], "distance": city["segment_distance_km"], 
                     "terrain": city.get("terrain", trip_request.terrain),
                     "road_type": city.get("road_type", trip_request.road_type)} 
                     for city in route_data["cities"]]
        
        reasoning = await ReasoningService.generate_reasoning({
            "vehicle_type": trip_request.vehicle_type,
            "fuel_type": trip_request.fuel_type,
            "distance_km": route_data["distance_km"],
            "terrain": trip_request.terrain,
            "road_type": trip_request.road_type,
            "load_weight": trip_request.load_weight,
            "cities": city_info,
            "total_cities": len(route_data["cities"])
        })
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return TripResponse(
            trip_id=trip_id,
            total_distance_km=route_data["distance_km"],
            total_fuel_consumption=fuel_consumption,
            total_co2_emission=total_emission,
            city_emissions=city_emissions,
            fuel_comparisons=fuel_comparisons,
            route_coordinates=route_data["coordinates"],
            reasoning=reasoning,
            calculation_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error calculating trip: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emission-factors")
async def get_emission_factors():
    """Get all emission factors for reference"""
    return EMISSION_FACTORS

@app.get("/vehicle-types")
async def get_vehicle_types():
    """Get available vehicle types"""
    return [{"value": vt.value, "label": vt.value.replace("_", " ").title()} for vt in VehicleType]

@app.get("/fuel-types")
async def get_fuel_types():
    """Get available fuel types"""
    return [{"value": ft.value, "label": ft.value.replace("_", " ").title()} for ft in FuelType]

@app.get("/terrain-types")
async def get_terrain_types():
    """Get available terrain types"""
    return [{"value": tt.value, "label": tt.value.title()} for tt in TerrainType]

@app.get("/road-types")
async def get_road_types():
    """Get available road types"""
    return [{"value": rt.value, "label": rt.value.title()} for rt in RoadType]

@app.post("/city-emissions-heatmap")
async def get_city_emissions_heatmap(trip_request: TripRequest):
    """Get city-wise emissions data for heatmap visualization"""
    try:
        # Geocode addresses if coordinates not provided
        if not trip_request.start_location.latitude:
            start_coords = await route_service.geocode_address(trip_request.start_location.address)
        else:
            start_coords = (trip_request.start_location.latitude, trip_request.start_location.longitude)
            
        if not trip_request.end_location.latitude:
            end_coords = await route_service.geocode_address(trip_request.end_location.address)
        else:
            end_coords = (trip_request.end_location.latitude, trip_request.end_location.longitude)
        
        # Get route with cities
        route_data = route_service.route
        
        # Calculate emissions for each city
        heatmap_data = []
        for city_data in route_data["cities"]:
            city_terrain = city_data.get("terrain", trip_request.terrain)
            city_road_type = city_data.get("road_type", trip_request.road_type)
            
            # Calculate emission for this city
            city_base_emission = EmissionCalculator.calculate_base_emission(
                trip_request.vehicle_type,
                trip_request.fuel_type,
                city_data["segment_distance_km"]
            )
            
            city_emission = EmissionCalculator.apply_modifiers(
                city_base_emission,
                city_terrain,
                city_road_type,
                trip_request.load_weight,
                city_data["segment_distance_km"]
            )
            
            heatmap_data.append({
                "city": city_data["name"],
                "latitude": city_data["latitude"],
                "longitude": city_data["longitude"],
                "emission_kg": city_emission.wtw_kg,
                "distance_km": city_data["segment_distance_km"],
                "terrain": city_terrain.value,
                "road_type": city_road_type.value,
                "emission_intensity": city_emission.wtw_kg / city_data["segment_distance_km"] if city_data["segment_distance_km"] > 0 else 0
            })
        
        return {
            "heatmap_data": heatmap_data,
            "total_cities": len(heatmap_data),
            "route_coordinates": route_data["coordinates"]
        }
        
    except Exception as e:
        logger.error(f"Error generating heatmap data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    route_service = RouteService()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")