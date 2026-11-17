"""
FastAPI router for Workspace File Management.
Provides endpoints for file tree inspection, reading file contents,
saving/updating files, and deleting workspace files.
Strictly enforces workspace containment and rejects path traversal.
"""

import logging
from fastapi import APIRouter, HTTPException, Response, status

from backend.app.schemas.files import (
    FileContentResponse,
    FileSaveRequest,
    FileSaveResponse,
    FileTreeResponse,
)
from backend.app.storage.file_store import (
    delete_file,
    get_file_tree,
    read_file,
    write_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects/{project_id}/files",
    tags=["files"],
)


@router.get("", response_model=FileTreeResponse)
@router.get("/", response_model=FileTreeResponse, include_in_schema=False)
def list_workspace_files(project_id: str) -> FileTreeResponse:
    """
    Get recursive file tree of the project workspace.
    """
    try:
        return get_file_tree(project_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Failed to build file tree for project '%s'", project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read workspace tree: {exc}",
        )


@router.get("/{path:path}", response_model=FileContentResponse)
def get_file_content(project_id: str, path: str) -> FileContentResponse:
    """
    Read the content and metadata of a specific file in the project workspace.
    """
    clean_path = path.strip()
    if not clean_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path cannot be empty.",
        )

    try:
        return read_file(project_id, clean_path)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except IsADirectoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Error reading file '%s' in project '%s'", path, project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {exc}",
        )


@router.put("/{path:path}", response_model=FileSaveResponse)
def save_workspace_file(
    project_id: str,
    path: str,
    body: FileSaveRequest,
) -> FileSaveResponse:
    """
    Create or save content to a file in the project workspace.
    Automatically creates any missing parent directories.
    """
    clean_path = path.strip()
    if not clean_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path cannot be empty.",
        )

    try:
        return write_file(project_id, clean_path, body.content)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except IsADirectoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Error writing file '%s' in project '%s'", path, project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {exc}",
        )


@router.delete("/{path:path}", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace_file(project_id: str, path: str) -> Response:
    """
    Delete a file from the project workspace.
    Prunes empty parent directories up to the workspace root.
    """
    clean_path = path.strip()
    if not clean_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path cannot be empty.",
        )

    try:
        delete_file(project_id, clean_path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Error deleting file '%s' in project '%s'", path, project_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {exc}",
        )
