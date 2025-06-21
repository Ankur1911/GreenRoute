import os
import json
from typing import Dict, Any
import google.generativeai as genai

from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY environment variable not set.")
else:
    try:
        genai.configure(api_key=api_key)
        print("Google Generative AI configured successfully.")
    except Exception as e:
        print(f"Failed to configure Google Generative AI: {e}")


class ReasoningService:
    """Service for generating explanations using AI reasoning"""
    
    @staticmethod
    async def generate_reasoning(trip_data: Dict[str, Any]) -> str:
        """Generate reasoning for CO2 calculations and fuel comparisons"""
        vehicle_type = trip_data["vehicle_type"]
        fuel_type = trip_data["fuel_type"]
        distance = trip_data["distance_km"]
        terrain = trip_data["terrain"]
        road_type = trip_data["road_type"]
        load_weight = trip_data["load_weight"]
        cities = trip_data.get("cities", [])
        total_cities = trip_data.get("total_cities", 0)
        
        city_breakdown = ""
        if cities:
            city_breakdown = "\n\nCity-wise Breakdown:\n"
            for city in cities:
                city_breakdown += f"• {city['name']}: {city['distance']:.1f} km "
                city_breakdown += f"({city['terrain'].value} terrain, {city['road_type'].value} roads)\n"
        
        prompt= f"""Generate a detailed CO2 emission calculation reasoning based on the following data:

1. **Route Information**:
    - **Total Distance**: {distance} km
    - **Total Number of City/Region Segments**: {total_cities}
    - **Vehicle Type**: {vehicle_type} (e.g., truck, van, pickup, etc.)
    - **Fuel Type**: {fuel_type} (e.g., diesel_b7, petrol, electric, hybrid)
    - **Load Weight**: {load_weight} kg
    - **Road Type**: {road_type}
    - **Terrain**: {terrain}


2. **Methodology**:
    - Base emissions should be calculated using the ISO 14083 methodology.
    - The **Tank-to-Wheel (TTW)** emissions are for direct combustion.
    - The **Well-to-Tank (WTT)** emissions are from upstream fuel production.
    - The **Well-to-Wheel (WtW)** emissions are the sum of TTW and WTT emissions.

3. **Modifiers**:
    - Terrain modifiers: flat (0%), hilly (+15%), mountainous (+35%).
    - Road type modifiers: highway (baseline), rural (+10%), urban (+25%).
    - Load weight impact on CO2 emissions: additional CO2 per kg based on vehicle weight.

4. **Fuel Type Comparison**:
    - Compare the fuel types based on emission reductions:
      - **Electric vehicles**: achieve 70-90% reduction in direct emissions (no direct emissions from fuel consumption).
      - **Diesel B7**: baseline fuel, use it for comparison.
      - **Petrol**: typically produces 5-15% more emissions than diesel.
      - **Hybrid**: reduces emissions by 40-60% due to electric assistance.

5. **Additional Considerations**:
    - Include a breakdown by city/region, showing the emission impact per city, considering terrain and road type.
    - Provide insights into how terrain and road type affect the emissions in each city, and how the load weight impacts the total emissions across the route.

Output the reasoning in a structured, easy-to-read format with the following sections:
- **Route Analysis**
- **Base Emissions** (with TTW, WTT, and WtW)
- **Segment-Specific Calculations** (city-wise breakdown, modifiers)
- **Load Weight Impact**
- **Fuel Type Comparison**
- **City-Wise Breakdown for Sustainability Reporting**

Ensure the HTML contains the following tags for clarity:
- Use `<h2>` for section titles (e.g., "Route Analysis").
- Use `<ul>` and `<li>` for lists of items (e.g., modifiers, fuel type comparisons).
- Use `<p>` for paragraphs of text.
- Format any numbers (emissions, distances, etc.) with appropriate decimal places.
- Ensure the HTML structure is easy to parse and render in a web browser.

Please **do not** return plain text. The response should be **only in HTML format**, suitable for embedding directly into a webpage using `innerHTML`.
""" 
        
            # Using a modern, capable model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = await model.generate_content_async(prompt, generation_config=generation_config)

        print("parts::::",response.candidates[0].content.parts[0].text)

        # reasoning = json.loads(response.text)
        data = response.candidates[0].content.parts[0].text
        data = json.loads(data)
        reasoning = next(iter(data.values()))
        return reasoning