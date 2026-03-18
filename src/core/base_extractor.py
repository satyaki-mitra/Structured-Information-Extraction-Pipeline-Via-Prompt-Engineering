# DEPENDENCIES
import logging
import warnings
from abc import ABC
from typing import Any
from typing import List
from typing import Dict
from abc import abstractmethod


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    Abstract base class for information extractors: defines the interface that all extractors (LLM-based, rule-based, etc.) must implement
    and ensures consistency across different extraction approaches
    """
    def __init__(self, extractor_name: str):
        """
        Initialize the base extractor
        
        Arguments:
        ----------
            extractor_name { str } : Name/identifier for this extractor
        """
        self.extractor_name = extractor_name
        
        logger.info(msg   = f"Initializing {extractor_name} extractor",
                    extra = {"request_id": "extractor_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
    
    
    @abstractmethod
    async def extract(self, linkedin_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract information from a LinkedIn post
        
        Arguments:
        ----------
            linkedin_post { Dict[str, Any] } : LinkedIn post data
        
        Returns:
        --------
            { Dict[str, Any] }               : Extracted information with structure:
                                               {"poster_name"    : str,
                                                "post_category"  : str,
                                                "change_count"   : int,
                                                "relevant"       : bool,
                                                "extracted_info" : List[Dict],
                                                "error"          : Optional[str],
                                               }
        
        Raises:
        -------
            NotImplementedError              : If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement extract method")
    
    
    @abstractmethod
    async def validate_input(self, linkedin_post: Dict[str, Any]) -> bool:
        """
        Validate input data before extraction
        
        Arguments:
        ----------
            linkedin_post { Dict[str, Any] } : LinkedIn post data to validate
        
        Returns:
        --------
                      { bool }               : True if input is valid, False otherwise
        
        Raises:
        -------
            NotImplementedError              : If subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement validate_input method")
    
    
    def get_extractor_info(self) -> Dict[str, str]:
        """
        Get information about this extractor
        
        Returns:
        --------
            { Dict[str, str] } : Extractor metadata
        """
        return {"name" : self.extractor_name,
                "type" : self.__class__.__name__,
               }
