import os
import sqlite3
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ecopulse-local-secret')
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')

CATEGORIES = ['Plastic', 'Paper', 'Glass', 'Metal', 'Organic', 'E-Waste', 'Other']


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db:
        db.close()


def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'volunteer', points INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT, location TEXT NOT NULL, event_date TEXT NOT NULL, start_time TEXT, end_time TEXT, max_volunteers INTEGER DEFAULT 50, target_waste REAL DEFAULT 100, category TEXT, difficulty TEXT, equipment TEXT, status TEXT DEFAULT 'Upcoming', image TEXT, created_by INTEGER REFERENCES users(id), created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS event_registrations (id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, emergency_contact TEXT, preferred_task TEXT, available_time TEXT, registered_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(event_id, user_id));
    CREATE TABLE IF NOT EXISTS waste_collection (id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE, category TEXT NOT NULL, quantity REAL NOT NULL, recorded_by INTEGER REFERENCES users(id), recorded_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(event_id, category));
    CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, event_id INTEGER REFERENCES events(id) ON DELETE CASCADE, name TEXT NOT NULL, user_id INTEGER REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS event_images (id INTEGER PRIMARY KEY, event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE, image_url TEXT NOT NULL, caption TEXT, image_type TEXT DEFAULT 'after', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS volunteer_points (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, event_id INTEGER REFERENCES events(id) ON DELETE SET NULL, points INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS badges (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, name TEXT NOT NULL, icon TEXT NOT NULL, UNIQUE(user_id, name));
    CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, message TEXT NOT NULL, is_read INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    if db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        db.execute('INSERT INTO users (name,email,phone,password,role,points) VALUES (?,?,?,?,?,?)', ('Asha Organizer', 'admin@ecopulse.local', '9000000000', generate_password_hash('admin123'), 'admin', 680))
        volunteers = [('Nila Green', 'nila@ecopulse.local', '9000000001', 420), ('Arun Kumar', 'arun@ecopulse.local', '9000000002', 275), ('Meera Shah', 'meera@ecopulse.local', '9000000003', 190)]
        for name, email, phone, points in volunteers:
            db.execute('INSERT INTO users (name,email,phone,password,role,points) VALUES (?,?,?,?,?,?)', (name, email, phone, generate_password_hash('volunteer123'), 'volunteer', points))
        admin_id = db.execute('SELECT id FROM users WHERE email=?', ('admin@ecopulse.local',)).fetchone()['id']
        samples = [
            ('Marina Beach Clean-Up', 'A sunrise shoreline sweep with sorting stations and a community breakfast.', 'Chennai', '2026-09-15', '06:30', '10:00', 100, 500, 'Beach Cleaning', 'Medium', 'Gloves, sacks, water bottles', 'Ongoing', 'https://images.unsplash.com/photo-1559027615-cd4628902d4a?auto=format&fit=crop&w=1200&q=85'),
            ('Community Park Cleaning', 'Restore the walking trails and give the neighborhood park room to breathe.', 'Coimbatore', '2026-09-21', '07:00', '10:30', 70, 300, 'Park Cleaning', 'Easy', 'Rakes, gloves, wheelbarrows', 'Upcoming', 'https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?auto=format&fit=crop&w=1200&q=85'),
            ('River Bank Clean-Up', 'A focused river-edge collection and waste segregation drive.', 'Madurai', '2026-10-04', '06:00', '09:30', 85, 400, 'River Cleaning', 'Hard', 'Boots, nets, first-aid kit', 'Upcoming', 'https://images.unsplash.com/photo-1618477461853-cf6ed80faba5?auto=format&fit=crop&w=1200&q=85'),
            ('Plastic-Free Street Drive', 'Help local shops and residents reset a busy market street.', 'Trichy', '2026-08-30', '08:00', '11:00', 50, 250, 'Plastic Collection', 'Easy', 'Tongs, bags, sorting labels', 'Completed', 'https://images.unsplash.com/photo-1604187351574-c75ca79f5807?auto=format&fit=crop&w=1200&q=85')]
        for sample in samples:
            db.execute('INSERT INTO events (name,description,location,event_date,start_time,end_time,max_volunteers,target_waste,category,difficulty,equipment,status,image,created_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (*sample, admin_id))
        event_ids = [row['id'] for row in db.execute('SELECT id FROM events ORDER BY id')]
        db.executemany('INSERT INTO waste_collection (event_id,category,quantity,recorded_by) VALUES (?,?,?,?)', [(event_ids[0], 'Plastic', 180, admin_id), (event_ids[0], 'Paper', 70, admin_id), (event_ids[0], 'Glass', 55, admin_id), (event_ids[1], 'Organic', 110, admin_id), (event_ids[1], 'Plastic', 40, admin_id), (event_ids[3], 'Plastic', 210, admin_id)])
        user_ids = [row['id'] for row in db.execute('SELECT id FROM users WHERE role="volunteer" ORDER BY id')]
        db.executemany('INSERT INTO event_registrations (event_id,user_id,preferred_task,available_time) VALUES (?,?,?,?)', [(event_ids[0], user_ids[0], 'Plastic Collection', 'Morning'), (event_ids[0], user_ids[1], 'Waste Sorting', 'Morning'), (event_ids[1], user_ids[2], 'Organic Collection', 'Morning'), (event_ids[3], user_ids[0], 'Transportation', 'Morning')])
        db.executemany('INSERT INTO badges (user_id,name,icon) VALUES (?,?,?)', [(user_ids[0], 'Community Hero', '✦'), (user_ids[0], 'Green Starter', '✿'), (user_ids[1], 'Green Starter', '✿')])
        db.commit()


def current_user():
    if 'user_id' not in session:
        return None
    return get_db().execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()


@app.context_processor
def inject_globals():
    return {'current_user': current_user(), 'categories': CATEGORIES, 'year': datetime.now().year}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('Please sign in to continue.', 'info')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user['role'] != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def event_stats(event):
    db = get_db()
    collected = db.execute('SELECT COALESCE(SUM(quantity),0) AS total FROM waste_collection WHERE event_id=?', (event['id'],)).fetchone()['total']
    volunteers = db.execute('SELECT COUNT(*) AS total FROM event_registrations WHERE event_id=?', (event['id'],)).fetchone()['total']
    progress = min(100, round((collected / event['target_waste']) * 100)) if event['target_waste'] else 0
    return {'collected': collected, 'volunteers': volunteers, 'progress': progress}


@app.route('/')
def index():
    db = get_db()
    events = db.execute('SELECT * FROM events ORDER BY event_date LIMIT 3').fetchall()
    featured = [{**dict(event), **event_stats(event)} for event in events]
    stats = {'events': db.execute('SELECT COUNT(*) FROM events').fetchone()[0], 'volunteers': db.execute('SELECT COUNT(*) FROM users WHERE role="volunteer"').fetchone()[0], 'waste': db.execute('SELECT COALESCE(SUM(quantity),0) FROM waste_collection').fetchone()[0], 'locations': db.execute('SELECT COUNT(DISTINCT location) FROM events').fetchone()[0]}
    return render_template('index.html', featured=featured, stats=stats)


@app.route('/events')
def events():
    db = get_db()
    query = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    sql = 'SELECT * FROM events WHERE (name LIKE ? OR location LIKE ? OR category LIKE ?)'
    params = [f'%{query}%', f'%{query}%', f'%{query}%']
    if status:
        sql += ' AND status=?'; params.append(status)
    sql += ' ORDER BY event_date'
    rows = db.execute(sql, params).fetchall()
    event_list = [{**dict(e), **event_stats(e)} for e in rows]
    return render_template('events.html', events=event_list, query=query, selected_status=status)


@app.route('/events/<int:event_id>')
def event_details(event_id):
    db = get_db(); event = db.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    if not event: abort(404)
    waste = db.execute('SELECT category, quantity FROM waste_collection WHERE event_id=? ORDER BY quantity DESC', (event_id,)).fetchall()
    registered = db.execute('SELECT u.id, u.name, r.preferred_task FROM event_registrations r JOIN users u ON u.id=r.user_id WHERE r.event_id=?', (event_id,)).fetchall()
    tasks = db.execute('SELECT t.*, u.name AS volunteer_name FROM tasks t LEFT JOIN users u ON u.id=t.user_id WHERE t.event_id=? ORDER BY t.name', (event_id,)).fetchall()
    gallery = db.execute('SELECT * FROM event_images WHERE event_id=? ORDER BY created_at DESC', (event_id,)).fetchall()
    return render_template('event_details.html', event=event, stats=event_stats(event), waste=waste, registered=registered, tasks=tasks, gallery=gallery)


@app.route('/events/<int:event_id>/join', methods=['POST'])
@login_required
def join_event(event_id):
    user = current_user()
    if user['role'] != 'volunteer': abort(403)
    db = get_db()
    try:
        db.execute('INSERT INTO event_registrations (event_id,user_id,emergency_contact,preferred_task,available_time) VALUES (?,?,?,?,?)', (event_id, user['id'], request.form.get('emergency_contact'), request.form.get('preferred_task'), request.form.get('available_time')))
        db.execute('UPDATE users SET points=points+20 WHERE id=?', (user['id'],))
        event = db.execute('SELECT name FROM events WHERE id=?', (event_id,)).fetchone()
        db.execute('INSERT INTO notifications (user_id,message) VALUES (?,?)', (user['id'], f'You successfully joined {event["name"]}.'))
        db.commit(); flash('You are registered. Your community is counting on you!', 'success')
    except sqlite3.IntegrityError:
        flash('You are already registered for this clean-up.', 'info')
    return redirect(url_for('event_details', event_id=event_id))


@app.route('/create-event', methods=['GET', 'POST'])
@admin_required
def create_event():
    if request.method == 'POST':
        form = request.form
        if not form.get('name') or not form.get('location') or not form.get('event_date'):
            flash('Name, location and date are required.', 'error'); return render_template('create_event.html')
        db = get_db()
        db.execute('INSERT INTO events (name,description,location,event_date,start_time,end_time,max_volunteers,target_waste,category,difficulty,equipment,status,image,created_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (form['name'], form.get('description'), form['location'], form['event_date'], form.get('start_time'), form.get('end_time'), form.get('max_volunteers', 50), form.get('target_waste', 100), form.get('category'), form.get('difficulty'), form.get('equipment'), 'Upcoming', form.get('image') or 'https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?auto=format&fit=crop&w=1200&q=85', session['user_id']))
        db.commit(); flash('Clean-up event published.', 'success'); return redirect(url_for('events'))
    return render_template('create_event.html')


@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    db = get_db(); event = db.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    if not event: abort(404)
    if request.method == 'POST':
        form = request.form
        db.execute('''UPDATE events SET name=?, description=?, location=?, event_date=?, start_time=?, end_time=?,
            max_volunteers=?, target_waste=?, category=?, difficulty=?, equipment=?, status=?, image=? WHERE id=?''',
            (form['name'], form.get('description'), form['location'], form['event_date'], form.get('start_time'),
             form.get('end_time'), form.get('max_volunteers', 50), form.get('target_waste', 100), form.get('category'),
             form.get('difficulty'), form.get('equipment'), form.get('status', 'Upcoming'), form.get('image') or event['image'], event_id))
        db.commit(); flash('Event details updated.', 'success'); return redirect(url_for('event_details', event_id=event_id))
    return render_template('create_event.html', event=event, editing=True)


@app.route('/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event(event_id):
    db = get_db(); db.execute('DELETE FROM events WHERE id=?', (event_id,)); db.commit()
    flash('Event removed from the calendar.', 'success'); return redirect(url_for('events'))


@app.route('/events/<int:event_id>/manage')
@admin_required
def manage_event(event_id):
    db = get_db(); event = db.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    if not event: abort(404)
    registered = db.execute('SELECT u.id, u.name FROM event_registrations r JOIN users u ON u.id=r.user_id WHERE r.event_id=?', (event_id,)).fetchall()
    tasks = db.execute('SELECT t.*, u.name AS volunteer_name FROM tasks t LEFT JOIN users u ON u.id=t.user_id WHERE t.event_id=?', (event_id,)).fetchall()
    gallery = db.execute('SELECT * FROM event_images WHERE event_id=? ORDER BY created_at DESC', (event_id,)).fetchall()
    return render_template('manage_event.html', event=event, registered=registered, tasks=tasks, gallery=gallery)


@app.route('/events/<int:event_id>/tasks', methods=['POST'])
@admin_required
def manage_tasks(event_id):
    db = get_db(); task_name = request.form.get('task_name', '').strip(); user_id = request.form.get('user_id') or None
    if task_name:
        db.execute('INSERT INTO tasks (event_id,name,user_id) VALUES (?,?,?)', (event_id, task_name, user_id))
        if user_id:
            db.execute('INSERT INTO notifications (user_id,message) VALUES (?,?)', (user_id, f'You were assigned to {task_name}.'))
        db.commit(); flash('Task assigned.', 'success')
    return redirect(url_for('event_details', event_id=event_id))


@app.route('/events/<int:event_id>/gallery', methods=['POST'])
@admin_required
def add_gallery_image(event_id):
    image_url = request.form.get('image_url', '').strip()
    if image_url:
        db = get_db(); db.execute('INSERT INTO event_images (event_id,image_url,caption,image_type) VALUES (?,?,?,?)', (event_id, image_url, request.form.get('caption'), request.form.get('image_type', 'after'))); db.commit(); flash('Gallery image added.', 'success')
    return redirect(url_for('event_details', event_id=event_id))


@app.route('/waste-tracker', methods=['GET', 'POST'])
@admin_required
def waste_tracker():
    db = get_db()
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        for category in CATEGORIES:
            value = request.form.get(category, '').strip()
            if value:
                db.execute('INSERT INTO waste_collection (event_id,category,quantity,recorded_by) VALUES (?,?,?,?) ON CONFLICT(event_id,category) DO UPDATE SET quantity=excluded.quantity, recorded_by=excluded.recorded_by', (event_id, category, float(value), session['user_id']))
        db.commit(); flash('Waste records updated.', 'success')
    events_data = [{**dict(e), **event_stats(e)} for e in db.execute('SELECT * FROM events ORDER BY event_date DESC').fetchall()]
    selected = request.args.get('event_id', events_data[0]['id'] if events_data else None)
    breakdown = db.execute('SELECT category,quantity FROM waste_collection WHERE event_id=?', (selected,)).fetchall() if selected else []
    return render_template('waste_tracker.html', events=events_data, selected=selected, breakdown=breakdown)


@app.route('/dashboard')
@admin_required
def dashboard():
    db = get_db(); rows = db.execute('SELECT * FROM events ORDER BY event_date').fetchall()
    all_stats = [event_stats(e) for e in rows]
    data = {'total_events': len(rows), 'upcoming': sum(e['status']=='Upcoming' for e in rows), 'active': sum(e['status']=='Ongoing' for e in rows), 'completed': sum(e['status']=='Completed' for e in rows), 'volunteers': db.execute('SELECT COUNT(*) FROM users WHERE role="volunteer"').fetchone()[0], 'waste': db.execute('SELECT COALESCE(SUM(quantity),0) FROM waste_collection').fetchone()[0], 'locations': db.execute('SELECT COUNT(DISTINCT location) FROM events').fetchone()[0]}
    categories = db.execute('SELECT category, SUM(quantity) total FROM waste_collection GROUP BY category ORDER BY total DESC').fetchall()
    return render_template('dashboard.html', data=data, events=rows, categories=categories)


@app.route('/impact')
def impact():
    db = get_db(); total = db.execute('SELECT COALESCE(SUM(quantity),0) FROM waste_collection').fetchone()[0]; plastic = db.execute('SELECT COALESCE(SUM(quantity),0) FROM waste_collection WHERE category="Plastic"').fetchone()[0]; volunteers = db.execute('SELECT COUNT(*) FROM users WHERE role="volunteer"').fetchone()[0]; completed = db.execute('SELECT COUNT(*) FROM events WHERE status="Completed"').fetchone()[0]
    score = round(total * 2 + volunteers * 18 + completed * 50)
    return render_template('impact.html', total=total, plastic=plastic, volunteers=volunteers, completed=completed, score=score)


@app.route('/leaderboard')
def leaderboard():
    db = get_db(); leaders = db.execute('SELECT u.name,u.points,COUNT(r.id) events_joined FROM users u LEFT JOIN event_registrations r ON r.user_id=u.id WHERE u.role="volunteer" GROUP BY u.id ORDER BY u.points DESC').fetchall()
    return render_template('leaderboard.html', leaders=leaders)


@app.route('/profile')
@login_required
def profile():
    db = get_db(); user = current_user(); joined = db.execute('SELECT e.*, r.registered_at FROM event_registrations r JOIN events e ON e.id=r.event_id WHERE r.user_id=? ORDER BY e.event_date DESC', (user['id'],)).fetchall(); badges = db.execute('SELECT * FROM badges WHERE user_id=?', (user['id'],)).fetchall()
    notifications = db.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 6', (user['id'],)).fetchall()
    return render_template('profile.html', user=user, joined=joined, badges=badges, notifications=notifications)


@app.route('/report/<int:event_id>')
@admin_required
def report(event_id):
    db = get_db(); event = db.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    if not event: abort(404)
    return render_template('report.html', event=event, stats=event_stats(event), waste=db.execute('SELECT * FROM waste_collection WHERE event_id=?', (event_id,)).fetchall())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_db().execute('SELECT * FROM users WHERE email=?', (request.form.get('email', '').lower().strip(),)).fetchone()
        if user and check_password_hash(user['password'], request.form.get('password', '')):
            session.clear(); session['user_id'] = user['id']; flash(f'Welcome back, {user["name"].split()[0]}.', 'success'); return redirect(request.args.get('next') or (url_for('dashboard') if user['role']=='admin' else url_for('profile')))
        flash('Email or password is incorrect.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form = request.form
        if len(form.get('password', '')) < 8 or form.get('password') != form.get('confirm_password'):
            flash('Use a matching password with at least 8 characters.', 'error'); return render_template('register.html')
        try:
            db = get_db(); db.execute('INSERT INTO users (name,email,phone,password,role) VALUES (?,?,?,?,?)', (form['name'], form['email'].lower().strip(), form.get('phone'), generate_password_hash(form['password']), 'volunteer')); db.commit(); flash('Account created. You can now sign in.', 'success'); return redirect(url_for('login'))
        except sqlite3.IntegrityError: flash('That email is already registered.', 'error')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))


@app.route('/api/event/<int:event_id>/stats')
def event_stats_api(event_id):
    event = get_db().execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    return jsonify(event_stats(event)) if event else ({'error': 'Not found'}, 404)


@app.route('/notifications')
@login_required
def notifications():
    rows = get_db().execute('SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    return render_template('notifications.html', notifications=rows)


with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', '5000')),
        debug=os.environ.get('FLASK_DEBUG', '').lower() == 'true',
    )
