"""
Vehicle Rental System — Project Agent
======================================
A self-contained agentic loop that inspects the codebase, surfaces
improvement suggestions, and can scaffold new endpoints.

Design
------
Follows a minimal ReAct pattern (Reason → Act → Observe) implemented in
plain Python — no LangChain, no external agent framework required.

Each "tool" is a regular function.  The agent maintains a state dict and a
history of tool results.  The planner decides which tool to call next based
on what has already been collected.

Usage
-----
    # From the project root:
    python -m agent.agent

    # Or programmatically:
    from agent.agent import ProjectAgent
    agent = ProjectAgent(".")
    suggestions = agent.run_analysis()
    for s in suggestions:
        print(s)
"""

from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Suggestion:
    file: str
    category: str
    message: str
    severity: str = "warning"   # info | warning | error
    line: int | None = None

    def __str__(self) -> str:
        icon = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(self.severity, "·")
        loc = f":{self.line}" if self.line else ""
        return f"  {icon} [{self.category}] {self.file}{loc} — {self.message}"


@dataclass
class ToolResult:
    tool: str
    success: bool
    output: Any
    error: str = ""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class ProjectAgent:
    """
    Minimal ReAct agent that inspects a FastAPI project.

    Capabilities
    ────────────
    1. read_files   — walk the project tree and load all .py source files
    2. analyze      — apply heuristic rules; populate self.state["suggestions"]
    3. add_endpoint — generate a new FastAPI endpoint from a spec dict and
                      optionally append it to the matching router file
    """

    _SKIP_DIRS = {"__pycache__", ".venv", "venv", ".git", "node_modules", "dist"}

    def __init__(self, project_root: str = ".", max_steps: int = 20) -> None:
        self.root = Path(project_root).resolve()
        self.max_steps = max_steps
        self.state: dict[str, Any] = {"files": {}, "suggestions": [], "step": 0}
        self.history: list[ToolResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_analysis(self) -> list[Suggestion]:
        """Execute the read → analyze pipeline and return suggestions."""
        self._act("read_files")
        self._act("analyze")
        return self.state["suggestions"]

    def add_endpoint(self, spec: dict) -> tuple[str, Path | None]:
        """
        Generate endpoint code from *spec* and optionally write it.

        Returns (generated_code, path_written_to | None).
        Spec keys:
            resource      str   e.g. "Office"
            method        str   get | post | patch | delete   (default: get)
            path          str   URL path (default: /<resource>s/{id})
            summary       str   one-line doc string (optional)
            require_auth  bool  (default: True)
            require_admin bool  (default: False)
            write         bool  append to router file?  (default: False)
        """
        if not self.state["files"]:
            self._act("read_files")
        result = self._act("add_endpoint", spec)
        if not result.success:
            return result.error, None
        code, dest = result.output
        return code, dest

    def interactive(self) -> None:
        """Simple REPL — type 'help' for commands."""
        print("Vehicle Rental System — Project Agent")
        print("Type 'help' for available commands.\n")
        commands = {
            "analyze":      self._cmd_analyze,
            "add-endpoint": self._cmd_add_endpoint,
            "history":      self._cmd_history,
            "help":         self._cmd_help,
            "quit":         None,
        }
        while True:
            try:
                raw = input("agent> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                break
            if raw == "quit":
                print("Bye.")
                break
            fn = commands.get(raw)
            if fn is None and raw:
                print(f"  Unknown command '{raw}'. Try: {', '.join(commands)}")
            elif fn:
                fn()

    # ------------------------------------------------------------------
    # Internal execution engine
    # ------------------------------------------------------------------

    def _act(self, tool: str, args: dict | None = None) -> ToolResult:
        self.state["step"] += 1
        args = args or {}
        _tools = {
            "read_files":   self._tool_read_files,
            "analyze":      self._tool_analyze,
            "add_endpoint": self._tool_add_endpoint,
        }
        fn = _tools.get(tool)
        if fn is None:
            result = ToolResult(tool=tool, success=False, output=None,
                                error=f"Unknown tool '{tool}'")
        else:
            try:
                output = fn(**args)
                result = ToolResult(tool=tool, success=True, output=output)
            except Exception as exc:
                result = ToolResult(tool=tool, success=False, output=None, error=str(exc))
        self.history.append(result)
        return result

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def _tool_read_files(self) -> dict[str, str]:
        files: dict[str, str] = {}
        for path in sorted(self.root.rglob("*.py")):
            if any(part in self._SKIP_DIRS for part in path.parts):
                continue
            rel = str(path.relative_to(self.root))
            try:
                files[rel] = path.read_text(encoding="utf-8")
            except OSError:
                pass
        self.state["files"] = files
        return files

    def _tool_analyze(self) -> list[Suggestion]:
        files: dict[str, str] = self.state.get("files", {})
        suggestions: list[Suggestion] = []
        for rel, src in files.items():
            suggestions += _check_long_functions(rel, src)
            suggestions += _check_bare_except(rel, src)
            suggestions += _check_missing_return_types(rel, src)
            suggestions += _check_todo_fixme(rel, src)
            suggestions += _check_router_missing_auth(rel, src)
            suggestions += _check_hardcoded_secrets(rel, src)
        suggestions += _check_missing_test_coverage(files)
        suggestions += _check_missing_pagination(files)
        self.state["suggestions"] = suggestions
        return suggestions

    def _tool_add_endpoint(
        self,
        resource: str,
        method: str = "get",
        path: str = "",
        summary: str = "",
        require_auth: bool = True,
        require_admin: bool = False,
        write: bool = False,
    ) -> tuple[str, Path | None]:
        method = method.lower()
        url_path = path or f"/{resource.lower()}s/{{id}}"
        response_model = f"{resource.capitalize()}Response"
        func_name = f"{method}_{resource.lower()}"

        # Build the dependencies list for the decorator
        dep_parts: list[str] = []
        if require_admin:
            dep_parts.append("Depends(require_admin)")
        elif require_auth:
            dep_parts.append("Depends(get_current_employee)")

        deps_str = ""
        if dep_parts:
            inner = ", ".join(dep_parts)
            deps_str = f",\n    dependencies=[{inner}]"

        status_code = {
            "post":   "status.HTTP_201_CREATED",
            "delete": "status.HTTP_204_NO_CONTENT",
        }.get(method, "status.HTTP_200_OK")

        if method == "delete":
            return_hint = "None"
            fn_params = f"{resource.lower()}_id: int, db: Session = Depends(get_db)"
            body = textwrap.dedent(f"""\
                try:
                    {resource.lower()}_svc.delete_{resource.lower()}(db, {resource.lower()}_id)
                except NotFoundError as exc:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
                except BusinessRuleError as exc:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))""")
        elif method == "post":
            return_hint = response_model
            fn_params = f"data: {resource.capitalize()}Create, db: Session = Depends(get_db)"
            body = f"return {resource.lower()}_svc.create_{resource.lower()}(db, data)"
        elif method == "patch":
            return_hint = response_model
            fn_params = f"{resource.lower()}_id: int, data: {resource.capitalize()}Update, db: Session = Depends(get_db)"
            body = textwrap.dedent(f"""\
                try:
                    return {resource.lower()}_svc.update_{resource.lower()}(db, {resource.lower()}_id, data)
                except NotFoundError as exc:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))""")
        else:  # get
            return_hint = response_model
            fn_params = f"{resource.lower()}_id: int, db: Session = Depends(get_db)"
            body = textwrap.dedent(f"""\
                try:
                    return {resource.lower()}_svc.get_{resource.lower()}(db, {resource.lower()}_id)
                except NotFoundError as exc:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))""")

        summary_line = f'    """{summary}"""\n' if summary else ""
        indented_body = textwrap.indent(body, "    ")
        resp_model_arg = "None" if method == "delete" else response_model

        code = textwrap.dedent(f"""\
            @router.{method}(
                "{url_path}",
                response_model={resp_model_arg},
                status_code={status_code}{deps_str},
            )
            def {func_name}(
                {fn_params},
            ) -> {return_hint}:
            {summary_line}{indented_body}
            """)

        dest: Path | None = None
        if write:
            dest = self._append_to_router(resource.lower(), code)

        return code, dest

    # ------------------------------------------------------------------
    # REPL commands
    # ------------------------------------------------------------------

    def _cmd_analyze(self) -> None:
        suggestions = self.run_analysis()
        if not suggestions:
            print("  ✓ No issues found — project looks clean!")
            return
        counts = {"error": 0, "warning": 0, "info": 0}
        for s in suggestions:
            counts[s.severity] += 1
            print(s)
        totals = ", ".join(f"{v} {k}(s)" for k, v in counts.items() if v)
        print(f"\n  {len(suggestions)} suggestion(s): {totals}")

    def _cmd_add_endpoint(self) -> None:
        print("Describe the new endpoint:")
        resource = input("  Resource name (e.g. Office): ").strip()
        if not resource:
            print("  Cancelled.")
            return
        method    = input("  HTTP method [get/post/patch/delete]: ").strip().lower() or "get"
        url_path  = input(f"  URL path (default: /{resource.lower()}s/{{id}}): ").strip()
        summary   = input("  Summary / docstring (optional): ").strip()
        admin_req = input("  Require admin role? [y/N]: ").strip().lower() == "y"

        code, _ = self.add_endpoint({
            "resource": resource, "method": method, "path": url_path,
            "summary": summary, "require_auth": True, "require_admin": admin_req,
            "write": False,
        })

        print("\n--- Generated code ---")
        print(code)
        print("----------------------")

        if input("Append to router file? [y/N]: ").strip().lower() == "y":
            dest = self._append_to_router(resource.lower(), code)
            print(f"  Written → {dest}")

    def _cmd_history(self) -> None:
        if not self.history:
            print("  No tool calls yet.")
            return
        for i, r in enumerate(self.history, 1):
            status = "✓" if r.success else "✗"
            preview = str(r.output)[:60].replace("\n", " ") if r.success else r.error
            print(f"  {i:2}. {status} {r.tool:<18} {preview}")

    @staticmethod
    def _cmd_help() -> None:
        print(
            "  analyze      — scan all .py files and report issues\n"
            "  add-endpoint — interactively generate a new FastAPI endpoint\n"
            "  history      — show tool call history\n"
            "  quit         — exit\n"
        )

    # ------------------------------------------------------------------
    # File I/O helper
    # ------------------------------------------------------------------

    def _append_to_router(self, resource: str, code: str) -> Path:
        router_path = self.root / "routers" / f"{resource}.py"
        if router_path.exists():
            existing = router_path.read_text(encoding="utf-8")
            router_path.write_text(existing.rstrip() + "\n\n\n" + code, encoding="utf-8")
        else:
            header = textwrap.dedent(f"""\
                from fastapi import APIRouter, Depends, HTTPException, status
                from sqlalchemy.orm import Session

                from core.dependencies import get_current_employee, require_admin
                from database import get_db
                from exceptions import BusinessRuleError, NotFoundError
                from services import {resource} as {resource}_svc

                router = APIRouter(
                    prefix="/{resource}s",
                    tags=["{resource}s"],
                    dependencies=[Depends(get_current_employee)],
                )

                """)
            router_path.write_text(header + code, encoding="utf-8")
        return router_path


# ---------------------------------------------------------------------------
# Heuristic check functions  (pure — no side effects, easy to unit-test)
# ---------------------------------------------------------------------------


def _check_long_functions(path: str, source: str) -> list[Suggestion]:
    """Functions longer than 40 lines are candidates for splitting."""
    out: list[Suggestion] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno
            if length > 40:
                out.append(Suggestion(
                    file=path, line=node.lineno, category="complexity",
                    message=f"'{node.name}' is {length} lines — consider splitting",
                    severity="warning",
                ))
    return out


def _check_bare_except(path: str, source: str) -> list[Suggestion]:
    """Bare `except:` silently swallows SystemExit and KeyboardInterrupt."""
    out: list[Suggestion] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            out.append(Suggestion(
                file=path, line=node.lineno, category="error-handling",
                message="Bare `except:` — use `except Exception:` to avoid catching system exits",
                severity="warning",
            ))
    return out


def _check_missing_return_types(path: str, source: str) -> list[Suggestion]:
    """Public functions without a return-type annotation."""
    if any(path.startswith(p) for p in ("tests/", "agent/")):
        return []
    out: list[Suggestion] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_") and node.returns is None:
                out.append(Suggestion(
                    file=path, line=node.lineno, category="type-hints",
                    message=f"'{node.name}' is missing a return type annotation",
                    severity="info",
                ))
    return out


def _check_todo_fixme(path: str, source: str) -> list[Suggestion]:
    out: list[Suggestion] = []
    for i, line in enumerate(source.splitlines(), 1):
        if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.IGNORECASE):
            out.append(Suggestion(
                file=path, line=i, category="tech-debt",
                message=line.strip(), severity="info",
            ))
    return out


def _check_router_missing_auth(path: str, source: str) -> list[Suggestion]:
    """Router files with no auth dependency are likely missing protection."""
    if "routers/" not in path:
        return []
    exempt = {"health.py", "auth.py"}
    if Path(path).name in exempt:
        return []
    has_auth = any(kw in source for kw in ("get_current_employee", "require_admin", "dependencies="))
    if not has_auth:
        return [Suggestion(
            file=path, category="security",
            message="No auth dependency found — endpoints may be publicly accessible",
            severity="error",
        )]
    return []


def _check_hardcoded_secrets(path: str, source: str) -> list[Suggestion]:
    patterns = [
        (r'password\s*=\s*["\'][^"\']{4,}["\']', "hardcoded password"),
        (r'secret\s*=\s*["\'][^"\']{4,}["\']',   "hardcoded secret"),
        (r'api_key\s*=\s*["\'][^"\']{4,}["\']',   "hardcoded API key"),
    ]
    out: list[Suggestion] = []
    for i, line in enumerate(source.splitlines(), 1):
        lower = line.lower()
        for pattern, label in patterns:
            if re.search(pattern, lower):
                out.append(Suggestion(
                    file=path, line=i, category="security",
                    message=f"Possible {label} — use an environment variable instead",
                    severity="error",
                ))
    return out


def _check_missing_test_coverage(files: dict[str, str]) -> list[Suggestion]:
    tested = {
        re.sub(r"^tests/test_", "", k).replace(".py", "")
        for k in files if k.startswith("tests/test_")
    }
    out: list[Suggestion] = []
    for path in files:
        if not path.startswith(("routers/", "services/")):
            continue
        stem = Path(path).stem
        if stem in ("__init__", "health") or stem in tested:
            continue
        out.append(Suggestion(
            file=path, category="testing",
            message=f"No test file for '{stem}' — consider adding tests/test_{stem}.py",
            severity="warning",
        ))
    return out


def _check_missing_pagination(files: dict[str, str]) -> list[Suggestion]:
    out: list[Suggestion] = []
    for path, source in files.items():
        if "routers/" not in path:
            continue
        if re.search(r'@router\.get\(""\)', source) and "limit" not in source and "offset" not in source:
            out.append(Suggestion(
                file=path, category="usability",
                message="List endpoint has no pagination (limit/offset) — may return unbounded rows",
                severity="warning",
            ))
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    agent = ProjectAgent(root)
    agent.interactive()
