"""
Client script for interacting with the Macro Engine API
Demonstrates how to use the API endpoints
"""

import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

class MacroEngineClient:
    """Client for Macro Engine API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def get_available_dates(self) -> dict:
        """Get available dates from Pass 4"""
        response = requests.get(f"{self.base_url}/available-dates")
        response.raise_for_status()
        return response.json()
    
    def get_available_investor_types(self) -> dict:
        """Get available investor types from Pass 5"""
        response = requests.get(f"{self.base_url}/available-investor-types")
        response.raise_for_status()
        return response.json()
    
    def get_recommendation(self, target_date: str, investor_type: str) -> dict:
        """
        Get portfolio recommendation
        
        Args:
            target_date: Date string (e.g., '2009-01-04')
            investor_type: One of Conservative, Balanced, Aggressive
        
        Returns:
            Portfolio recommendation with regime data and portfolio details
        """
        payload = {
            "target_date": target_date,
            "investor_type": investor_type
        }
        response = requests.post(
            f"{self.base_url}/recommend",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_regime_data(self, target_date: Optional[str] = None) -> dict:
        """Get regime data from Pass 4"""
        params = {}
        if target_date:
            params["target_date"] = target_date
        
        response = requests.get(f"{self.base_url}/regime-data", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_portfolio_execution(self) -> dict:
        """Get portfolio execution output from Pass 6"""
        response = requests.get(f"{self.base_url}/portfolio-execution")
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> dict:
        """Check API health status"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

def main():
    """Example usage of the API client"""
    client = MacroEngineClient()
    
    print("=" * 60)
    print("Macro Engine API Client - Example Usage")
    print("=" * 60)
    
    # Check health
    print("\n1. Health Check")
    print("-" * 60)
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    # Get available dates
    print("\n2. Available Dates (from Pass 4)")
    print("-" * 60)
    dates = client.get_available_dates()
    print(json.dumps(dates, indent=2))
    
    # Get available investor types
    print("\n3. Available Investor Types (from Pass 5)")
    print("-" * 60)
    investor_types = client.get_available_investor_types()
    print(json.dumps(investor_types, indent=2))
    
    # Get a recommendation
    if dates["count"] > 0 and investor_types["count"] > 0:
        target_date = dates["dates"][0]
        investor_type = investor_types["investor_types"][0]
        
        print(f"\n4. Portfolio Recommendation")
        print(f"   Target Date: {target_date}")
        print(f"   Investor Type: {investor_type}")
        print("-" * 60)
        
        recommendation = client.get_recommendation(target_date, investor_type)
        print(json.dumps(recommendation, indent=2))
    
    # Get regime data
    print("\n5. Regime Data (from Pass 4)")
    print("-" * 60)
    regime_data = client.get_regime_data()
    print(json.dumps(regime_data, indent=2))
    
    # Get portfolio execution
    print("\n6. Portfolio Execution (from Pass 6)")
    print("-" * 60)
    portfolio = client.get_portfolio_execution()
    print(json.dumps(portfolio, indent=2))

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API. Make sure the server is running.")
        print("Run: python -m uvicorn api_server:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")
