# DEPENDENCIES
import os
import logging
import warnings
from openai import AsyncOpenAI
from .model_config import TIMEOUT
from .model_config import MAX_RETRIES
from .model_config import OPENAI_API_KEY

# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# LOGGING 
logger = logging.getLogger(__name__)


# OPENAI CLIENT CREATOR
async def create_openai_client() -> AsyncOpenAI:
    """
    Creates / initializes the OpenAI client for the GPT-3.5-Turbo-Instruct model

    Errors:
    -------
        EnvironmentVariableError : If required environment variables are not set or invalid type
        
        ClientCreationError      : If there is an error during the creation of the OpenAI client

    Returns:
    --------
           { Asynchronous }      : An instance of AsyncOpenAI client
    """
    # VALIDATE ENVIRONMENT VARIABLES
    if (not all([OPENAI_API_KEY, MAX_RETRIES, TIMEOUT])):
        error_message = ("EnvironmentVariableError: Missing required environment variables."
                         "Ensure 'OPENAI_API_KEY', 'TIMEOUT' & 'MAX_RETRIES' are set")
        
        logger.error(msg   = error_message, 
                     extra = {"request_id": "openai_client_creation"})
        
        return error_message
    
    try:
        # Initialize the Async OpenAI client
        openai_client = AsyncOpenAI(api_key     = OPENAI_API_KEY,
                                    timeout     = TIMEOUT,
                                    max_retries = MAX_RETRIES,
                                   )
        
        logger.info(msg   = 'Successfully created AsyncOpenAI API client', 
                    extra = {"request_id": "openai_client_creation"})
        
        return openai_client
    
    except Exception as ClientCreationError:
         exception_error_message = f"ClientCreationError: Error creating the AsyncOpenAI client: {repr(ClientCreationError)}"
         
         logger.error(msg      = exception_error_message, 
                      extra    = {"request_id": "openai_client_creation"}, 
                      exc_info = True)
         
         return exception_error_message
    

    