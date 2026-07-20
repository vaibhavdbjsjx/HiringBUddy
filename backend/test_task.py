from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import db_models
import schemas
from routers.candidates import process_resume_background
from services.resume_parser import extract_text_from_pdf

engine = create_engine('sqlite:///./hiring_buddy.db', connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Mock PDF bytes
pdf_bytes = b'Python React AWS node.js sql html css'

# Add fake candidate to db
new_cand = db_models.Candidate(name="Test User", status="processing")
db.add(new_cand)
db.commit()
db.refresh(new_cand)

print(f"Created candidate {new_cand.id}")

# Extract
text = "Python React AWS node.js sql html css user@example.com"
print("Extracted text:", text)

# Process
process_resume_background(new_cand.id, text, db)

# Print DB result
c = db.query(db_models.Candidate).filter(db_models.Candidate.id == new_cand.id).first()
print("Final skills in DB:", c.skills)
print("Final status:", c.status)
