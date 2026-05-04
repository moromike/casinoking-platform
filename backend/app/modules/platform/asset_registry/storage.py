from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Protocol


class AssetStorage(Protocol):
    def write_if_missing(self, *, relative_path: str, content: bytes) -> None:
        ...

    def exists(self, *, relative_path: str) -> bool:
        ...


class FilesystemAssetStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write_if_missing(self, *, relative_path: str, content: bytes) -> None:
        target = self._resolve(relative_path)
        if target.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def exists(self, *, relative_path: str) -> bool:
        return self._resolve(relative_path).exists()

    def _resolve(self, relative_path: str) -> Path:
        pure_path = PurePosixPath(relative_path)
        if pure_path.is_absolute() or ".." in pure_path.parts:
            raise ValueError("Asset path must be relative and normalized")
        return self.root.joinpath(*pure_path.parts)
