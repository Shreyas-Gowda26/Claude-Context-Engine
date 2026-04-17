"""AST-aware code chunking using tree-sitter."""
import hashlib

import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser

from context_engine.models import Chunk, ChunkType

_FUNCTION_TYPES = {
    "function_definition", "function_declaration", "method_definition", "arrow_function",
}
_CLASS_TYPES = {
    "class_definition", "class_declaration",
}

_LANGUAGES = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjavascript.language()),
}


class Chunker:
    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {}

    def _get_parser(self, language: str) -> Parser | None:
        if language not in _LANGUAGES:
            return None
        if language not in self._parsers:
            parser = Parser(_LANGUAGES[language])
            self._parsers[language] = parser
        return self._parsers[language]

    def chunk(self, source: str, file_path: str, language: str) -> list[Chunk]:
        parser = self._get_parser(language)
        if parser is None:
            return [self._fallback_chunk(source, file_path, language)]
        tree = parser.parse(source.encode("utf-8"))
        chunks = []
        self._walk(tree.root_node, source, file_path, language, chunks)
        if not chunks:
            return [self._fallback_chunk(source, file_path, language)]
        return chunks

    def _walk(self, node, source, file_path, language, chunks):
        if node.type in _FUNCTION_TYPES:
            chunks.append(self._node_to_chunk(node, source, file_path, language, ChunkType.FUNCTION))
        elif node.type in _CLASS_TYPES:
            chunks.append(self._node_to_chunk(node, source, file_path, language, ChunkType.CLASS))
        for child in node.children:
            self._walk(child, source, file_path, language, chunks)

    def _node_to_chunk(self, node, source, file_path, language, chunk_type):
        content = source[node.start_byte:node.end_byte]
        start_line = node.start_point.row + 1
        end_line = node.end_point.row + 1
        chunk_id = hashlib.sha256(
            f"{file_path}:{start_line}:{end_line}:{content[:100]}".encode()
        ).hexdigest()[:16]
        return Chunk(
            id=chunk_id, content=content, chunk_type=chunk_type,
            file_path=file_path, start_line=start_line, end_line=end_line, language=language,
        )

    def _fallback_chunk(self, source, file_path, language):
        chunk_id = hashlib.sha256(f"{file_path}:module".encode()).hexdigest()[:16]
        lines = source.strip().split("\n")
        return Chunk(
            id=chunk_id, content=source, chunk_type=ChunkType.MODULE,
            file_path=file_path, start_line=1, end_line=len(lines), language=language,
        )
