from flask import Flask, render_template, request, redirect, url_for, session, jsonify, render_template_string, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os, csv, io
from datetime import datetime

app = Flask(__name__)

# --- 1. إعدادات الأمان الاحترافية ---
app.secret_key = os.environ.get('SECRET_KEY', "ghalib_park_secure_2026_top_secret")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800
)

# --- 2. إعداد قاعدة البيانات بالمسار المطلق (طلبك الأخير لضمان العمل أونلاين) ---
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'science_park_final.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 3. إدارة الصلاحيات (Admin & Reviewers) ---
ADMIN_USERNAME = "ghalib"
# كلمة السر الافتراضية "ghalib2026"
ADMIN_PASSWORD_HASH = generate_password_hash("32768:8:1$tlk3jzFdLVU9P1hB$ee963a727beedec10de2c0619313cb89113b50884bc00c0b6d5f0d025efa9ca2b6955bceb79980c4385296f64dd256a6c81715705e68eaee6cde0b3c477121a4")

REVIEWERS_DATA = {
    'medical2026': {'role': 'مقيم طبي', 'sector': 'طبي'},
    'engineer2026': {'role': 'مقيم هندسي', 'sector': 'تقني'},
    'admin2026': {'role': 'مقيم إداري', 'sector': 'إداري'}
}


# --- 4. نماذج البيانات (Models) الشاملة لكل خصائص ECHO ---
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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)  # خاصة بسوق العمل

    # خصائص النظام البيئي المتقدمة
    status = db.Column(db.String(50), default='pending')
    score = db.Column(db.Integer, default=0)
    internal_notes = db.Column(db.Text)
    mentor_name = db.Column(db.String(100), default="لم يحدد بعد")
    incubation_path = db.Column(db.String(100), default="مرحلة التقييم")
    legal_status = db.Column(db.String(100), default="قيد المراجعة")


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100))
    problem_title = db.Column(db.String(200))
    problem_description = db.Column(db.Text)
    reward = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# --- 5. حماية المسارات (Decorators) ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated_function


def reviewer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'reviewer_role' not in session:
            return redirect(url_for('reviewer_login'))
        return f(*args, **kwargs)

    return decorated_function


# --- 6. المسارات التشغيلية (Routes) ---

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
    new_entry = Entry(
        name=data['name'], role=data['role'], sector=data['sector'],
        contact_method=data['method'], contact_value=data['value'],
        innov_type=request.form.get('innov_type'),
        project_stage=request.form.get('stage'),
        description=request.form.get('desc')
    )
    db.session.add(new_entry)
    db.session.commit()
    p_id = new_entry.id
    session.pop('temp_data', None)
    return render_template('thanks.html', name=data['name'], id=p_id)


# --- 7. بوابة الإدارة والمقيمين ---

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_portal'))
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
    entries = Entry.query.order_by(Entry.timestamp.desc()).all()
    stats = {
        'total': len(entries),
        'ideas': len([e for e in entries if e.sector == 'idea']),
        'problems': len([e for e in entries if e.sector == 'problem']),
        'seminar': len([e for e in entries if e.sector == 'seminar']),
        'projects': len([e for e in entries if e.sector == 'real_project']),
        'jobs': len([e for e in entries if e.sector == 'job'])
    }
    return render_template('admin.html', entries=entries, stats=stats)


@app.route('/update_entry/<int:id>', methods=['POST'])
def update_entry(id):
    if not session.get('admin_logged_in') and 'reviewer_role' not in session:
        return jsonify({"success": False}), 403
    entry = Entry.query.get_or_404(id)
    data = request.json
    if entry:
        if 'reviewer_role' in session:
            entry.mentor_name = session['reviewer_role']
            entry.status = 'review'
        # تحديث كافة الحقول الممكنة
        for key in ['status', 'score', 'mentor_name', 'incubation_path', 'legal_status', 'internal_notes']:
            if key in data: setattr(entry, key, data[key])
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 404


# --- 8. النظام البيئي الخارجي (Showroom, Jobs, Challenges) ---

@app.route('/showroom')
def showroom():
    projects = Entry.query.filter(Entry.status.in_(['approved', 'incubated'])).order_by(Entry.score.desc()).all()
    return render_template('showroom.html', projects=projects, stats={'total_featured': len(projects)})


@app.route('/project/<int:id>')
def project_detail(id):
    project = Entry.query.get_or_404(id)
    return render_template('project_profile.html', p=project)


@app.route('/job_market')
def job_market():
    approved_jobs = Entry.query.filter_by(sector='job', is_approved=True).order_by(Entry.timestamp.desc()).all()
    return render_template('job_market.html', jobs=approved_jobs)


@app.route('/challenges')
def challenges():
    all_c = Challenge.query.order_by(Challenge.timestamp.desc()).all()
    return render_template('challenges.html', challenges=all_c)


@app.route('/post_challenge', methods=['GET', 'POST'])
def post_challenge():
    if request.method == 'POST':
        new_c = Challenge(
            company_name=request.form.get('company_name'),
            problem_title=request.form.get('problem_title'),
            problem_description=request.form.get('problem_description'),
            reward=request.form.get('reward')
        )
        db.session.add(new_c)
        db.session.commit()
        return redirect(url_for('challenges'))
    return render_template('post_challenge.html')


# --- 9. التتبع والتحليلات والشهادات ---

@app.route('/track_status', methods=['GET', 'POST'])
def track_status():
    result = None
    if request.method == 'POST':
        result = Entry.query.filter_by(contact_value=request.form.get('phone')).first()
    return render_template('track.html', result=result)


@app.route('/analytics')
@admin_required
def analytics():
    entries = Entry.query.all()
    total = len(entries)
    if total == 0: return "No data."
    approved = len([e for e in entries if e.status == 'approved'])
    incubated = len([e for e in entries if e.status == 'incubated'])
    pending = len([e for e in entries if e.status == 'pending'])
    sectors = {
        'idea': len([e for e in entries if e.sector == 'idea']),
        'problem': len([e for e in entries if e.sector == 'problem']),
        'real_project': len([e for e in entries if e.sector == 'real_project']),
        'job': len([e for e in entries if e.sector == 'job'])
    }
    roles = {
        'student': len([e for e in entries if e.role == 'طالب']),
        'staff': len([e for e in entries if e.role == 'تدريسي']),
        'company': len([e for e in entries if e.role == 'شركة'])
    }
    avg_score = round(sum([e.score for e in entries]) / total, 1)
    top_innovators = Entry.query.filter(Entry.score > 0).order_by(Entry.score.desc()).limit(5).all()
    return render_template('analytics.html', total=total, approved=approved, incubated=incubated,
                           pending=pending, sectors=sectors, roles=roles, avg=avg_score, top_innovators=top_innovators)


@app.route('/certificate/<int:id>')
def view_certificate(id):
    p = Entry.query.get_or_404(id)
    if p.status not in ['approved', 'incubated']: return "Not approved.", 403
    return render_template('certificate.html', p=p, date=datetime.now().strftime('%Y-%m-%d'))


# --- 10. المقيمون العلميون ---

@app.route('/reviewer_login', methods=['GET', 'POST'])
def reviewer_login():
    if request.method == 'POST':
        code = request.form.get('access_code')
        if code in REVIEWERS_DATA:
            session['reviewer_role'] = REVIEWERS_DATA[code]['role']
            session['reviewer_sector'] = REVIEWERS_DATA[code]['sector']
            return redirect(url_for('reviewer_dashboard'))
    return render_template_string('''
        <body style="font-family:sans-serif; text-align:center; padding:100px; background:#1e3c72; color:white;">
            <img src="/static/kitab_logo.png" width="100">
            <h2>بوابة التقييم العلمي - حدائق العلوم</h2>
            <form method="POST">
                <input type="password" name="access_code" placeholder="أدخل رمز الوصول الخاص بالقسم" required style="padding:15px; border-radius:10px; border:none; width:300px;"><br><br>
                <button type="submit" style="padding:10px 30px; background:#f1c40f; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">دخول للمراجعة</button>
            </form>
        </body>
    ''')


@app.route('/reviewer_dashboard')
@reviewer_required
def reviewer_dashboard():
    entries = Entry.query.filter(Entry.innov_type.contains(session['reviewer_sector'])).all()
    return render_template('reviewer_admin.html', entries=entries, role=session['reviewer_role'])


# --- 11. الوظائف الإضافية ---

@app.route('/approve/<int:id>')
@admin_required
def approve_entry(id):
    entry = Entry.query.get(id)
    if entry: entry.is_approved = True; db.session.commit()
    return redirect(url_for('admin_portal'))


@app.route('/export_data')
@admin_required
def export_data():
    entries = Entry.query.all()
    output = io.StringIO();
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['الاسم', 'المسار', 'الحالة', 'التقييم', 'الموجه', 'الوصف'])
    for e in entries:
        safe_desc = f"'{e.description}" if str(e.description).startswith(('=', '+', '-', '@')) else e.description
        writer.writerow([e.name, e.sector, e.status, e.score, e.mentor_name, safe_desc])
    output.seek(0)
    return Response(output.read(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=Science_Park_Safe_Report.csv"})


@app.route('/delete/<int:id>')
@admin_required
def delete_entry(id):
    entry = Entry.query.get(id)
    if entry: db.session.delete(entry); db.session.commit()
    return redirect(url_for('admin_portal'))


@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)