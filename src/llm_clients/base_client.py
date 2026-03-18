# DEPENDENCIES
import logging
import warnings
from abc import ABC
from typing import Any
from typing import Dict
from typing import Optional
from abc import abstractmethod


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM client implementations: Defines the interface that all LLM clients must implement and
    ensures consistency across different LLM providers (OpenAI, Anthropic, etc.)
    """
    def __init__(self, api_key: str, model_name: str, **kwargs):
        """
        Initialize the base LLM client
        
        Arguments:
        ----------
            api_key    { str } : API key for the LLM provider
            
            model_name { str } : Name of the model to use
            
            **kwargs           : Additional configuration parameters
        """
        self.api_key    = api_key
        self.model_name = model_name
        self.config     = kwargs
        
        logger.info(msg   = f"Initializing {self.__class__.__name__} with model: {model_name}",
                    extra = {"request_id": "client_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
            
    
    @abstractmethod
    async def create_client(self) -> Any:
        """
        Create and return the LLM client instance: must be implemented by subclasses to create provider-specific clients
        
        Returns:
        --------
                  { Any }       : The LLM client instance
        
        Raises:
        -------
            NotImplementedError : If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement create_client method")
    
    
    @abstractmethod
    async def generate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a completion from the LLM
        
        Arguments:
        ----------
            prompt   { str }    : The prompt to send to the LLM

            **kwargs            : Additional parameters for the completion request
        
        Returns:
        --------
            { Dict[str, Any] }  : Dictionary containing the completion response
        
        Raises:
        -------
            NotImplementedError : If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement generate_completion method")
    
    
    @abstractmethod
    async def close(self) -> None:
        """
        Close the LLM client and cleanup resources: must be implemented by subclasses to properly cleanup resources
        
        Raises:
        -------
            NotImplementedError : If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement close method")
    
    
    def validate_config(self) -> bool:
        """
        Validate client configuration
        
        Returns:
        --------
            { bool } : True if configuration is valid, False otherwise
        """
        if not self.api_key:
            logger.error(msg   = "API key is not set",
                         extra = {"request_id": "config_validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            return False
        
        if not self.model_name:
            logger.error(msg   = "Model name is not set",
                         extra = {"request_id": "config_validation", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )

            return False
        
        return True