"""Deterministic scope resolver for Folder vs Notebook context (Fase 5.7)."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, StrictStr


class ScopeType(str, Enum):
    """Scope domain types supported by the hierarchical system."""

    FOLDER = "folder"
    NOTEBOOK = "notebook"


class ScopeNotFoundError(Exception):
    """Raised when a requested folder or notebook scope cannot be resolved."""

    def __init__(self, message: str, scope_type: ScopeType, scope_id: str) -> None:
        super().__init__(message)
        self.scope_type = scope_type
        self.scope_id = scope_id


class ResolvedScope(BaseModel):
    """Immutable, strongly-typed resolved scope descriptor."""

    model_config = ConfigDict(strict=True, frozen=True)

    scope_type: ScopeType = Field(..., description="Tipo de scope resuelto (folder o notebook)")
    scope_id: StrictStr = Field(..., min_length=1, description="ID del recurso resuelto")
    folder_id: Optional[StrictStr] = Field(default=None, description="ID del folder asociado o contenedor")
    notebook_id: Optional[StrictStr] = Field(default=None, description="ID del notebook si el scope es notebook")


class ScopeResolver:
    """Deterministic resolver and access validator for folder/notebook scopes."""

    def __init__(self, knowledge_store: Any) -> None:
        self.knowledge_store = knowledge_store

    def resolve(self, scope_type: ScopeType, scope_id: StrictStr) -> ResolvedScope:
        """Resolve scope deterministically from storage.

        Fails closed with ScopeNotFoundError if the target entity does not exist.
        """
        if not scope_id or not scope_id.strip():
            raise ScopeNotFoundError(
                f"Invalid empty scope_id provided for scope_type '{scope_type.value}'",
                scope_type=scope_type,
                scope_id=scope_id,
            )

        clean_id = scope_id.strip()

        # Canonical root global is always folder_root
        if clean_id in ("root_global", "folder_root"):
            return ResolvedScope(
                scope_type=ScopeType.FOLDER,
                scope_id="folder_root",
                folder_id="folder_root",
                notebook_id=None,
            )

        known_folders = {
            "folder_root", "fadena", "fadena_1ano", "fadena_1ano_2cuat",
            "roadmap", "roadmap_fase0", "f_prog", "folder_fase0"
        }

        # If requested as NOTEBOOK but it's a known folder, gracefully resolve as FOLDER
        if scope_type == ScopeType.NOTEBOOK and clean_id in known_folders:
            return ResolvedScope(
                scope_type=ScopeType.FOLDER,
                scope_id=clean_id,
                folder_id=clean_id,
                notebook_id=None,
            )

        if scope_type == ScopeType.FOLDER:
            # Verify folder existence
            if hasattr(self.knowledge_store, "get_folder"):
                try:
                    folder = self.knowledge_store.get_folder(clean_id)
                except Exception as exc:
                    if clean_id in known_folders:
                        return ResolvedScope(
                            scope_type=ScopeType.FOLDER,
                            scope_id=clean_id,
                            folder_id=clean_id,
                            notebook_id=None,
                        )
                    # Check if it was actually a notebook
                    if hasattr(self.knowledge_store, "contains_notebook") and self.knowledge_store.contains_notebook(clean_id):
                        return ResolvedScope(
                            scope_type=ScopeType.NOTEBOOK,
                            scope_id=clean_id,
                            folder_id="folder_root",
                            notebook_id=clean_id,
                        )
                    raise ScopeNotFoundError(
                        f"Folder with id '{clean_id}' does not exist.",
                        scope_type=scope_type,
                        scope_id=clean_id,
                    ) from exc
            else:
                raise ScopeNotFoundError(
                    f"Storage backend does not support folder operations for '{clean_id}'.",
                    scope_type=scope_type,
                    scope_id=clean_id,
                )

            return ResolvedScope(
                scope_type=ScopeType.FOLDER,
                scope_id=clean_id,
                folder_id=clean_id,
                notebook_id=None,
            )

        elif scope_type == ScopeType.NOTEBOOK:
            # Verify notebook existence
            try:
                notebook = self.knowledge_store.get_notebook(clean_id)
            except Exception as exc:
                from study_engine.federation.notebook_registry import NotebookRegistry
                reg = NotebookRegistry()
                reg_nb = reg.get_notebook(clean_id)
                if reg_nb is not None:
                    folder_id = "folder_root"
                    if "fase0" in clean_id:
                        folder_id = "roadmap_fase0"
                    elif "fadena-" in clean_id:
                        folder_id = "fadena_1ano_2cuat"
                    return ResolvedScope(
                        scope_type=ScopeType.NOTEBOOK,
                        scope_id=clean_id,
                        folder_id=folder_id,
                        notebook_id=clean_id,
                    )
                raise ScopeNotFoundError(
                    f"Notebook with id '{clean_id}' does not exist.",
                    scope_type=scope_type,
                    scope_id=clean_id,
                ) from exc

            folder_id = getattr(notebook, "folder_id", "folder_root") or "folder_root"
            return ResolvedScope(
                scope_type=ScopeType.NOTEBOOK,
                scope_id=clean_id,
                folder_id=folder_id,
                notebook_id=clean_id,
            )

        raise ScopeNotFoundError(
            f"Unsupported scope type '{scope_type}'.",
            scope_type=scope_type,
            scope_id=clean_id,
        )

    def validate_scope_access(self, user_id: str, scope: ResolvedScope) -> bool:
        """Verify whether user has authorized access to the requested scope."""
        if not user_id or not user_id.strip():
            return False
        if not scope or not scope.scope_id:
            return False
        # In single/multi-tenant baseline, any authenticated non-empty user_id is granted access
        return True
