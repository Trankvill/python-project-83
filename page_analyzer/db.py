import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


def connect_to_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def get_queries_for_urls():
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('SELECT urls.id, urls.name,'
                'MAX(url_checks.created_at), '
                'MAX(url_checks.status_code) '
                'FROM urls '
                'LEFT JOIN url_checks '
                'ON urls.id = url_checks.url_id '
                'GROUP BY urls.id '
                'ORDER BY urls.id ASC')
    site = cur.fetchall()
    conn.commit()
    cur.close()
    return site
