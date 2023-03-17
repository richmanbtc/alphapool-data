import os
from functools import partial
import threading
import joblib
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas_gbq
from .logger import create_logger


def fetch(fetcher):
    data_id = fetcher.data_id
    log_level = os.getenv('ALPHAPOOL_LOG_LEVEL')
    keys = fetcher.keys
    logger = create_logger(log_level, f'{data_id}-{keys}')
    try:
        do_fetch(fetcher, logger)
    except Exception as e:
        logger.error(e, exc_info=True)


def do_fetch(fetcher, logger):
    project_id = os.getenv('GC_PROJECT_ID')
    dataset_name = os.getenv('ALPHAPOOL_DATASET')

    data_id = fetcher.data_id
    table_id = f'{dataset_name}.{data_id}'
    keys = fetcher.keys
    logger.info(f'start table_id:{table_id} keys:{keys}')

    replace_mode = getattr(fetcher, 'replace_mode', False)

    client = bigquery.Client(project=project_id)

    while True:
        last_timestamp = None
        if table_exists(client, table_id):
            query = f'SELECT MAX(timestamp) as last_timestamp FROM `{table_id}`'
            if len(keys) > 0:
                cond = []
                for key_col in keys:
                    cond.append(f"`{key_col}`='{keys[key_col]}'")
                cond = ' AND '.join(cond)
                query += f' WHERE {cond}'
            query_job = client.query(query)
            for row in query_job:
                if row['last_timestamp'] is not None:
                    last_timestamp = row['last_timestamp']
        logger.info(f'last_timestamp:{last_timestamp}')

        df = fetcher.fetch(last_timestamp=last_timestamp)

        if df.shape[0] == 0:
            logger.info('empty df')
            break

        cols = list(df.columns)
        for key_col in keys:
            df[key_col] = keys[key_col]
            cols = [key_col] + cols
        df = df[cols]
        df = df.reset_index()
        logger.info(f'df.columns {df.columns}')

        if not table_exists(client, table_id):
            create_table(
                table_id=table_id,
                keys=list(keys.keys()),
                dtypes=df.dtypes,
                client=client,
                logger=logger,
            )

        pandas_gbq.to_gbq(df, table_id, project_id=project_id,
                          if_exists='replace' if replace_mode else 'append')
        logger.info(f'upload {df.shape}')

    logger.info('finished')


def table_exists(client=None, table_id=None):
    try:
        client.get_table(table_id)
        return True
    except NotFound:
        return False


def create_table(client=None, keys=None, dtypes=None, logger=None, table_id=None):
    bq_schema = []
    for col in dtypes.index:
        dtype = dtypes[col]
        if dtype == 'object':
            type = 'STRING'
        elif dtype == 'float64':
            type = 'FLOAT64'
        elif dtype == 'int64':
            type = 'INT64'
        else:
            raise Exception(f'unknown dtype {dtype}')
        bq_schema.append(bigquery.SchemaField(
            col, type, mode="REQUIRED"
        ))
    table = bigquery.Table(table_id, schema=bq_schema)
    table.range_partitioning = bigquery.RangePartitioning(
        field="timestamp",
        range_=bigquery.PartitionRange(
            start=0,
            end=1 << 32,
            interval=28 * 24 * 60 * 60,
        ),
    )
    table.clustering_fields = keys + ["timestamp"]
    table = client.create_table(table)
    logger.info(f'table created bq_schema:{bq_schema}')
    return table


fetcher_path = os.getenv('ALPHAPOOL_FETCHER_PATH')
fetchers = joblib.load(fetcher_path)

threads = []
for fetcher in fetchers:
    thread = threading.Thread(target=partial(fetch, fetcher))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()
