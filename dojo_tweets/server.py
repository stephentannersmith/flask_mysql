from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
import re
from flask_bcrypt import Bcrypt

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
strongRegex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])(?=.{8,})")

app = Flask(__name__)
app.secret_key = "fSD;fkljsf;ldskfjSD:GLiwougerafvbcv872t3riwegDSklfJHD"
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template("login_reg.html")

@app.route('/success')
def tweet_landing():
    if 'user_id' not in session:
        return redirect('/')
    
    query = "SELECT * FROM users WHERE id_user = %(uid)s"
    data = {"uid": session["user_id"]}
    mysql = connectToMySQL("dojo_tweets")
    result = mysql.query_db(query, data)
    if result:
        query = "SELECT tweets.id_tweet, tweets.authors, tweets.content, users.first_name, users.last_name FROM users JOIN tweets ON users.id_user = tweets.authors;"
        mysql = connectToMySQL("dojo_tweets")
        tweets = mysql.query_db(query)

        query = "SELECT liked_tweets.tweet_id FROM liked_tweets WHERE liked_tweets.user_id = %(u_id)s"
        data = {'u_id': session['user_id']}
        mysql = connectToMySQL("dojo_tweets")
        tweets_loggedin_user_likes = mysql.query_db(query, data)

        l_t_i = [tweet['tweet_id'] for tweet in tweets_loggedin_user_likes]

        print(l_t_i)

        return render_template('tweet_landing.html', user_data = result[0], tweets=tweets, l_t_i=l_t_i)
    else:
        return redirect('/')

@app.route('/on_tweet', methods=["POST"])
def on_tweet():
    valid = True 
    tweet_content = request.form.get('tweet_content')
    if len(tweet_content) < 1:
        valid = False
        flash("Tweets must be at least 1 character long.")

    if valid:
        query = "INSERT INTO tweets (content, authors, created_at, updated_at) VALUES (%(tweet)s, %(user_fk)s, NOW(), NOW());"
        data = {
            "tweet": tweet_content,
            "user_fk": session['user_id']
        }
        mysql = connectToMySQL("dojo_tweets")
        mysql.query_db(query, data)
    
    return redirect('/success')

@app.route("/on_delete/<id_tweet>")
def on_delete(id_tweet):
    if 'user_id' not in session:
        return redirect('/')
    query = "DELETE FROM tweets WHERE tweets.id_tweet = %(id_tweet)s"
    data = {'id_tweet': id_tweet}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect('/success')

@app.route("/edit/<id_tweet>")
def edit_form(id_tweet):
    query = "SELECT tweets.id_tweet, tweets.content FROM tweets WHERE tweets.id_tweet = %(id_tweet)s"
    data = {"id_tweet": id_tweet}
    mysql = connectToMySQL("dojo_tweets")
    tweet = mysql.query_db(query, data)
    if tweet:
        return render_template("tweet_edit.html", tweet_data=tweet[0])
    return redirect("/success")

@app.route("/on_edit/<id_tweet>", methods=["POST"])
def on_edit(id_tweet):
    query = "UPDATE tweets SET tweets.content = %(tweet)s WHERE tweets.id_tweet = %(id_tweet)s "
    data = { "tweet": request.form.get("tweet_edit"), "id_tweet": id_tweet }
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route('/like/<tweet_id>')
def like_tweet(tweet_id):
    query = "INSERT INTO liked_tweets (user_id, tweet_id) VALUES (%(u_id)s, %(t_id)s)"
    data = {'u_id': session['user_id'], 't_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route('/unlike/<tweet_id>')
def unlike_tweet(tweet_id):
    query = "DELETE FROM liked_tweets WHERE user_id = %(u_id)s AND tweet_id = %(t_id)s"
    data = {'u_id': session['user_id'], 't_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route('/details/<id_tweet>')
def details_tweet(id_tweet):
    query = "SELECT users.first_name, users.last_name, tweets.created_at, tweets.content FROM users JOIN tweets ON users.id_user = tweets.authors WHERE tweets.id_tweet = %(tid)s"
    data = {'tid': id_tweet}
    mysql = connectToMySQL("dojo_tweets")
    tweet_data = mysql.query_db(query, data)
    if tweet_data:
        tweet_data = tweet_data[0]
    print(tweet_data)

    query = "SELECT users.first_name, users.last_name FROM liked_tweets JOIN users ON users.id_user = liked_tweets.user_id WHERE liked_tweets.tweet_id = %(tid)s"
    data = {'tid': id_tweet}
    mysql = connectToMySQL("dojo_tweets")
    like_data = mysql.query_db(query, data)
    if like_data:
        like_data = like_data[0]

    return render_template("details.html", tweet_data=tweet_data, like_data=like_data)

@app.route('/users/create', methods=["POST"])
def process():
    
    valid = True
    if len(request.form['first_name']) < 1:
        valid = False
        flash("First name must be at least 2 characters long.")

    if len(request.form['last_name']) < 1:
        valid = False
        flash("Last name must be at least 2 characters long.")

    if len(request.form['email']) < 2:
        valid = False
        flash("Email needs to be valid.")

    if not EMAIL_REGEX.match(request.form['email']): # test whether a field matches the pattern
        flash("Invalid email address!")

    if len(request.form["password"]) < 8:
        valid = False
        flash("Password must be at least 8 characters.")

    # if not strongRegex.match(request.form['password']):
    #     flash("Password must contain at least one lowercase, one uppercase, one numeric, one special character, grandma's banana bread recipe, and a blood sacrifice.")
    #     valid = False

    if request.form["password"] != request.form["conf_password"]:
        valid = False
        flash("Passwords must match.")

    db = connectToMySQL('dojo_tweets')
    validate_email_query = 'SELECT email FROM users WHERE email=%(email)s;'
    form_data = {
        'email': request.form['email']
    }
    existing_users = db.query_db(validate_email_query, form_data)

    if existing_users:
        flash("Email already in use")
        valid = False

    if not valid:
        # redirect to the form page, don't create user
        flash("Something went wrong.")
        return redirect('/')

    pw_hash = bcrypt.generate_password_hash(request.form['password'])
    
    db = connectToMySQL("dojo_tweets")
    create_query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(password_hash)s, NOW(), NOW());"
    create_data = {
        "fn": request.form["first_name"],
        "ln": request.form["last_name"],
        "em": request.form["email"],
        "password_hash": pw_hash
        }

    user_id = db.query_db(create_query, create_data)
    session['user_id'] = user_id
    return redirect('/success')

@app.route("/follow_users")
def show_follow_users():
    # look for users i have already followed
    query = "SELECT * FROM user_has_followers WHERE follower = %(uid)s"
    data = {'uid': session['user_id']}
    mysql = connectToMySQL("dojo_tweets")
    followed_users = mysql.query_db(query,data)

    followed_users_list = [info['user'] for info in followed_users]
    
    followed = []
    not_followed = []

    for user in followed_users:
        if user['user'] == session['user_id']:
            continue
        if user['user'] in followed_users_list:
            followed.append(user)
        else:
            not_followed.append(user)

    return render_template("follow_users.html", followed=followed, not_followed=not_followed)

@app.route("/on_follow/<user_id>")
def follow(user_id):
    mysql = connectToMySQL("dojo_tweets")
    query = "INSERT INTO user_has_followers (user,follower) VALUES (%(u_id)s, %(f_id)s"
    data = {'u_id': session['user_id'], 'f_id': user_id}
    mysql.query_db(query, data)
    return redirect("/follow_users")

@app.route('/login', methods=["POST"])
def login():
    db = connectToMySQL("dojo_tweets")
    query = "SELECT users.id_user, users.email, users.password FROM users WHERE email = %(le)s;"
    stored_user = {
        "le": request.form["lemail"]
    }
    selected_users = db.query_db(query,stored_user)
    is_correct_login = bcrypt.check_password_hash(selected_users[0]["password"], request.form["lpassword"])
    if len(selected_users) < 1:
        flash("Email must be at least 1 character long.")
        return redirect('/')
    if len(request.form["lpassword"]) < 1:
        flash("Password must be at least 1 character long.")
        return redirect('/')
    if not is_correct_login:
        flash("Password is incorrect")
        return redirect('/')
    elif is_correct_login:
        session['user_id'] = selected_users[0]["id_user"]
    return redirect('/success')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__  == "__main__":
    app.run(debug=True)