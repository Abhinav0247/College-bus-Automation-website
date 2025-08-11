from flask import Flask, render_template, request, redirect, session, url_for, send_file
from flask_mysqldb import MySQL
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
from PIL import Image, ImageFile 
import io,os


ImageFile.LOAD_TRUNCATED_IMAGES = True
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'bus'

mysql = MySQL(app)

# Student registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        student_id = request.form['student_id']
        student_name = request.form['student_name']
        branch_name = request.form['branch_name']
        semester = request.form['semester']
        phone_no = request.form['phone_no']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO bus_user (student_id, student_name, branch_name, phone_no, password, sem) VALUES (%s, %s, %s, %s, %s, %s)", 
                    (student_id, student_name, branch_name, phone_no, password, semester))
        mysql.connection.commit()
        cur.close()
        return render_template("login.html")

# Home page
@app.route('/')
def home():
    return render_template("homepage.html")

# Student home page
@app.route('/main')
def main():
    return render_template("main.html")

# Admin home page
@app.route('/admin')
def admin():
    return render_template("admin.html")

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT student_id, password FROM bus_user WHERE student_id = %s", (student_id,))
        user = cur.fetchone()
        
        if user is not None and password == user[1]:
            session['student_id'] = user[0]
            cur.close() 
            return redirect(url_for('main'))
        
        if student_id == "admin" and password == "admin@123":
            session['student_id'] = student_id
            return redirect(url_for('admin'))
        
        cur.close()
        return render_template('login.html', error='Invalid student ID or password')
    
    return render_template('login.html')



@app.route('/updatebusreg', methods=['POST'])
def updatebusreg():
    if request.method == 'POST':
        student_id = session['student_id']
        place = request.form['place']
        route = request.form['route']
        feeamount = request.form['feeamount']
        academicyear = request.form['academicyear']
        email = request.form['email']
        
        # Handle image file upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                image_data = image_file.read()

                cur = mysql.connection.cursor()
                cur.execute("UPDATE bus_user SET place = %s, route = %s, fee = %s, academic_year = %s, email = %s, image = %s WHERE student_id = %s", 
                            (place, route, feeamount, academicyear, email, image_data, student_id))
                mysql.connection.commit()
                cur.close()

        return render_template("main.html")

    return redirect(url_for('index'))


import base64
@app.route('/buspass')
def buspass():
    student_id = session['student_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT student_name, branch_name, sem, place, academic_year, route, image FROM bus_user WHERE student_id = %s", 
                (student_id,))
    passdata = cur.fetchall()
    cur.close()

    # Convert BLOB data to base64
    passdata = [(student_name, branch_name, sem, place, academic_year, route, base64.b64encode(image).decode('utf-8')) for (student_name, branch_name, sem, place, academic_year, route, image) in passdata]

    return render_template("pass.html", passdata=passdata, student_id=student_id)


# Payment page
@app.route('/payment')
def payment():
    student_id = session['student_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT fee, paid, due FROM bus_user WHERE student_id = %s", (student_id,))
    feedata = cur.fetchall()
    cur.close()
    return render_template("payment.html", feedata=feedata)

# Bus registration page
@app.route('/busreg')
def busreg():
    return render_template("busreg.html")



# Contact page
@app.route('/contact')
def contact():
    return render_template("contact.html")

# Logout
@app.route('/logout')
def logout():
    session.pop('student_id', None)
    session.pop('bus_no', None)
    return render_template("homepage.html")

# Pay button redirect
@app.route('/paysbi')
def paysbi():
    return redirect("https://www.onlinesbi.sbi/sbicollect")

# Admin page payment update
@app.route('/updateinfo', methods=['GET', 'POST'])
def updateinfo():
    if request.method == 'GET':
        return render_template('admin.html')
    elif request.method == 'POST':
        student_id = request.form['student_id']
        paid = request.form['paid']
        due = request.form['due']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE bus_user SET paid = %s, due = %s WHERE student_id = %s", (paid, due, student_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('admin'))

# Student details
@app.route('/details')
def details():
    if 'student_id' not in session:
        return "Unauthorized", 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT student_id, password, student_name, branch_name, sem, place, route, phone_no, email, fee, paid, due FROM bus_user")
    students_data = cur.fetchall()
    cur.close()
    return render_template("details.html", students_data=students_data)

# Due students
@app.route('/due')
def due():
    if 'student_id' not in session:
        return "Unauthorized", 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT student_id, password, student_name, branch_name, sem, place, route, phone_no, email, fee, paid, due FROM bus_user WHERE fee != 0 AND due != 0")
    students_dat = cur.fetchall()
    cur.close()
    return render_template("due.html", students_dat=students_dat)

# Download bus pass

@app.route('/downloadpass', methods=['GET','POST'])
def downloadpass():
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT student_name, branch_name, sem, place, academic_year, route, image FROM bus_user WHERE student_id = %s", 
                (student_id,))
    passdata = cur.fetchone()
    cur.close()

    if not passdata:
        return "No data found for the student.", 404

    # Extract data
    student_name, branch_name, sem, place, academic_year, route, image_data = passdata

    # Save image data to a temporary file
    image_filename = f"student_image_{student_id}.jpg"
    with open(image_filename, 'wb') as img_file:
        img_file.write(image_data)

    # Generate PDF with ReportLab
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Draw background and border
    c.setFillColorRGB(255, 255, 255) 
    c.rect(0, 0, width, height, fill=1)
    c.setLineWidth(1)
    c.setFillColor("white")
    c.roundRect(30, height - 180, width - 60, 150, 10, stroke=1, fill=1)

    # Title and subtitle
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0, 0, 0.5)
    c.drawCentredString(width / 2, height - 180 + 60, "College of Engineering Trikaripur")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, height - 180 + 40, "Cheemeni, Kasaragod Dist-671313")

    # Main heading
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 200, "Student Bus Pass")

    # Student details
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 230, f"Name: {student_name}")
    c.drawString(50, height - 250, f"Student ID: {student_id}")
    c.drawString(50, height - 270, f"Branch: {branch_name}")
    c.drawString(50, height - 290, f"Semester: {sem}")
    c.drawString(50, height - 310, f"Place: {place}")
    c.drawString(50, height - 330, f"Academic Year: {academic_year}")
    c.drawString(50, height - 350, f"Route: {route}")
    c.drawString(50, height - 370, "Validity: MAY 2024")

    # Draw the image
    c.drawImage(image_filename, width - 160, height - 240, width=100, height=100)

    c.showPage()
    c.save()

    # Cleanup: delete the temporary image file
    os.remove(image_filename)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='bus_pass.pdf', mimetype='application/pdf')

# Bus update page
@app.route('/busupdate')
def busupdate():
    return render_template("busupdate.html")

# Bus info update function
@app.route('/updatebusinfo', methods=['GET', 'POST'])
def updatebusinfo():
    if request.method == 'GET':
        return render_template('busupdate.html')  
    elif request.method == 'POST':
        bus_no = request.form['bus_no']
        bus_route = request.form['bus_route']
        bus_fee = request.form['bus_fee']
        bus_time = request.form['bus_time']
        driver_name = request.form['driver_name']
        driver_no = request.form['driver_no']
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE bus_admin SET bus_route = %s, bus_fee = %s, bus_time = %s, driver_name = %s, driver_no = %s WHERE bus_no = %s", 
                    (bus_route, bus_fee, bus_time, driver_name, driver_no, bus_no))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('busupdate'))

# Bus look-up
@app.route('/buslook')
def buslook():
    # session['bus_no'] = bus_no
    # if 'bus_no' not in session:
    #     return "Unauthorized", 401

    # bus_no = session['bus_no']
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bus_admin")
    bus_data = cur.fetchall()
    cur.close()
    
    return render_template("buslook.html", bus_data=bus_data)

@app.route('/businfo')
def businfo():
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bus_admin")
    bus_data = cur.fetchall()
    cur.close()
    
    return render_template("businfo.html", bus_data=bus_data)


if __name__ == '__main__':
    app.run(debug=True)
