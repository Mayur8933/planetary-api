from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2000@localhost/planets'
app.config['JWT_SECRET_KEY']='super-secret' #change this in real world
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#serializing SQLALchemy results with marshmallow
ma = Marshmallow(app)

#JWT Token
jwt = JWTManager(app)

#database models
class User(db.Model):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
      

class Planet(db.Model):
    __tablename__ = "Planets"
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "first_name", "last_name", "email", "password")

class PlanetSchema(ma.Schema):
    class Meta:
        fields = ("planet_id", "planet_name", "planet_type", "home_star", "mass", "radius", "distance")

user_schema = UserSchema()
users_schema = UserSchema(many = True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many = True)

@app.route("/")
def home():
    return "Hello world!"


@app.route("/super_simple")
def super_simple():
    return jsonify(message="Hello from the planetary API.")


#working with URL parameters
@app.route("/parameters/<string:name>/<int:age>")
def url_variables(name:str, age:int):
 
    if age < 18:
        return jsonify(message="Sorry " + name + " you're not old enough"), 401
    else:
        return jsonify(message="Welcome " + name + " you're old enough")
    

#Get and post method for planets api
# @app.route("/planets", methods = ["POST","GET"])
# def plnets():
#     if request.method == "POST":
#         if request.is_json:
#             data = request.get_json()
#             user = User(first_name = data["first_name"], last_name = data["last_name"],email = data["email"],password = data["password"])
#             db.session.add(user)
#             db.session.commit()
#             return jsonify(message = "User " + user.first_name + " successfuly created...") 
#         else:
#             return jsonify(error = "The request payload is not in JSON format.") 
        
#     elif request.method == "GET":
#         user_list = User.query.all()
#         result = users_schema.dump(user_list)
#         return(result)

#regeister a user
@app.route("/register", methods=['POST'])
def register():
    email = request.form["email"]
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message="That email already exists")
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully"), 201
    
#Authenticating users and passing the token
@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        #using form data
        email = request.json['email']
        password = request.json['password']
    else:
        #using JSON Object
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()

    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='login Succeeded', access_token=access_token)
    else:
        return jsonify(message='Bad email or password'),401
    
#Create, Read, Update, Delete

#Get a single planet Details
#Read
@app.route("/planet_details/<int:planet_id>", methods=['GET'])
@jwt_required()
def planet_details(planet_id:int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    print("Planet", planet)
    if planet:
        result = planet_schema.dump(planet)
        # planets = Planet.query.all()

        # result = planets_schema.dump(planets)
        print("result",result)
        return jsonify(result)
    else:
        return jsonify(message="That planet does not exist"), 404
    

#create
@app.route("/add_planet", methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.form['planet_name']
    planet = Planet.query.filter_by(planet_name=planet_name).first()
    if planet:
        return jsonify("There is already a planet by that name.")
    else:
        planet_type=request.form['planet_type']
        home_star=request.form['home_star']
        mass=request.form['mass']
        radius=request.form['radius']
        distance=request.form['distance']

        new_planet = Planet(planet_name=planet_name, planet_type=planet_type, home_star=home_star, mass=mass, radius=radius, distance=distance)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="You added a planet"),201
    

#update
@app.route("/update_planet", methods=['PUT'])
@jwt_required()
def update_planet():
    planet_id = request.form['planet_id']
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name=request.form['planet_name']
        planet.planet_type=request.form['planet_type']
        planet.home_star=request.form['home_star']
        planet.mass=float(request.form['mass'])
        planet.radius=float(request.form['radius'])
        planet.distance=float(request.form['distance'])

        db.session.commit()
        return jsonify(message = "you updated a planet")
    else:
        return jsonify(message="That planet does not exist"),404
    

#Delete
@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def remove_planet(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="You deleted a Plant"), 202
    else:
        return jsonify(message="That Planet does not exist"),404



if __name__ == '__main__':
    app.run()

