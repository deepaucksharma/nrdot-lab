"""
GraphQL client for New Relic Data Base (NRDB) API.

This module handles interaction with New Relic's GraphQL API with proper pagination support.
"""

import os
import time
import json
from typing import Dict, Any, Optional, List, Union, Iterator, Callable, TypeVar
import requests
from urllib.parse import urljoin

T = TypeVar('T')

class NRDBClient:
    """Client for interacting with the New Relic GraphQL API with pagination support."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        region: str = "US",
        timeout: float = 30.0,
        max_retries: int = 3,
        cache_ttl: float = 900.0,  # 15 minutes cache
    ) -> None:
        """
        Initialize the NRDB client.
        
        Args:
            api_key: New Relic API key (defaults to environment variable)
            region: Region ("US" or "EU", default: "US")
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            cache_ttl: Cache TTL in seconds
        """
        self.api_key = api_key or os.environ.get("NEW_RELIC_API_KEY")
        if not self.api_key:
            self.api_key = os.environ.get("NEW_RELIC_LICENSE_KEY")
            
        if not self.api_key:
            raise ValueError(
                "API key not provided. Set NEW_RELIC_API_KEY environment variable."
            )
            
        self.region = region.upper()
        if self.region not in ("US", "EU"):
            raise ValueError(f"Invalid region: {region}. Must be 'US' or 'EU'.")
            
        self.base_url = f"https://api.{'eu.' if self.region == 'EU' else ''}newrelic.com/graphql"
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
        }
    
    def _get_from_cache(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """Get response from cache if available and not expired."""
        cache_entry = self.cache.get(query_hash)
        if not cache_entry:
            return None
            
        if time.time() - cache_entry["timestamp"] > self.cache_ttl:
            # Cache expired
            del self.cache[query_hash]
            return None
            
        return cache_entry["data"]
    
    def _store_in_cache(self, query_hash: str, data: Dict[str, Any]) -> None:
        """Store response in cache."""
        self.cache[query_hash] = {
            "timestamp": time.time(),
            "data": data,
        }
    
    def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the New Relic API.
        
        Args:
            query: GraphQL query string
            variables: Variables for the query
            use_cache: Whether to use cached results if available
            
        Returns:
            Query response
        """
        payload = {
            "query": query,
            "variables": variables or {},
        }
        
        # Use query and variables as cache key
        query_hash = json.dumps(payload, sort_keys=True)
        
        # Check cache if enabled
        if use_cache:
            cached_result = self._get_from_cache(query_hash)
            if cached_result:
                return cached_result
        
        # Make the request with retries
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                response = requests.post(
                    self.base_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout,
                )
                
                if response.status_code == 429:
                    # Rate limited, wait and retry
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    time.sleep(retry_after)
                    retries += 1
                    continue
                    
                response.raise_for_status()
                result = response.json()
                
                if "errors" in result:
                    error_msg = "; ".join(err.get("message", "Unknown error") for err in result["errors"])
                    raise ValueError(f"GraphQL query error: {error_msg}")
                    
                # Store in cache if successful
                if use_cache:
                    self._store_in_cache(query_hash, result)
                    
                return result
                
            except requests.RequestException as e:
                last_error = e
                retries += 1
                if retries <= self.max_retries:
                    # Exponential backoff
                    sleep_time = 2 ** retries
                    time.sleep(sleep_time)
        
        # If we get here, all retries failed
        raise RuntimeError(f"Failed to execute query after {self.max_retries} retries: {last_error}")
    
    def paginated_query(
        self,
        query: str,
        variables: Dict[str, Any],
        process_page: Callable[[Dict[str, Any]], T],
        max_pages: int = 50,
        use_cache: bool = True,
    ) -> List[T]:
        """
        Execute a paginated GraphQL query against the New Relic API.
        
        Args:
            query: GraphQL query string with cursor parameter
            variables: Variables for the query
            process_page: Function to process each page of results
            max_pages: Maximum number of pages to fetch
            use_cache: Whether to use cached results if available
            
        Returns:
            Combined results from all pages
        """
        results: List[T] = []
        page_count = 0
        next_cursor = None
        
        while page_count < max_pages:
            # Update cursor for pagination
            if next_cursor:
                variables["cursor"] = next_cursor
            
            # Execute query for this page
            response = self.execute_query(query, variables, use_cache=use_cache)
            
            # Process results
            page_result = process_page(response)
            if isinstance(page_result, list):
                results.extend(page_result)
            else:
                results.append(page_result)
            
            # Check for next cursor
            try:
                next_cursor = response.get("data", {}).get("actor", {}).get("nrql", {}).get("pageInfo", {}).get("nextCursor")
            except (KeyError, AttributeError):
                next_cursor = None
            
            # Break if no more pages
            if not next_cursor:
                break
                
            page_count += 1
        
        return results
    
    def get_histogram_paginated(
        self,
        window: str = "6h",
        entity_name_filter: Optional[str] = None,
        limit: int = 500,
        max_pages: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get histogram of bytecountestimate faceted by processId with pagination.
        
        Args:
            window: Time window (e.g., "6h", "1d")
            entity_name_filter: Optional filter for entityName
            limit: Maximum number of results per page
            max_pages: Maximum number of pages to fetch
            
        Returns:
            Combined histogram data from all pages
        """
        # Build WHERE clause
        where_clause = ""
        if entity_name_filter:
            where_clause = f"WHERE entityName NOT LIKE '{entity_name_filter}'"
        
        # Build GraphQL query
        query = """
        query ProcessHistogram($nrql: String!, $cursor: String) {
          actor {
            nrql(query: $nrql, cursor: $cursor) {
              results
              metadata {
                facets
              }
              suggestedFacets {
                name
              }
              totalResult
              currentResults
              nrql
              pageInfo {
                nextCursor
                limitedResultSet
              }
            }
          }
        }
        """
        
        variables = {
            "nrql": f"""FROM ProcessSample 
                      {where_clause}
                      SELECT histogram(bytecountestimate(),20,10) AS bytes,
                             uniqueCount(processId) AS pids
                      SINCE {window} AGO
                      LIMIT {limit}""",
            "cursor": None,
        }
        
        def extract_results(response: Dict[str, Any]) -> List[Dict[str, Any]]:
            try:
                return response.get("data", {}).get("actor", {}).get("nrql", {}).get("results", [])
            except (KeyError, AttributeError):
                return []
        
        return self.paginated_query(
            query=query,
            variables=variables,
            process_page=extract_results,
            max_pages=max_pages
        )
    
    def get_histogram(
        self,
        window: str = "6h",
        entity_name_filter: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        """
        Get histogram of bytecountestimate faceted by processId (single page).
        
        Args:
            window: Time window (e.g., "6h", "1d")
            entity_name_filter: Optional filter for entityName
            cursor: Pagination cursor
            limit: Maximum number of results
            
        Returns:
            Histogram data
        """
        # Build WHERE clause
        where_clause = ""
        if entity_name_filter:
            where_clause = f"WHERE entityName NOT LIKE '{entity_name_filter}'"
        
        # Build GraphQL query
        query = """
        query ProcessHistogram($nrql: String!, $cursor: String) {
          actor {
            nrql(query: $nrql, cursor: $cursor) {
              results
              metadata {
                facets
              }
              suggestedFacets {
                name
              }
              totalResult
              currentResults
              nrql
              pageInfo {
                nextCursor
                limitedResultSet
              }
            }
          }
        }
        """
        
        variables = {
            "nrql": f"""FROM ProcessSample 
                      {where_clause}
                      SELECT histogram(bytecountestimate(),20,10) AS bytes,
                             uniqueCount(processId) AS pids
                      SINCE {window} AGO
                      LIMIT {limit}""",
            "cursor": cursor,
        }
        
        return self.execute_query(query, variables)
    
    def get_process_list_paginated(
        self,
        window: str = "6h",
        entity_filter: Optional[str] = None,
        limit: int = 1000,
        max_pages: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get complete list of processes with pagination support.
        
        Args:
            window: Time window (e.g., "6h", "1d")
            entity_filter: Optional filter for entityName/entityGuid
            limit: Maximum results per page
            max_pages: Maximum number of pages to fetch
            
        Returns:
            Combined process data from all pages
        """
        # Build WHERE clause
        where_clause = ""
        if entity_filter:
            where_clause = f"WHERE {entity_filter}"
        
        # Build GraphQL query
        query = """
        query ProcessList($nrql: String!, $cursor: String) {
          actor {
            nrql(query: $nrql, cursor: $cursor) {
              results
              nrql
              pageInfo {
                nextCursor
                limitedResultSet
              }
            }
          }
        }
        """
        
        variables = {
            "nrql": f"""FROM ProcessSample 
                      {where_clause}
                      SELECT processId, processDisplayName, commandLine,
                             bytecountestimate, cpuPercent, 
                             entityName, entityGuid
                      SINCE {window} AGO
                      LIMIT {limit}""",
            "cursor": None,
        }
        
        def extract_results(response: Dict[str, Any]) -> List[Dict[str, Any]]:
            try:
                return response.get("data", {}).get("actor", {}).get("nrql", {}).get("results", [])
            except (KeyError, AttributeError):
                return []
        
        return self.paginated_query(
            query=query,
            variables=variables,
            process_page=extract_results,
            max_pages=max_pages
        )
    
    def get_tier1_visibility(
        self,
        process_names: List[str],
        window: str = "15m",
    ) -> Dict[str, Any]:
        """
        Check visibility of Tier-1 processes.
        
        Args:
            process_names: List of process display names
            window: Time window (e.g., "15m", "1h")
            
        Returns:
            Visibility data
        """
        # Format process names for NRQL
        process_list = ",".join(f"'{name}'" for name in process_names)
        
        query = """
        query Tier1Visibility($nrql: String!) {
          actor {
            nrql(query: $nrql) {
              results
              totalResult
            }
          }
        }
        """
        
        variables = {
            "nrql": f"""FROM ProcessSample
                      SELECT uniqueCount(entityName)
                      WHERE processDisplayName IN ({process_list})
                      FACET processDisplayName
                      SINCE {window} AGO""",
        }
        
        return self.execute_query(query, variables)
    
    def get_tier1_processes(self, window: str = "1d") -> List[Dict[str, Any]]:
        """
        Get list of processes ranked by prevalence across fleet.
        
        Args:
            window: Time window (e.g., "1d", "7d")
            
        Returns:
            List of processes with prevalence data
        """
        query = """
        query Tier1Processes($nrql: String!) {
          actor {
            nrql(query: $nrql) {
              results
              totalResult
            }
          }
        }
        """
        
        variables = {
            "nrql": f"""FROM ProcessSample
                      SELECT uniqueCount(entityName) as hostCount
                      FACET processDisplayName
                      SINCE {window} AGO
                      LIMIT 1000""",
        }
        
        response = self.execute_query(query, variables)
        try:
            return response.get("data", {}).get("actor", {}).get("nrql", {}).get("results", [])
        except (KeyError, AttributeError):
            return []
