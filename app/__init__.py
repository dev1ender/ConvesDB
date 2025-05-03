"""
Main application package.

This package provides a framework-agnostic API for processing natural language queries.
"""

from app.core import get_app, app_instance
from app.factory import ApplicationFactory
from app.application import Application

__all__ = ['app_instance', 'get_app', 'ApplicationFactory', 'Application']

__version__ = "1.0.0"
__author__ = "dev1ender" 