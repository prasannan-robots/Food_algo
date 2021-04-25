from flask import Flask,blueprints

# Create app function to create app
def create_app():
    from .view import view
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '*$@&*(%@(*YHFRUFHOWUHO*@$(FHSUkgfauguo'# for session
    app.register_blueprint(view, url_prefix='/')# added blueprint of view.py to show the page
    return app