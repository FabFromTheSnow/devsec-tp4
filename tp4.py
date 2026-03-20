#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YnovShop - Application e-commerce vulnérable (TP SAST Semgrep)
=================================================================
YNOV Campus - Master 1 Cybersécurité - Séance 04

⚠️ ATTENTION : Cette application contient VOLONTAIREMENT des vulnérabilités
critiques à des fins pédagogiques. NE JAMAIS déployer en production !

Objectif du TP : Identifier, exploiter et corriger les 3 vulnérabilités CRITICAL.
"""

from flask import Flask, render_template_string, request, redirect, url_for, session
from markupsafe import escape
import sqlite3
import os

app = Flask(__name__)

# ==================================================================================
# ⚠️ VULNÉRABILITÉ 1 : Secret hardcodé (CWE-798)
# ==================================================================================
# CRITIQUE : Ne JAMAIS stocker de secrets en clair dans le code source !
# IMPACT : Si ce code est poussé sur Git/GitHub, n'importe qui peut voler la clé
# DÉTECTION : semgrep --config p/secrets .
# CORRECTION : Utiliser os.environ.get('SECRET_KEY') avec fichier .env
# ==================================================================================
SECRET_KEY = "super-secret-key-production-2026-ynov-flask-app"
app.secret_key = SECRET_KEY

DATABASE_URI = "sqlite:///ynovshop.db"


def init_db():
    """Initialise la base de données avec les tables et données de test."""
    conn = sqlite3.connect('ynovshop.db')
    cursor = conn.cursor()

    # Table users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT 'customer'
        )
    """)

    # Table products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)

    # Table reviews (avis clients)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    # Insertion de données de test
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        test_users = [
            ('admin', 'admin123', 'admin@ynovshop.com', 'admin'),
            ('alice', 'password123', 'alice@example.com', 'customer'),
            ('bob', 'qwerty456', 'bob@example.com', 'customer')
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            test_users
        )

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        test_products = [
            ('Laptop YNOV Pro', 'Ordinateur portable haute performance 16GB RAM', 1299.99, 15),
            ('Souris Gaming RGB', 'Souris ergonomique avec éclairage RGB', 49.99, 50),
            ('Clavier Mécanique', 'Clavier mécanique switches Cherry MX', 129.99, 30),
            ('Écran 27 pouces 4K', 'Moniteur IPS 4K 144Hz pour professionnels', 599.99, 8),
            ('Webcam Full HD', 'Caméra 1080p pour visioconférences', 89.99, 25)
        ]
        cursor.executemany(
            "INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
            test_products
        )

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec succès.")


@app.route('/')
def index():
    """Page d'accueil de YnovShop."""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>YnovShop - E-commerce</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            header { background: #6c3fc5; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            nav a { color: white; margin-right: 15px; text-decoration: none; }
            .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .btn { display: inline-block; background: #6c3fc5; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; }
        </style>
    </head>
    <body>
        <header>
            <h1>🛒 YnovShop - E-commerce</h1>
            <nav>
                <a href="/">Accueil</a>
                <a href="/products">Produits</a>
                <a href="/search">Rechercher</a>
                <a href="/reviews">Avis clients</a>
                <a href="/login">Connexion</a>
            </nav>
        </header>
        <div class="container">
            <h2>Bienvenue sur YnovShop !</h2>
            <p>Découvrez nos produits high-tech pour étudiants et professionnels en cybersécurité.</p>
            <a href="/products" class="btn">Voir tous les produits</a>
        </div>
    </body>
    </html>
    """)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion."""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        conn = sqlite3.connect('ynovshop.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/')
        return "❌ Échec de connexion"

    return render_template_string("""
    <html>
    <body style="font-family: Arial; max-width: 400px; margin: 100px auto;">
        <h2>🔐 Connexion</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Nom d'utilisateur" style="width: 100%; padding: 10px; margin: 10px 0;">
            <input type="password" name="password" placeholder="Mot de passe" style="width: 100%; padding: 10px; margin: 10px 0;">
            <button type="submit" style="background: #6c3fc5; color: white; padding: 10px 20px; border: none;">Connexion</button>
        </form>
        <p style="font-size: 12px;">Test : admin/admin123</p>
    </body>
    </html>
    """)


@app.route('/products')
def products():
    """Liste des produits."""
    conn = sqlite3.connect('ynovshop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products_list = cursor.fetchall()
    conn.close()

    html = '<h1>Catalogue Produits</h1>'
    for p in products_list:
        html += f'<div><h3>{p[1]}</h3><p>{p[2]}</p><strong>{p[3]} €</strong></div>'
    return html


# ==================================================================================
# ⚠️ VULNÉRABILITÉ 2 : SQL Injection (CWE-89)
# ==================================================================================
@app.route('/search')
def search():
    search_term = request.args.get('q', '')
    results = []

    if search_term:
        conn = sqlite3.connect('ynovshop.db')
        cursor = conn.cursor()
        query = "SELECT * FROM products WHERE name LIKE ?"
        try:
            cursor.execute(query, (f'%{search_term}%',))
            results = cursor.fetchall()
        except sqlite3.Error as e:
            results = [("ERROR", str(e))]
        conn.close()

    return render_template_string("""
    <h1>Recherche</h1>
    <form>
        <input type="text" name="q" value="{{ search_term }}" placeholder="Rechercher...">
        <button>Search</button>
    </form>
    <div>Résultats : {{ results|length }}</div>
    {% for r in results %}
        <div>{{ r[1] }} - {{ r[3] }} €</div>
    {% endfor %}
    """, search_term=search_term, results=results)
# ==================================================================================
# ⚠️ VULNÉRABILITÉ 3 : XSS Stocké (CWE-79)
# ==================================================================================
@app.route('/reviews')
def reviews():
    """Avis clients VULNÉRABLE à XSS Stocké."""
    conn = sqlite3.connect('ynovshop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews ORDER BY created_at DESC LIMIT 20")
    reviews_list = cursor.fetchall()
    conn.close()

    html = '<h1>💬 Avis Clients</h1>'
    html += '<p>⚠️ Test XSS: &lt;script&gt;alert(document.cookie)&lt;/script&gt;</p>'
    html += '<a href="/add-review">Écrire un avis</a><hr>'

    for review in reviews_list:
        # 🚨 DANGER : Affichage direct sans échappement HTML
        html += f'<div><strong>{review[2]}</strong>: {review[3]}</div>'

    return html


@app.route('/add-review', methods=['GET', 'POST'])
def add_review():
    """Ajout d'avis (stockage sans sanitization)."""
    if request.method == 'POST':
        username = session.get('user', 'Anonyme')
        content = request.form.get('content', '')

        conn = sqlite3.connect('ynovshop.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reviews (product_id, username, content) VALUES (?, ?, ?)", (1, username, content))
        conn.commit()
        conn.close()
        return redirect('/reviews')

    return """
    <h1>Écrire un Avis</h1>
    <form method="POST">
        <textarea name="content" rows="5" style="width: 100%;"></textarea>
        <button type="submit">Publier</button>
    </form>
    """


if __name__ == '__main__':
    if not os.path.exists('ynovshop.db'):
        print("🔧 Initialisation de la base de données...")
        init_db()

    print("""
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                  YnovShop - Application Vulnérable                     ║
    ║               YNOV Campus - TP SAST Semgrep - 2026                    ║
    ╚════════════════════════════════════════════════════════════════════════╝

    ⚠️  3 vulnérabilités CRITICAL présentes :
        1. Secret hardcodé (ligne 28) - CWE-798
        2. SQL Injection (ligne 193) - CWE-89
        3. XSS Stocké (ligne 218) - CWE-79

    🚀 Application lancée sur http://127.0.0.1:5000
    """)

    app.run(debug=False, host='127.0.0.1', port=5000)
