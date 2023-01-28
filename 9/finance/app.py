import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology_err, apology_impl, login_required, lookup, usd

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

        # Query db for holdings
        tab = db.execute("SELECT symbol, name, qty, price FROM holdings, assets\
            WHERE holdings.asset_id=assets.id\
            AND holdings.user_id=?", user_id)

        # Create portfolio
        if len(tab) == 0:   # user's portfolio empty
            return render_template("index.html", user=user, cash=cash, holdings=None, sum=None, total=None, admin=admin)
        else:
            holdings = []
            for row in range(len(tab)):         # row += value is sufficient? ## row['value'] = qty * price
                symbol = tab[row]["symbol"]
                name = tab[row]["name"]
                qty = tab[row]["qty"]
                price = tab[row]["price"]
                value = (qty * price)
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
            table = db.execute("select price, symbol, name from assets limit 25")

            return render_template("advanced.html", user=user, cash=cash, table=table, holdings=holdings, sum=sum, total=total, admin=admin)


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
            symbol = request.form.get("symbol").upper()
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
                db.execute("update assets set price=? where id=?", asset_id)      # off for develop
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
            if "quick-order" in request.form:    # symbol and qty from quick order form, the follow same
                shares = round(float(request.form.get("shares")), 2)
                multi = int(request.form.get("multiplier"))
                tb = db.execute("select symbol from assets limit 25") # same select as advanced view table
                for i in range(len(tb)):
                    if tb[i]["symbol"] in request.form:
                        symbol = tb[i]["symbol"]
                if not symbol:
                    flash('symbol err')
                    return redirect("/")
                shares = (shares * multi)

            else: # Standard buy order
                symbol = request.form.get("symbol").upper()
                if symbol == '':
                    return render_template("buy.html")
                shares = request.form.get("shares")    # need to accept 2 decimal places, shares gets float type - unimpld
                if not shares or not int(shares) > 0:
                    flash("please enter valid NUM shares")
                    return render_template("buy.html")
                else:
                    shares = round(float(shares), 2)

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
                    flash('SYMBOL not found')
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
            if value > int(cash):
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
            return apology_err("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology_err("invalid username and/or password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # POST
    if request.method == "POST":

        if "quick-search" in request.form:
            gohome = True
        else:
            gohome = False
        s = request.form.get("name").upper() # Should allow symbol or name

        # Retrieve asset symbol - logic follows dynamic table data, see /search route
        row = db.execute("select symbol from assets where symbol=? or name like ? limit 1", s, '%'+ s +'%')
        if len(row) == 0:   # not in our db
            symbol = s

            # Lookup
            if not lookup(symbol):
                flash("SYMBOL not found")
                return render_template("quote.html")
            else:
                quote = lookup(symbol)
                price = quote["price"]

            # Insert new assets
                symbol = quote["symbol"]
                name = quote["name"]
                db.execute("INSERT INTO assets (class, symbol, name, price) values ('stock',?,?,?)", symbol, name, price)
                flash("{}: ${}".format(symbol, price))
                if gohome:
                    return redirect("/")
                else:
                    return render_template("quote.html", symbol=symbol)
        else:
            symbol = row[0]["symbol"]
            quote = lookup(symbol)
            price = quote["price"]
            db.execute("UPDATE assets SET price=? WHERE symbol=?", price, symbol)
            flash("Found {}: ${}".format(symbol, price))
            if gohome:
                return redirect("/")
            else:
                return render_template("quote.html", symbol=symbol)

    # GET
    else:
        return render_template("quote.html", symbol=None)


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
            flash("please input new username")
            return redirect("/register")
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
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        return redirect("/login")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # GET
    if request.method == "GET":
        return(render_template("/sell.html"))

    # POST
    user_id = session["user_id"]
    if user_id == 1:
        admin = True
    else:
        admin = False

    # Max order size
    if "maximum-order-size" in request.form:
        symbol = request.form.get("symbol").upper()
        if symbol == '':
            return render_template("sell.html")

        row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
        if len(row) == 0:   # bad symbol err, if owned we expect to return an asset record
            flash("err bad symbol")
            return render_template("sell.html")
        else:
            asset_id = row[0]["id"]

        # Get current cash and shares
        row = db.execute("SELECT * FROM users WHERE id=?", user_id)
        cash = row[0]["cash"]
        row = db.execute("SELECT * FROM holdings WHERE asset_id=? AND user_id=?", asset_id, user_id)
        if len(row) == 0:   # asset not in holdings
            flash("rejected: you don't own that")
            return render_template("sell.html")
        qty = row[0]["qty"]

        # # Lookup quote
        if admin:
            row = db.execute("SELECT * FROM assets WHERE symbol=?", symbol)
            price = row[0]["price"]
        else:
            if lookup(symbol) is None:      # Check is a valid symbol
                flash("symbol not found")
                return render_template("sell.html")
            else:
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
            tb = db.execute("select id, symbol from assets limit 25")   # This needs to match the table sent to advanced order template to ensure we return a symbol
            for i in range(len(tb)):
                if tb[i]["symbol"] in request.form:
                    symbol = tb[i]["symbol"]
                    asset_id = tb[i]["id"]
            shares = (shares * exp)

        else: # Standard sell order
            symbol = request.form.get("symbol").upper()
            if symbol == '':
                return render_template("sell.html")
            shares = request.form.get("shares")
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
            return render_template("sell.html")
        elif len(row) != 1:   # should return 1 row
            flash("backend err: failed table constraint, offender {}".format(symbol))
            return render_template("sell.html")
        else:
            hodl_id = row[0]["id"]
            qty = row[0]["qty"]
        if not shares or not shares > 0:
            flash("please enter valid NUM shares")
            return render_template("sell.html")
        if shares > qty:
            flash("rejected: low user shares")
            return render_template("sell.html")

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
    """Remove ticker from watchlist"""

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
    """ """

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
        row = db.execute("SELECT * FROM assets WHERE symbol=? OR name LIKE ? LIMIT 1", q, '%'+ q +'%') # Where asset id in trades for this user
    else:
        row = []

    # We pass db row and user portfolio to search.html
    # jinja: if symbol in watchlist, say so, else render button to add it
    return render_template("search.html", row=row, holdings=holdings)
    return apology_impl("not impl'd")


@app.route("/watch", methods=["POST"])
@login_required
def add_watching():
    """ """

    user_id = session["user_id"]
    symbols = []
    tb = db.execute("select * from assets")
    for i in range(len(tb)):
        s = tb[i]["symbol"]
        symbols.append(s)       # redundant?
        if s in request.form:
            db.execute("insert into holdings (asset_id, qty, user_id) values (?,0,?)", tb[i]["id"], user_id)
            flash("added")
            return render_template("quote.html", symbol=s)

    flash("symbol fail")
    return render_template("quote.html")


@app.route("/stat", methods=["GET"])
def display_stats():
    """ """

    # We need list of user dicts sorted by portfolio sum
    list = []

    # For each user, get largest holding and total value of holdings excluding idle cash
    users = db.execute("select id from users")
    for user in range(len(users)):
        id = users[user]["id"]

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

        if sum[0]["sum(qty*price)"] is None:     # user has no holdings
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
                        list.insert(i, dict)

    return render_template("stat.html", list=list)


