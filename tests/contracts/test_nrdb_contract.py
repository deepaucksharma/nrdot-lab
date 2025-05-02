"""Contract tests for NRDB GraphQL API responses."""

import json
import os
import pytest
import jsonschema
from pathlib import Path
import vcr
from process_lab.nrdb.client import NRDBClient

# Load the GraphQL response schema
SCHEMA_PATH = Path(__file__).parent / 'schema_graphql_response.json'
SCHEMA = json.loads(SCHEMA_PATH.read_text())

# Configure VCR for recording API interactions
vcr_config = vcr.VCR(
    cassette_library_dir=Path(__file__).parent.parent / 'vcr_cassettes',
    record_mode='once',
    match_on=['uri', 'method', 'body'],
    filter_headers=['Api-Key', 'api-key'],
    filter_query_parameters=['key', 'api_key'],
)


@pytest.fixture
def mock_env():
    """Set mock environment variables for testing."""
    old_env = os.environ.copy()
    os.environ['NEW_RELIC_API_KEY'] = 'test_api_key'
    yield
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def nrdb_client(mock_env):
    """Create an NRDB client for testing."""
    return NRDBClient(api_key='test_api_key')


@vcr_config.use_cassette('histogram_response.yaml')
def test_histogram_response_schema(nrdb_client):
    """Test that histogram response matches schema."""
    # This test will use the recorded response from VCR
    response = nrdb_client.get_histogram(window='1h')
    
    # Validate response against schema
    jsonschema.validate(response, SCHEMA)
    
    # Additional contract assertions
    assert 'data' in response
    assert 'actor' in response['data']
    assert 'nrql' in response['data']['actor']
    assert 'results' in response['data']['actor']['nrql']


@vcr_config.use_cassette('tier1_visibility_response.yaml')
def test_tier1_visibility_response_schema(nrdb_client):
    """Test that tier1 visibility response matches schema."""
    # This test will use the recorded response from VCR
    process_names = ['nginx', 'java', 'mysqld']
    response = nrdb_client.get_tier1_visibility(process_names=process_names, window='15m')
    
    # Validate response against schema
    jsonschema.validate(response, SCHEMA)
    
    # Additional contract assertions
    assert 'data' in response
    assert 'actor' in response['data']
    assert 'nrql' in response['data']['actor']
    assert 'results' in response['data']['actor']['nrql']


def test_response_schema_with_error():
    """Test the error part of the schema."""
    # Sample error response
    error_response = {
        "data": None,
        "errors": [
            {
                "message": "Invalid query: syntax error",
                "path": ["actor", "nrql"],
                "extensions": {
                    "errorClass": "SYNTAX_ERROR"
                }
            }
        ]
    }
    
    # Validate against schema
    jsonschema.validate(error_response, SCHEMA)


def test_fields_present_in_histogram_schema():
    """Test that required fields for histogram are allowed by the schema."""
    # Sample expected fields in a histogram response
    expected_fields = [
        "data.actor.nrql.results[].bytes.buckets",
        "data.actor.nrql.results[].bytes.mean", 
        "data.actor.nrql.results[].pids",
        "data.actor.nrql.pageInfo.nextCursor"
    ]
    
    # Test schema with a sample response that has these fields
    sample = {
        "data": {
            "actor": {
                "nrql": {
                    "results": [{
                        "bytes": {
                            "buckets": [100, 200, 300],
                            "mean": 200.5
                        },
                        "pids": 150
                    }],
                    "pageInfo": {
                        "nextCursor": "abc123",
                        "limitedResultSet": True
                    }
                }
            }
        }
    }
    
    # This should validate without errors
    jsonschema.validate(sample, SCHEMA)
