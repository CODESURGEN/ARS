import os
import contextlib
import pymssql
from dotenv import load_dotenv


load_dotenv()

def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def create_connection():
    
    db_host = _get_env("DB_HOST")
    db_user = _get_env("DB_USER")
    db_password = _get_env("DB_PASSWORD")
    db_name = _get_env("DB_NAME")
    db_port = _get_env("DB_PORT")

    return pymssql.connect(
        server=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port,
    )


def close_connection(connection) -> None:
    if connection is None:
        return
    with contextlib.suppress(Exception):
        connection.close()


def list_tables(connection, query: str) -> tuple[list[tuple], list[str]]:
    """Run query"""
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else []
        return rows, columns


if __name__ == "__main__":
    conn = None
    try:
        conn = create_connection()
        joint_query = """
        SELECT
        c.CustOrderNumber,
        c.TaxAmount,
        c.ShippingCharge,
        c.CouponValue,
        c.Subtotal,
        c.TotalAmount,
        c.OrderedDate,
        c.OrderStatusName,
        v.VendorID,
        v.Subtotal as VenderSubtotal,
        v.ShippingCharges as Vshipping,
        v.TotalAmount as VTotal

        FROM
            CustOrderDetails AS c
        INNER JOIN
            VendorOrders AS v
        ON
            c.CustOrderNumber = v.PONumber
        WHERE
            c.OrderedDate >= '2025-08-01'
        ORDER BY
            c.OrderedDate DESC;

            """
        rows, cols = list_tables(conn, joint_query)
        print(len(rows))
    except Exception as exc:
        print("Connection failed:", exc)
    finally:
        close_connection(conn)


