from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SelectField
from wtforms import IntegerField
from flask_pymongo import PyMongo



app = Flask(__name__)

#config Mongodb
app.config["MONGO_URI"] = "mongodb://localhost:27017/myApp"
mongo = PyMongo(app)





# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Welcome123*'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


#Articles = Articles()

# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')





# Register Form Class


class RegistrationForm(Form):
    room_no = IntegerField('Room_number', [validators.Length(min=1, max=50)])
    block_no = IntegerField('Block_number', [validators.Length(min=4, max=25)])
    warden = SelectField('Preferred Warden',choices=[('Ram Nayak','Ram Nayak'),('Shyam Shetty','Shyam Shetty'),('Suma Rai','Suma Rai')])
    

@app.route('/register_room',methods=['GET','POST'])
def register_room():
    form = RegistrationForm(request.form) 
    if request.method=='GET':
       cur = mysql.connection.cursor()

   
       result = cur.execute("SELECT room_no,block_no FROM rooms WHERE alloc_status='unallocated'")

       room = cur.fetchall()

       if result > 0:
         return render_template('register_room.html', room=room,form=form)
       else:
         msg = 'No Room Is Empty'
         return render_template('register_room.html', msg=msg)
    # Close connection
       cur.close()
    
    else:
        
         room_no=form.room_no.data
         block_no=form.block_no.data
         warden=form.warden.data
         cur = mysql.connection.cursor()
         cur.execute("INSERT INTO room_alloc VALUES(%s, %s, %s,'unallocated')", ([session['username']], room_no, block_no))
         mysql.connection.commit()
         cur.execute("UPDATE users set warden=%s where username=%s", (warden,[session['username']]))
         mysql.connection.commit()
         cur.close()

         return redirect(url_for('dashboard'))

@app.route('/allot_room')
def allot_room():
    
    
       cur = mysql.connection.cursor()
       result = cur.execute("SELECT room_alloc.username,room_alloc.room_no,room_alloc.block_no,users.GPA FROM users,room_alloc WHERE room_alloc.username =users.username ORDER BY GPA DESC")
       students = cur.fetchall()
       if result > 0:
          return render_template('allot_room.html', students=students)
       else:
          msg = 'No request for rooms'
          return render_template('allot_room.html', msg=msg)
    # Close connection
       cur.close()
    
            



# User Register
class RegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=2, max=50)])
    second_name = StringField('Second Name', [validators.Length(min=1, max=25)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    username=StringField('Username', [validators.Length(min=4, max=25)])
    gender=StringField('Gender', [validators.Length(min=4, max=25)])
    GPA=IntegerField('GPA')
    contactno=StringField('Contact No.', [validators.Length(min=1, max=15)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password',)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        second_name = form.second_name.data
        last_name = form.last_name.data
        email = form.email.data
        username = form.username.data
        gender = form.gender.data
        GPA=form.GPA.data
        contactno = form.contactno.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(first_name, second_name, last_name, email,username,gender,GPA,contactno,password) VALUES(%s, %s, %s, %s ,%s ,%s,%s,%s,%s)", (first_name, second_name, last_name, email,username,gender,GPA,contactno,password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                


                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/Warden_login', methods=['GET', 'POST'])
def warden_login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM warden WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if password_candidate==password:
                # Passed
                session['logged_in'] = True
                session['username'] = username
                


                flash('You are now logged in', 'success')
                return redirect(url_for('warden_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('Warden_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('Warden_login.html', error=error)

    return render_template('Warden_login.html') 

@app.route('/allot/<string:id>', methods=['POST'])
def allot(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("UPDATE rooms SET alloc_status='allocated' WHERE room_no=%s",[id])

    

    # Commit to DB


    cur.execute("UPDATE room_alloc set stat='allocated' where room_no=%s",[id])


    cur.execute("UPDATE rooms join room_alloc on rooms.room_no=room_alloc.room_no set rooms.username=room_alloc.username where room_alloc.stat='allocated'")   
    mysql.connection.commit()
    
    #Close connection
    cur.close()

    flash('Room Alloted', 'success')

    return redirect(url_for('warden_dashboard'))




# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

   
    result = cur.execute("SELECT * FROM users WHERE username = %s", [session['username']])

    users = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', users=users)
    else:
        msg = 'No User Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()


@app.route('/warden_dashboard')
@is_logged_in
def warden_dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

     
    result = cur.execute("SELECT * FROM warden WHERE username = %s", [session['username']])

    wardens = cur.fetchall()

    if result > 0:
        return render_template('warden_dashboard.html', wardens=wardens)
    else:
        msg = 'No User Found'
        return render_template('warden_dashboard.html', msg=msg)
    # Close connection
    cur.close()    



@app.route('/room_info')
def room_info():
     
       cur=mysql.connection.cursor() 

       result=cur.execute("SELECT * from rooms where username=%s",[session['username']])

       if result > 0:
            # Get stored hash
            data = cur.fetchall()
            return render_template('room_info.html',data=data)
            
        
       else:
            error = 'Room has not been allocated yet'
            return render_template('room_info.html', error=error)

       cur.close()

class messform(FlaskForm):
   type=SelectField('Type',choices=[('Veg','Veg'),('Non_Veg','Non_Veg')])
   super=SelectField('Supervisor',choices=[('Ram','Ram'),('Shyam','Shyam'),('Gopal','Gopal'),('Vishnu','Vishnu')])



@app.route("/mess",methods=['GET','POST'])
def mess():
    form=messform(request.form)
    if request.method=='GET':
      vmenu = mongo.db.menu_veg.find({})
      nmenu = mongo.db.menu_nonveg.find({})
      return render_template("mess.html",
        vmenu=vmenu,nmenu=nmenu,form=form)
    else:
         type=form.type.data
         super=form.super.data
         cur = mysql.connection.cursor()
         cur.execute("INSERT INTO  mess VALUES(%s, %s)",(type, super))
         mysql.connection.commit()
         cur.execute("UPDATE users set mess_type=%s where username=%s",(type,[session['username']]))
         mysql.connection.commit()
         cur.close()

         return redirect(url_for('dashboard'))



class attendanceform(FlaskForm):
   studname=StringField('Student Name', [validators.Length(min=2, max=50)])
   date=StringField('Attend Date', [validators.Length(min=2, max=50)])
   present=SelectField('Is Present',choices=[('present','Yes'),('absent','No')])
   remark=StringField('Remark', [validators.Length(min=0, max=50)])



@app.route("/attendance",methods=['GET','POST'])
def attendance():
    form=attendanceform(request.form)
    if request.method=='GET':
       
            return render_template('attendance.html', form=form)
       


    else:   

         
        studname = form.studname.data
        date = form.date.data
        present = form.present.data
        remark = form.remark.data
        

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO attendance(username, _date, status,remark) VALUES(%s, %s, %s, %s )", (studname, date, present, remark))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        
        return redirect(url_for('warden_dashboard'))
   


   



@app.route("/attendance_info")
def attendance_info():
   
        cur = mysql.connection.cursor()

   
        result = cur.execute("SELECT * FROM attendance where username=%s ",[session['username']])

        att_details = cur.fetchall()

        if result > 0:
            return render_template('attendance_info.html', details=att_details)
        else:
            msg = 'Attendance not marked yet'
            return render_template('attendance_info.html', msg=msg)
    # Close connection
        cur.close()



@app.route("/attendance_view")
def attendance_view():
   
        cur = mysql.connection.cursor()

   
        result = cur.execute("SELECT * FROM attendance")

        att_details = cur.fetchall()

        if result > 0:
            return render_template('attendance_view.html', details=att_details)
        else:
            msg = 'Attendance not marked yet'
            return render_template('attendance_view.html', msg=msg)
    # Close connection
        cur.close()   


class paymentform(FlaskForm):
   date=StringField('Payment Date', [validators.Length(min=2, max=50)])
   paid_by=SelectField('Paid By', choices=[('Bank','Bank'),('DBBL','DBBL'),('Bkash','Bkash')])
   mobile_no=IntegerField('Transaction no. or mobile no.')
   amount=StringField('Amount')



@app.route("/payment",methods=['GET','POST'])
def payment():
    
    cur = mysql.connection.cursor()
    result=cur.execute("select mess_type from users where username=%s", [session['username']])
    data = cur.fetchone()
    t = data['mess_type']
    if t=='Veg':
       amt='50000'
    elif t=='Non_Veg':
       amt='75000'
    else:
       amt='25000'

    cur.close()
    form=paymentform(request.form)
    form.amount.data=amt
    if request.method=='GET':
            
            return render_template('payment.html', form=form)
       


    else:   

         
        date = form.date.data
        paid_by = form.paid_by.data
        mobile_no = form.mobile_no.data
        

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO fee( _date,paid_by,transaction_no,amount) VALUES(%s, %s, %s, %s )", (date, paid_by, mobile_no, amt))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        
        return redirect(url_for('warden_dashboard'))
             


    
   
       
    
 
        
         




if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)



