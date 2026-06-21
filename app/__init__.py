from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

def create_app():
    main = Flask(__name__)
    
    main.config['SECRET_KEY'] = '46dafe8269cb8a1ad5f000a190dc89210539d272778262a3f11e51a75078ad49'
    main.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    main.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(main)
    migrate.init_app(main,db)
    
    socketio.init_app(main)

    from .models import User,Groups
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(main)
    
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    from .auth import auth as auth_blueprint
    main.register_blueprint(auth_blueprint)
    
    from .main import app as main_blueprint
    main.register_blueprint(main_blueprint)

    return main