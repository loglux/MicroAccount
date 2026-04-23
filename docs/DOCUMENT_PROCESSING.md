# Document Processing

## Purpose

Attachments must not be treated as dead files.

The system should evolve toward a document-processing pipeline that can handle:

- text-based PDF invoices
- scanned PDF invoices
- image receipts
- mixed-quality mobile scans

## Design principles

- extraction is assistive, not authoritative
- OCR must not silently create final accounting entries
- extracted fields should prefill forms and enter a review workflow
- original files remain the source artifact

## Processing stages

1. file uploaded
2. attachment stored locally
   - the first uploaded file defaults to `primary_document`
   - later files default to `supporting_document`
3. processing task created
4. detector chooses strategy
   - text PDF extraction
   - OCR for scanned PDF
   - OCR for image receipt
5. parser derives structured guesses
6. user reviews and confirms
7. confirmed fields can prefill the expense record

## Data model

### `attachments`

The attachment record should include processing metadata:

- `document_role`
- `processing_status`
- `processing_error`

Attachment roles:

- `primary_document`: main source for field prefill
- `supporting_document`: additional evidence such as payment receipts

### `document_extractions`

Each extraction attempt records:

- extractor name
- processing status
- document type guess
- extracted text
- supplier guess
- invoice number guess
- invoice date guess
- total amount guess
- currency guess
- confidence score
- parser notes

## Suggested module layout

- `app/documents/ingest.py`
- `app/documents/extract.py`
- `app/documents/ocr.py`
- `app/documents/parse.py`
- `app/documents/schemas.py`

## Recommended rollout

### Phase 1

- placeholder pipeline only
- attachment processing status visible in data model
- extraction rows stored even if processing is not yet active

### Phase 2

- born-digital PDF text extraction
- text retention in `document_extractions`
- manual review screen
- prefill expense fields from extracted supplier/date/amount guesses

### Phase 3

- OCR for scanned receipts and scanned invoices
- supplier and amount parsing heuristics
- expense form prefill from extracted data

## Future document sources

The upload flow is the first document source, not the last one.

Useful future inputs:

- email copy-paste into a parser textbox
- forwarded invoice email import
- `.eml` upload
- vendor portal PDF export import

These should all feed the same extraction and review pipeline instead of creating separate parsing logic for each source.

## Notes

The first working OCR implementation should be conservative.

Low-confidence data should be shown as suggestions, not automatically written into final accounting fields.
