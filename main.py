from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:lc101@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y33kGcyk&P3B'

class BlogPost(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    body = db.Column(db.String(10000))
    deleted = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.deleted = False
        self.owner = owner


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blog = db.relationship('BlogPost', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'register']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'] )
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            flash("Logged in")
            return redirect('/blog')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        # TODO - validate user's data

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/')
        else:
            #TODO - better response
            return '<h1>Duplicate user</h1>'
    return render_template('register.html')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')

@app.route('/blog', methods=['POST', 'GET'])
def index():
    owner = User.query.filter_by(email=session['email']).first()
    blog = BlogPost.query.filter_by(deleted=False, owner=owner).all()
    blog_id = request.args.get('id')
    if not blog_id:
        return render_template("blog.html", title="Blog Town!", blog=blog)
    else:
        post = BlogPost.query.filter_by(id=blog_id).first()
        return render_template("post.html", post=post)

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    owner = User.query.filter_by(email=session['email']).first()
    if request.method == 'POST':
        blog_title = request.form['title']
        blog_body = request.form['body']
        if not blog_title or not blog_body:
            flash("Title and body cannot be left empty", "error")
            return redirect ('/newpost')
        new_post = BlogPost(blog_title, blog_body, owner)
        db.session.add(new_post)
        db.session.commit()
        new_post_id = new_post.id
        post = BlogPost.query.filter_by(id=new_post_id).first()
        return render_template("post.html", post=post)
    return render_template('newpost.html')


@app.route('/delete', methods=['POST'])
def delete_task():
    blog_id = int(request.form['blog-id'])
    blog = BlogPost.query.get(blog_id)
    blog.deleted = True
    db.session.add(blog)
    db.session.commit()

    return redirect('/blog')


if __name__ == '__main__':
    app.run()