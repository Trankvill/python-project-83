import psycopg2
import os
import validators
import datetime
import requests
from bs4 import BeautifulSoup
from flask import (
    Flask, render_template,
    request, redirect,
    flash, get_flashed_messages,
    url_for)
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


@app.route('/')
def index():
    messages = get_flashed_messages()
    return render_template(
        'home.html',
        title='Анализатор страниц',
        messages=messages
    )


@app.post('/urls/add')
def urls_add():
    dt = datetime.datetime.now()
    form = request.form.to_dict()
    valid_url = validators.url(form['url'])
    if valid_url and len(form['url']) <= 255:
        cur = conn.cursor()
        cur.execute('SELECT id FROM urls WHERE name=(%s);',
                    (form['url'],))
        id_find = cur.fetchone()
        cur.close()
        print(id_find)
        if id_find:
            flash('Такой сайт уже есть')
            return redirect(url_for('show_url', id=id_find[0]))
        cur = conn.cursor()
        cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s);",
                    (form['url'], dt))
        cur.execute('SELECT id FROM urls WHERE name=(%s);',
                    (form['url'],))
        id_find = cur.fetchone()
        cur.close()
        flash('Страница успешно добавлена')
        return redirect(url_for('show_url', id=id_find[0]))
    flash('Не верный URL')
    return redirect(url_for('index'))


@app.get('/urls/')
def get_urls():
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
    cur.close()
    return render_template('urls.html',
                           site=site
                           )


@app.get('/urls/<int:id>/')
def show_url(id):
    cur = conn.cursor()
    cur.execute('SELECT * FROM urls WHERE id=(%s);',
                (id,))
    site = cur.fetchone()
    cur.execute('SELECT * FROM url_checks WHERE url_id = (%s)'
                'ORDER BY created_at DESC;',
                (id,))
    site2 = cur.fetchall()
    cur.close()
    messages = get_flashed_messages()
    return render_template('show_url.html',
                           site=site,
                           site2=site2,
                           messages=messages
                           )


@app.post('/urls/<int:id>/checks')
def urls_id_checks_post(id):
    try:
        dt = datetime.datetime.now()
        cur = conn.cursor()
        cur.execute('SELECT name FROM urls WHERE id=(%s);',
                    (id,))
        site = cur.fetchone()
        r = requests.get(site[0])
        code = r.status_code
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        tag = {'h1': ' ',
               'title': ' ',
               'meta': ' '
               }
        for t in tag:
            if soup.find(t) is not None:
                if t == 'meta' and soup.find('meta').get('content') is not None:
                    tag['meta'] = soup.find('meta').get('content')
                    break
                tag[t] = soup.find(t).text
        cur = conn.cursor()
        cur.execute('INSERT INTO url_checks (url_id,'
                    'created_at, status_code, h1, description, title) '
                    'VALUES ((%s), (%s), (%s), (%s), (%s), (%s));',
                    (id, dt, code, tag['h1'], tag['meta'], tag['title']))
        cur.close()
        flash('Страница успешно проверена')
        return redirect(url_for('show_url', id=id))
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке')
        return redirect(url_for('show_url', id=id))
