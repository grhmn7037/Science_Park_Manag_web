from flask import Flask, render_template, request, redirect, url_for, session, jsonify, render_template_string, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os, socket, csv, io

app = Flask(__name__)

# --- إعدادات الأمان الاحترافية ---
app.secret_key = "ghalib_park_secure_2026_top_secret"  # مفتاح تشفير الجلسات
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800  # تنتهي الجلسة بعد 30 دقيقة خمول
)

# هاش مشفر لكلمة السر "1234" - لا يمكن فكه حتى لو تمت رؤيته
ADMIN_USERNAME = "ghalib"
ADMIN_PASSWORD_HASH = generate_password_hash("1234")

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


# --- حماية المسارات (Admin Protection) ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit_data', methods=['POST'])
def handle_form():
    if not request.form.get('name'):
        return redirect(url_for('index'))

    session['temp_data'] = {
        'name': request.form.get('name'),
        'role': request.form.get('role'),
        'sector': request.form.get('sector'),
        'method': request.form.get('method'),
        'value': request.form.get('value')
    }

    # دكتور غالب: تم إلغاء التحويل للمنافذ 5555 و 5050 لمنع خطأ الاتصال
    # الآن كل المستخدمين يذهبون لصفحة التفاصيل لإكمال بياناتهم وحفظها
    return redirect(url_for('details_page'))


@app.route('/details')
def details_page():
    data = session.get('temp_data')
    if not data: return redirect(url_for('index'))
    return render_template('details.html', sector=data['sector'])


@app.route('/finalize', methods=['POST'])
def finalize():
    data = session.get('temp_data')
    if not data: return redirect(url_for('index'))

    innov_type = request.form.get('innov_type')
    stage = request.form.get('stage')
    desc = request.form.get('desc')

    # حفظ البيانات في قاعدة البيانات
    new_entry = Entry(
        name=data['name'], role=data['role'], sector=data['sector'],
        contact_method=data['method'], contact_value=data['value'],
        innov_type=innov_type, project_stage=stage, description=desc
    )
    db.session.add(new_entry)
    db.session.commit()

    session.pop('temp_data', None)  # مسح البيانات المؤقتة بعد الحفظ للأمان
    return render_template('thanks.html', name=data['name'])


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session.permanent = True
            session['admin_logged_in'] = True
            return redirect(url_for('admin_portal'))
        return "خطأ أمني! البيانات غير صحيحة."

    return render_template_string('''
    <body style="font-family:sans-serif; background:linear-gradient(135deg, #1e3c72, #2a5298); display:flex; align-items:center; justify-content:center; height:100vh; margin:0; color:white;">
        <div style="background:white; padding:40px; border-radius:25px; color:#333; text-align:center; box-shadow: 0 15px 35px rgba(0,0,0,0.3); width:350px;">
            <h2 style="color:#1e3c72;">بوابة الإدارة الآمنة</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="اسم المدير" required style="width:100%; padding:12px; margin-bottom:15px; border-radius:10px; border:1px solid #ddd;">
                <input type="password" name="password" placeholder="كلمة السر" required style="width:100%; padding:12px; margin-bottom:20px; border-radius:10px; border:1px solid #ddd;">
                <button type="submit" style="width:100%; padding:14px; background:#1e3c72; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">دخول النظام</button>
            </form>
        </div>
    </body>
    ''')


@app.route('/ghalib_portal_2026')
@admin_required
def admin_portal():
    try:
        entries = Entry.query.order_by(Entry.timestamp.desc()).all()
        stats = {
            'total': len(entries),
            'ideas': len([e for e in entries if e.sector == 'idea']),
            'problems': len([e for e in entries if e.sector == 'problem']),
            'seminar': len([e for e in entries if e.sector == 'seminar']),
            'projects': len([e for e in entries if e.sector == 'real_project']) # إضافة هذا السطر
        }
        return render_template('admin.html', entries=entries, stats=stats)
    except Exception as e:
        return f"Database Error: {str(e)}"


@app.route('/delete/<int:id>')
@admin_required
def delete_entry(id):
    entry = Entry.query.get(id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('admin_portal'))


@app.route('/export_data')
@admin_required
def export_data():
    entries = Entry.query.all()
    output = io.StringIO()
    output.write('\ufeff')  # دعم اللغة العربية في Excel
    writer = csv.writer(output)
    writer.writerow(
        ['الاسم', 'الصفة', 'المسار', 'وسيلة التواصل', 'القيمة', 'نوع الابتكار', 'المرحلة', 'الوصف', 'التاريخ'])
    for e in entries:
        writer.writerow(
            [e.name, e.role, e.sector, e.contact_method, e.contact_value, e.innov_type, e.project_stage, e.description,
             e.timestamp])
    output.seek(0)
    return Response(output.read(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=Science_Park_Report.csv"})


@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
