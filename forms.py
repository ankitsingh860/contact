from flask import Flask, config, render_template, request, flash, session , redirect
from flask.helpers import url_for
from flask_wtf import FlaskForm
from sqlalchemy.sql.operators import exists
from wtforms import StringField, TextAreaField, SubmitField, RadioField, SelectField
from wtforms import validators
from wtforms.validators import DataRequired
from wtforms.fields.core import IntegerField
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail,Message
from threading import Thread
from flask_migrate import Migrate, migrate
import os
basedir = os.path.abspath(os.path.dirname((__file__)))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard321'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

app.config['MAIL_SUBJECT_PREFIX'] = '[Contact]'
app.config['MAIL_SENDER'] = 'Admin <ankit.singhdws@gmail.com>'
app.config['ADMIN'] = os.environ.get('ADMIN')

db = SQLAlchemy(app)
mail=Mail(app)
migrate = Migrate(app,db)

def send_mail_async(app,msg):
    with app.app_context():
        mail.send(msg) 

def send_mail(to,subject,template,**kwargs):
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + subject,sender=app.config['MAIL_SENDER'],recipients = [to])
    msg.body = render_template(template + '.txt',**kwargs)
    msg.html = render_template(template + '.html',**kwargs)
    thr = Thread(target=send_mail_async,args=[app,msg])
    thr.start()
    return thr     

class User(db.Model):
   __tablename__ = 'users'
   id = db.Column(db.Integer,primary_key=True)
   username = db.Column(db.String(64),unique=True,index=True)
   
   def __repr__(self):
       return '< User %r >' % self.username

class ContactForm(FlaskForm):
    name = StringField("Full Name",validators = [DataRequired()])
    Age = IntegerField("Age",validators = [DataRequired()])
    Gender = RadioField('Gender', choices = [('M','Male'),('F','Female')])
    email = StringField("Email",validators = [DataRequired()])
    mobno = IntegerField("Mob No",validators = [DataRequired()])
    language = SelectField('Languages', choices = [('c','C'),('cpp','C++'), ('py','Python'), ('java','Java')])
    query = TextAreaField("Query",validators = [DataRequired()])
    submit = SubmitField("SUBMIT")

@app.route('/contact', methods = ['GET','POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.data).first()
        if user is None:
            user =  User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['exists'] = False
            if app.config['ADMIN']:
               send_mail(app.config['ADMIN'],'New User', 'mail/new_user',user=user)
        else:
            session['exists'] = True
        session['name'] = form.name.data
        form.name.data = ''
        flash('Your Answers are Saved Thanks For Submitting')
        return redirect(url_for('contact'))
    return render_template('contact.html',form=form,name=session.get('name'),exists=session.get('exists'))
   

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'),500 

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User }


if __name__=='__main__':
    app.run(debug = True)