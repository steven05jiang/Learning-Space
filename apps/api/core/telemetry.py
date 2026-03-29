"""OpenTelemetry setup — traces to Phoenix, metrics to Prometheus.

Graceful degradation: if either backend is unreachable or setup fails,
a warning is logged and the service continues normally.
"""

import logging

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str, endpoint: str, app=None) -> bool:
    """Configure OTLP trace exporter → Phoenix. Returns True if successful."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            timeout=5,  # don't block app startup if Phoenix is slow
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        # Auto-instrument FastAPI — pass app instance so existing app gets patched
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        if app is not None:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        else:
            FastAPIInstrumentor().instrument(tracer_provider=provider)

        # Auto-instrument LangChain/LangGraph (OpenInference)
        from openinference.instrumentation.langchain import LangChainInstrumentor

        LangChainInstrumentor().instrument(tracer_provider=provider)

        logger.info("Tracing enabled → %s (service=%s)", endpoint, service_name)
        return True
    except Exception as e:
        logger.warning("Tracing setup failed, continuing without traces: %s", e)
        return False


def setup_metrics(service_name: str) -> bool:
    """Configure Prometheus scrape exporter — exposes /metrics for Prometheus to pull.
    Returns the ASGI app to mount, or None on failure.
    """
    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.prometheus import PrometheusMetricReader
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.resources import Resource
        from prometheus_client import make_asgi_app

        resource = Resource.create({"service.name": service_name})
        reader = PrometheusMetricReader()
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)

        logger.info("Metrics enabled → /metrics endpoint (service=%s)", service_name)
        return make_asgi_app()
    except Exception as e:
        logger.warning("Metrics setup failed, continuing without metrics: %s", e)
        return None


def setup_telemetry(
    service_name: str, traces_endpoint: str, metrics_enabled: bool, app=None
):
    """Initialize telemetry. Each backend fails independently.

    Returns the Prometheus ASGI app to mount at /metrics, or None.
    """
    if traces_endpoint:
        setup_tracing(service_name, traces_endpoint, app=app)
    else:
        logger.info("Tracing disabled (OTLP_TRACES_ENDPOINT not set)")

    if metrics_enabled:
        return setup_metrics(service_name)
    else:
        logger.info("Metrics disabled (PROMETHEUS_METRICS not set)")
        return None
