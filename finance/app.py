## db tables: users, assets, holdings, trades ##
import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
with open("api.txt", 'r') as f:
    os.environ["API_KEY"] = f.read()
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Get username and cash
    user_id = session["user_id"]
    row = db.execute('SELECT * FROM users WHERE id = ?', user_id)
    username = row[0]["username"]
    cash = row[0]["cash"]

    # Crunch portfolio data
    holdings = []
    asset_val = 0
    tb = db.execute(
        '''
        SELECT symbol, name, qty, price
        FROM assets, holdings
        WHERE holdings.asset_id = assets.id
        AND holdings.user_id = ?
        ''', user_id
    )
    if len(tb) > 0:
        for row in tb:
            qty = row["qty"]
            if qty > 0:

                # Fetch quote
                quote = lookup(row["symbol"])
                price = quote["price"]
                # price = row["price"]

                value = qty * price
                asset_val += value
                d = {
                    "symbol": row["symbol"],
                    "name": row["name"],
                    "qty": qty,
                    "price": price,
                    "value": value
                }
                holdings.append(d)

    total = cash + asset_val

    return render_template("index.html", username=username, cash=cash, holdings=holdings, asset_val=asset_val, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # POST
    if request.method == "POST":
        user_id = session["user_id"]

        # Validate input
        symbol = request.form.get("symbol").upper()
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("invalid quantity")
        if shares < 1:
            return apology("invalid quantity")

        # Lookup
        quote = lookup(symbol)
        if quote is None:
            return apology("symbol not found")
        name = quote["name"]
        price = quote["price"]
        val = price * shares

        # debug only
        # name = 'Apple Inc'
        # price = 123.00
        # val = price * shares

        # Get user cash
        row = db.execute('SELECT cash FROM users WHERE id = ?', user_id)
        cash = row[0]["cash"]
        if val > cash:
            return apology("rejected: low cash")
        cash -= val

        # Update records - assets, holdings, users, trades
        # Note we can use the try/except method for insert/update provided we've defined UNIQUE table constraints at the schema level
        try:
            asset_id = db.execute('INSERT INTO assets (name, symbol, price) VALUES (?,?,?)', name, symbol, price)
        except:
            row = db.execute('SELECT id FROM assets WHERE symbol = ?', symbol)
            asset_id = row[0]["id"]
            db.execute('UPDATE assets SET price = ? WHERE id = ?', price, asset_id)

        try:
            db.execute('INSERT INTO holdings (asset_id, user_id, qty) VALUES (?,?,?)', asset_id, user_id, shares)
        except:
            row = db.execute('SELECT qty FROM holdings WHERE asset_id = ? AND user_id = ?', asset_id, user_id)
            qty = row[0]["qty"]
            qty += shares
            db.execute('UPDATE holdings SET qty = ? WHERE asset_id = ? AND user_id = ?', qty, asset_id, user_id)

        db.execute('UPDATE users SET cash = ? WHERE id = ?', cash, user_id)
        db.execute("INSERT INTO trades (type, asset_id, user_id, shares, price) VALUES ('buy',?,?,?,?)", asset_id, user_id, shares, price)

        flash("done")
        return redirect("/")

    # GET
    return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # POST
    if request.method == "POST":
        user_id = session["user_id"]

        # Validate input
        symbol = request.form.get("symbol").upper()
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("invalid quantity")
        if shares < 1:
            return apology("invalid quantity")

        # Lookup
        quote = lookup(symbol)
        if quote is None:
            return apology("symbol not found")
        price = quote["price"]
        val = price * shares

        # debug only
        # price = 123.00
        # val = price * shares

        # Get user inventory
        error = None
        row = db.execute('SELECT cash FROM users WHERE id = ?', user_id)
        cash = row[0]["cash"]

        row = db.execute('SELECT id FROM assets WHERE symbol = ?', symbol)
        asset_id = row[0]["id"]
        row = db.execute('SELECT qty FROM holdings WHERE asset_id = ? AND user_id = ?', asset_id, user_id)
        qty = row[0]["qty"] # assume user submitted valid symbol from drop-down list

        if qty == 0:
            error = "rejected: you don't own it"
        if shares > qty:
            error = "rejected: low inventory"
        if error is not None:
            return apology(error)
        cash += val
        qty -= shares

        # Update records - assets, holdings, users, trades
        db.execute('UPDATE assets SET price = ? WHERE id = ?', price, asset_id)
        db.execute('UPDATE holdings SET qty = ? WHERE asset_id = ? AND user_id = ?', qty, asset_id, user_id)
        db.execute('UPDATE users SET cash = ? WHERE id = ?', cash, user_id)
        db.execute("INSERT INTO trades (type, asset_id, user_id, shares, price) VALUES ('sell',?,?,?,?)", asset_id, user_id, shares, price)

        flash("done")
        return redirect("/")

    # GET

    # Fetch user symbols
    symbols = []
    tb = db.execute(
        '''
        SELECT symbol, qty
        FROM assets, holdings AS h
        WHERE h.asset_id=assets.id
        AND h.user_id = ?
        ''', session["user_id"])

    for row in tb:
        if row["qty"] > 0:
            symbols.append(row["symbol"])

    return render_template("sell.html", symbols=symbols)


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # POST
    if request.method == "POST":

        symbol = request.form.get("symbol").upper()

        # Lookup
        quote = lookup(symbol)
        if quote is not None:
            name = quote["name"]
            symbol = quote["symbol"]
            price = quote["price"]

            # Update our db
            try:
                db.execute('INSERT INTO assets (symbol, name, price) VALUES (?,?,?)', symbol, name, price)
            except ValueError:
                db.execute('UPDATE assets SET price = ? WHERE symbol = ?', price, symbol)

            flash("Found: {} {}".format(symbol, usd(price)))
            return redirect(url_for("quote"))

        # Symbol not found
        return apology("None")

    # GET
    return render_template("quote.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    trades = db.execute(
        '''
        SELECT type, symbol, shares, t.price, time
        FROM trades AS t, assets AS a
        WHERE t.asset_id = a.id
        AND t.user_id = ?
        ORDER BY time DESC
        ''', session["user_id"]
    )
    return render_template("history.html", trades=trades)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # POST
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")
        error = None

        if username is None or username == '':
            error = "please enter username"
        elif password is None or password == '':
            error = "please enter password"
        elif password != confirm:
            error = "password fields must match"

        if error is not None:
            return apology(error)

        # Add new user
        row = db.execute('SELECT * FROM users WHERE username = ?', username)
        if len(row) != 0:
            error = f"sorry, {username} taken"
        else:
            hash = generate_password_hash(password)
            db.execute('INSERT INTO users (username, hash) VALUES (?,?)', username, hash)
            return redirect("/login")

        return apology(error)

    # GET
    return render_template("register.html")