from flask import Flask, redirect, render_template, request
from mysqlconnection import connectToMySQL
app = Flask(__name__)

@app.route('/')
def index():
    mysql = connectToMySQL("pets")
    pets = mysql.query_db("SELECT * FROM pets;")
    print(pets)
    return render_template("index.html", all_pets = pets)
            
@app.route("/show_pets", methods=["POST"])
def add_pets_to_db():
    mysql = connectToMySQL("pets")

    query= "INSERT INTO pets (name, type, created_at, updated_at) VALUES (%(pn)s, %(pt)s, NOW(), NOW());" 
    data = {
        "pn": request.form["pet_name"],
        "pt": request.form["pet_type"],
    }
    new_friend_id = mysql.query_db(query,data) # pylint: disable=unused-variable
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)