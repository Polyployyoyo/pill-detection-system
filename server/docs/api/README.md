## Pill Detection Server API Documentation

### Overview

This document describes the currently implemented REST API endpoints for the `drugs`, `detect`, `logs`, and `lockers` routes.

---

### REST API Endpoints

All endpoints return JSON responses.

#### Drugs

- **GET `/drugs`**
  - **Description**: Get a list of all drugs from the database.
  - **Query parameters**: None.
  - **Response 200**: Array of drug objects.
  - **Response 500**: Server could not read drugs because of database connection.

- **GET `/drugs/{drug_id}`**
  - **Description**: Get a single drug by its ID.
  - **Path parameters**:
    - **drug_id** (`integer`): ID of the drug to retrieve.
  - **Response 200**: Drug object.
  - **Response 404**: Server could not find a requested drug to read.
  - **Response 500**: Server could not read drugs because of database connection.

#### Detection

- **POST `/detect`**
  - **Description**: Detect objects in an uploaded image using the YOLO model.
  - **Request body**:
    - **file** (`multipart/form-data`, required): Image file to process.
  - **Response 200**:
    - **count** (`object`): Dictionary of detected label counts.
    - **confidence** (`object`): Dictionary of confidence scores by detected label.
    - **image_format** (`string`): Format of the annotated image (`.jpg`).
    - **annotated_image_base64** (`string`): Annotated image encoded as Base64.
  - **Response 400**: Invalid image file. Please upload a valid image.
  - **Response 404**: File not found. Please upload a file.
  - **Response 500**: Error processing image.

#### Logs

- **GET `/logs`**
  - **Description**: Get a list of detection logs, joined with drug trade names, ordered by latest detection time.
  - **Query parameters**: None.
  - **Response 200**: Array of detection log objects.
  - **Response 500**: Server could not read logs because of database connection.

- **POST `/logs`**
  - **Description**: Create a new detection log entry.
  - **Request body** (`application/json`, required):
    - **drug_id** (`integer`): ID of the detected drug.
    - **detected_quantity** (`integer`): Detected quantity for this log.
    - **confidence** (`number`): Detection confidence score.
  - **Response 201**: Created detection log object.
  - **Response 500**: Server could not create log because of database connection.

- **DELETE `/logs/{log_id}`**
  - **Description**: Delete a detection log by ID.
  - **Path parameters**:
    - **log_id** (`integer`): ID of the log to delete.
  - **Response 200**: Deleted detection log object.
  - **Response 404**: Server could not find a requested log to delete.
  - **Response 500**: Server could not delete log because of database connection.

#### Lockers

- **GET `/lockers`**
  - **Description**: Get a list of locker-drug records with optional keyword filtering.
  - **Query parameters**:
    - **keyword** (`string`, optional): Filters by locker name, drug trade name, or slot code.
  - **Response 200**: Array of locker-drug records.
  - **Response 500**: Server could not read drug locker because of database connection.

- **GET `/lockers/drug/{drug_id}`**
  - **Description**: Get locker records for a specific drug ID.
  - **Path parameters**:
    - **drug_id** (`integer`): ID of the drug.
  - **Response 200**: Array of locker records for the given drug.
  - **Response 404**: Server could not find a requested locker to read.
  - **Response 500**: Server could not read locker because of database connection.

- **GET `/lockers/{locker_id}`**
  - **Description**: Get all drug records in a specific locker.
  - **Path parameters**:
    - **locker_id** (`integer`): ID of the locker.
  - **Response 200**: Array of locker records for the given locker.
  - **Response 404**: Server could not find a requested locker to read.
  - **Response 500**: Server could not read locker because of database connection.

- **PUT `/lockers/{locker_id}/drug/{drug_id}/add/{quantity}`**
  - **Description**: Increase stock quantity for a specific drug in a locker.
  - **Path parameters**:
    - **locker_id** (`integer`): ID of the locker.
    - **drug_id** (`integer`): ID of the drug.
    - **quantity** (`integer`): Amount to add.
  - **Response 200**: Updated locker-drug record.
  - **Response 404**: Server could not find a requested drug to update.
  - **Response 500**: Server could not update locker because of database connection.

- **PUT `/lockers/{locker_id}/drug/{drug_id}/subtract/{quantity}`**
  - **Description**: Decrease stock quantity for a specific drug in a locker.
  - **Path parameters**:
    - **locker_id** (`integer`): ID of the locker.
    - **drug_id** (`integer`): ID of the drug.
    - **quantity** (`integer`): Amount to subtract.
  - **Response 200**: Updated locker-drug record.
  - **Response 404**: Server could not find a requested drug to update.
  - **Response 500**: Server could not update locker because of database connection.

- **PUT `/lockers/transfer`**
  - **Description**: Transfer stock quantity of a drug between two lockers.
  - **Request body** (`application/json`, required):
    - **source_locker_id** (`integer`): Source locker ID.
    - **destination_locker_id** (`integer`): Destination locker ID.
    - **drug_id** (`integer`): Drug ID to transfer.
    - **quantity** (`integer`): Quantity to transfer.
  - **Response 200**:
    - **message** (`string`): `Stock transferred successfully`.
    - **source** (`object`): Updated source locker-drug record.
    - **destination** (`object`): Updated destination locker-drug record.
  - **Response 400**:
    - Source and destination lockers must be different.
    - Transfer quantity must be a positive integer.
    - Insufficient stock in source locker.
  - **Response 404**: Server could not find source or destination locker record.
  - **Response 500**: Server could not transfer stock because of database connection.

---

### Notes

- Route prefixes are configured as `/drugs`, `/detect`, `/logs`, and `/lockers`.
- Responses are based on current implementation in `server/app/routes/drug.py`, `server/app/routes/detect.py`, `server/app/routes/log.py`, and `server/app/routes/locker.py`.
