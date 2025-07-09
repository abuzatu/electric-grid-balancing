"""Python module for utils related to ibis."""

# python modules
import ibis
import ibis.expr.types as ir
from typing import Any, List
import pandas as pd
import ibis.expr.datatypes as dt


def drop_table_from_database(
    backend_connection: ibis.backends.BaseBackend,
    table_name: str,
) -> None:
    """Drop table from the database."""
    try:
        # Drop the table
        backend_connection.drop_table(
            table_name, force=True
        )  # force=True is like IF EXISTS
        print(f"Table {table_name} deleted successfully")

        # Verify tables after deletion
        tables = backend_connection.list_tables()
        print("Remaining tables in the database:", tables)

    except Exception as e:
        print(f"Error deleting table: {e}")


def pandas_to_ibis_schema(df):
    """Convert pandas dtypes to ibis dtypes."""
    # type_mapping = {
    #     'object': dt.string,
    #     'float64': dt.float64,
    #     'int64': dt.int64,
    #     'datetime64[ns]': dt.timestamp,
    #     'bool': dt.boolean
    # }
    type_mapping = {
        "object": dt.string(nullable=True),  # Allow NULL for strings
        "float64": dt.float64(nullable=True),
        "int64": dt.int64(nullable=True),
        "datetime64[ns]": dt.timestamp(nullable=True),
        "bool": dt.boolean(nullable=True),
    }

    schema = {}
    for column, dtype in df.dtypes.items():
        if dtype.name == "object":
            schema[column] = dt.string
        elif dtype.name == "float64":
            schema[column] = dt.float64
        elif dtype.name == "int64":
            schema[column] = dt.int64
        elif dtype.name.startswith("datetime"):
            schema[column] = dt.timestamp
        else:
            schema[column] = dt.string  # fallback

    return schema


def add_or_update_a_pandas_df_to_a_table_from_database(
    backend_connection: ibis.backends.BaseBackend,
    table_name: str,
    df: pd.DataFrame,
    # ibis_schema,
    drop_table: bool,
) -> None:
    """Do add_or_update_a_pandas_df_to_a_table_from_database.

    But there is an option also to drop the entire table if you want to update
    a small table.
    """
    # Create or append to table
    if backend_connection is None:
        print(f"backend_connection={backend_connection} is empty")
    # print(
    #     f"in add_or_update_a_pandas_df_to_a_table_from_database backend_connection={backend_connection}"
    # )
    # print(df.head())
    # print(df.shape)
    # print(f"table_name={table_name}")
    # print(f"type(backend_connection)={backend_connection}")
    try:
        if table_name in backend_connection.list_tables() and drop_table:
            print(f"Dropping existing table {table_name} before creating new one")
            backend_connection.drop_table(table_name, force=True)
    except Exception as e:
        print(f"Error: {e}")
    try:
        if table_name in backend_connection.list_tables():
            # print(f"DDDD - Appending df to existing table {table_name}.")
            backend_connection.insert(
                table_name,
                df,
            )
            # table = backend_connection.table(table_name)
            # table.insert(df)
            # Convert DataFrame to records for insert
            # records = df.to_dict(orient='records')

            # # Insert data using insert_data
            # backend_connection.insert(
            #     table_name,
            #     records,
            #     overwrite=False,
            # )
        else:
            # print(f"EEEE - Creating new table {table_name} from ibis schema.")
            # ibis_schema = pandas_to_ibis_schema(df)
            # backend_connection.create_table(
            #     table_name,
            #     schema=ibis_schema,
            # )
            # print(f"EEEE - Inserting in new table {table_name} from a df of len {len(df)}.")
            # backend_connection.insert(
            #     table_name,
            #     df,
            # )
            # # alternatively way to insert
            # table = backend_connection.table(table_name)
            # table.insert(df)
            # print(f"Updated weather readings for {df['city'].iloc[0]}")
            # old
            backend_connection.create_table(
                table_name,
                df,
            )

        # Verify the data
        table = backend_connection.table(table_name)
        # print("\nFirst few rows:")
        # print(table.execute().head())

    except Exception as e:
        print(f"Error: {e}")


def remove_duplicates_in_table(
    table: ibis.Table, distinct_columns: List[str]
) -> ibis.Table:
    """Remove duplicates based on a list of colums, can be pk, or [date, query, page]."""
    other_columns = [col for col in table.columns if col not in distinct_columns]
    return table.group_by(distinct_columns).aggregate(
        **{col: table[col].max() for col in other_columns}
    )


def safe_backup_and_remove_duplicates_in_database(
    backend_connection: ibis.backends.BaseBackend,
    table_name: str,
    backup_table_name: str,
    distinct_columns: List[str],
) -> None:
    """Safely backup the original table and remove duplicates.

    Create a backup for the old table. And create the new table.
    """
    # Step 1: Read the table
    table = backend_connection.table(table_name)

    # Step 2: Check if the backup table already exists and drop it if necessary
    if backup_table_name in backend_connection.list_tables():
        print(f"Backup table {backup_table_name} already exists. Dropping it.")
        backend_connection.drop_table(backup_table_name, force=True)

    # Step 3: Create a backup table manually
    print(f"Creating backup table {backup_table_name}.")
    backend_connection.create_table(backup_table_name, table)

    # Step 4: Remove duplicates
    deduplicated_table = remove_duplicates_in_table(table, distinct_columns)

    # Step 5: Execute the deduplicated table to a Pandas DataFrame
    deduplicated_df = deduplicated_table.execute()
    # print(deduplicated_df.head())

    # Step 6: Drop the original table
    backend_connection.drop_table(table_name, force=True)
    # Step 7: Create a new table with the deduplicated data
    backend_connection.create_table(table_name, deduplicated_df)

    print(
        f"Table {table_name} has been backed up as {backup_table_name} and updated to remove duplicates."
    )

    # just for safety, as it is a big dataframe
    del deduplicated_df


def remove_rows_in_a_table_based_on_an_ibis_expression(
    backend_connection: ibis.backends.BaseBackend,
    table: ibis.Table,
    condition: ir.relations.Table,
) -> None:
    """Remove rows in a table in our database in the connection based on an ibis expression.

    e.g. in Snowflake, if there is a problematic date, like duplicates, or a crash,
    remove rows for one brand/one country for that date, so we can run again.
    """
    # Step 1: Convert condition to SQL query
    # Convert the Ibis expression to a SQL string
    condition_sql = condition.compile()
    # Extract the WHERE clause: but then we need to take only the part after WHERE
    condition_sql = condition_sql.split("WHERE ")[1]
    # remove the t0
    condition_sql = condition_sql.replace('"t0".', "")
    # Step 2: Construct the DELETE query
    delete_query = f'DELETE FROM "{table.get_name().lower()}" WHERE {condition_sql}'
    # Step 3: Execute the DELETE query
    backend_connection.raw_sql(delete_query)
    # done
    print(f"We have executed DELETE query:\n{delete_query}")


def keep_limited_entries_per_day(
    table: ibis.Table, date_column: str, limit_entries_per_day: int
) -> ibis.Table:
    """Limit the number of entries per day to a small number chosen randomly, to allow for fast testing."""
    if (limit_entries_per_day is None) or (limit_entries_per_day == -1):
        return table

    assert limit_entries_per_day > 0

    # Add a row number partitioned by date and ordered randomly
    table_with_row_num = table.mutate(
        row_num=ibis.row_number().over(
            ibis.window(group_by=date_column, order_by=ibis.random())
        )
    )

    # Filter to keep only the specified number of rows per day
    table_result = table_with_row_num.filter(
        table_with_row_num.row_num <= limit_entries_per_day
    )

    # Remove the row_num column
    table_result = table_result.drop("row_num")

    # return
    return table_result


# Find out the unique brand
def get_first_unique_value_of_column(table: ir.Table, column_name: str) -> str:
    """Get the first unique string from a given column, in ordr of counts."""
    unique_values = (
        table[column_name]
        .value_counts()
        .filter(lambda x: x[column_name] != "None")
        .order_by(ibis.desc(column_name))
        .limit(1)[column_name]
    )
    # Execute the query to get the result
    result = unique_values.execute()
    # Return the first (and only) value if it exists, otherwise return None
    return result[0] if len(result) > 0 else None


# the ibis equivalent of value_counts() from pandas
# get value counts including null values
def get_value_counts_one_column(table: ir.Table, column_name: str):
    """Get value counts."""
    value_counts = (
        table.group_by(column_name)
        .aggregate(count=lambda t: t.count())
        .order_by(ibis.desc("count"))
    )
    # Execute the query to get the result
    result = value_counts.execute()
    return result


# the ibis equivalent of value_counts() from pandas
# get value counts including null values for a list of columns
def get_value_counts(table: ir.Table, column_names: List[str]):
    """Get value counts for a list of columns."""
    value_counts = (
        table.group_by(column_names)
        .aggregate(count=lambda t: t.count())
        .order_by(ibis.desc("count"))
    )
    # Execute the query to get the result
    result = value_counts.execute()
    return result


def check_if_a_value_is_present_in_a_column_in_the_table(
    table: ir.Table,
    column_name: str,
    value: Any,
) -> bool:
    """Check if a value is present in a column."""
    return bool(table[column_name].isin([value]).any().execute())


def delete_rows_in_a_table_based_on_sql_condition(
    backend_connection: ibis.backends.BaseBackend,
    table_name: str,
    sql_condition: str,
) -> None:
    """Delete rows in a table based on a sql condition.

    The most standard being when a column has a value.
    E.g. to delete all rows with "norgate" column of value "OJ"
    condition_sql = 'norgate = "OJ"'
    """
    if table_name not in backend_connection.list_tables():
        print(f"Table {table_name} does not exist in the database.")
        return
    # Write the DELETE SQL query
    delete_query = f'DELETE FROM "{table_name}" WHERE {sql_condition};'
    # Get the raw SQLite3 connection
    raw_connection = backend_connection.con
    # Execute the DELETE query
    with raw_connection:
        raw_connection.execute(delete_query)


def remove_specific_date_from_cot_tables(
    ibis_conn: ibis.backends.BaseBackend,
    date_to_remove: str,
    dry_run: bool,
) -> None:
    """Remove specific date from cot tables.

    This is useful when we have a date that is problematic, like a duplicate,
    or a crash, and we want to remove it.

    E.g. to remove the date "2025-04-22" from all cot tables, you can use:
    remove_specific_date_from_cot_tables(ibis_conn, date_to_remove="2025-04-22", dry_run=False)
    """
    all_tables = ibis_conn.list_tables()
    cot_index_tables = [table for table in all_tables if table.startswith("cot_index_")]

    # Convert string to datetime
    target_date = pd.Timestamp(date_to_remove)

    for table_name in cot_index_tables:
        print(f"Processing table: {table_name}")
        table = ibis_conn.table(table_name)

        # Count rows to be deleted using date extraction from timestamp
        rows_to_delete = (
            table.filter(table.datetime.cast("date") == target_date.date())
            .count()
            .execute()
        )

        print(f"Found {rows_to_delete} rows to delete in {table_name}")

        if not dry_run and rows_to_delete > 0:
            try:
                # Using raw SQL with proper timestamp comparison
                delete_sql = f"""
                DELETE FROM {table_name}
                WHERE DATE(datetime) = DATE('{target_date}')
                """
                ibis_conn.raw_sql(delete_sql)
                print(
                    f"Successfully removed {rows_to_delete} entries for {date_to_remove} from {table_name}"
                )
            except Exception as e:
                print(f"Error processing {table_name}: {str(e)}")
        else:
            print("Dry run - no changes made" if dry_run else "No rows to delete")
