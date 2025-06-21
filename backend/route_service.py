import logging
import httpx
from fastapi import HTTPException
from typing import List, Dict, Any
import math

from models import TerrainType, RoadType


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RouteService:
    """Service for route calculation and optimization"""
    def __init__(self):
        self.route = {}
    
    async def geocode_address(self, address: str) -> tuple:
        """Convert address to coordinates using Nominatim"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 1
                    },
                    timeout=5.0
                )
                data = response.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
                else:
                    raise ValueError(f"Address not found: {address}")
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            raise HTTPException(status_code=400, detail=f"Could not geocode address: {address}")


    async def get_route_with_cities(self, start_coords: tuple, end_coords: tuple) -> Dict[str, Any]:
        """Get route with detailed city information"""
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        
        try:
            # Using OSRM (free routing service)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}",
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "steps": "true",
                        "annotations": "true"
                    },
                    timeout=10.0
                )
                data = response.json()
                
                if data["code"] == "Ok":
                    route = data["routes"][0]
                    
                    # Get cities along the route
                    cities_data = await self.get_cities_along_route(
                        route["geometry"]["coordinates"]
                    )
                    
                    return {
                        "distance_km": route["distance"] / 1000,
                        "duration_seconds": route["duration"],
                        "coordinates": route["geometry"]["coordinates"],
                        "steps": route["legs"][0]["steps"],
                        "cities": cities_data
                    }
                else:
                    raise ValueError("Route not found")
                    
        except Exception as e:
            logger.error(f"Routing error: {e}")
            # Fallback to simple distance calculation
            distance_km = RouteService.haversine_distance(start_coords, end_coords)
            cities_data = await RouteService.get_cities_along_simple_route(start_coords, end_coords)
            return {
                "distance_km": distance_km,
                "duration_seconds": distance_km * 60,  # Rough estimate
                "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
                "steps": [],
                "cities": cities_data
            }


    async def get_cities_along_route(self, coordinates: List[List[float]]) -> List[Dict[str, Any]]:
        """Get cities along the route with their segments"""
        cities = []
        
        # Sample points along the route to find cities
        sample_points = self.sample_route_points(coordinates, max_points=10)
        
        async with httpx.AsyncClient() as client:
            for i, (lon, lat) in enumerate(sample_points):
                try:
                    # Reverse geocode to get city information
                    response = await client.get(
                        "https://nominatim.openstreetmap.org/reverse",
                        params={
                            "lat": lat,
                            "lon": lon,
                            "format": "json",
                            "zoom": 10
                        },
                        timeout=3.0
                    )
                    
                    data = response.json()
                    if data and "address" in data:
                        city_name = (data["address"].get("city") or 
                                   data["address"].get("town") or 
                                   data["address"].get("village") or 
                                   data["address"].get("county") or
                                   f"Location {i+1}")
                        
                        # Calculate segment distance
                        if i == 0:
                            segment_distance = RouteService.calculate_segment_distance(
                                coordinates, 0, len(coordinates) // len(sample_points)
                            )
                        else:
                            start_idx = (i * len(coordinates)) // len(sample_points)
                            end_idx = ((i + 1) * len(coordinates)) // len(sample_points)
                            segment_distance = RouteService.calculate_segment_distance(
                                coordinates, start_idx, end_idx
                            )
                        
                        # Determine terrain and road type based on location
                        terrain, road_type = RouteService.determine_terrain_and_road(data["address"])
                        
                        cities.append({
                            "name": city_name,
                            "latitude": lat,
                            "longitude": lon,
                            "segment_distance_km": segment_distance,
                            "terrain": terrain,
                            "road_type": road_type,
                            "address_data": data["address"]
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to geocode point {lat}, {lon}: {e}")
                    # Add fallback city data
                    cities.append({
                        "name": f"Route Segment {i+1}",
                        "latitude": lat,
                        "longitude": lon,
                        "segment_distance_km": RouteService.calculate_total_distance(coordinates) / len(sample_points),
                        "terrain": TerrainType.FLAT,
                        "road_type": RoadType.HIGHWAY,
                        "address_data": {}
                    })
        
        # If no cities found, create at least one segment
        if not cities:
            total_distance = RouteService.calculate_total_distance(coordinates)
            mid_point = coordinates[len(coordinates) // 2]
            cities.append({
                "name": "Route",
                "latitude": mid_point[1],
                "longitude": mid_point[0],
                "segment_distance_km": total_distance,
                "terrain": TerrainType.FLAT,
                "road_type": RoadType.HIGHWAY,
                "address_data": {}
            })
        
        return cities

    @staticmethod
    async def get_cities_along_simple_route(start_coords: tuple, end_coords: tuple) -> List[Dict[str, Any]]:
        """Get cities for simple fallback route"""
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        distance = RouteService.haversine_distance(start_coords, end_coords)
        
        # Create midpoint
        mid_lat = (start_lat + end_lat) / 2
        mid_lon = (start_lon + end_lon) / 2
        
        cities = []
        async with httpx.AsyncClient() as client:
            try:
                # Get city for midpoint
                response = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={
                        "lat": mid_lat,
                        "lon": mid_lon,
                        "format": "json",
                        "zoom": 10
                    },
                    timeout=3.0
                )
                
                data = response.json()
                city_name = "Route"
                if data and "address" in data:
                    city_name = (data["address"].get("city") or 
                               data["address"].get("town") or 
                               data["address"].get("village") or
                               "Route")
                
                cities.append({
                    "name": city_name,
                    "latitude": mid_lat,
                    "longitude": mid_lon,
                    "segment_distance_km": distance,
                    "terrain": TerrainType.FLAT,
                    "road_type": RoadType.HIGHWAY,
                    "address_data": data.get("address", {}) if data else {}
                })
                
            except Exception as e:
                logger.warning(f"Failed to get city data for midpoint: {e}")
                cities.append({
                    "name": "Route",
                    "latitude": mid_lat,
                    "longitude": mid_lon,
                    "segment_distance_km": distance,
                    "terrain": TerrainType.FLAT,
                    "road_type": RoadType.HIGHWAY,
                    "address_data": {}
                })
        
        return cities

    def sample_route_points(self, coordinates: List[List[float]], max_points: int = 10) -> List[List[float]]:
        """Sample points along the route for city detection"""
        if len(coordinates) <= max_points:
            return coordinates
        
        step = len(coordinates) // max_points
        return [coordinates[i] for i in range(0, len(coordinates), step)]

    @staticmethod
    def calculate_segment_distance(coordinates: List[List[float]], start_idx: int, end_idx: int) -> float:
        """Calculate distance for a segment of the route"""
        if start_idx >= len(coordinates) or end_idx >= len(coordinates):
            return 0.0
        
        total_distance = 0.0
        for i in range(start_idx, min(end_idx, len(coordinates) - 1)):
            coord1 = (coordinates[i][1], coordinates[i][0])  # lat, lon
            coord2 = (coordinates[i + 1][1], coordinates[i + 1][0])  # lat, lon
            total_distance += RouteService.haversine_distance(coord1, coord2)
        
        return total_distance

    @staticmethod
    def calculate_total_distance(coordinates: List[List[float]]) -> float:
        """Calculate total distance of the route"""
        return RouteService.calculate_segment_distance(coordinates, 0, len(coordinates) - 1)

    @staticmethod
    def determine_terrain_and_road(address_data: Dict[str, Any]) -> tuple:
        """Determine terrain and road type based on address data"""
        # Simple heuristics based on address components
        terrain = TerrainType.FLAT
        road_type = RoadType.HIGHWAY
        
        # Check for mountainous areas
        if any(keyword in str(address_data).lower() for keyword in 
               ['mountain', 'hill', 'peak', 'ridge', 'alpine']):
            terrain = TerrainType.MOUNTAINOUS
        elif any(keyword in str(address_data).lower() for keyword in 
                ['hill', 'elevated', 'plateau']):
            terrain = TerrainType.HILLY
        
        # Check for urban areas
        if address_data.get('city') or address_data.get('town'):
            road_type = RoadType.URBAN
        elif any(keyword in str(address_data).lower() for keyword in 
                ['village', 'rural', 'county', 'countryside']):
            road_type = RoadType.RURAL
        
        return terrain, road_type

    @staticmethod
    async def get_route(start_coords: tuple, end_coords: tuple) -> Dict[str, Any]:
        """Wrapper for backward compatibility"""
        return await RouteService.get_route_with_cities(start_coords, end_coords)
    
    @staticmethod
    def haversine_distance(coord1: tuple, coord2: tuple) -> float:
        """Calculate distance between two coordinates"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        
        c = 2 * math.asin(math.sqrt(a))
        return R * c
