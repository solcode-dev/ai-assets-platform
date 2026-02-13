class DomainException(Exception):
    """기본 도메인 예외"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFoundException(DomainException):
    """리소스를 찾을 수 없을 때 발생하는 예외"""
    def __init__(self, resource: str, id_name: str = "ID", value: any = None):
        self.resource = resource
        self.id_name = id_name
        self.value = value
        message = f"{resource} with {id_name} {value} not found"
        super().__init__(message, status_code=404)

class ValidationException(DomainException):
    """데이터 검증 실패 시 발생하는 예외"""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)

class ExternalServiceException(DomainException):
    """외부 서비스 호출 실패 시 발생하는 예외 (Vertex AI 등)"""
    def __init__(self, message: str = "External service error"):
        super().__init__(message, status_code=502)  # Bad Gateway
