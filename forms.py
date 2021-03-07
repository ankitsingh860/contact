from flask import Flask, config, render_template, request, flash, session , redirect, url_for
#from flask.helpers import url_for
from flask_wtf import FlaskForm
#from sqlalchemy.orm import query
#from sqlalchemy.sql.operators import exists
from wtforms import StringField, TextAreaField, SubmitField, RadioField, SelectField
from wtforms.validators import DataRequired
from wtforms.fields.core import IntegerField
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_mail import Mail,Message
from flask_migrate import Migrate
from threading import Thread
import os
basedir = os.path.abspath(os.path.dirname((__file__)))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

app.config['MAIL_SUBJECT_PREFIX'] = '[QUERY]'
app.config['MAIL_SENDER'] = 'Admin <ankit.singhdws@gmail.com>'
app.config['ADMIN'] = os.environ.get('ADMIN')

db = SQLAlchemy(app)
mail = Mail(app)
moment = Moment(app)
migrate = Migrate(app,db)

def send_mail_async(app,msg):
    with app.app_context():
        mail.send(msg) 

def send_mail(to,subject,template,**kwargs):
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + subject,sender=app.config['MAIL_MAIL_SENDER'],recipients = [to])
    msg.body = render_template(template + '.txt',**kwargs)
    msg.html = render_template(template + '.html',**kwargs)
    thr = Thread(target=send_mail_async,args=[app,msg])
    thr.start()
    return thr     

class User(db.Model):
   __tablename__ = 'contact'
   id = db.Column(db.Integer,primary_key=True)
   name = db.Column(db.String(30),unique=False, nullable= False)
   Age = db.Column(db.Integer , unique=False , nullable = False)
   Gender = db.Column(db.String(30) , unique=False , nullable = False)
   email = db.Column(db.String(40), unique=False, nullable=False)
   mobno = db.Column(db.Integer, unique=False, nullable=False)
   language = db.Column(db.String(25), unique=False, nullable=False)
   message = db.Column(db.String(300), unique=False, nullable=False) 
   
   def __repr__(self):
       return f"User('{self.name}' , '{self.Age}' , '{self.Gender}' , '{self.email}' , '{self.mobno}' , '{self.language}' , '{self.query}')"
         
class ContactForm(FlaskForm):
    name = StringField("Full Name",validators = [DataRequired()])
    Age = IntegerField("Age",validators = [DataRequired()])
    Gender = SelectField('Gender', choices = [('M','Male'),('F','Female')])
    email = StringField("Email",validators = [DataRequired()])
    mobno = IntegerField("Mob No",validators = [DataRequired()])
    language = SelectField('Languages', choices = [('c','C'),('cpp','C++'), ('py','Python'), ('java','Java')])
    query = TextAreaField("Query",validators = [DataRequired()])
    submit = SubmitField("SUBMIT")

@app.route('/contact', methods = ['GET','POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user is None:
            user =  User(name=form.name.data,Age=form.Age.data,Gender=form.Gender.data,email=form.email.data,mobno=form.mobno.data,language=form.language.data,message=form.query.data)
            db.session.add(user)
            db.session.commit()
            session['exists'] = False
            if app.config['ADMIN']:
               send_mail(app.config['ADMIN'],'New User', 'mail/new_query',user=user)
        else:
            session['exists'] = True
        session['name'] = form.name.data
        form.name.data = ''
        flash('Your Answers are Saved Thanks For Submitting')
        return render_template("contact.html",form=form)

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