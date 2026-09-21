"""Hierarchy domain package for Folder, Notebook Scope, ScopeResolver and FolderOrchestrator."""

from study_engine.hierarchy.folder import Folder
from study_engine.hierarchy.scope_resolver import (
    ResolvedScope,
    ScopeNotFoundError,
    ScopeResolver,
    ScopeType,
)
from study_engine.hierarchy.folder_orchestrator import FolderOrchestrator

__all__ = [
    "Folder",
    "ScopeType",
    "ResolvedScope",
    "ScopeResolver",
    "ScopeNotFoundError",
    "FolderOrchestrator",
]
