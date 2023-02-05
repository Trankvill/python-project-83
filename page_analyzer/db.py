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


def get_queries_for_create_url_exist(dt, form):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('SELECT id FROM urls WHERE name=(%s);',
                (form['url'],))
    id_find = cur.fetchone()
    conn.commit()
    cur.close()
    return id_find


def get_queries_for_create_url_not_exist(dt, form):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s);",
                (form['url'], dt))
    cur.execute('SELECT id FROM urls WHERE name=(%s);',
                (form['url'],))
    id_find = cur.fetchone()
    conn.commit()
    cur.close()
    return id_find


def get_queries_for_show_url(id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM urls WHERE id=(%s);',
                (id,))
    site = cur.fetchone()
    cur.execute('SELECT * FROM url_checks WHERE url_id = (%s)'
                'ORDER BY created_at DESC;',
                (id,))
    site2 = cur.fetchall()
    conn.commit()
    cur.close()
    return site, site2


def get_queries_for_site_check(id):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('SELECT name FROM urls WHERE id=(%s);',
                (id,))
    site = cur.fetchone()
    conn.commit()
    cur.close()
    return site


def get_queries_for_check(id, dt, code, tag):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO url_checks (url_id,'
                'created_at, status_code, h1, description, title) '
                'VALUES ((%s), (%s), (%s), (%s), (%s), (%s));',
                (id, dt, code, tag['h1'], tag['meta'], tag['title']))
    conn.commit()
    cur.close()
