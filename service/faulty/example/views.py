import random

from django.http import HttpResponse


def f0():
    a = 1/0


def f1():
    a = a


def f2():
    a = []
    a[1]


def f3():
    raise Exception("example")


def index(request):
    random.choice([f0, f1, f2, f3])()
    return HttpResponse("App is faulty!")


def manual(request):
    import logging
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    import os

    resource = Resource(attributes={
        "service.name": "service-app"
    })

    class SpanFormatter(logging.Formatter):
        def format(self, record):
            trace_id = trace.get_current_span().get_span_context().trace_id
            if trace_id == 0:
                record.trace_id = None
            else:
                record.trace_id = "{trace:032x}".format(trace=trace_id)
            return super().format(record)

    trace.set_tracer_provider(
        TracerProvider(resource=resource)
    )
    otlp_exporter = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"), insecure=True)
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    tracer = trace.get_tracer(__name__)
    log = logging.getLogger(__name__)
    ch = logging.StreamHandler()
    log.setLevel(logging.ERROR)
    ch.setFormatter(
        SpanFormatter(
            'time="%(asctime)s" service=%(name)s level=%(levelname)s %(message)s trace_id=%(trace_id)s'
        )
    )
    with tracer.start_as_current_span("exc") as span:
        try:
            random.choice([f0, f1, f2, f3])()
        except Exception as ex:
            trace_id = trace.get_current_span().get_span_context().trace_id
            log.error("trace id: {trace:032x}".format(trace=trace_id))
            span.record_exception(ex)
    return HttpResponse("App is faulty!")
