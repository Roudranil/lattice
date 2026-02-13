import ast
import builtins
import inspect
import typing
from copy import deepcopy
from functools import wraps
from typing import (
    Annotated,
    Any,
    Dict,
    Iterable,
    List,
    Set,
    Type,
    TypeVar,
    get_args,
    get_origin,
)

from docstring_parser import parse
from langchain.agents.middleware import AgentMiddleware
from langchain.tools import InjectedState, InjectedStore, ToolRuntime, tool
from pydantic import ConfigDict, Field, create_model
from pydantic.json_schema import SkipJsonSchema

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


class SkipSchemaMarker:
    pass


SkipSchema = Annotated[T, SkipSchemaMarker]

_SKIP_SCHEMA_TYPES: Set[Type[Any]] = {
    SkipSchema,
    SkipJsonSchema,
    InjectedState,
    InjectedStore,
    ToolRuntime,
}
_SKIP_SCHEMA_MARKERS: Set[Type[Any]] = {SkipSchemaMarker}


def _is_skip_schema(annotation: Any) -> bool:
    if annotation is None:
        return False
    origin = get_origin(annotation)
    # --- Handle Annotated[T, ...] ---
    if origin is Annotated:
        base, *meta = get_args(annotation)
        # Marker metadata check
        for m in meta:
            if isinstance(m, tuple(_SKIP_SCHEMA_MARKERS)) or m in _SKIP_SCHEMA_MARKERS:
                return True
        # Recurse into base
        return _is_skip_schema(base)
    # --- Handle typing generics safely ---
    if origin is not None:
        return _is_skip_schema(origin)
    # --- Handle real classes ONLY ---
    if inspect.isclass(annotation):
        for skip_type in _SKIP_SCHEMA_TYPES:
            if inspect.isclass(skip_type) and issubclass(annotation, skip_type):
                return True
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


def _wrap_tool_with_error_handling(func):
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


def wrap_tool_with_doc_and_error_handling(
    func,
    custom_name: str = None,
    custom_description: str = None,
    custom_param_descriptions: dict = {},
):
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
        _provided_custom_param_desc = custom_param_descriptions.get(name, None)
        description = (
            _provided_custom_param_desc
            if _provided_custom_param_desc
            else (doc_param.description if doc_param else "")
        )

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
    final_description = (
        custom_description if custom_description else _merge_docstring(doc)
    )

    # resolve custom name
    final_name = custom_name if custom_name else func.__name__
    # create pydantic schema
    args_schema = create_model(
        final_name,
        __doc__=final_description,
        **fields,
    )
    args_schema.model_config = ConfigDict(
        json_schema_extra={"title": final_name, "description": final_description}
    )
    return tool(
        _wrap_tool_with_error_handling(func),
        args_schema=args_schema,
        description=final_description,
    )


def filter_tool_from_middleware_by_name(
    middleware: AgentMiddleware | List[AgentMiddleware],
    include: str | List[str] | Dict[str, List[str]] = [],
    exclude: str | List[str] | Dict[str, List[str]] = [],
) -> AgentMiddleware | List[AgentMiddleware]:
    """Exclude tools from one or more middlewares by name.

    Parameters
    ----------
    middleware : AgentMiddleware | List[AgentMiddleware]
        The middleware or list of middleware to modify.
    include : str | List[str] | Dict[str, List[str]]
        The tool names to include in the middleware.
    exclude : str | List[str] | Dict[str, List[str]]
        The tool names to exclude from the middleware.

    Returns
    -------
    AgentMiddleware | List[AgentMiddleware]
        The modified middleware or list of middleware with the specified tools excluded
        or included based on the `include` flag.
    """
    # if the tool names have been provided as a dict
    # keys -> middleware names, values -> list of tool names to exclude from that middleware
    if isinstance(include, dict) or isinstance(exclude, dict):
        # middleware must be a list of middleware for this case
        if not isinstance(middleware, list):
            return middleware
        mw_map = {getattr(mw, "name", None): mw for mw in middleware}
        # iterate over all middleware names
        # and see which middleware matches the name from the middleware list
        # and recursively call the function to exclude the tools from that middleware
        keys = set()
        if isinstance(include, dict):
            keys.update(include.keys())
        if isinstance(exclude, dict):
            keys.update(exclude.keys())
        for mw_name in keys:
            if mw_name in mw_map:
                filter_tool_from_middleware_by_name(
                    mw_map[mw_name],
                    include.get(mw_name) if isinstance(include, dict) else include,
                    exclude.get(mw_name) if isinstance(exclude, dict) else exclude,
                )
        return middleware

    # if neither include nor exclude is provided, return the middleware as is
    if not include and not exclude:
        return middleware

    # now the base cases
    # convert single instances to list
    if not isinstance(middleware, list):
        middlewares = [middleware]
    else:
        middlewares = middleware
    # convert tool names to set
    # we do not want duplicate tool names
    if isinstance(include, str):
        include_set = {include}
    elif include is None:
        include_set = None
    else:
        include_set = set(include)

    if isinstance(exclude, str):
        exclude_set = {exclude}
    elif exclude is None:
        exclude_set = None
    else:
        exclude_set = set(exclude)
    # iterate over all middleware
    # filter out tools
    filtered_middlewares = []
    for mw in middlewares:
        # if the middleware does not have tools attribute or it is None, skip it
        if not hasattr(mw, "tools") or mw.tools is None:
            continue
        # single-pass filtering
        if include_set is not None:
            mw.tools = [
                tool for tool in mw.tools if getattr(tool, "name", None) in include_set
            ]
        if exclude_set is not None:
            mw.tools = [
                tool
                for tool in mw.tools
                if getattr(tool, "name", None) not in exclude_set
            ]
        filtered_middlewares.append(mw)

    return (
        filtered_middlewares[0]
        if len(filtered_middlewares) == 1
        else filtered_middlewares
    )


NODE_HOOKS: List[str] = [
    "before_agent",
    "before_model",
    "after_model",
    "after_agent",
]

WRAP_HOOKS: List[str] = [
    "wrap_model_call",
    "wrap_tool_call",
]


def _normalize_middlewares(middlewares: Any | Iterable[Any] | None) -> list[Any]:
    """normalize middleware input into list."""
    if middlewares is None:
        return []
    if isinstance(middlewares, Iterable) and not isinstance(middlewares, (str, bytes)):
        return list(middlewares)
    return [middlewares]


def _unwrap_callable(obj: Any) -> Any:
    """unwrap decorator stacks."""
    while hasattr(obj, "__wrapped__"):
        obj = obj.__wrapped__
    return obj


def _middleware_name(mw: Any) -> str:
    """resolve middleware display name."""
    if hasattr(mw, "name") and mw.name:
        return str(mw.name)
    if inspect.isfunction(mw):
        return _unwrap_callable(mw).__name__
    if hasattr(mw, "__class__"):
        return mw.__class__.__name__
    return str(mw)


def _hook_is_overridden(mw: Any, hook: str) -> bool:
    """detect whether middleware overrides hook."""
    method = getattr(mw, hook, None)
    if method is None or not callable(method):
        return False
    cls = type(mw)
    base_method = None
    for base in cls.__mro__[1:]:
        if hook in base.__dict__:
            base_method = base.__dict__[hook]
            break
    if base_method is None:
        return True
    method_func = getattr(method, "__func__", method)
    return method_func is not base_method


def _middlewares_for_hook(middlewares: list[Any], hook: str) -> list[str]:
    """collect middleware names implementing hook."""
    return [_middleware_name(mw) for mw in middlewares if _hook_is_overridden(mw, hook)]


def _print_section(title: str, names: list[str]) -> None:
    """print middleware section."""
    if not names:
        return
    print(f"{title}:")
    for name in names:
        print(f"  {name}")
    print()


def _print_wrap_chain(title: str, names: list[str]) -> None:
    """print nested wrap chain."""
    print(f"{title}:")
    if not names:
        return
    for depth, name in enumerate(names, 1):
        print(f"{'  ' * depth}{name}")
    print()


def visualize_middleware_hook_order(
    middlewares: Any | Iterable[Any] | None,
) -> None:
    """print middleware hook execution order."""
    middleware_list = _normalize_middlewares(middlewares)
    before_agent = _middlewares_for_hook(middleware_list, "before_agent")
    before_model = _middlewares_for_hook(middleware_list, "before_model")
    wrap_model = _middlewares_for_hook(middleware_list, "wrap_model_call")
    wrap_tool = _middlewares_for_hook(middleware_list, "wrap_tool_call")
    after_model = list(reversed(_middlewares_for_hook(middleware_list, "after_model")))
    after_agent = list(reversed(_middlewares_for_hook(middleware_list, "after_agent")))
    _print_section("before_agent order", before_agent)
    _print_section("before_model order", before_model)
    _print_wrap_chain("wrap_model_call nesting", wrap_model)
    _print_section("after_model order", after_model)
    _print_wrap_chain("wrap_tool_call nesting", wrap_tool)
    _print_section("after_agent order", after_agent)


__all__ = [
    "SkipSchema",
    "wrap_tool_with_doc_and_error_handling",
    "filter_tool_from_middleware_by_name",
    "visualize_middleware_hook_order",
]
