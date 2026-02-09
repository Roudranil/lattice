import ast
import builtins
import inspect
import typing
from functools import wraps
from typing import Annotated, Any, TypeVar, get_args, get_origin

from docstring_parser import parse
from langchain.tools import tool
from pydantic import ConfigDict, Field, create_model

_ALLOWED_NAMES = {
    **vars(typing),
    **vars(builtins),
}
_ALLOWED_NAMES.update(
    {
        "List": typing.List,
        "Dict": typing.Dict,
        "Tuple": typing.Tuple,
        "Set": typing.Set,
    }
)

T = TypeVar("T")


class _SkipSchemaMarker:
    pass


SkipSchema = Annotated[T, _SkipSchemaMarker]


def _is_skip_schema(annotation):
    if get_origin(annotation) is Annotated:
        _, *meta = get_args(annotation)
        return any(
            isinstance(m, _SkipSchemaMarker) or m is _SkipSchemaMarker for m in meta
        )
    return False


def _unwrap_skip_schema(annotation):
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        return args[0]
    return annotation


def _safe_eval_type(type_name: str) -> Any:
    """Safely convert docstring type string → Python type."""

    if not type_name:
        return Any

    try:
        node = ast.parse(type_name, mode="eval").body
        return _resolve_ast_node(node)
    except Exception:
        return Any


def _resolve_ast_node(node):
    if isinstance(node, ast.Name):
        return _resolve_name(node.id)

    if isinstance(node, ast.Subscript):
        base = _resolve_ast_node(node.value)
        args = _resolve_subscript(node.slice)
        return base[args]

    if isinstance(node, ast.Tuple):
        return tuple(_resolve_ast_node(el) for el in node.elts)

    raise ValueError("Unsupported type expression")


def _resolve_subscript(slice_node):
    if isinstance(slice_node, ast.Tuple):
        return tuple(_resolve_ast_node(el) for el in slice_node.elts)

    return _resolve_ast_node(slice_node)


def _resolve_name(name):
    if name in _ALLOWED_NAMES:
        return _ALLOWED_NAMES[name]

    raise ValueError(f"Unsupported type name: {name}")


def _is_optional(annotation):
    origin = get_origin(annotation)
    if origin is typing.Union:
        return type(None) in get_args(annotation)
    return False


def _merge_docstring(doc):
    """Merge short + long description cleanly."""
    parts = []
    if doc.short_description:
        parts.append(doc.short_description.strip())
    if doc.long_description:
        parts.append(doc.long_description.strip())
    return "\n\n".join(parts).strip()


def wrap_tool_with_error_handling(func):
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapped(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return f"Error: {e}"
    else:

        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return f"Error: {e}"

    return wrapped


def wrap_tool_with_auto_doc(func):
    raw_doc = inspect.getdoc(func) or ""
    doc = parse(raw_doc)

    signature = inspect.signature(func)
    annotations = typing.get_type_hints(func, include_extras=True)

    fields = {}

    # build parameter schema
    for name, param in signature.parameters.items():
        doc_param = next((p for p in doc.params if p.arg_name == name), None)
        # resolve types
        # there may be some weird types at times
        annotation = annotations.get(name)
        if annotation and _is_skip_schema(annotation):
            continue
        if annotation is None and doc_param and doc_param.type_name:
            annotation = _safe_eval_type(doc_param.type_name)
        if annotation is None:
            annotation = Any

        # resolve description
        description = doc_param.description if doc_param else ""

        # what if there are default values
        default = ...
        if param.default is not inspect.Parameter.empty:
            default = param.default

        # infer optionals
        if default is None and not _is_optional(annotation):
            annotation = typing.Optional[annotation]

        fields[name] = (annotation, Field(default=default, description=description))

    # resolve func description
    # return_description = doc.returns.description if doc.returns else None
    # resolve tool description
    tool_description = _merge_docstring(doc)
    # create pydantic schema
    args_schema = create_model(
        f"{func.__name__}",
        __doc__=tool_description,
        **fields,
    )
    args_schema.model_config = ConfigDict(
        json_schema_extra={"description": tool_description}
    )
    return tool(
        wrap_tool_with_error_handling(func),
        args_schema=args_schema,
        description=tool_description,
    )
