"""Runtime management of Telegram notification recipients."""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/telegram-recipients", tags=["Telegram Recipients"])


def _repo(request: Request):
    return request.app.state.recipient_repo


class RecipientPayload(BaseModel):
    chat_id: str


@router.get("", response_model=list[str], status_code=status.HTTP_200_OK)
def list_recipients(request: Request) -> list[str]:
    """Return all subscribed Telegram chat_ids."""
    return _repo(request).all()


@router.post("", response_model=list[str], status_code=status.HTTP_201_CREATED)
def add_recipient(payload: RecipientPayload, request: Request) -> list[str]:
    """Subscribe a chat_id. Returns 409 if already present."""
    added = _repo(request).add(payload.chat_id)
    if not added:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"chat_id '{payload.chat_id}' is already subscribed.",
        )
    return _repo(request).all()


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recipient(chat_id: str, request: Request) -> None:
    """Unsubscribe a chat_id. Returns 404 if not found."""
    if not _repo(request).remove(chat_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"chat_id '{chat_id}' is not subscribed.",
        )
