class AlgorithmRuntimeError(RuntimeError):
    """Base error raised by the algorithm runtime layer."""


class AlgorithmConfigurationError(AlgorithmRuntimeError):
    """The algorithm manifest is missing or invalid."""


class AlgorithmEnvironmentError(AlgorithmRuntimeError):
    """The requested runtime is unavailable or not installed."""


class AlgorithmExecutionError(AlgorithmRuntimeError):
    """The algorithm process failed or exceeded its timeout."""


class AlgorithmProtocolError(AlgorithmRuntimeError):
    """The algorithm did not return a valid AlgorithmResult payload."""
