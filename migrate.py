from iot_app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT true"))
    db.commit()
    print('Column is_active added successfully')
except Exception as e:
    print('Error:', e)
    db.rollback()
finally:
    db.close()
