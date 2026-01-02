"""Custom exceptions for PyAutoGUI.
"""

class PyAutoGUIException(Exception):
    """PyAutoGUI code will raise this exception class for any invalid actions. If PyAutoGUI raises some other exception,
    you should assume that this is caused by a bug in PyAutoGUI itself (including a failure to catch potential
    exceptions raised by PyAutoGUI).
    """


class FailSafeException(PyAutoGUIException):
    """This exception is raised by PyAutoGUI functions when the user puts the mouse cursor into one of the "failsafe
    points" (by default, one of the four corners of the primary monitor). This exception shouldn't be caught; it's
    meant to provide a way to terminate a misbehaving script.
    """


class ImageNotFoundException(PyAutoGUIException):
    """This exception is the PyAutoGUI version of PyScreeze's `ImageNotFoundException`, which is raised when a locate*()
    function call is unable to find an image.

    Ideally, `pyscreeze.ImageNotFoundException` should never be raised by PyAutoGUI.
    """
