"""
Custom DRF exception handler — normalises all error responses to
{"detail": "..."} or {"field": ["..."]} so the React frontend has
a consistent shape to parse.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — let Django's 500 handler deal with it.
        return None

    # DRF already built a response; just make sure the status is passed
    # through cleanly so the frontend can rely on HTTP status codes.
    return response
