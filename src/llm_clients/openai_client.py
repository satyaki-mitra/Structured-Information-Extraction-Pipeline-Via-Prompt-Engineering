# DEPENDENCIES
import json
import random
import asyncio
import logging
import warnings
from typing import Any
from typing import Dict
from typing import Optional
from openai import AsyncOpenAI
from config.settings import settings
from src.llm_clients.base_client import BaseLLMClient


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """
    OpenAI client implementation for GPT models: handles API interactions, retries, rate limiting, and error handling
    for OpenAI's completion and chat completion endpoints
    """
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None,
                 seed: Optional[int] = None, max_retries: Optional[int] = None, timeout: Optional[int] = None, base_delay: Optional[int] = None):
        """
        Initialize OpenAI client with configuration
        
        Arguments:
        ----------
            api_key      { str }   : OpenAI API key (defaults to settings)
           
            model_name   { str }   : Model name (defaults to settings)
           
            temperature  { float } : Sampling temperature (defaults to settings)
           
            max_tokens   { int }   : Maximum tokens in response (defaults to settings)
           
            seed         { int }   : Random seed for reproducibility (defaults to settings)
           
            max_retries  { int }   : Maximum retry attempts (defaults to settings)
           
            timeout      { int }   : Request timeout in seconds (defaults to settings)
           
            base_delay   { int }   : Base delay for exponential backoff (defaults to settings)
        """
        # Use settings as defaults
        api_key                             = api_key or settings.openai_api_key
        model_name                          = model_name or settings.openai_model_name
        
        super().__init__(api_key    = api_key, 
                         model_name = model_name,
                        )

        
        # Store configuration
        self.temperature                    = temperature if temperature is not None else settings.model_temperature
        self.max_tokens                     = max_tokens if max_tokens is not None else settings.max_tokens
        self.seed                           = seed if seed is not None else settings.model_seed
        self.max_retries                    = max_retries if max_retries is not None else settings.max_retries
        self.timeout                        = timeout if timeout is not None else settings.timeout
        self.base_delay                     = base_delay if base_delay is not None else settings.base_delay
        
        # Client instance (created lazily)
        self.client : Optional[AsyncOpenAI] = None
        
        logger.info(msg   = f"OpenAI client configured with model: {self.model_name}",
                    extra = {"request_id": "openai_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
    
    
    async def create_client(self) -> AsyncOpenAI:
        """
        Create and return AsyncOpenAI client instance
        
        Returns:
        --------
            { AsyncOpenAI } : Configured AsyncOpenAI client
        
        Raises:
        -------
            ValueError      : If API key or configuration is invalid

            Exception       : If client creation fails
        """
        if not self.validate_config():
            error_message = "Invalid OpenAI client configuration"
            
            logger.error(msg   = error_message,
                         extra = {"request_id": "client_creation", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            raise ValueError(error_message)
        
        try:
            self.client = AsyncOpenAI(api_key     = self.api_key,
                                      timeout     = self.timeout,
                                      max_retries = self.max_retries,
                                     )
            
            logger.info(msg   = "Successfully created AsyncOpenAI client",
                        extra = {"request_id": "client_creation", "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
            
            return self.client
        
        except Exception as client_error:
            error_message = f"Failed to create OpenAI client: {repr(client_error)}"
            
            logger.error(msg      = error_message,
                         extra    = {"request_id": "client_creation", "batch_id": "N/A", "batch_item_id": "N/A"},
                         exc_info = True,
                        )
            raise
    
    
    async def generate_completion(self, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None, 
                                  seed: Optional[int] = None, request_id: str = "completion") -> Dict[str, Any]:
        """
        Generate completion from OpenAI model with retry logic
        
        Arguments:
        ----------
            prompt      { str }   : The prompt to send to the model

            temperature { float } : Override default temperature (optional)
            
            max_tokens  { int }   : Override default max_tokens (optional)
            
            seed        { int }   : Override default seed (optional)
            
            request_id  { str }   : Request identifier for logging
        
        Returns:
        --------
            { Dict[str, Any] }    : Dictionary with keys:
                                    - 'text': The generated text
                                    - 'model': Model used
                                    - 'usage': Token usage information
        
        Raises:
        -------
            ValueError            : If prompt is empty
            
            Exception             : If all retry attempts fail
        """
        if not prompt or not prompt.strip():
            error_message = "Prompt cannot be empty"
            
            logger.error(msg   = error_message,
                         extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            raise ValueError(error_message)
        
        # Ensure client is created
        if not self.client:
            await self.create_client()
        
        # Use instance defaults if not overridden
        temperature = temperature if temperature is not None else self.temperature
        max_tokens  = max_tokens if max_tokens is not None else self.max_tokens
        seed        = seed if seed is not None else self.seed
        
        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(msg   = f"Attempt {attempt + 1}/{self.max_retries} for completion",
                             extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                            )
                
                # Call OpenAI API
                response = await self.client.completions.create(model       = self.model_name,
                                                                prompt      = prompt,
                                                                temperature = temperature,
                                                                max_tokens  = max_tokens,
                                                                seed        = seed,
                                                               )
                
                # Extract response
                result   = {'text'  : response.choices[0].text.strip(),
                            'model' : response.model,
                            'usage' : {'prompt_tokens'     : response.usage.prompt_tokens,
                                       'completion_tokens' : response.usage.completion_tokens,
                                       'total_tokens'      : response.usage.total_tokens,
                                      }
                           }
                
                logger.info(msg   = f"Successfully generated completion (tokens: {result['usage']['total_tokens']})",
                            extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                           )
                
                return result
            
            except Exception as api_error:
                error_str = repr(api_error)
                
                # Check if it's a rate limit error
                if (("429" in error_str) and (attempt < (self.max_retries - 1))):
                    # Exponential backoff with jitter
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    
                    logger.warning(msg   = f"Rate limited. Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{self.max_retries})",
                                   extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                                  )
                    
                    await asyncio.sleep(delay)
                
                else:
                    # Non-rate-limit error or final attempt
                    error_message = f"OpenAI API error: {error_str}"
                    
                    logger.error(msg      = error_message,
                                 extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                                 exc_info = True,
                                )
                    raise
        
        # Should not reach here, but just in case
        raise Exception("Max retries exceeded for OpenAI completion")
    
    
    async def close(self) -> None:
        """
        Close the OpenAI client and cleanup resources
        """
        if self.client:
            await self.client.close()
            
            logger.info(msg   = "OpenAI client closed successfully",
                        extra = {"request_id": "client_close", "batch_id": "N/A", "batch_item_id": "N/A"},
                       )

            self.client = None