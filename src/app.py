"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Sitemap route
@app.route('/')
def sitemap():
    return generate_sitemap(app)



# People routes
@app.route('/api/people', methods=['GET'])
def get_all_people():
    people = db.session.execute(db.select(People)).scalars().all()
    serialized = [person.serialize() for person in people]
    return jsonify(serialized), 200

@app.route('/api/people', methods=['POST'])
def create_person():
    data = request.get_json()

    required_fields = ["name", "birth_year", "gender", "height", "skin_color", "eye_color"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    new_person = People(
        name=data["name"],
        birth_year=data["birth_year"],
        gender=data["gender"],
        height=data["height"],
        skin_color=data["skin_color"],
        eye_color=data["eye_color"]
    )

    db.session.add(new_person)
    db.session.commit()

    return jsonify(new_person.serialize()), 201

@app.route('/api/people/<int:people_id>', methods=['GET'])
def get_single_person(people_id):
    person = db.session.get(People, people_id)
    if person is None:
        return jsonify({"error": "Person not found"}), 404
    return jsonify(person.serialize()), 200

# Planets route
@app.route('/api/planets', methods=['GET'])
def get_all_planets():
    planets = db.session.execute(db.select(Planet)).scalars().all()
    serialized = [planet.serialize() for planet in planets]
    return jsonify(serialized), 200


@app.route('/api/planets', methods=['POST'])
def create_planet():
    data = request.get_json()

    required_fields = ["name", "population", "terrain"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    new_planet = Planet(
        name=data["name"],
        population=data["population"],
        terrain=data["terrain"]
    )

    db.session.add(new_planet)
    db.session.commit()

    return jsonify(new_planet.serialize()), 201

@app.route('/api/planets/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet = db.session.get(Planet, planet_id)

    if planet is None:
        return jsonify({"error": "Planet not found"}), 404

    return jsonify(planet.serialize()), 200

@app.route('/api/users', methods=['GET'])
def get_all_users():
    users = db.session.execute(db.select(User)).scalars().all()
    serialized = [user.serialize() for user in users]
    return jsonify(serialized), 200

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()

    required_fields = ["email", "password", "is_active"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    new_user = User(
        email=data["email"],
        password=data["password"],
        is_active=data["is_active"]
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.serialize()), 201


@app.route('/api/users/favorites', methods=['GET'])
def get_all_favorites():
    favorites = db.session.execute(db.select(Favorite)).scalars().all()
    serialized = [fav.serialize() for fav in favorites]
    return jsonify(serialized), 200

@app.route('/api/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user_id = 1  # temporary hardcoded "current user" ID

    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"error": "Planet not found"}), 404

    new_favorite = Favorite(user_id=user_id, planet_id=planet_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify(new_favorite.serialize()), 201

@app.route('/api/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user_id = 1  # hardcoded for now

    person = db.session.get(People, people_id)
    if person is None:
        return jsonify({"error": "Person not found"}), 404

    new_favorite = Favorite(user_id=user_id, person_id=people_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify(new_favorite.serialize()), 201

@app.route('/api/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    user_id = 1  # hardcoded for now

    favorite = db.session.execute(
        db.select(Favorite).filter_by(user_id=user_id, person_id=people_id)
    ).scalar()

    if favorite is None:
        return jsonify({"error": "Favorite person not found"}), 404

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "Favorite person deleted successfully"}), 200

@app.route('/api/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = 1  # hardcoded for now

    favorite = db.session.execute(
        db.select(Favorite).filter_by(user_id=user_id, planet_id=planet_id)
    ).scalar()

    if favorite is None:
        return jsonify({"error": "Favorite planet not found"}), 404

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "Favorite planet deleted successfully"}), 200


# Run the app
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
