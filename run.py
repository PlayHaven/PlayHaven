from app import create_app, db

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Initialized the database.")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
