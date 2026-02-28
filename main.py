from flask import Flask, render_template, request, redirect, url_for, session, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os, socket, time

app = Flask(__name__)
# --- ثوابت الدخول (يمكنك تغييرها لاحقاً) ---
ADMIN_USERNAME = "ghalib"  # اسم المدير
ADMIN_PASSWORD = "1234"  # كلمة السر

app.secret_key = "ghalib_premium_2026"

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///science_park_final.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    role = db.Column(db.String(50))
    sector = db.Column(db.String(50))
    contact_method = db.Column(db.String(50))
    contact_value = db.Column(db.String(100))
    innov_type = db.Column(db.String(100))
    project_stage = db.Column(db.String(100))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except: ip = '127.0.0.1'
    finally: s.close()
    return ip

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_data', methods=['POST'])
def handle_form():
    session['temp_data'] = {
        'name': request.form.get('name'),
        'role': request.form.get('role'),
        'sector': request.form.get('sector'),
        'method': request.form.get('method'),
        'value': request.form.get('value')
    }
    local_ip = get_local_ip()
    sector = session['temp_data']['sector']

    if sector == 'real_project':
        save_to_db(session['temp_data'], "N/A", "N/A", "Direct Access")
        return redirect(f"http://{local_ip}:5555")
    elif sector == 'seminar':
        save_to_db(session['temp_data'], "N/A", "N/A", "Seminar Participant")
        return redirect(f"http://{local_ip}:5050/join")
    else:
        return redirect(url_for('details_page'))

@app.route('/details')
def details_page():
    data = session.get('temp_data')
    return render_template('details.html', sector=data['sector'])

@app.route('/finalize', methods=['POST'])
def finalize():
    data = session.get('temp_data')
    innov_type = request.form.get('innov_type')
    stage = request.form.get('stage')
    desc = request.form.get('desc')
    save_to_db(data, innov_type, stage, desc)
    return render_template('thanks.html', name=data['name'])

def save_to_db(data, innov_type, stage, desc):
    new_entry = Entry(
        name=data['name'], role=data['role'], sector=data['sector'],
        contact_method=data['method'], contact_value=data['value'],
        innov_type=innov_type, project_stage=stage, description=desc
    )
    db.session.add(new_entry)
    db.session.commit()

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # التحقق من الاسم وكلمة السر معاً
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_portal'))
        else:
            return '''
                <div style="text-align:center; padding:50px; font-family:sans-serif;">
                    <h2 style="color:red;">خطأ في بيانات الدخول!</h2>
                    <p>الاسم أو كلمة السر غير صحيحة.</p>
                    <a href="/admin_login" style="color:blue;">حاول مرة أخرى</a>
                </div>
            '''

    # واجهة دخول احترافية تحتوي على حقلين
    return render_template_string('''
    <body style="font-family:'Segoe UI', sans-serif; background:linear-gradient(135deg, #1e3c72, #2a5298); display:flex; align-items:center; justify-content:center; height:100vh; margin:0; color:white;">
        <div style="background:white; padding:40px; border-radius:25px; color:#333; text-align:center; box-shadow: 0 15px 35px rgba(0,0,0,0.3); width:350px;">
            <img src="/static/kitab_logo.png" style="width:100px; margin-bottom:15px;">
            <h2 style="color:#1e3c72; margin-bottom:20px;">نظام إدارة القسم</h2>

            <form method="POST">
                <div style="text-align:right; margin-bottom:5px; font-size:14px; color:#666;">اسم المدير:</div>
                <input type="text" name="username" placeholder="Admin Name" required 
                       style="width:100%; padding:12px; margin-bottom:15px; border-radius:10px; border:1px solid #ddd; box-sizing:border-box; font-size:16px;">

                <div style="text-align:right; margin-bottom:5px; font-size:14px; color:#666;">كلمة السر:</div>
                <input type="password" name="password" placeholder="Password" required 
                       style="width:100%; padding:12px; margin-bottom:20px; border-radius:10px; border:1px solid #ddd; box-sizing:border-box; font-size:16px;">

                <button type="submit" 
                        style="width:100%; padding:14px; background:linear-gradient(to right, #1e3c72, #2a5298); color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size:16px; transition:0.3s;">
                    دخول المنصة الأمنة
                </button>
            </form>
            <div style="margin-top:20px; font-size:11px; color:#999;">بوابة حدائق العلوم والتكنولوجيا - جامعة الكتاب</div>
        </div>
    </body>
    ''')

@app.route('/ghalib_portal_2026')
def admin_portal():
    # 1. التأكد من تسجيل الدخول
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    try:
        # 2. جلب البيانات من قاعدة البيانات
        entries = Entry.query.order_by(Entry.timestamp.desc()).all()

        # 3. حساب الإحصائيات للوحة التحكم
        stats = {
            'total': len(entries),
            'ideas': len([e for e in entries if e.sector == 'idea']),
            'problems': len([e for e in entries if e.sector == 'problem']),
            'seminar': len([e for e in entries if e.sector == 'seminar'])
        }

        # 4. إرجاع الصفحة (السطر الأهم لعدم حدوث الخطأ)
        return render_template('admin.html', entries=entries, stats=stats)

    except Exception as e:
        # في حال حدوث خطأ في قاعدة البيانات، يظهر تنبيه بدلاً من انهيار السيرفر
        return f"Database Error: {str(e)}"

@app.route('/admin_logout')
def admin_logout():
    # مسح حالة الدخول من المتصفح
    session.pop('admin_logged_in', None)
    # التوجه فوراً إلى الصفحة الرئيسية (index)
    return redirect(url_for('index'))

    # --- تحديث: حذف سجل من قاعدة البيانات ---
    @app.route('/delete/<int:id>')
    def delete_entry(id):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        entry = Entry.query.get(id)
        if entry:
            db.session.delete(entry)
            db.session.commit()
        return redirect(url_for('admin_portal'))

    # --- تحديث: تصدير البيانات إلى ملف CSV (Excel) ---
    @app.route('/export_data')
    def export_data():
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))

        import csv, io
        from flask import Response

        entries = Entry.query.all()
        output = io.StringIO()
        # إضافة علامة BOM لضمان ظهور اللغة العربية بشكل صحيح في Excel
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(
            ['الاسم', 'الصفة', 'المسار', 'وسيلة التواصل', 'القيمة', 'نوع الابتكار', 'المرحلة', 'الوصف', 'التاريخ'])

        for e in entries:
            writer.writerow([e.name, e.role, e.sector, e.contact_method, e.contact_value, e.innov_type, e.project_stage,
                             e.description, e.timestamp])

        output.seek(0)
        return Response(output.read(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment;filename=science_park_report.csv"})

    # بقية كود الجلب والإحصائيات كما هو...
# # تسجيل الخروج (للأمان)
# @app.route('/admin_login', methods=['GET', 'POST'])
# def admin_login():
#     if request.method == 'POST':
#         pw = request.form.get('password')
#         if pw == ADMIN_PASSWORD:
#             session['admin_logged_in'] = True
#             return redirect(url_for('admin_portal'))
#         else:
#             return "كلمة السر خاطئة! <a href='/admin_login'>حاول ثانية</a>"
#
#     return render_template_string('''
#     <body style="font-family:sans-serif; background:linear-gradient(135deg, #1e3c72, #2a5298); display:flex; align-items:center; justify-content:center; height:100vh; margin:0; color:white;">
#         <div style="background:white; padding:30px; border-radius:20px; color:#333; text-align:center; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
#             <img src="/static/kitab_logo.png" style="width:80px; margin-bottom:10px;">
#             <h2 style="color:#1e3c72;">دخول المدير</h2>
#             <form method="POST">
#                 <input type="password" name="password" placeholder="أدخل كلمة السر" required style="width:100%; padding:12px; margin:10px 0; border-radius:10px; border:1px solid #ddd; box-sizing:border-box;">
#                 <button type="submit" style="width:100%; padding:12px; background:#1e3c72; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">دخول النظام</button>
#             </form>
#         </div>
#     </body>
#     ''')
# --- تحديث: حذف سجل من قاعدة البيانات ---
@app.route('/delete/<int:id>')
def delete_entry(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    entry = Entry.query.get(id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('admin_portal'))


# --- تحديث: تصدير البيانات إلى ملف CSV (Excel) ---
@app.route('/export_data')
def export_data():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    import csv, io
    from flask import Response

    entries = Entry.query.all()
    output = io.StringIO()
    # إضافة علامة BOM لضمان ظهور اللغة العربية بشكل صحيح في Excel
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(
        ['الاسم', 'الصفة', 'المسار', 'وسيلة التواصل', 'القيمة', 'نوع الابتكار', 'المرحلة', 'الوصف', 'التاريخ'])

    for e in entries:
        writer.writerow(
            [e.name, e.role, e.sector, e.contact_method, e.contact_value, e.innov_type, e.project_stage, e.description,
             e.timestamp])

    output.seek(0)
    return Response(output.read(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=science_park_report.csv"})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)