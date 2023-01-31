import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
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
api = "iex.txt"
with open(api, 'r') as file:
    line = file.read()
os.environ["API_KEY"] = line
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""

    # POST
    if request.method == "POST":

        # Toggle theme preference
        if "mood" in request.form:
            id = session["user_id"]
            row = db.execute("select * from settings where user_id=?", id)
            theme = row[0]["theme"]
            if theme == "light":
                db.execute("update settings set theme='dark' where user_id=?", id)
            else:
                db.execute("update settings set theme='light' where user_id=?", id)
            return redirect("/")

        # For all asset id in holdings
        tab = db.execute("SELECT symbol FROM assets, holdings\
            WHERE holdings.asset_id=assets.id")

        # Lookup quote
        for i in range(len(tab)):
            symbol = tab[i]["symbol"]
            quote = lookup(symbol)
            price = quote["price"]

            # Update our assets db
            db.execute("UPDATE assets SET price=? WHERE symbol=?", price, symbol)

        return redirect("/")

    # GET
    else:
        user_id = session["user_id"]
        if user_id == 1:
            admin = True
        else:
            admin = False
        row = db.execute("SELECT * FROM users WHERE id=?", user_id)
        user = row[0]["username"]
        cash = row[0]["cash"]

        # User preferences - theme only for now
        # prefs = {}
        row = db.execute("select * from settings where user_id=?", user_id)
        session["theme"] = row[0]["theme"]

        # Query db for holdings
        tab = db.execute("SELECT symbol, name, qty, price FROM holdings, assets\
            WHERE holdings.asset_id=assets.id\
            AND holdings.user_id=?", user_id)

        # Create portfolio
        if len(tab) == 0:   # user's portfolio empty
            return render_template("index.html", user=user, cash=cash, holdings=None, sum=None, total=None, admin=admin)
        else:
            holdings = []
            for row in range(len(tab)):
                symbol = tab[row]["symbol"]
                name = tab[row]["name"]
                qty = tab[row]["qty"]
                price = tab[row]["price"]
                value = round(float(qty * price), 2)   # can do this with sql
                hodl = {
                    "symbol": symbol,
                    "name": name,
                    "qty": qty,
                    "price": price,
                    "value": value
                    }
                holdings.append(hodl)

            # Sum portolio value
            sum = 0
            for i in range(len(holdings)):
                sum += holdings[i]["value"]
            total = sum + cash

            # Expanded view data
            table = []          # get symbols for user's recent trades
            tb = db.execute("select distinct assets.price, symbol, name from assets, trades\
                    where trades.asset_id=assets.id\
                    and trades.user_id=?\
                    order by time desc", user_id)
            for row in range(len(tb)):
                d = {
                    "price": tb[row]["price"],
                    "symbol": tb[row]["symbol"],
                    "name": tb[row]["name"]
                }
                table.append(d)
                if len(table) == 25:
                    break

            # Fill in table with generic records - filter duplicates - hacky
            if len(table) < 25:
                tb = db.execute("select price, symbol, name from assets limit 25")
                for row in range(len(tb)):
                    tb[row]["match"] = 0
                    for i in range(len(table)):
                        if tb[row]["symbol"] == table[i]["symbol"]:
                            tb[row]["match"] += 1

                for row in range(len(tb)):
                    if tb[row]["match"] == 0:
                        d = {
                            "price": tb[row]["price"],
                            "symbol": tb[row]["symbol"],
                            "name": tb[row]["name"]
                        }
                        table.append(d)
                        if len(table) == 25:
                            break

            return render_template("advanced.html", user=user, cash=cash, table=table,\
                                                    holdings=holdings, sum=sum, total=total, admin=admin)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # GET
    if request.method == "GET":
        return render_template("buy.html")

    # POST
    else:
        user_id = session["user_id"]
        if user_id == 1:
            admin = True
        else:
            admin = False

        if "maximum-order-size" in request.form:    # Max order size
            try:
                symbol = request.form.get("symbol").upper()
            except:
                return redirect("/buy")
            if symbol == '':
                return redirect("/buy")
            row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
            if len(row) == 0:      # not in our db
                unseen = True
            else:
                asset_id = row[0]["id"]
                unseen = False

            # Lookup quote
            if admin:
                row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
                price = row[0]["price"]
            else:
                if lookup(symbol) is None:
                    flash("symbol not found")
                    return render_template("buy.html")
                else:
                    quote = lookup(symbol)
                    price = quote["price"]

            # Get user cash and current holdings
            row = db.execute("SELECT * FROM users WHERE id=?", user_id)
            cash = row[0]["cash"]
            if unseen:
                qty = 0
            else:
                row = db.execute("SELECT * FROM holdings, assets, users\
                        WHERE holdings.asset_id=assets.id\
                        AND holdings.user_id=users.id\
                        AND assets.id=? AND users.id=?", asset_id, user_id)
                if len(row) == 0: # not in user holdings or watching
                    qty = 0
                    new = True
                else:
                    qty = row[0]["qty"]
                    new = False

            # Update records - holdings, user cash, assets, trades
            shares = (cash / price)
            shares = round(shares, 2)
            qty += shares
            if unseen:
                asset_id = db.execute("insert into assets (class, symbol, name) values ('stock',?,?)", quote["symbol"], quote["name"])
            else:
                db.execute("update assets set price=? where id=?", price, asset_id)      # off for develop
            if new:
                db.execute("insert into holdings (asset_id, qty, user_id) values (?,?,?)", asset_id, qty, user_id)
            else:
                db.execute("update holdings set qty=? where holdings.asset_id=? and holdings.user_id=?", qty, asset_id, user_id)
            db.execute("update users set cash=0 where id=?", user_id)
            db.execute("INSERT INTO trades (type, user_id, asset_id, qty, price, time)\
                    VALUES ('buy',?,?,?,?,datetime('now'))", user_id, asset_id, shares, price)

            flash("executed")
            return redirect("/")

        else:
            if "quick-order" in request.form:    # symbol and qty from quick order form, then follow same
                symbol = request.form.get("symbol")
                if not symbol:
                    flash('symbol err')
                    return redirect("/")
                shares = round(float(request.form.get("shares")), 2)
                multi = int(request.form.get("multiplier"))
                if not shares or not shares > 0:
                    flash("invalid quantity")
                    return redirect("/")
                else:
                    shares = (shares * multi)

            else: # Standard buy order
                symbol = request.form.get("symbol").upper()
                if symbol == '':
                    return render_template("buy.html")
                shares = request.form.get("shares")
                if not shares or not int(shares) > 0:
                    flash("invalid quantity")
                    return render_template("buy.html")
                else:
                    shares = round(float(request.form.get("shares")), 2)


            # Lookup quote and add symbol to our db
            if user_id == 1:    # we are admin
                row = db.execute("select * from assets where symbol=?", symbol)
                if len(row) == 0:
                    flash('bad symbol')
                    return render_template("buy.html")
                else:
                    price = row[0]["price"]
                    price = round(float(price), 2)
            else:
                if not lookup(symbol):
                    flash('symbol not found')
                    return render_template("buy.html")
                else:
                    quote = lookup(symbol)
                    symbol = quote["symbol"]
                    name = quote["name"]
                    price = quote["price"]

            # Validate input
            row = db.execute("SELECT * from users WHERE id=?", user_id)
            cash = row[0]["cash"]
            value = (price * shares)
            if value > cash:
                flash("rejected: low cash")
                return render_template("buy.html")
            else:
                cash -= value

            # Update records - assets, holdings, cash, trades
            row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
            if len(row) == 0:   # not in our db
                asset_id = db.execute("insert into assets (class, symbol, name, price) values ('stock',?,?,?)", symbol, name, price)   # assume class="stock"
            else:
                asset_id = row[0]["id"]
                db.execute("update assets set price=? where id=?", price, asset_id)
            row = db.execute("SELECT id, qty FROM holdings\
                WHERE holdings.asset_id=? AND holdings.user_id=?", asset_id, user_id)
            if len(row) == 0:   # asset not in user portfolio
                db.execute("INSERT INTO holdings (asset_id, qty, user_id) VALUES (?, ?, ?)", asset_id, shares, user_id)
            else:   # asset exists in portfolio or watching
                hodl_id = row[0]["id"]
                qty = row[0]["qty"]
                qty += shares
                db.execute("UPDATE holdings SET qty=? WHERE id=?", qty, hodl_id)

            db.execute("UPDATE users SET cash=? WHERE id=?", cash, user_id)
            db.execute("INSERT INTO trades (type, user_id, asset_id, qty, price, time)\
                VALUES ('buy',?,?,?,?,datetime('now'))", user_id, asset_id, shares, price)

            if shares > 100:
                flash("executed")
            else:
                flash("done")
            return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Create view of db
    tab = db.execute("SELECT type, symbol, qty, trades.price, time FROM trades, assets, users\
            WHERE trades.asset_id=assets.id \
            AND trades.user_id=users.id\
            AND users.id=? ORDER BY time DESC", session["user_id"])

    # Build trades list
    trades = []
    for row in range(len(tab)):
        tx = {
            "type": tab[row]["type"],
            "symbol": tab[row]["symbol"],
            "qty": tab[row]["qty"],
            "price": tab[row]["price"],
            "time": tab[row]["time"]
        }
        trades.append(tx)   # can just append row or need to define object? tx = tab[row]
    return render_template("trades.html", trades=trades)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("please enter username")
            return render_template("login.html")
            return redirect("/login")
            return apology_err("must provide username", 403)

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


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")




@app.route("/quote")
@login_required
def quote():
    """Go to quote search page."""

    return render_template("quote.html", quote=None)


@app.route("/quoted")
@login_required
def return_quote():
    """Request a stock quote via a pre-configured API"""

    if "quick-search" in request.args:
        gohome = True
    else:
        gohome = False
    s = request.args.get("name").upper()

    # List of symbols in user holdings
    user_id = session["user_id"]
    holdings = []
    tb = db.execute("select symbol from assets, holdings where holdings.asset_id=assets.id\
            and holdings.user_id=?", user_id)
    for i in range(len(tb)):
        symbol = tb[i]["symbol"]
        holdings.append(symbol)

    # Retrieve asset symbol - logic follows dynamic table data, see /search route
    row = db.execute("select symbol from assets where symbol=? or name like ? limit 1", s, '%'+ s +'%')
    if len(row) == 0:   # not in our db
        symbol = s

        # Lookup
        if not lookup(symbol):
            flash('symbol not found')
            return render_template("quote.html")
        else:
            quote = lookup(symbol)
            price = quote["price"]

        # Insert new assets
            symbol = quote["symbol"]
            name = quote["name"]
            db.execute("INSERT INTO assets (class, symbol, name, price) values ('stock',?,?,?)", symbol, name, price)
            flash("Found {}: ${}".format(symbol, price))
            if gohome:
                return redirect("/")
            else:
                return render_template("quote.html", quote=quote, holdings=holdings)
    else:
        symbol = row[0]["symbol"]
        quote = lookup(symbol)
        price = quote["price"]
        db.execute("UPDATE assets SET price=? WHERE symbol=?", price, symbol)
        flash("Found {}: ${}".format(symbol, price))
        if gohome:
            return redirect("/")
        else:
            return render_template("quote.html", quote=quote, holdings=holdings)



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User arrives via GET
    if request.method == "GET":
        return render_template("register.html")

    # User arrives via POST
    else:
        # Validate input
        if not request.form.get("username"):
            return render_template("register.html")
        row = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if not len(row) == 0:
            flash("sry, username taken")
            return redirect("/register")
        if not request.form.get("password") or not request.form.get("password") == request.form.get("confirmation"):
            flash("err bad password")
            return redirect("/register")

        # Add new user to db
        username = request.form.get("username")
        hash = generate_password_hash(password=request.form.get("password"))
        id = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        db.execute("insert into settings (user_id) values (?)", id)
        return redirect("/login")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # GET
    if request.method == "GET":

        # Get user holdings
        symbols = []
        tb = db.execute("select symbol from assets, holdings where holdings.asset_id=assets.id\
             and holdings.user_id=? and qty>0", session["user_id"])
        if len(tb) == 0:
            symbols = None
        else:
            for row in range(len(tb)):
                symbols.append(tb[row]["symbol"])

        return render_template("/sell.html", symbols=symbols)

    # POST
    user_id = session["user_id"]
    if user_id == 1:
        admin = True
    else:
        admin = False

    # Max order size
    if "maximum-order-size" in request.form:
        try:
            symbol = request.form.get("symbol").upper()
        except:
            return redirect("/sell")

        row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
        if len(row) == 0:   # bad symbol err, if owned we expect to return an asset record
            flash("err bad symbol")
            return redirect("/sell")
        else:
            asset_id = row[0]["id"]

        # Get current cash and shares
        row = db.execute("SELECT * FROM users WHERE id=?", user_id)
        cash = row[0]["cash"]
        row = db.execute("SELECT * FROM holdings WHERE asset_id=? AND user_id=?", asset_id, user_id)
        if len(row) == 0:   # asset not in holdings
            flash("rejected: you don't own that")
            return redirect("/sell")
        qty = row[0]["qty"]

        # # Lookup quote
        if admin:
            row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
            price = row[0]["price"]
        else:
            if lookup(symbol) is None:      # Check is a valid symbol
                flash("symbol not found")
                return redirect("/sell")
            else:
                quote = lookup(symbol)
                price = quote["price"]
        cash += (price * qty)

        # Update records - holdings, user cash, assets, trades
        db.execute("update holdings set qty=0 where asset_id=? and user_id=?", asset_id, user_id)
        db.execute("update users set cash=? where id=?", cash, user_id)
        db.execute("update assets set price=? where id=?", price, asset_id)      # off for develop
        db.execute("INSERT INTO trades (type, user_id, asset_id, qty, price, time)\
                VALUES ('sell',?,?,?,?,datetime('now'))", user_id, asset_id, qty, price)

        flash("executed")
        return redirect("/")


    else:
        # Quick order form - symbol and shares come from separate form, then follow same
        if "quick-order" in request.form:
            shares = round(float(request.form.get("shares")), 2)
            exp = int(request.form.get("multiplier"))
            symbol = request.form.get("symbol")
            if not symbol:
                flash('symbol err')
                return redirect("/")
            shares = (shares * exp)

        else: # Standard sell order
            symbol = request.form.get("symbol").upper()
            if symbol == '':
                return redirect("/sell")
            try:
                shares = round(float(request.form.get("shares")), 2)
            except:
                return redirect("/sell")

        row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
        if len(row) == 0:   # assume if owned, then symbol returns an asset id
            flash("err: bad SYMBOL")
            return render_template("sell.html")
        elif len(row) != 1:
            flash("backend err: failed table constraint, offender {}".format(symbol))
            return render_template("sell.html")
        else:
            asset_id = row[0]["id"]

        # Validate input
        row = db.execute("SELECT id, qty FROM holdings\
                WHERE holdings.asset_id=?\
                AND holdings.user_id=?", asset_id, user_id)
        if len(row) == 0 or row[0]["qty"] == 0:   # asset not in user holdings
            flash("rejected: you don't own that")
            return redirect("/sell")
        elif len(row) != 1:   # should return 1 row
            flash("backend err: failed table constraint, offender {}".format(symbol))
            return render_template("sell.html")
        else:
            hodl_id = row[0]["id"]
            qty = row[0]["qty"]
        if not shares or not shares > 0:
            flash("invalid quantity")
            return redirect("/sell")
        if shares > qty:
            flash("rejected: low user shares")
            return redirect("/sell")

        # Lookup quote
        if user_id == 1:    # we are admin
            row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
            price = row[0]["price"]
        else:
            if not lookup(symbol):
                flash("SYMBOL not found")
                return render_template("sell.html")
            else:
                quote = lookup(symbol)
                price = quote["price"]

        # Update records - last price, holdings, cash, trades
        qty -= shares
        row = db.execute("SELECT * FROM users WHERE id=?", user_id)
        cash = row[0]["cash"]
        cash += (shares * price)

        db.execute("UPDATE assets SET price=? WHERE id=?", price, asset_id)   # off for develop
        db.execute("UPDATE holdings SET qty=? WHERE id=?", qty, hodl_id)
        db.execute("UPDATE users SET cash=? WHERE id=?", cash, user_id)
        db.execute("INSERT INTO trades (type, user_id, asset_id, qty, price, time)\
            VALUES ('sell',?,?,?,?,datetime('now'))", user_id, asset_id, shares, price)

        if shares > 100:
            flash("executed")
        else:
            flash("done")
        return redirect("/")

@app.route("/unwatch", methods=["POST"])
@login_required
def remove_holding():
    """Remove stock symbol from watchlist"""

    # User's current holdings including watch only
    tab = db.execute("SELECT symbol, holdings.asset_id FROM holdings, assets\
        WHERE holdings.asset_id=assets.id\
        AND holdings.user_id=?", session["user_id"])

    # Remove from holdings table
    for i in range(len(tab)):
        if tab[i]["symbol"] in request.form:
            asset_id = tab[i]["asset_id"]
            db.execute("delete from holdings where asset_id=? and user_id=?", asset_id, session["user_id"])
            return redirect("/")


@app.route("/search", methods=["GET"])
@login_required
def search():
    """Handle an automated request for database records"""

    # List of symbols in user holdings
    user_id = session["user_id"]
    holdings = []
    tb = db.execute("select symbol from assets, holdings where holdings.asset_id=assets.id\
            and holdings.user_id=?", user_id)
    for i in range(len(tb)):
        symbol = tb[i]["symbol"]
        holdings.append(symbol)

    # Pull row of database matching symbol or name
    q = request.args.get("q").upper()
    if q:
        row = db.execute("SELECT * FROM assets WHERE symbol=? OR name LIKE ? LIMIT 1", q, '%'+ q +'%')
    else:
        row = []

    # We pass db row and user portfolio to search.html
    # jinja: if symbol in watchlist, say so, else render button to add it
    return render_template("search.html", row=row, holdings=holdings)


@app.route("/watch", methods=["POST"])
@login_required
def add_watching():
    """Add a stock symbol to user watch list"""

    s = request.form.get("symbol")      # sym comes directly from our db through /search route
    if not s:
        flash('backend err see admin')
        return redirect("/quote")
    else:
        row = db.execute("select id from assets where symbol=?", s)
        asset_id = row[0]["id"]
        user_id = session["user_id"]
        db.execute("insert into holdings (asset_id, qty, user_id) values (?,0,?)", asset_id, user_id)
        flash("added {}".format(s))
        return render_template("quote.html", symbol=s)


@app.route("/stat", methods=["GET"])
def display_stats():
    """Display leaderboard for all users"""

    # We need list of user dicts sorted by portfolio sum
    list = []

    # For each user, get largest holding and total value of holdings excluding idle cash
    users = db.execute("select * from users")
    for user in range(len(users)):
        id = users[user]["id"]
        if "user_id" in session:
            if id == session["user_id"]:    # if not logged in, we won't have a session?
                thisuser = users[user]["username"]
        else:
            thisuser = None

        # Largest symbol - 1 row
        large = db.execute("select symbol, max(qty*price) from holdings, assets, users\
                where holdings.asset_id=assets.id\
                and holdings.user_id=users.id\
                and holdings.user_id=?",id)

        # Total portfolio - 1 row
        sum = db.execute("select username, sum(qty*price) from holdings, assets, users\
                where holdings.asset_id=assets.id\
                and holdings.user_id=users.id\
                and holdings.user_id=?",id)

        if sum[0]["sum(qty*price)"] is None:     # lacking price data
            continue
        else:
            dict = {
                    "name": sum[0]["username"],
                    "symbol": large[0]["symbol"],
                    "sum": round(float(sum[0]["sum(qty*price)"]), 2)
                    }
            if len(list) == 0: # first iteration
                list.append(dict)
            elif dict["sum"] < list[-1]["sum"]:
                list.append(dict)       # same result, use or:
            else:
                for i in range(len(list)):
                    if dict["sum"] > list[i]["sum"]:      # linear search, we can do better
                        idx = i
                        break
                list.insert(idx, dict)

    return render_template("stat.html", list=list, thisuser=thisuser)


@app.route("/publish", methods=["POST"])
@login_required
def publish():
    """Send user to social network to share trades"""
    # #
    return apology("Not implemented")
    return render_template("apologyImpl.html", message="Not implemented")
