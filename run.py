from backend.app import create_app, celery_app

flask_app = create_app()
flask_app.app_context().push()


if __name__ == "__main__":
    flask_app.run(port=5005)