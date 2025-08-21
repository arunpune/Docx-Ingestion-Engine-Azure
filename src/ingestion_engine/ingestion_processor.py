"""
Ingestion Engine - CosmosDB (NoSQL) version
- Two Cosmos collections: Emails (master), Attachments (child)
- Coordinates OCR processing via Service Bus
"""
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from azure.cosmos import CosmosClient, PartitionKey, exceptions as cosmos_exceptions
from azure.servicebus import ServiceBusClient

from ..shared.config import settings
from ..shared.utils import send_to_service_bus

logger = logging.getLogger(__name__)


# -------------------------
# Cosmos DB Service (2 collections)
# -------------------------
class CosmosDBService:
    def __init__(self):
        endpoint = "https://insuranceapp123.documents.azure.com:443/"
        key = "BoKEjc0syOSjllt3UVlKc6vMegTUbQagf8v4czmoE0Qnoj379542q9HZfIngfp60rdvI39S6ZINdACDbCQi8aw==" 
        self.db_name = "insuranceapp123"
        if not endpoint or not key:
            raise RuntimeError(
                "Missing CosmosDB credentials. Set AZURE_COSMOS_ENDPOINT and AZURE_COSMOS_KEY."
            )

        self.database_name = os.getenv("COSMOS_DB_NAME", "IngestionDB")
        self.emails_container_name = os.getenv("COSMOS_EMAILS_CONTAINER", "Emails")
        self.attachments_container_name = os.getenv("COSMOS_ATTACHMENTS_CONTAINER", "Attachments")

        self.client = CosmosClient(endpoint, key)
        self.database = self.client.create_database_if_not_exists(id=self.database_name)

        # Partition keys:
        # Emails: partition by /id (email/document id)
        # Attachments: partition by /emailId (query all attachments for an email efficiently)
        self.emails_container = self.database.create_container_if_not_exists(
            id=self.emails_container_name,
            partition_key=PartitionKey(path="/id"),
            offer_throughput=400
        )
        self.attachments_container = self.database.create_container_if_not_exists(
            id=self.attachments_container_name,
            partition_key=PartitionKey(path="/emailId"),
            offer_throughput=400
        )

    # ----- Emails -----
    def upsert_email(self, doc: Dict):
        return self.emails_container.upsert_item(doc)

    def update_email_status(self, email_id: str, status: str):
        # Reads with (id, partition_key=id) then updates
        item = self.emails_container.read_item(item=email_id, partition_key=email_id)
        item["status"] = status
        item["updatedAt"] = datetime.utcnow().isoformat()
        return self.emails_container.upsert_item(item)

    # ----- Attachments -----
    def upsert_attachment(self, doc: Dict):
        return self.attachments_container.upsert_item(doc)

    def list_attachments(self, email_id: str) -> List[Dict]:
        query = "SELECT * FROM c WHERE c.emailId = @emailId ORDER BY c.attachmentNumber"
        params = [{"name": "@emailId", "value": email_id}]
        return list(
            self.attachments_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            )
        )


# -------------------------
# Ingestion Engine
# -------------------------
class IngestionEngine:
    """Handles ingestion of processed emails and files, coordinates OCR processing (CosmosDB)."""

    def __init__(self):
        self.db = CosmosDBService()

    def process_ingestion_message(self, message: Dict) -> bool:
        """
        Process an ingestion message from Service Bus.

        Expected message shape (email):
        {
          "processing_id": "proc-123",
          "source_type": "email",
          "email": {
            "id": "email-uuid-001",
            "from": "...",
            "to": ["..."],
            "cc": ["..."],
            "subject": "...",
            "body": "...",
            "date": "YYYY-MM-DD",
            "time": "HH:MM:SS",
            "email_uri": "https://.../raw.eml"
          },
          "attachments": [
            {"uri": "https://.../a.pdf", "filename": "a.pdf"},
            {"uri": "https://.../b.jpg", "filename": "b.jpg"}
          ]
        }

        Expected message shape (file):
        {
          "processing_id": "proc-456",
          "source_type": "file",
          "file_uri": "https://.../file.docx",
          "file_metadata": {"filename": "file.docx"}
        }
        """
        processing_id = message.get("processing_id")
        source_type = message.get("source_type")

        if not processing_id:
            logger.error("Processing ID not found in message")
            return False

        logger.info(f"[Cosmos] Process message: processing_id={processing_id}, source_type={source_type}")

        try:
            if source_type == "email":
                return self._process_email_ingestion(processing_id, message)
            elif source_type == "file":
                return self._process_file_ingestion(processing_id, message)
            else:
                logger.error(f"Unknown source type: {source_type}")
                return False

        except Exception as e:
            logger.error(f"Error processing ingestion message: {e}")
            return False

    def _process_email_ingestion(self, processing_id: str, message: Dict) -> bool:
        """Process email ingestion: write Email doc, write minimal Attachment docs, send each to OCR."""
        email_payload = message.get("email") or {}
        attachments = message.get("attachments", []) or []

        # Build Email master doc (partition key = id)
        email_id = email_payload.get("id") or processing_id  # fallback
        email_doc = {
            "id": email_id,
            "processingId": processing_id,
            "sourceType": "email",
            "from": email_payload.get("from"),
            "to": email_payload.get("to", []),
            "cc": email_payload.get("cc", []),
            "subject": email_payload.get("subject"),
            "body": email_payload.get("body"),
            "date": email_payload.get("date"),
            "time": email_payload.get("time"),
            "emailUri": email_payload.get("email_uri"),
            "attachmentCount": len(attachments),
            "status": "processing",  # received -> processing -> ocr_pending/completed/failed
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }

        self.db.upsert_email(email_doc)

        # If no attachments, mark completed
        if not attachments:
            self.db.update_email_status(email_id, "completed")
            logger.info(f"[Cosmos] Email {email_id}: no attachments, marked completed.")
            return True

        # For each attachment, create a minimal child doc and send to OCR
        for i, att in enumerate(attachments):
            blob_url = att.get("uri")
            filename = att.get("filename", f"attachment_{i+1}")

            attach_doc = {
                "id": f"{email_id}-{i+1}",     # unique
                "emailId": email_id,           # partition key
                "processingId": processing_id, # traceability
                "attachmentNumber": i + 1,
                "blobUrl": blob_url,
                "fileName": filename
            }
            self.db.upsert_attachment(attach_doc)

            # Send for OCR
            self._send_to_ocr_engine(
                processing_id=processing_id,
                file_uri=blob_url,
                filename=filename
            )

        # Update email status
        self.db.update_email_status(email_id, "ocr_pending")
        logger.info(f"[Cosmos] Email {email_id}: {len(attachments)} attachments sent to OCR.")
        return True

    def _process_file_ingestion(self, processing_id: str, message: Dict) -> bool:
        """Process non-email file ingestion: store as an 'email-like' doc with sourceType=file, then OCR."""
        file_uri = message.get("file_uri")
        file_metadata = message.get("file_metadata", {}) or {}

        if not file_uri:
            logger.error(f"[Cosmos] File URI missing for processing_id={processing_id}")
            return False

        # Treat as a master doc in Emails collection to keep only two collections overall
        # Partition key = id
        file_doc_id = file_metadata.get("id") or processing_id
        email_like_doc = {
            "id": file_doc_id,
            "processingId": processing_id,
            "sourceType": "file",
            "fileName": file_metadata.get("filename", "unknown"),
            "fileUri": file_uri,
            "attachmentCount": 0,
            "status": "processing",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }
        self.db.upsert_email(email_like_doc)

        # Send file for OCR
        self._send_to_ocr_engine(
            processing_id=processing_id,
            file_uri=file_uri,
            filename=file_metadata.get("filename", "unknown")
        )

        # Update status
        self.db.update_email_status(file_doc_id, "ocr_pending")
        logger.info(f"[Cosmos] File ingestion complete for id={file_doc_id}, sent to OCR.")
        return True

    def _send_to_ocr_engine(self, processing_id: str, file_uri: str, filename: str):
        """Send file to OCR engine for text extraction."""
        ocr_message = {
            "processing_id": processing_id,
            "file_uri": file_uri,
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat(),
            "action": "extract_text"
        }
        # Use a dedicated OCR queue
        send_to_service_bus(ocr_message, "ocr-processing-queue")
        logger.info(f"[OCR] queued: processing_id={processing_id}, file={filename}")

    def update_processing_status(self, email_or_file_id: str, status: str):
        """Update status of a master doc (Email or File) in Emails collection."""
        try:
            self.db.update_email_status(email_or_file_id, status)
            logger.info(f"[Cosmos] Updated status for {email_or_file_id} -> {status}")
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"[Cosmos] Failed to update status for {email_or_file_id}: {e}")


# -------------------------
# Service Bus Worker
# -------------------------
class IngestionWorker:
    """Worker class for processing Service Bus messages."""

    def __init__(self):
        self.engine = IngestionEngine()

    def _parse_message_body(self, message) -> Dict:
        """
        Robustly parse Service Bus message body to dict.
        Handles both AmqpAnnotatedMessage body sections and string bodies.
        """
        try:
            # For azure-servicebus v7, message.body is a generator of bytes sections
            if hasattr(message, "body"):
                data = b"".join(section for section in message.body)
                return json.loads(data.decode("utf-8"))
        except Exception:
            pass

        # Fallback: try str(message)
        try:
            return json.loads(str(message))
        except Exception:
            logger.exception("Failed to parse message body as JSON.")
            return {}

    def start_listening(self):
        """Start listening for messages from Service Bus."""
        # Hardcoded Service Bus connection string and queue name
        SERVICE_BUS_CONNECTION_STRING = "Endpoint=sb://insuranceapp123.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=SIIXcxsyJmH92UE4870jGqkeVtcAQdUm4+ASbKDk4vI="
        QUEUE_NAME = "insuranceapp"  # Change if your queue name is different
        try:
            with ServiceBusClient.from_connection_string(SERVICE_BUS_CONNECTION_STRING) as client:
                with client.get_queue_receiver(queue_name=QUEUE_NAME) as receiver:
                    logger.info("Ingestion worker (Cosmos) started, listening for messages...")

                    for message in receiver:
                        try:
                            body = self._parse_message_body(message)
                            pid = body.get("processing_id")
                            logger.info(f"[SB] Received message pid={pid}")

                            success = self.engine.process_ingestion_message(body)

                            if success:
                                receiver.complete_message(message)
                                logger.info("[SB] Message processed successfully")
                            else:
                                receiver.abandon_message(message)
                                logger.error("[SB] Message processing failed, message abandoned")

                        except Exception as e:
                            logger.exception(f"[SB] Error processing message: {e}")
                            receiver.dead_letter_message(message)

        except Exception as e:
            logger.exception(f"[SB] Ingestion worker error: {e}")
            raise


def start_ingestion_worker():
    """Start the ingestion worker."""
    worker = IngestionWorker()
    worker.start_listening()


if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    start_ingestion_worker()
