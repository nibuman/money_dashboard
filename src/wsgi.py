from app import app, server  # noqa:F401

# `server` is accessed by gunicorn from here, so import is required!
if __name__ == "__main__":
    app.run()
