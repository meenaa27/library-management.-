from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'abcd2123445'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Kaviya@12345@localhost/library_sys'
db = SQLAlchemy(app)

# Create database models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    stock = db.Column(db.Integer, default=0)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    outstanding_debt = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    rent_fee = db.Column(db.Float, default=0.0)

# Create database tables
db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/books', methods=['GET', 'POST'])
def books():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        stock = int(request.form['stock'])
        book = Book(title=title, author=author, stock=stock)
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('books'))
    books = Book.query.all()
    return render_template('books.html', books=books)

@app.route('/members', methods=['GET', 'POST'])
def members():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        member = Member(name=name, email=email)
        db.session.add(member)
        db.session.commit()
        flash('Member added successfully!', 'success')
        return redirect(url_for('members'))
    members = Member.query.all()
    return render_template('members.html', members=members)

@app.route('/issue', methods=['GET', 'POST'])
def issue():
    if request.method == 'POST':
        book_id = int(request.form['book'])
        member_id = int(request.form['member'])
        book = Book.query.get(book_id)
        member = Member.query.get(member_id)
        if not book or not member:
            flash('Invalid book or member!', 'danger')
        elif book.stock <= 0:
            flash('Book is out of stock!', 'danger')
        else:
            book.stock -= 1
            transaction = Transaction(book_id=book_id, member_id=member_id, issue_date=date.today())
            db.session.add(transaction)
            db.session.commit()
            flash(f'Book "{book.title}" issued to {member.name}!', 'success')
        return redirect(url_for('issue'))
    books = Book.query.filter(Book.stock > 0).all()
    members = Member.query.all()
    return render_template('issue.html', books=books, members=members)

@app.route('/return', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        book_id = request.form['book']
        member_id = request.form['member']

        book = Book.query.get(book_id)
        member = Member.query.get(member_id)

        if not book or not member:
            flash('Book or Member not found!', 'danger')
        else:
            transaction = Transaction.query.filter_by(book_id=book.id, member_id=member.id, returned=False).first()

            if not transaction:
                flash('Transaction not found!', 'danger')
            else:
                transaction.returned = True
                transaction.return_date = datetime.now()
                db.session.commit()

                # Calculate rent fee and update outstanding debt
                rent_days = (transaction.return_date - transaction.issue_date).days
                transaction.rent_fee = rent_days * book.rent_per_day
                member.outstanding_debt += transaction.rent_fee
                db.session.commit()

                # Check if the member's outstanding debt exceeds Rs. 500
                if member.outstanding_debt > 500:
                    flash(f'Member {member.name} has outstanding debt exceeding Rs. 500!', 'warning')

                flash(f'Book "{book.title}" returned by {member.name}!', 'success')
        return redirect(url_for('return_book'))

    books = Book.query.filter_by(status='Issued').all()
    members = Member.query.all()
    return render_template('return.html', books=books, members=members)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        books = Book.query.filter(Book.title.ilike(f'%{keyword}%') | Book.author.ilike(f'%{keyword}%')).all()
        return render_template('search.html', books=books, keyword=keyword)
    return render_template('search.html', books=[])

def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
