from flask import Flask ,render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import  psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "supersecretkey123"
DATABASE_URL = os.getenv("DATABASE_URL")
#print("DATABASE_URL:", DATABASE_URL)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route("/")
def home():
    try:
        conn = get_db_connection()
    
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return f"database connected successfully! Current time: {result[0]}"
    except Exception as e:
        return f"databse connection failed:{e}"




# register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("insert into users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed_password))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/login")
    return render_template("register.html")

# login route
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("select id, password from users where email = %s", (email,))

        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            return "invalid email or password"
    return render_template("login.html")

# dashboard route
# if user is not logged it , cant access #dashboard page
# protected route

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    #fetch user name from database using user_id stored in session
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("select name from users where id = %s", (user_id,))
    #fetch the user's name
    user = cur.fetchone()
    cur.close()
    conn.close()
    # render the dashboard template with the user's name
    return render_template("dashboard.html", name = user[0])
# name = user[0] , name will be used in html page to use name var to show users name. 



#upload route
@app.route("/upload", methods = ["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        title = request.form["title"]
        file = request.files["certificates"]
         
        if file.name == "":
            return "No selected file"
        filename = secure_filename(file.filename)

        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        user_id = session["user_id"]
        
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("insert into certificates (user_id, title, certificate_url) values (%s, %s, %s)", (user_id, title, filename))

        conn.commit()
        cur.close()
        conn.close()

        

        return "File uploaded successfully"
    return render_template("upload.html")

# logout route-
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
if __name__ == "__main__":
    app.run(debug=True)