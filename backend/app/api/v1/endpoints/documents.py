import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.models.document import Category, Document, Tag
from app.schemas.auth import UserRead
from app.services.document_storage import ALLOWED_TYPES, MAX_FILE_BYTES, encrypt_and_store, extract_text, read_and_decrypt, remove_stored_file

router = APIRouter()


def _document_json(document: Document) -> dict:
    return {
        "id": str(document.id),
        "title": document.title,
        "filename": document.original_filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "category": document.category.name if document.category else None,
        "tags": [tag.name for tag in document.tags],
        "uploaded_at": document.uploaded_at.isoformat(),
        "is_sensitive": document.is_sensitive,
    }


@router.get("/categories")
async def list_categories(user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.owner_id == user.id).order_by(Category.name))
    return [{"id": str(item.id), "name": item.name} for item in result.scalars().all()]


@router.get("")
async def list_documents(
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Document).join(Category, isouter=True).where(
        or_(Document.owner_id == user.id, Category.name == "Case Reports")
    ).order_by(Document.uploaded_at.desc())
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Document.title.ilike(pattern), Document.original_filename.ilike(pattern), Document.extracted_text.ilike(pattern)))
    if category and category != "All categories":
        stmt = stmt.where(Category.name == category)
    result = await db.execute(stmt)
    return [_document_json(item) for item in result.scalars().unique().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None, max_length=240),
    category: str = Form(default="Uncategorized", max_length=80),
    tags: str = Form(default=""),
    user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Only PDF, JPG, PNG, and CSV files are supported")
    data = await file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(413, "File exceeds the 25 MB upload limit")
    category_result = await db.execute(select(Category).where(Category.owner_id == user.id, Category.name == category.strip()))
    category_record = category_result.scalars().first()
    if not category_record:
        category_record = Category(id=uuid.uuid4(), owner_id=user.id, name=category.strip() or "Uncategorized")
        db.add(category_record)
        await db.flush()
    storage_key, sha256 = encrypt_and_store(data, user.id)
    document = Document(
        id=uuid.uuid4(), owner_id=user.id, category_id=category_record.id,
        title=(title or Path(file.filename or "document").stem).strip(),
        original_filename=file.filename or "document", storage_key=storage_key,
        mime_type=file.content_type, size_bytes=len(data), sha256=sha256,
        extracted_text=extract_text(data, file.content_type), is_sensitive=True,
    )
    for name in {value.strip().lower() for value in tags.split(",") if value.strip()}:
        tag_result = await db.execute(select(Tag).where(Tag.owner_id == user.id, Tag.name == name))
        tag = tag_result.scalars().first()
        if not tag:
            tag = Tag(id=uuid.uuid4(), owner_id=user.id, name=name)
            db.add(tag)
        document.tags.append(tag)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return _document_json(document)


@router.get("/{document_id}/download")
async def download_document(document_id: uuid.UUID, user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalars().first()
    if not document:
        raise HTTPException(404, "Document not found")
    return Response(read_and_decrypt(document.storage_key), media_type=document.mime_type, headers={"Content-Disposition": f'attachment; filename="{document.original_filename}"'})


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: uuid.UUID, user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id, Document.owner_id == user.id))
    document = result.scalars().first()
    if not document:
        raise HTTPException(404, "Document not found")
    remove_stored_file(document.storage_key)
    await db.delete(document)
    await db.commit()