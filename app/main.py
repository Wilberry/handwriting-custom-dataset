"""Main FastAPI application for handwriting recognition and admin UI."""

import numpy as np
from urllib.parse import urlencode
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.audit import record_event
from app.config import Settings, get_settings
from app.database import get_db
from app.ml import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    aggregate_writer_scores,
    compare_embeddings,
    extract_embedding,
)
from app.observability import RequestContextMiddleware
from app.routers import audit, datasets, samples, students
from app.security import require_admin, require_api_key, require_same_origin
from app.storage import (
    StorageConfigurationError,
    delete_reference_image,
    persist_reference_image,
)
from app.uploads import InvalidUploadError, save_image_upload

app = FastAPI(title="Custom-Dataset Handwriting Identification API")
app.add_middleware(RequestContextMiddleware)
app.include_router(datasets.router)
app.include_router(students.router)
app.include_router(samples.router)
app.include_router(audit.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.exception_handler(StorageConfigurationError)
def storage_configuration_error(_request: Request, exc: StorageConfigurationError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def run_prediction(db: Session, dataset_id: int, threshold: float, file_location: str):
    dataset = crud.get_dataset(db, dataset_id)
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
            "predicted_student_name": None,
            "similarity_score": None,
            "top_matches": [],
            "message": "No handwriting samples in this dataset",
        }

    stored_embeddings = []
    student_ids = []
    for sample in samples_list:
        if (
            not sample.embedding
            or sample.embedding_model != EMBEDDING_MODEL
            or sample.embedding_dimension != EMBEDDING_DIMENSION
        ):
            continue
        embedding = np.frombuffer(sample.embedding, dtype=np.float32)
        if embedding.shape != new_embedding.shape:
            continue
        stored_embeddings.append(embedding)
        student_ids.append(sample.student_id)

    if not stored_embeddings:
        return {
            "match": False,
            "predicted_student_id": None,
            "predicted_student_name": None,
            "similarity_score": None,
            "top_matches": [],
            "message": "No compatible handwriting embeddings in this dataset",
        }

    similarities = compare_embeddings(new_embedding, stored_embeddings)
    ranked_writers = aggregate_writer_scores(similarities, student_ids)
    best_match = ranked_writers[0]
    best_student_id = best_match["student_id"]
    best_score = best_match["score"]
    students_by_id = {
        student.id: student
        for student in db.query(models.Student)
        .filter(models.Student.id.in_([item["student_id"] for item in ranked_writers]))
        .all()
    }
    top_matches = [
        {
            "student_id": item["student_id"],
            "student_name": students_by_id[item["student_id"]].name,
            "similarity_score": item["score"],
        }
        for item in ranked_writers[:3]
    ]

    if best_score < threshold:
        return {
            "match": False,
            "predicted_student_id": None,
            "predicted_student_name": None,
            "similarity_score": best_score,
            "top_matches": top_matches,
            "message": "No confident match found",
        }

    return {
        "match": True,
        "predicted_student_id": best_student_id,
        "predicted_student_name": students_by_id[best_student_id].name,
        "similarity_score": best_score,
        "top_matches": top_matches,
        "message": None,
    }


def admin_context(
    request: Request,
    db: Session,
    dataset_id: int | None = None,
    message: str | None = None,
    prediction: dict | None = None,
):
    datasets_list = crud.get_datasets(db, limit=200)
    selected_dataset = crud.get_dataset(db, dataset_id) if dataset_id else None
    students_list = (
        crud.get_students_by_dataset(db, dataset_id, limit=200) if selected_dataset else []
    )
    sample_list = (
        db.query(models.HandwritingSample)
        .join(models.Student)
        .filter(models.Student.dataset_id == dataset_id)
        .order_by(models.HandwritingSample.id.desc())
        .limit(200)
        .all()
        if selected_dataset
        else []
    )
    return {
        "request": request,
        "datasets": datasets_list,
        "students": students_list,
        "samples": sample_list,
        "selected_dataset": selected_dataset,
        "selected_dataset_id": dataset_id if selected_dataset else None,
        "message": message,
        "prediction": prediction,
        "stats": {
            "datasets": db.query(models.Dataset).count(),
            "students": db.query(models.Student).count(),
            "samples": db.query(models.HandwritingSample).count(),
        },
    }


def admin_redirect(message: str, dataset_id: int | None = None):
    params = {"message": message}
    if dataset_id is not None:
        params["dataset_id"] = dataset_id
    return RedirectResponse(url=f"/admin?{urlencode(params)}", status_code=303)


@app.get("/")
def root():
    return {"message": "Handwriting identification API running"}


@app.get("/health/live", tags=["Health"])
def liveness():
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
def readiness(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    if settings.is_production and not settings.security_is_configured:
        raise HTTPException(status_code=503, detail="Production security is not configured")
    if not settings.storage_is_configured:
        raise HTTPException(status_code=503, detail="Storage is not configured")
    db.execute(text("SELECT 1 FROM datasets LIMIT 1"))
    return {"status": "ready"}


@app.get("/admin", dependencies=[Depends(require_admin)])
def admin_page(
    request: Request,
    dataset_id: int | None = None,
    message: str | None = None,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context=admin_context(request, db, dataset_id, message),
    )


@app.post(
    "/admin/datasets/create",
    dependencies=[Depends(require_admin), Depends(require_same_origin)],
)
def admin_create_dataset(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    try:
        created = crud.create_dataset(db, name)
        record_event(db, request, "dataset.created", "dataset", created.id)
        message = "Dataset created"
    except crud.DuplicateRecordError:
        message = "Dataset name already exists"
    except crud.InvalidRecordError as exc:
        message = str(exc)
    return admin_redirect(message)


@app.post(
    "/admin/students/create",
    dependencies=[Depends(require_admin), Depends(require_same_origin)],
)
def admin_create_student(
    request: Request,
    name: str = Form(...),
    dataset_id: int = Form(...),
    db: Session = Depends(get_db),
):
    dataset = crud.get_dataset(db, dataset_id)
    if not dataset:
        return admin_redirect("Dataset not found")

    try:
        created = crud.create_student(db, name, dataset_id)
        record_event(db, request, "student.created", "student", created.id)
    except crud.DuplicateRecordError:
        return admin_redirect("Student already exists", dataset_id)
    except crud.InvalidRecordError as exc:
        return admin_redirect(str(exc), dataset_id)
    return admin_redirect("Student created", dataset_id)


@app.post(
    "/admin/samples/upload",
    dependencies=[Depends(require_admin), Depends(require_same_origin)],
)
def admin_upload_sample(
    request: Request,
    student_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    student = crud.get_student(db, student_id)
    if not student:
        return admin_redirect("Student not found")

    try:
        file_path = save_image_upload(file)
        embedding = extract_embedding(str(file_path))
        locator = persist_reference_image(file_path)
        created = crud.create_handwriting_sample(db, locator, student_id, embedding.tobytes())
        record_event(db, request, "sample.created", "sample", created.id)
    except InvalidUploadError as exc:
        return admin_redirect(str(exc), student.dataset_id)
    except Exception:
        if "file_path" in locals():
            file_path.unlink(missing_ok=True)
        if "locator" in locals():
            delete_reference_image(locator)
        raise

    return admin_redirect("Sample uploaded", student.dataset_id)


@app.post(
    "/admin/datasets/{dataset_id}/delete",
    dependencies=[Depends(require_admin), Depends(require_same_origin)],
)
def admin_delete_dataset(request: Request, dataset_id: int, db: Session = Depends(get_db)):
    dataset = crud.get_dataset(db, dataset_id)
    if not dataset:
        return admin_redirect("Dataset not found")
    image_paths = crud.delete_dataset(db, dataset)
    for locator in image_paths:
        delete_reference_image(locator)
    record_event(
        db,
        request,
        "dataset.deleted",
        "dataset",
        dataset_id,
        {"removed_sample_files": len(image_paths)},
    )
    return admin_redirect("Dataset and associated records deleted")


@app.post(
    "/admin/students/{student_id}/delete",
    dependencies=[Depends(require_admin), Depends(require_same_origin)],
)
def admin_delete_student(request: Request, student_id: int, db: Session = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        return admin_redirect("Student not found")
    dataset_id = student.dataset_id
    image_paths = crud.delete_student(db, student)
    for locator in image_paths:
        delete_reference_image(locator)
    record_event(
        db,
        request,
        "student.deleted",
        "student",
        student_id,
        {"removed_sample_files": len(image_paths)},
    )
    return admin_redirect("Student and associated samples deleted", dataset_id)


@app.post(
    "/admin/samples/{sample_id}/delete",
    dependencies=[Depends(require_admin), Depends(require_same_origin)],
)
def admin_delete_sample(request: Request, sample_id: int, db: Session = Depends(get_db)):
    sample = crud.get_sample(db, sample_id)
    if not sample:
        return admin_redirect("Sample not found")
    dataset_id = sample.student.dataset_id
    locator = crud.delete_handwriting_sample(db, sample)
    delete_reference_image(locator)
    record_event(db, request, "sample.deleted", "sample", sample_id)
    return admin_redirect("Sample deleted", dataset_id)


@app.post(
    "/admin/predict",
    dependencies=[Depends(require_admin), Depends(require_same_origin)],
)
def admin_predict(
    request: Request,
    dataset_id: int = Form(...),
    threshold: float = Form(0.75, ge=0.0, le=1.0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        file_path = save_image_upload(file)
        prediction = run_prediction(db, dataset_id, threshold, str(file_path))
        record_event(
            db,
            request,
            "prediction.completed",
            "dataset",
            dataset_id,
            {
                "match": prediction["match"],
                "similarity_score": prediction["similarity_score"],
            },
        )
    except InvalidUploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if "file_path" in locals():
            file_path.unlink(missing_ok=True)
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context=admin_context(request, db, dataset_id, prediction=prediction),
    )


@app.post(
    "/predict/",
    dependencies=[Depends(require_api_key)],
    response_model=schemas.PredictionResponse,
)
def predict(
    request: Request,
    dataset_id: int = Form(..., gt=0),
    threshold: float = Form(0.75, ge=0.0, le=1.0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        file_path = save_image_upload(file)
        prediction = run_prediction(db, dataset_id, threshold, str(file_path))
        record_event(
            db,
            request,
            "prediction.completed",
            "dataset",
            dataset_id,
            {
                "match": prediction["match"],
                "similarity_score": prediction["similarity_score"],
            },
        )
        return prediction
    except InvalidUploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if "file_path" in locals():
            file_path.unlink(missing_ok=True)


@app.get(
    "/samples/",
    dependencies=[Depends(require_api_key)],
    response_model=list[schemas.HandwritingSampleResponse],
)
def list_samples(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.HandwritingSample)
        .order_by(models.HandwritingSample.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
