"""
WSGI config for faulty project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from uwsgidecorators import postfork

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'faulty.settings')

application = get_wsgi_application()


@postfork
def init_tracing():
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'))
    ))
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(
        ConsoleSpanExporter()
    ))
