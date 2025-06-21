# 🌿 GreenRoute : CO2 Emission Tracking and Route Optimization

GreenRoute is an intelligent API service for calculating and optimizing CO2 emissions for logistics and transportation routes. It provides detailed emission breakdowns based on vehicle type, fuel, load weight, terrain, and road conditions, leveraging established standards and AI-powered reasoning to deliver actionable sustainability insights.

This project consists of a powerful **FastAPI backend** that performs all the calculations and a simple **HTML/JavaScript frontend** to interact with the API.

[![Made with FastAPI](https://img.shields.io/badge/Made%20with-FastAPI-brightgreen.svg)](https://fastapi.tiangolo.com/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)

***

## Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [How to Run](#how-to-run)
  - [Backend Server](#backend-server)
  - [Frontend Application](#frontend-application)
- [API Endpoints](#api-endpoints)
  - [Calculate Trip](#calculate-trip)
  - [Other Endpoints](#other-endpoints)
- [Project Structure](#project-structure)

***

## About The Project

In an era of increasing focus on Environmental, Social, and Governance (ESG) criteria, businesses in the logistics sector face growing pressure to monitor and reduce their carbon footprint. GreenRoute addresses this need by providing a robust tool to accurately measure CO2 emissions from freight transport.

The API adheres to international standards like **ISO 14083** and the **GLEC Framework** to calculate emissions, considering the full **Well-to-Wheel (WTW)** lifecycle, which includes both **Well-to-Tank (WTT)** and **Tank-to-Wheel (TTW)** emissions.

By integrating with routing services and using AI to generate detailed reports, GreenRoute not only calculates emissions but also helps companies understand the impact of their operational choices and identify opportunities for greater efficiency and sustainability.

***

## Key Features

-   **Dynamic CO2 Calculation**: Accurately computes CO2 emissions based on a wide range of parameters.
-   **Well-to-Wheel (WTW) Analysis**: Provides a complete emission picture, including upstream fuel production (WTT) and direct combustion (TTW).
-   **Intelligent Routing**: Uses OSRM to fetch optimized routes and breaks them down into segments for granular analysis.
-   **Factor-Based Adjustments**: Modifies emission calculations based on real-world factors like terrain (flat, hilly), road type (urban, highway), and cargo weight.
-   **Alternative Fuel Comparison**: Compares emissions for the selected fuel type against alternatives like Electric, Hybrid, and Petrol.
-   **AI-Powered Reasoning**: Leverages the Google Gemini API to generate human-readable reports explaining the emission results and providing sustainability recommendations.
-   **City-wise Emission Breakdown**: Segments the route by cities or regions to pinpoint emission hotspots.
-   **Heatmap Data Generation**: Provides data structured for frontend heatmap visualizations to show emission intensity along the route.

***

## Tech Stack

-   **Backend**: Python, FastAPI, Uvicorn
-   **Data Validation**: Pydantic
-   **AI Integration**: Google Gemini API (`google-generativeai`)
-   **HTTP Requests**: `httpx`
-   **Environment Management**: `python-dotenv`
-   **Frontend**: HTML, CSS, JavaScript (for API calls)
-   **External APIs**:
    -   OpenStreetMap (Nominatim for geocoding)
    -   Project OSRM (for route optimization)

***

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

-   Python 3.8 or higher
-   `pip` (Python package installer)
-   A Google Gemini API Key

### Installation

1.  **Clone the repository**
    ```sh
    git clone [https://github.com/Ankur1911/GreenRoute.git](https://github.com/Ankur1911/GreenRoute.git)
    cd GreenRoute
    ```

2.  **Set up the Backend**
    -   Navigate to the backend directory:
        ```sh
        cd backend
        ```
    -   Create and activate a virtual environment (recommended):
        ```sh
        # For macOS/Linux
        python3 -m venv venv
        source venv/bin/activate

        # For Windows
        python -m venv venv
        .\venv\Scripts\activate
        ```
    -   Install the required Python packages using: 
        ```sh
        pip install -r requirements.txt
        ```
    -   Create an environment file to store your API key.
        ```
        # .env file
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
        ```
      

3.  **Frontend Setup**
    -   The frontend is a simple `index.html` file with vanilla JavaScript. It requires no special installation or build steps.

***

## How to Run

### Backend Server

1.  Make sure you are in the `backend` directory with your virtual environment activated.
2.  Run the FastAPI application using Uvicorn:
    ```sh
    uvicorn main:app --reload
    ```
3.  The API server will start, typically on `http://127.0.0.1:8000`.
4.  You can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

### Frontend Application

1.  Navigate to the `frontend` directory.
2.  Open the `index.html` file directly in your web browser (e.g., Chrome, Firefox).
3.  The frontend will make requests to the backend server running at `http://127.0.0.1:8000`.

***

## API Endpoints

The following are the primary endpoints provided by the GreenRoute API.

### Calculate Trip

This is the main endpoint for calculating trip emissions.

-   **URL**: `/calculate-trip`
-   **Method**: `POST`
-   **Request Body**:
    ```json
    {
      "start_location": {
        "address": "Mumbai, India"
      },
      "end_location": {
        "address": "Delhi, India"
      },
      "vehicle_type": "truck",
      "fuel_type": "diesel_b7",
      "load_weight": 10000,
      "terrain": "flat",
      "road_type": "highway"
    }
    ```
-   **Success Response (200 OK)**:
    Returns a detailed JSON object including total distance, fuel consumption, CO2 breakdown, city-wise emissions, fuel comparisons, route coordinates, and the AI-generated reasoning.

### Other Endpoints

-   `POST /city-emissions-heatmap`: Generates data specifically for visualizing emission intensity on a map.
-   `GET /health`: A simple health check endpoint.
-   `GET /vehicle-types`: Returns a list of available vehicle types.
-   `GET /fuel-types`: Returns a list of available fuel types.
-   `GET /terrain-types`: Returns a list of available terrain types.
-   `GET /road-types`: Returns a list of available road types.

***

---
