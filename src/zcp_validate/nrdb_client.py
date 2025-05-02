"""
NRDB client for querying New Relic data.

Implements a client with circuit breaker pattern and error handling.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Union

import requests
from pydantic import BaseModel


class NRDBConfig(BaseModel):
    """
    NRDB client configuration.
    """
    api_key: str
    account_id: str
    region: str = "us"  # us or eu
    timeout_s: int = 30
    circuit_breaker_threshold: int = 3
    circuit_breaker_reset_s: int = 60


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent overwhelming failing services.
    """
    
    def __init__(self, threshold: int = 3, reset_seconds: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            threshold: Number of consecutive failures to open circuit
            reset_seconds: Time to wait before resetting circuit
        """
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._failures = 0
        self._open_since = 0.0
    
    @property
    def is_open(self) -> bool:
        """
        Check if circuit is open.
        
        Returns:
            True if circuit is open, False otherwise
        """
        # Check if we should try to reset
        if self._failures >= self._threshold:
            current_time = time.time()
            if current_time - self._open_since >= self._reset_seconds:
                # Reset circuit
                self._failures = 0
                return False
            return True
        return False
    
    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self._failures += 1
        if self._failures == self._threshold:
            self._open_since = time.time()
    
    def record_success(self):
        """Record a success and reset the failure count."""
        self._failures = 0


class NRDBClient:
    """
    Client for querying NRDB (New Relic Database).
    
    Implements circuit breaker pattern to prevent overwhelming the API
    during outages or excessive errors.
    """
    
    def __init__(self, config: Optional[NRDBConfig] = None):
        """
        Initialize NRDB client.
        
        Args:
            config: Client configuration
        """
        self._config = config or self._default_config()
        self._circuit_breaker = CircuitBreaker(
            threshold=self._config.circuit_breaker_threshold,
            reset_seconds=self._config.circuit_breaker_reset_s
        )
    
    @staticmethod
    def _default_config() -> NRDBConfig:
        """
        Get default configuration from environment variables.
        
        Returns:
            Default configuration
        """
        return NRDBConfig(
            api_key=os.environ.get("NEW_RELIC_API_KEY", ""),
            account_id=os.environ.get("NEW_RELIC_ACCOUNT_ID", ""),
            region=os.environ.get("NEW_RELIC_REGION", "us"),
            timeout_s=int(os.environ.get("NEW_RELIC_TIMEOUT", "30"))
        )
    
    def query(self, nrql: str) -> Dict[str, Any]:
        """
        Execute an NRQL query.
        
        Args:
            nrql: NRQL query string
            
        Returns:
            Query result
            
        Raises:
            ValueError: If API key or account ID is missing
            RuntimeError: If circuit breaker is open
            requests.exceptions.RequestException: If request fails
        """
        if not self._config.api_key:
            raise ValueError("NEW_RELIC_API_KEY environment variable or config is required")
        
        if not self._config.account_id:
            raise ValueError("NEW_RELIC_ACCOUNT_ID environment variable or config is required")
        
        # Check circuit breaker
        if self._circuit_breaker.is_open:
            raise RuntimeError("Circuit breaker is open, NRDB may be experiencing issues")
        
        # Determine API endpoint based on region
        base_url = "https://api.newrelic.com" if self._config.region == "us" else "https://api.eu.newrelic.com"
        url = f"{base_url}/graphql"
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "API-Key": self._config.api_key
        }
        
        query = """
        {
            actor {
                account(id: %s) {
                    nrql(query: "%s") {
                        results
                    }
                }
            }
        }
        """ % (self._config.account_id, nrql.replace('"', '\\"'))
        
        payload = {"query": query}
        
        try:
            start_time = time.time()
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self._config.timeout_s
            )
            response.raise_for_status()
            
            # Record success
            self._circuit_breaker.record_success()
            
            # Parse response
            data = response.json()
            
            # Check for errors in the GraphQL response
            if "errors" in data:
                error_message = "; ".join([error.get("message", "Unknown error") for error in data["errors"]])
                raise RuntimeError(f"GraphQL error: {error_message}")
            
            # Extract results
            results = data.get("data", {}).get("actor", {}).get("account", {}).get("nrql", {}).get("results", [])
            return {
                "results": results,
                "duration_ms": (time.time() - start_time) * 1000
            }
            
        except (requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
            # Record failure
            self._circuit_breaker.record_failure()
            raise
