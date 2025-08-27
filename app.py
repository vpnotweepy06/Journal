from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from models import db, Entry, User
from forms import EntryForm, LoginForm, RegisterForm
from colors import ghibli_palette
import io
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables immediately when app starts
with app.app_context():
    db.create_all()

# -----------------------
# Index / All Entries
# -----------------------
@app.route('/')
def index():
    if "username" not in session:
        flash("Please log in to view your journal entries.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    # Only fetch entries for the logged-in user
    entries = Entry.query.filter_by(user_id=user.id).order_by(Entry.created_at.desc()).all()
    return render_template('index.html', entries=entries, username=session.get('username'), colors=ghibli_palette)

# -----------------------
# Register
# -----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("Username already taken. Try another.", "warning")
            return redirect(url_for('register'))

        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', form=form, colors=ghibli_palette)

# -----------------------
# Login
# -----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['username'] = user.username
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html', form=form, colors=ghibli_palette)

# -----------------------
# Logout
# -----------------------
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You’ve been logged out.", "info")
    return redirect(url_for('login'))

# -----------------------
# Profile
# -----------------------
@app.route('/profile')
def profile():
    if 'username' not in session:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    entry_count = Entry.query.filter_by(user_id=user.id).count()
    return render_template('profile.html', user=user, entry_count=entry_count, colors=ghibli_palette)

# -----------------------
# Add Entry
# -----------------------
@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if 'username' not in session:
        flash("Please log in to add entries.", "warning")
        return redirect(url_for('login'))
    
    form = EntryForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=session['username']).first()
        entry = Entry(
            title=form.title.data,
            content=form.content.data,
            tags=form.tags.data,
            user_id=user.id
        )
        db.session.add(entry)
        db.session.commit()
        flash("Entry added successfully!", "success")
        return redirect(url_for('index'))
    
    return render_template('add_entry.html', form=form, colors=ghibli_palette)

# -----------------------
# View Entry
# -----------------------
@app.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    if 'username' not in session:
        flash("Please log in to view entries.", "warning")
        return redirect(url_for('login'))

    entry = Entry.query.get_or_404(entry_id)
    user = User.query.filter_by(username=session['username']).first()

    # Ownership check
    if entry.user_id != user.id:
        flash("You don't have permission to view this entry.", "danger")
        return redirect(url_for('index'))

    return render_template('view_entry.html', entry=entry, colors=ghibli_palette)

# -----------------------
# Edit Entry
# -----------------------
@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    if 'username' not in session:
        flash("Please log in to edit entries.", "warning")
        return redirect(url_for('login'))

    entry = Entry.query.get_or_404(entry_id)
    user = User.query.filter_by(username=session['username']).first()

    # Ownership check
    if entry.user_id != user.id:
        flash("You don't have permission to edit this entry.", "danger")
        return redirect(url_for('index'))

    form = EntryForm(obj=entry)
    if form.validate_on_submit():
        entry.title = form.title.data
        entry.content = form.content.data
        entry.tags = form.tags.data
        db.session.commit()
        flash("Entry updated successfully!", "success")
        return redirect(url_for('view_entry', entry_id=entry.id))

    return render_template('edit_entry.html', form=form, entry=entry, colors=ghibli_palette)

# -----------------------
# Delete Entry
# -----------------------
@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    if 'username' not in session:
        flash("Please log in to delete entries.", "warning")
        return redirect(url_for('login'))

    entry = Entry.query.get_or_404(entry_id)
    user = User.query.filter_by(username=session['username']).first()

    # Ownership check
    if entry.user_id != user.id:
        flash("You don't have permission to delete this entry.", "danger")
        return redirect(url_for('index'))

    db.session.delete(entry)
    db.session.commit()
    flash("Entry deleted successfully!", "warning")
    return redirect(url_for('index'))

# -----------------------
# Export Entries as CSV
# -----------------------
@app.route('/export')
def export_entries():
    if 'username' not in session:
        flash("Please log in to export entries.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    # Only export the logged-in user's entries
    entries = Entry.query.filter_by(user_id=user.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Title', 'Content', 'Tags', 'Created At', 'Updated At'])

    for e in entries:
        writer.writerow([e.id, e.title, e.content, e.tags, e.created_at, e.updated_at])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="journal_entries.csv"
    )

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
