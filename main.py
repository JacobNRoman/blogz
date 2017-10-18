from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:ruletheworld@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y33kGcyk&P3B'

class BlogPost(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    body = db.Column(db.String(10000))
    deleted = db.Column(db.Boolean)
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    

    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.deleted = False
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
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
    allowed_routes = ['login', 'register', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'] )
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            # This elegantly validates for us. "if user" will return false if the query fails(meaning username was entered wrong) and the second clause makes sure the password that was entered matches the password on file. 
            session['email'] = email
            #creates the session['email'] object that allows us to have a persistent login
            flash("Logged in")
            return redirect('/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        #TODO: insert some kind of email validation. Regex? NOTE: current build uses usernames, not email. So, substitute TODO: refactor code to stop using 'email' keyword and use username instead.
        password = request.form['password']
        #TODO: Complexity checker?
        verify = request.form['verify']
        # everything below is layers of validation.
        if not email or not password or not verify:
            flash("You must provide a valid email, password, and password verification")
            return redirect("/register")
        if len(email) < 4:
            flash("Username must be longer than three characters")
            return redirect("/register")
        if len(password) < 4:
            flash("Password must be longer than three characters")
            return redirect("/register")
        if password != verify:
            flash("Password and verification fields do not match")
            return redirect('/register')
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            # This only runs if registration is successful
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/blog')
        else:
            flash("User with this email already exists")
            return redirect('/register')
    return render_template('register.html')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/blog')

@app.route("/")
def index():
    # This renders the 'Home' page, which is a list of all users that links to each individual user's blog page. 
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/blog', methods=['POST', 'GET'])
@app.route('/blog/<int:page_num>')
def blog(page_num=None):
    # blog renders a list of all blog posts by all authors. It also contains several subroutes using query parameters for reaching specific posts and author's blogs. 
    blog_id = request.args.get('id')
    user_id = request.args.get('user')
    # blog_id only exists if the user clicks on a specific post's heading. The code below renders a specific post's page if blog_id exists.
    if blog_id:
        post = BlogPost.query.filter_by(id=blog_id).first()
        user = User.query.filter_by(id=post.owner_id).first()
        return render_template("post.html", post=post, user=user)
    # user_id is provided by the author headings on index and below posts. 
    if user_id:
        user = User.query.filter_by(id=user_id).first()
        blog = BlogPost.query.filter_by(deleted=False, owner_id=user_id).order_by(BlogPost.pub_date.desc()).paginate(per_page=5, page=page_num, error_out=True)
        return render_template("authorblog.html", blog=blog, user=user)
    else:
        # this renders the 'normal' blog page
        user = User.query.all()
        blog = BlogPost.query.filter_by(deleted=False).order_by(BlogPost.pub_date.desc()).paginate(per_page=5, page=page_num, error_out=True)  
        return render_template("blog.html", title="Blog Town!", blog=blog, user=user)
        

@app.route('/userblog', methods=['POST', 'GET'])
def users_blog():
    # users_blog exists to provide a page that displays a current users personal blog and allows them to delete their posts. 
    owner = User.query.filter_by(email=session['email']).first()
    blog = BlogPost.query.filter_by(deleted=False, owner=owner).order_by(BlogPost.pub_date.desc()).all()
    blog_id = request.args.get('id')
    # blog_id only exists if the user clicks on a specific post's heading. The code below renders a specific post's page if blog_id exists.
    if not blog_id:
        return render_template("userblog.html", title="Blog Town!", blog=blog)
    else:
        post = BlogPost.query.filter_by(id=blog_id).first()
        return render_template("post.html", post=post)

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    owner = User.query.filter_by(email=session['email']).first()
    if request.method == 'POST':
        # the indented code below handles the submission and creation of a new post
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
        user = User.query.filter_by(id=post.owner_id).first()
        # after a new post is submitted the user is redirected to that new post's individual page. 
        return render_template("post.html", post=post, user=user)
    return render_template('newpost.html')


@app.route('/delete', methods=['POST'])
def delete_post():
    # this function handles the deleting of posts that occurs on userblog
    blog_id = int(request.form['blog-id'])
    blog = BlogPost.query.get(blog_id)
    blog.deleted = True
    db.session.add(blog)
    db.session.commit()

    return redirect('/userblog')


if __name__ == '__main__':
    app.run()