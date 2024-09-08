from flask import Flask, json, redirect, render_template, flash, request,send_file
from flask.globals import request, session
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from flask_login import login_required, logout_user, login_user, login_manager, LoginManager, current_user
from flask_mail import Mail
import json

# my database connection

local_server = True
app = Flask(__name__)
app.secret_key="RRAKESH"
@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    pdf_path = 'path_to_your_pdf_file.pdf'  # Replace with the path to your PDF file
    return send_file(pdf_path, as_attachment=True)


#config file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

#configure the mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)


# this is for getting the unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# app.confing['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/databasename'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/covid'
db = SQLAlchemy(app)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))

#************************** Start of data bases****************************************

#test db
class Test(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))


#user login db
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    srfid = db.Column(db.String(20),unique=True)
    email = db.Column(db.String(50))
    dob = db.Column(db.String(1000))

#hospital user db
class Hospitaluser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20))
    email = db.Column(db.String(50))
    password = db.Column(db.String(1000))

#hospital user db

class Hospitaldata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode=db.Column(db.String(20),unique=True)
    hname=db.Column(db.String(100))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)


#booking patient db
class Bookingpatient(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    bedtype=db.Column(db.String(100))
    hcode=db.Column(db.String(20))
    spo2=db.Column(db.Integer)
    pname=db.Column(db.String(100))
    pphone=db.Column(db.String(100))
    paddress=db.Column(db.String(100))

#Trigger data
class Trig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode=db.Column(db.String(20))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)
    querys=db.Column(db.String(50))
    date=db.Column(db.String(50))

#************************** End of data bases****************************************


#**************************Differnt pages ********************************************

#home
@app.route("/")
def home():
    return render_template("index.html")

#********************************Admin pages*********************************************\

#-------------------admin login------------------

@app.route('/admin', methods=['POST', 'GET'])
def admin():

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if(username == params['user'] and password == params['password']):
            session['user'] = username
            flash("login success", "info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credentials", "danger")

    return render_template("admin.html")


#------------------add hospital user-------------------
@app.route('/addHospitalUser', methods=['POST', 'GET'])
def hospitalUser():

    if('user' in session and session['user'] == params['user']):

        if request.method == "POST":
            hcode = request.form.get('hcode')
            email = request.form.get('email')
            password = request.form.get('password')
            encpassword = generate_password_hash(password)
            #hcode = hcode.upper()
            emailUser = Hospitaluser.query.filter_by(email=email).first()
            if emailUser:
                flash("Email or srif is already taken", "warning")
            sql_query=text(f"INSERT INTO `hospitaluser` (`hcode`,`email`,`password`) VALUES ('{hcode}','{email}','{encpassword}')  ")
            new_user = db.session.execute(sql_query)
            db.session.commit()
            #db.engine.execute(
            #   f"INSERT INTO `hospitaluser` (`hcode`,`email`,`password`) VALUES ('{hcode}','{email}','{encpassword}') ")

            # mail.send_message('COVID CARE CENTER', sender=params['gmail-user'], recipients=[
            #                  email], body=f"Welcome thanks for choosing us\nYour Login Credentials Are:\n Email Address: {email}\nPassword: {password}\n\nHospital Code {hcode}\n\n Do not share your password\n\n\nThank You...")
            flash("Data Sent and Inserted Successfully", "warning")
            return render_template("hospitallogin.html")
    else:
        flash("Login and try Again", "warning")
        return render_template("addHosUser.html")

from sqlalchemy import text
#----------------------hospital login-----------------------

@app.route('/hospitallogin', methods=['POST', 'GET'])
def hospitallogin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = Hospitaluser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Success", "info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials", "danger")
            return render_template("hospitallogin.html")

    return render_template("hospitallogin.html")


#---------------------hospital data info----------------------

@app.route("/addhospitalinfo", methods=['POST', 'GET'])
def addhospitalinfo():
    email = current_user.email
    posts = Hospitaluser.query.filter_by(email=email).first()
    code = posts.hcode
    postsdata = Hospitaldata.query.filter_by(hcode=code).first()

    if request.method == "POST":
        hcode = request.form.get('hcode')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbed')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('ventbeds')
        hcode = hcode.upper()
        huser = Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser = Hospitaldata.query.filter_by(hcode=hcode).first()
        if hduser:
            flash("Data is already Present you can update it..", "primary")
            return render_template("hospitaldata.html")
        if huser:
            sql_query = text (f"INSERT INTO `hospitaldata` (`hcode`,`hname`,`normalbed`,`hicubed`,`icubed`,`vbed`) VALUES ('{hcode}','{hname}','{nbed}','{hbed}','{ibed}','{vbed}')")
            new_user = db.session.execute(sql_query)
            db.session.commit()
            # db.engine.execute(
            #     f"INSERT INTO `hospitaldata` (`hcode`,`hname`,`normalbed`,`hicubed`,`icubed`,`vbed`) VALUES ('{hcode}','{hname}','{nbed}','{hbed}','{ibed}','{vbed}')")
            flash("Data Is Added", "primary")
        else:
            flash("Hospital Code not Exist", "warning")

    return render_template("hospitaldata.html", postsdata=postsdata)


#----------------hospital data edit-----------------------

@app.route("/hedit/<string:id>", methods=['POST', 'GET'])
@login_required
def hedit(id):
    posts = Hospitaldata.query.filter_by(id=id).first()

    if request.method == "POST":
        hcode = request.form.get('hcode')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbed')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('ventbeds')
        hcode = hcode.upper()
        sql_query=text(f"UPDATE `hospitaldata` SET `hcode` ='{hcode}',`hname`='{hname}',`normalbed`='{nbed}',`hicubed`='{hbed}',`icubed`='{ibed}',`vbed`='{vbed}' WHERE `hospitaldata`.`id`={id}")
        new_user = db.session.execute(sql_query)
        db.session.commit()
        # db.engine.execute(
        #     f"UPDATE `hospitaldata` SET `hcode` ='{hcode}',`hname`='{hname}',`normalbed`='{nbed}',`hicubed`='{hbed}',`icubed`='{ibed}',`vbed`='{vbed}' WHERE `hospitaldata`.`id`={id}")
        # flash("Slot Updated", "info")
        return redirect("/addhospitalinfo")

    return render_template("hedit.html", posts=posts)


#----------------------hospital data delete---------------------

@app.route("/hdelete/<string:id>", methods=['POST', 'GET'])
@login_required
def hdelete(id):
    sql_query=text(f"DELETE FROM `hospitaldata` WHERE `hospitaldata`.`id`={id}")
    new_user = db.session.execute(sql_query)
    # db.engine.execute(
    #     f"DELETE FROM `hospitaldata` WHERE `hospitaldata`.`id`={id}")
    flash("Date Deleted", "danger")
    return redirect("/addhospitalinfo")
    # return redirect("/addhospitalinfo")


#*****************************   User/Patient pages *****************************************\

#-------------User signup page--------------
@app.route("/signup",methods=['POST','GET'])
def signup():
    if request.method == "POST":
        id = request.form.get('srf')
        email = request.form.get('email')
        dob = request.form.get('dob')
        #print(id,email,dob)
        encpassword = generate_password_hash(dob)

        user=User.query.filter_by(id=id).first()
        emailUser=User.query.filter_by(email=email).first()
        if user or emailUser:
            flash("Email or srif is already taken","warning")
            return render_template("userSignup.html")
        sql_query=text(f"INSERT INTO `user` (`id`,`email`,`dob`) VALUES ('{id}','{email}','{encpassword}') ")
        new_user = db.session.execute(sql_query)
        db.session.commit()
        flash("SignUp Success Please Login", "success")
        return render_template("userlogin.html")

    return render_template("userSignup.html")


#--------------------User login feedback ---------------------


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        srfid = request.form.get('srf')
        dob = request.form.get('dob')

        user = User.query.filter_by(srfid=srfid).first()
        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login succesful","info")
            return render_template("index.html")
        else:
            flash("Invalid credentials","danger")
            return render_template("userlogin.html")
        
    return render_template("userlogin.html")



#----------------patient bed booking-------------

@app.route("/slotbooking", methods=['POST', 'GET'])
@login_required
def slotbooking():
    # Retrieve all records from the hospitaldata table
    query = Hospitaldata.query.all()

    if request.method == "POST":
        id = request.form.get('id')
        bedtype = request.form.get('bedtype')
        hcode = request.form.get('hcode')
        spo2 = request.form.get('spo2')
        pname = request.form.get('pname')
        pphone = request.form.get('pphone')
        paddress = request.form.get('paddress')

        # Check if the hospital code exists in the Hospitaldata table
        check2 = Hospitaldata.query.filter_by(hcode=hcode).first()
        if not check2:
            flash("Enter Hospital Data ", "warning")
        else:
            # Update the bed count based on bed type
            if bedtype == "NormalBed":
                Hospitaldata.query.filter_by(hcode=hcode).update({Hospitaldata.normalbed: Hospitaldata.normalbed - 1})
            elif bedtype == "HICUBed":
                Hospitaldata.query.filter_by(hcode=hcode).update({Hospitaldata.hicubed: Hospitaldata.hicubed - 1})
            elif bedtype == "ICUBed":
                Hospitaldata.query.filter_by(hcode=hcode).update({Hospitaldata.icubed: Hospitaldata.icubed - 1})
            elif bedtype == "VENTILATORBed":
                Hospitaldata.query.filter_by(hcode=hcode).update({Hospitaldata.vbed: Hospitaldata.vbed - 1})

            # Check the bed availability after update
            check = Hospitaldata.query.filter_by(hcode=hcode).first()
            if check and check.normalbed >= 0 and check.hicubed >= 0 and check.icubed >= 0 and check.vbed >= 0:
                # If beds are available, book the slot
                sql_query = text("INSERT INTO bookingpatient (srfid, bedtype, hcode, spo2, pname, pphone, paddress) VALUES (:srfid, :bedtype, :hcode, :spo2, :pname, :pphone, :paddress)")
                db.session.commit()
                flash("Slot is Booked. Kindly Visit Hospital for Further Procedure", "success")
            else:
                flash("Beds are not available for the selected type", "danger")

    return render_template("booking.html", query=query)



#-----------------patient details--------------

@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.srfid
    print(code)
    data=Bookingpatient.query.filter_by(srfid=code).first()
    
    return render_template("details.html",data=data)


#-------------logout admin-----------

@app.route("/logoutadmin")
def logoutadmin():
    session.pop('user')
    flash("You are logout admin", "primary")

    return redirect('/admin')

#------------logout user--------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul", "warning")
    return redirect(url_for('login'))


#---------------triggered data-------------------

@app.route("/triggers")
def triggers():
    query=Trig.query.all() 
    return render_template("triggers.html",query=query)

#testing whether db is connected or not
@app.route("/test")
def test():
    
    try:
        a = Test.query.all()
        print(a)
        return 'My database is connected'
    except Exception as e:
        print(e)
        return f'database not connected {e}'

app.run(debug=True)


