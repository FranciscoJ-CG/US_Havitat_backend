# /helpers/handle_exceptions.py
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings


def handle_exceptions(response_message,  scope, exception, error_code=status.HTTP_500_INTERNAL_SERVER_ERROR):   

    if settings.ENV == 'develop':
        print(f'error -------, {scope}-----> {response_message}')
        print(str(exception))

    if isinstance(exception, (DRFValidationError, DjangoValidationError)):
        error_detail = exception.detail if hasattr(exception, 'detail') else str(exception)
        return Response({'detail': error_detail}, status=status.HTTP_400_BAD_REQUEST)

    print(f'error -------, {scope}-----> {str(exception)}')
    # logger.debug(f'Error in {scope}: {str(exception)}')
    return Response({'detail': response_message}, status=error_code)
