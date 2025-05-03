"""
Core exception classes for the application.
"""

class CoreException(Exception):
    """Base exception for all core-related exceptions."""
    pass

class ConfigurationError(CoreException):
    """Exception raised for errors in the configuration."""
    pass

class ComponentRegistryError(CoreException):
    """Exception raised for errors in the component registry."""
    pass

class WorkflowError(CoreException):
    """Exception raised for errors in workflow execution."""
    pass

class ServiceError(CoreException):
    """Exception raised for errors in service operations."""
    pass

class InitializationError(CoreException):
    """Exception raised for errors during application initialization."""
    pass 