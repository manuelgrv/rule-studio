from dataclasses import dataclass

@dataclass
class Diagnostic:
    code: str
    message: str
    path: str = "$"
    line: int | None = None
    column: int | None = None

class CompileError(ValueError):
    def __init__(self, code, message, path="$", line=None, column=None):
        self.diagnostic = Diagnostic(code, message, path, line, column)
        super().__init__(f"{code} at {path}: {message}")

class EvaluationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)
