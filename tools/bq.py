
from google.cloud import bigquery
import logging, os

logger = logging.getLogger(__name__)


def get_query_job(query: str, dry_run: bool = True) -> bigquery.QueryJob:
    client = bigquery.Client()
    job_config = bigquery.QueryJobConfig(dry_run=dry_run, use_query_cache=False)

    return client.query(query, job_config=job_config)


def get_scan_cost(size_mb: float) -> float:
    """
    Calculates the cost of scanning data in BigQuery based on the MB scanned in USD $

    Args:
        size_mb: The scan size in MB.

    Returns:
        A float indicating the amount of data the query will process in MB.
    """
    tb = size_mb / (1024 * 1024)
    raw_cost = tb * float(os.getenv("BQ_ON_DEMAND_COST_PER_TB"))

    return round(raw_cost, 2)


    
def get_dry_run_size(query: str) -> str:
    """
    Performs a dry run of a BigQuery query to estimate the number of MB processed.

    Args:
        query: The BigQuery SQL query to be tested.

    Returns:
        A float indicating the amount of data the query will process in MB.

    Raises:
        Exceptions: If the query fails to run.
    """

    query_job = get_query_job(query=query, dry_run=True)

    bytes_processed = query_job.total_bytes_processed
    megabytes = bytes_processed / (1024 * 1024)

    return megabytes



def get_query_equivalence(query1: str, query2: str) -> bool:
    """
    Tests the equivalence of two different BigQuery result sets.

    Args:
        query1: The first BigQuery SQL query to be tested
        query2: The second BigQuery SQL query to be tested

    Returns:
        Boolean indicating if the two queries return the same result set according to their farm_fingerprints.

    Raises:
        ValueErrors: According to get_farm_fingerprint
        Exceptions: If either of the queries fail to run.
    """
    ff1 = get_farm_fingerprint(query=query1)
    ff2 = get_farm_fingerprint(query=query2)

    return ff1 == ff2



def get_farm_fingerprint(query: str) -> int:
    """
    Takes a query, runs it if possible and then returns the farm fingerprint hash of the results.
    The farm fingerprint hash can be used to compare the equality of two different query results sets.

    Args:
        query: The BigQuery SQL query to be tested.

    Returns:
        Integer the farm fingerprint hash of the result set.

    Raises:
        ValueErrors: If the query exceeds the maximum scan size, or if it can't return a scalar value.
        Exceptions: If the query fails to run.
    """
    
    max_scan_size_tb = float(os.getenv("BQ_QUERY_TEST_MAX_TB_SCAN"))
    scan_size_tb = get_dry_run_size(query=query) / (1024 * 1024)
    if scan_size_tb > max_scan_size_tb:
        raise ValueError(f"Query exceeds the maximum scan size of {max_scan_size_tb} TB")

    ff_query = f"""
        WITH Q AS (
            {query}
        )
        SELECT FARM_FINGERPRINT(
            TO_JSON_STRING(ARRAY(
                SELECT AS STRUCT * FROM Q
            ))
        )
    """

    ff_query_job = get_query_job(query=ff_query, dry_run=False)
    ff_results = ff_query_job.result()

    if ff_results.total_rows == 0:
        raise ValueError("Query returned no results.")

    row = next(ff_results)

    return int(row[0])