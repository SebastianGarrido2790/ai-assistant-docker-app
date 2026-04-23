"""
OpenTelemetry integration for tracing and metrics.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

def setup_telemetry():
    """Configure OpenTelemetry Tracer Provider."""
    provider = TracerProvider()
    
    # Export spans to console for now, or could use OTLP exporter if we had a backend
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)

setup_telemetry()
tracer = trace.get_tracer("ai-assistant-tracer")
