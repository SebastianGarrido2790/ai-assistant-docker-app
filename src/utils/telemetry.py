"""
OpenTelemetry integration for tracing and metrics.

Supports two exporter backends, selected via the OTEL_EXPORTER_TYPE
environment variable:
  - "console" (default): Prints spans to stdout. Ideal for local development.
  - "otlp": Ships spans via HTTP/Protobuf to an OTLP-compatible backend
    (e.g., Jaeger, Grafana Tempo). Requires OTEL_EXPORTER_OTLP_ENDPOINT
    to be set (default: http://localhost:4318).
"""

import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Read exporter config at import time — these are stable for the lifetime of the process.
OTEL_EXPORTER_TYPE = os.environ.get("OTEL_EXPORTER_TYPE", "console").lower()
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"
)


def setup_telemetry() -> None:
    """Configure OpenTelemetry Tracer Provider with env-driven exporter selection.

    Reads ``OTEL_EXPORTER_TYPE`` to choose between console (stdout) and OTLP
    (Jaeger/Tempo) exporters. The OTLP endpoint is resolved from
    ``OTEL_EXPORTER_OTLP_ENDPOINT``.
    """
    provider = TracerProvider()

    if OTEL_EXPORTER_TYPE == "otlp":
        # Lazy import so the package is only required when OTLP is enabled.
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=f"{OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces")
    else:
        exporter = ConsoleSpanExporter()

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


setup_telemetry()
tracer = trace.get_tracer("ai-assistant-tracer")
