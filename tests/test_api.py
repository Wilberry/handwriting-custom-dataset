from app.uploads import UPLOAD_DIR


def create_dataset(client, name="Writers"):
    return client.post("/datasets/", json={"name": name})


def create_student(client, dataset_id, name="Ada"):
    return client.post("/students/", json={"name": name, "dataset_id": dataset_id})


def test_dataset_and_student_workflow(client):
    dataset = create_dataset(client)
    assert dataset.status_code == 201
    assert dataset.json() == {"id": 1, "name": "Writers"}

    duplicate = create_dataset(client)
    assert duplicate.status_code == 409

    missing_parent = create_student(client, 999)
    assert missing_parent.status_code == 404

    student = create_student(client, dataset.json()["id"])
    assert student.status_code == 201
    assert student.json()["name"] == "Ada"

    duplicate_student = create_student(client, dataset.json()["id"])
    assert duplicate_student.status_code == 409

    events = client.get("/audit-events/?limit=10")
    assert events.status_code == 200
    assert [event["event_type"] for event in events.json()] == [
        "student.created",
        "dataset.created",
    ]


def test_list_endpoints_are_paginated(client):
    create_dataset(client, "First")
    create_dataset(client, "Second")
    create_dataset(client, "Third")
    page = client.get("/datasets/?offset=1&limit=1")
    assert page.status_code == 200
    assert [dataset["name"] for dataset in page.json()] == ["Second"]
    assert client.get("/datasets/?limit=201").status_code == 422


def test_audit_retention_validation(client):
    create_dataset(client)
    assert client.delete("/audit-events/retention?older_than_days=0").status_code == 422
    response = client.delete("/audit-events/retention?older_than_days=1")
    assert response.status_code == 200
    assert response.json()["deleted"] == 0


def test_admin_selected_dataset_and_delete_workflow(client):
    dataset_id = create_dataset(client, "Portfolio writers").json()["id"]
    page = client.get(f"/admin?dataset_id={dataset_id}")
    assert page.status_code == 200
    assert "Portfolio writers" in page.text
    assert "Identify a writer" in page.text
    assert "Reference inventory" in page.text

    deleted = client.post(
        f"/admin/datasets/{dataset_id}/delete",
        headers={"Origin": "http://testserver"},
        follow_redirects=False,
    )
    assert deleted.status_code == 303
    assert client.get(f"/students/{dataset_id}").status_code == 404


def test_names_are_trimmed_and_blank_names_are_rejected(client):
    created = create_dataset(client, "  Writers  ")
    assert created.status_code == 201
    assert created.json()["name"] == "Writers"
    assert create_dataset(client, "   ").status_code == 422


def test_health_checks(client):
    response = client.get(
        "/health/live", headers={"X-Request-ID": "b2e913bd-5128-4fae-b654-a58535d6c86a"}
    )
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"] == "b2e913bd-5128-4fae-b654-a58535d6c86a"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_sample_upload_and_prediction_cleanup(client, image_bytes, fake_embedding, tmp_path):
    dataset_id = create_dataset(client).json()["id"]
    student_id = create_student(client, dataset_id).json()["id"]

    missing_student = client.post(
        "/samples/999", files={"file": ("sample.png", image_bytes, "image/png")}
    )
    assert missing_student.status_code == 404

    sample = client.post(
        f"/samples/{student_id}",
        files={"file": ("../../unsafe.png", image_bytes, "image/png")},
    )
    assert sample.status_code == 201
    stored_path = next(UPLOAD_DIR.iterdir())
    assert stored_path.exists()
    assert stored_path.parent.name == "uploads"
    assert "unsafe" not in stored_path.name

    before_prediction = set(stored_path.parent.iterdir())
    prediction = client.post(
        "/predict/",
        data={"dataset_id": dataset_id, "threshold": 0.75},
        files={"file": ("query.png", image_bytes, "image/png")},
    )
    assert prediction.status_code == 200
    assert prediction.json()["match"] is True
    assert prediction.json()["predicted_student_id"] == student_id
    assert prediction.json()["predicted_student_name"] == "Ada"
    assert prediction.json()["top_matches"][0]["student_id"] == student_id
    assert set(stored_path.parent.iterdir()) == before_prediction


def test_invalid_upload_and_threshold_are_rejected(client, image_bytes):
    dataset_id = create_dataset(client).json()["id"]
    student_id = create_student(client, dataset_id).json()["id"]

    invalid = client.post(
        f"/samples/{student_id}",
        files={"file": ("fake.png", b"not an image", "image/png")},
    )
    assert invalid.status_code == 422

    threshold = client.post(
        "/predict/",
        data={"dataset_id": dataset_id, "threshold": 1.5},
        files={"file": ("query.png", image_bytes, "image/png")},
    )
    assert threshold.status_code == 422


def test_update_and_delete_lifecycle(client, image_bytes, fake_embedding):
    dataset_id = create_dataset(client).json()["id"]
    student_id = create_student(client, dataset_id).json()["id"]

    renamed_dataset = client.put(f"/datasets/{dataset_id}", json={"name": "Renamed writers"})
    assert renamed_dataset.status_code == 200
    assert renamed_dataset.json()["name"] == "Renamed writers"

    renamed_student = client.put(f"/students/{student_id}", json={"name": "Grace"})
    assert renamed_student.status_code == 200
    assert renamed_student.json()["name"] == "Grace"

    sample = client.post(
        f"/samples/{student_id}",
        files={"file": ("sample.png", image_bytes, "image/png")},
    )
    sample_path = next(UPLOAD_DIR.iterdir())
    assert sample_path.exists()

    assert client.delete(f"/samples/{sample.json()['id']}").status_code == 204
    assert not sample_path.exists()
    assert client.delete(f"/samples/{sample.json()['id']}").status_code == 404

    client.post(
        f"/samples/{student_id}",
        files={"file": ("sample.png", image_bytes, "image/png")},
    )
    second_path = next(UPLOAD_DIR.iterdir())
    assert client.delete(f"/students/{student_id}").status_code == 204
    assert not second_path.exists()
    assert client.delete(f"/students/{student_id}").status_code == 404

    assert client.delete(f"/datasets/{dataset_id}").status_code == 204
    assert client.delete(f"/datasets/{dataset_id}").status_code == 404
