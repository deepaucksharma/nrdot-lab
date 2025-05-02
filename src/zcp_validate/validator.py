"""
Validator implementation for checking configurations against actual data.
"""

import time
from typing import Dict, List, Optional

from zcp_core.bus import Event, publish
from zcp_core.schema import validate as validate_schema
from zcp_validate.models import HostValidationResult, ValidationJob, ValidationResult
from zcp_validate.nrdb_client import NRDBClient, NRDBConfig


class Validator:
    """
    Validates configurations against actual data from NRDB.
    """
    
    def __init__(self, nrdb_client: Optional[NRDBClient] = None):
        """
        Initialize validator.
        
        Args:
            nrdb_client: NRDB client to use (or create a new one)
        """
        self._nrdb_client = nrdb_client or NRDBClient()
    
    def validate(self, job: ValidationJob) -> ValidationResult:
        """
        Validate a job.
        
        Args:
            job: Validation job
            
        Returns:
            Validation result
        """
        start_time = time.time()
        host_results = {}
        
        # Query NRDB for actual ingest data
        try:
            # Get ingest data for all hosts in one query
            query_result = self._query_actual_ingest(
                hosts=job.hosts,
                timeframe_hours=job.timeframe_hours
            )
            
            # Process results for each host
            for host in job.hosts:
                # Get actual ingest for this host
                actual_gib_day = self._extract_host_ingest(query_result, host)
                
                # Calculate deviation
                deviation = abs(actual_gib_day - job.expected_gib_day) / job.expected_gib_day if job.expected_gib_day > 0 else 0
                within_threshold = deviation <= job.threshold
                
                # Create result
                host_results[host] = HostValidationResult(
                    hostname=host,
                    expected_gib_day=job.expected_gib_day,
                    actual_gib_day=actual_gib_day,
                    within_threshold=within_threshold,
                    deviation_percent=deviation * 100,
                    message=self._generate_message(actual_gib_day, job.expected_gib_day, deviation, within_threshold)
                )
                
        except Exception as e:
            # If NRDB query fails, create error results for all hosts
            for host in job.hosts:
                host_results[host] = HostValidationResult(
                    hostname=host,
                    expected_gib_day=job.expected_gib_day,
                    actual_gib_day=0.0,
                    within_threshold=False,
                    deviation_percent=100.0,
                    message=f"Error querying NRDB: {str(e)}"
                )
        
        # Calculate pass rate
        pass_count = sum(1 for r in host_results.values() if r.within_threshold)
        pass_rate = pass_count / len(host_results) if host_results else 0.0
        
        # Create validation result
        result = ValidationResult(
            host_results=host_results,
            query_duration_ms=(time.time() - start_time) * 1000,
            pass_rate=pass_rate
        )
        
        # Validate against schema
        try:
            validate_schema(result.dict(), "ValidationResult")
        except Exception as e:
            print(f"Warning: Schema validation failed: {e}")
        
        # Publish event
        publish(Event(
            topic="validate.result",
            payload={
                "pass": result.overall_pass,
                "actual_gib_day": sum(r.actual_gib_day for r in host_results.values()) / len(host_results) if host_results else 0.0
            }
        ))
        
        return result
    
    def _query_actual_ingest(self, hosts: List[str], timeframe_hours: int) -> Dict:
        """
        Query NRDB for actual ingest data.
        
        Args:
            hosts: List of hosts to query
            timeframe_hours: Timeframe in hours
            
        Returns:
            Query result
        """
        # Build host filter
        host_filter = " OR ".join([f"hostname = '{host}'" for host in hosts])
        
        # Build NRQL query
        nrql = f"""
        FROM NrConsumption 
        SELECT sum(bytesIngested)/1024/1024/1024 as giBIngested 
        WHERE metricName='ProcessSample' AND ({host_filter})
        FACET hostname
        SINCE {timeframe_hours} HOURS AGO
        """
        
        # Execute query
        return self._nrdb_client.query(nrql)
    
    def _extract_host_ingest(self, query_result: Dict, hostname: str) -> float:
        """
        Extract actual ingest for a host from query results.
        
        Args:
            query_result: NRDB query result
            hostname: Host to extract
            
        Returns:
            Actual ingest in GiB/day
        """
        # Extract results for this host
        results = query_result.get("results", [])
        timeframe_hours = 24  # Default timeframe
        
        for result in results:
            if result.get("hostname") == hostname:
                # Convert to GiB/day
                gib_ingested = result.get("giBIngested", 0.0)
                return (gib_ingested / timeframe_hours) * 24
        
        # Host not found in results
        return 0.0
    
    @staticmethod
    def _generate_message(actual: float, expected: float, deviation: float, within_threshold: bool) -> str:
        """
        Generate a human-readable message for the validation result.
        
        Args:
            actual: Actual ingest
            expected: Expected ingest
            deviation: Deviation ratio
            within_threshold: Whether within threshold
            
        Returns:
            Human-readable message
        """
        status = "PASS" if within_threshold else "FAIL"
        comparison = "higher" if actual > expected else "lower"
        
        return (
            f"{status}: Actual ingest is {actual:.2f} GiB/day, "
            f"which is {deviation * 100:.1f}% {comparison} than expected ({expected:.2f} GiB/day)"
        )
