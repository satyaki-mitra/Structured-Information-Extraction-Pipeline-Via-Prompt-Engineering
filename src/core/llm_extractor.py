# DEPENDENCIES
import json
import logging
import warnings
from typing import Any
from typing import Dict
from typing import Optional
from src.core.validator import DataValidator
from src.core.base_extractor import BaseExtractor
from src.llm_clients.openai_client import OpenAIClient
from src.prompts.template_manager import PromptTemplateManager


# IGNORE ALL WARNINGS
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = logging.getLogger(__name__)


class LLMExtractor(BaseExtractor):
    """
    LLM-based information extractor for LinkedIn posts: uses OpenAI GPT models to extract structured job information from unstructured posts
    and implements the BaseExtractor interface
    """
    def __init__(self, llm_client: Optional[OpenAIClient] = None, prompt_version: str = "v4"):
        """
        Initialize LLM extractor
        
        Arguments:
        ----------
            llm_client      { OpenAIClient } : OpenAI client instance (creates new if None)
            
            prompt_version      { str }      : Prompt template version to use
        """
        super().__init__(extractor_name = "LLMExtractor")
        
        # Initialize LLM client
        self.llm_client     = llm_client or OpenAIClient()
        
        # Initialize prompt template manager
        self.prompt_manager = PromptTemplateManager()
        self.prompt_version = prompt_version
        
        # Initialize validator
        self.validator      = DataValidator()
        
        logger.info(msg   = f"LLMExtractor initialized with prompt version: {prompt_version}",
                    extra = {"request_id": "llm_extractor_init", "batch_id": "N/A", "batch_item_id": "N/A"},
                   )
    
    
    async def validate_input(self, linkedin_post: Dict[str, Any]) -> bool:
        """
        Validate input LinkedIn post data
        
        Arguments:
        ----------
            linkedin_post { Dict[str, Any] } : LinkedIn post data
        
        Returns:
        --------
                       { bool }              : True if valid, False otherwise
        """
        is_valid, error_message = self.validator.validate_linkedin_post(linkedin_post)
        
        if not is_valid:
            logger.error(msg   = f"Input validation failed: {error_message}",
                         extra = {"request_id": "llm_extract", "batch_id": "N/A", "batch_item_id": "N/A"},
                        )
        
        return is_valid
    
    
    async def extract(self, linkedin_post: Dict[str, Any], request_id: str = "llm_extract") -> Dict[str, Any]:
        """
        Extract information from LinkedIn post using LLM
        
        Arguments:
        ----------
            linkedin_post { Dict[str, Any] } : LinkedIn post data with keys:
                                               - name        : str
                                               - about       : str
                                               - description : str
                                               - (optional) userProfileUrl, source, searchJobTitle, companyLinks

            request_id          { str }       : Request identifier for logging
        
        Returns:
        --------
                 { Dict[str, Any] }           : Extraction result with keys:
                                                - poster_name    : str
                                                - post_category  : str
                                                - change_count   : int
                                                - relevant       : bool
                                                - extracted_info : List[Dict]
                                                - error          : Optional[str]
        """
        # Validate input
        if not await self.validate_input(linkedin_post):
            return {"poster_name"    : linkedin_post.get('name', ''),
                    "post_category"  : "5",
                    "change_count"   : 0,
                    "relevant"       : False,
                    "extracted_info" : [],
                    "error"          : "Invalid input data",
                   }
        
        try:
            # Extract required fields
            poster_name = linkedin_post.get('name', '').replace('\n', ' ').strip()
            about       = linkedin_post.get('about', '').replace('\n', ' ').strip()
            description = linkedin_post.get('description', '').replace('\n', ' ').strip()
            
            logger.info(msg   = f"Extracting information for post by: {poster_name[:50]}...",
                        extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
            
            # Create prompt
            prompt            = self.prompt_manager.format_prompt(poster_name = poster_name,
                                                                  about       = about,
                                                                  description = description,
                                                                  version     = self.prompt_version,
                                                                 )
            
            # Generate completion from LLM
            completion_result = await self.llm_client.generate_completion(prompt     = prompt,
                                                                          request_id = request_id,
                                                                         )
            
            # Parse JSON response
            response_text     = completion_result['text']
            
            try:
                extracted_data = json.loads(response_text)
           
            except json.JSONDecodeError as json_error:
                logger.error(msg   = f"Failed to parse JSON response: {json_error}",
                             extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                            )
                
                return {"poster_name"    : poster_name,
                        "post_category"  : "5",
                        "change_count"   : 0,
                        "relevant"       : False,
                        "extracted_info" : [],
                        "error"          : f"JSON parsing error: {str(json_error)}",
                       }
            
            # Validate extraction result
            is_valid, validation_error = self.validator.validate_extraction_result(extracted_data)
            
            if not is_valid:
                logger.warning(msg   = f"Extraction result validation failed: {validation_error}",
                               extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                              )

                return {"poster_name"    : poster_name,
                        "post_category"  : "5",
                        "change_count"   : 0,
                        "relevant"       : False,
                        "extracted_info" : [],
                        "error"          : f"Validation error: {validation_error}",
                       }
            
            # Clean extracted information
            cleaned_info = self.validator.clean_extracted_info(extracted_data.get('extracted_info', []))
            
            # Update result with cleaned data
            result       = {"poster_name"    : extracted_data.get('poster_name', poster_name),
                            "post_category"  : extracted_data.get('post_category', '5'),
                            "change_count"   : len(cleaned_info),
                            "relevant"       : len(cleaned_info) > 0,
                            "extracted_info" : cleaned_info,
                           }
            
            logger.info(msg   = f"Successfully extracted {result['change_count']} job changes",
                        extra = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
            
            return result
        
        except Exception as extraction_error:
            error_message = f"Extraction error: {repr(extraction_error)}"
            
            logger.error(msg      = error_message,
                         extra    = {"request_id": request_id, "batch_id": "N/A", "batch_item_id": "N/A"},
                         exc_info = True,
                        )
            
            return {"poster_name"    : linkedin_post.get('name', ''),
                    "post_category"  : "5",
                    "change_count"   : 0,
                    "relevant"       : False,
                    "extracted_info" : [],
                    "error"          : error_message,
                   }
    
    
    async def close(self) -> None:
        """
        Close LLM client and cleanup resources
        """
        if self.llm_client:
            await self.llm_client.close()
            
            logger.info(msg   = "LLMExtractor closed successfully",
                        extra = {"request_id": "llm_extractor_close", "batch_id": "N/A", "batch_item_id": "N/A"},
                       )
