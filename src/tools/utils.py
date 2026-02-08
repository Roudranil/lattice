import builtins
import inspect
import typing
from typing import Annotated, Any, TypeVar, get_args, get_origin

from docstring_parser import parse
from langchain.tools import tool
from pydantic import ConfigDict, Field, create_model

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


def _safe_eval_type(type_name: str):
    """Best effort conversion from docstring type string → python type."""
    if not type_name:
        return Any

    if hasattr(builtins, type_name):
        return getattr(builtins, type_name)

    try:
        return eval(type_name, vars(typing))
    except Exception:
        return Any


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


def tool_with_auto_doc(func):
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
        if param.default is not inspect._empty:
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
        __config__={
            "json_schema_extra": {
                "description": tool_description,
                # "returns": return_description,
            }
        },
        **fields,
    )
    args_schema.model_config = ConfigDict(
        json_schema_extra={"description": tool_description}
    )
    return tool(
        func,
        args_schema=args_schema,
        description=tool_description,
    )
