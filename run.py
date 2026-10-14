"""Development server: python run.py  (then open http://127.0.0.1:5000)."""
from art_cds import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
