"""Main FastAPI application for handwriting recognition and admin UI."""

from pathlib import Path
import shutil
from uuid import uuid4

import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, models
from app.database import SessionLocal, engine
from app.ml import compare_embeddings, extract_embedding
from app.routers import datasets, samples, students

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Handwriting Recognition Production API")
app.include_router(datasets.router)
app.include_router(students.router)
app.include_router(samples.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "upload.bin").suffix
    destination = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return destination


def run_prediction(db: Session, dataset_id: int, threshold: float, file_location: str):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    new_embedding = extract_embedding(file_location)
    samples_list = (
        db.query(models.HandwritingSample)
        .join(models.Student)
        .filter(models.Student.dataset_id == dataset_id)
        .all()
    )

    if not samples_list:
        return {
            "match": False,
            "predicted_student_id": None,
            "similarity_score": None,
            "message": "No handwriting samples in this dataset",
        }

    stored_embeddings = [np.frombuffer(sample.embedding, dtype=np.float32) for sample in samples_list]
    student_ids = [sample.student_id for sample in samples_list]

    similarities = compare_embeddings(new_embedding, stored_embeddings)
    best_match_index = int(np.argmax(similarities))
    best_score = float(similarities[best_match_index])

    if best_score < threshold:
        return {
            "match": False,
            "predicted_student_id": None,
            "similarity_score": best_score,
            "message": "No confident match found",
        }

    return {
        "match": True,
        "predicted_student_id": student_ids[best_match_index],
        "similarity_score": best_score,
        "message": None,
    }


@app.get("/")
def root():
    return {"message": "Production API Running"}


@app.get("/admin")
def admin_page(request: Request, dataset_id: int | None = None, message: str | None = None, db: Session = Depends(get_db)):
    datasets_list = crud.get_datasets(db)
    students_list = crud.get_students_by_dataset(db, dataset_id) if dataset_id else []
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "datasets": datasets_list,
            "students": students_list,
            "selected_dataset_id": dataset_id,
            "message": message,
            "prediction": None,
        },
    )


@app.post("/admin/datasets/create")
def admin_create_dataset(name: str = Form(...), db: Session = Depends(get_db)):
    crud.create_dataset(db, name)
    return RedirectResponse(url="/admin?message=Dataset+created", status_code=303)


@app.post("/admin/students/create")
def admin_create_student(name: str = Form(...), dataset_id: int = Form(...), db: Session = Depends(get_db)):
    dataset = db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()
    if not dataset:
        return RedirectResponse(url="/admin?message=Dataset+not+found", status_code=303)

    crud.create_student(db, name, dataset_id)
    return RedirectResponse(url=f"/admin?dataset_id={dataset_id}&message=Student+created", status_code=303)


@app.post("/admin/samples/upload")
def admin_upload_sample(student_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return RedirectResponse(url="/admin?message=Student+not+found", status_code=303)

    file_path = save_upload(file)
    embedding = extract_embedding(str(file_path))
    crud.create_handwriting_sample(db, str(file_path), student_id, embedding.tobytes())

    return RedirectResponse(url=f"/admin?dataset_id={student.dataset_id}&message=Sample+uploaded", status_code=303)


@app.post("/admin/predict")
def admin_predict(
    request: Request,
    dataset_id: int = Form(...),
    threshold: float = Form(0.75),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_path = save_upload(file)
    prediction = run_prediction(db, dataset_id, threshold, str(file_path))
    datasets_list = crud.get_datasets(db)
    students_list = crud.get_students_by_dataset(db, dataset_id)

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "datasets": datasets_list,
            "students": students_list,
            "selected_dataset_id": dataset_id,
            "message": None,
            "prediction": prediction,
        },
    )


@app.post("/predict/")
def predict(dataset_id: int = Form(...), threshold: float = Form(0.75), file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = save_upload(file)
    return run_prediction(db, dataset_id, threshold, str(file_path))


@app.get("/samples/")
def list_samples(db: Session = Depends(get_db)):
    all_samples = db.query(models.HandwritingSample).all()
    return [{"id": item.id, "image_path": item.image_path, "student_id": item.student_id} for item in all_samples]
