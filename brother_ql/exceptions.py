
class BrotherQLError(Exception):
    pass

class BrotherQLUnsupportedCmd(BrotherQLError):
    pass

class BrotherQLUnknownModel(BrotherQLError):
    pass

class BrotherQLRasterError(BrotherQLError):
    pass
