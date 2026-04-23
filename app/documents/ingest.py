from __future__ import annotations

from app.documents.schemas import DocumentProcessingTask
from app.domain.models import Attachment


def build_processing_task(attachment: Attachment) -> DocumentProcessingTask:
    return DocumentProcessingTask(
        attachment_id=attachment.id,
        storage_path=attachment.storage_path,
        mime_type=attachment.mime_type,
    )
