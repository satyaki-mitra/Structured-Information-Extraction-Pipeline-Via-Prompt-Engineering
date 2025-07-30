# DEPENDENCIES
import os
import json
import random
import asyncio
import logging
import warnings
from .model_config import SEED
from .model_config import BASE_DELAY
from .model_config import MAX_TOKENS
from .model_config import MAX_RETRIES
from .model_config import OPENAI_MODEL_NAME
from .model_config import MODEL_TEMPERATURE
from .gpt_prompt_creator import create_prompt
from .gpt_client_creator import create_openai_client
from .gpt_post_processor import post_process_extracted_info


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# LOGGING 
logger = logging.getLogger(__name__)


# EXTRACT INFORMATION FROM LINKEDIN POSTS USING OPENAI GPT CLIENT
async def extract_information(linkedin_post: dict) -> dict:
    """
    Process a single input LinkedIn post by performing the following steps:
    1. Classifies the text data as per our interest into two classes: Relevant or Irrelevant
    2. Extracts Specified information from Relevant LinkedIn posts using GPT (LLM)

    Arguments:
    ----------
        linkedin_post { dict }     : The LinkedIn post scraped, in a python dictionary format (JSON),
                                     with keys name, about, description, userPRofileUrl, source etc.

    Errors:
    -------
        InputError                 : If required arguments are not of valid data type

        DataExtractionError        : If any exception occurs while extracting information
                                     using LLM from LinkedIn posts

    Returns:
    --------
               { dict }            :  A python dictionary, containing input data key:value pairs, 
                                      as well as extracted information in same key:value format, if any

    """
    # Input type checking 
    if (not isinstance(linkedin_post, dict)):
        error_message = f"InputError: Expected a python dictionary for linkedin_post, got: {type(linkedin_post)} instead"
        
        logger.error(msg   = error_message, 
                     extra = {"request_id": "data_extraction"})
        
        return error_message_2

    
    try:
        # Extract only required parts from the input linkedin_post variable
        poster_name                   = linkedin_post.get('name', None).replace('\n', ' ')
        about                         = linkedin_post.get('about', None).replace('\n', ' ')
        description                   = linkedin_post.get('description', None).replace('\n', ' ')
        
        # Also, extract some auxiliary keys and their corresponding values for output generation
        user_profile_url              = linkedin_post.get('userProfileUrl', None)
        data_source                   = linkedin_post.get('source', None)
        search_job_title              = linkedin_post.get('searchJobTitle', None)
        company_links                 = linkedin_post.get('companyLinks', [])

        # Create the data extraction and classification prompt
        data_extraction_prompt_result = await create_prompt(poster_name = poster_name,
                                                            about       = about,
                                                            description = description)
        
        # Check if prompt has been created successfully or not
        if ("Error" in data_extraction_prompt_result):
            logger.warning(msg   = "Prompt creation failed", 
                           extra = {"request_id": "data_extraction"})
            
            return {'name'           : poster_name,
                    'about'          : about,
                    'description'    : description,
                    'userProfileUrl' : user_profile_url,
                    'source'         : data_source,
                    'searchJobTitle' : search_job_title,
                    'companyLinks'   : company_links,
                    'error'          : data_extraction_prompt_result,
                   } 
        
        
        # Create OpenAI Client 
        openai_client_instance = await create_openai_client()

        if (isinstance(openai_client_instance, str)):
            logger.warning(msg   = "OpenAI client creation failed", 
                           extra = {"request_id": "data_extraction"})
            
            return {'name'           : poster_name,
                    'about'          : about,
                    'description'    : description,
                    'userProfileUrl' : user_profile_url,
                    'source'         : data_source,
                    'searchJobTitle' : search_job_title,
                    'companyLinks'   : company_links,
                    'error'          : openai_client_instance,
                   } 

        for attempt in range(MAX_RETRIES):
            try:
                # Ask GPT to get the response
                raw_gpt_response = await openai_client_instance.completions.create(model       = OPENAI_MODEL_NAME,
                                                                                   prompt      = data_extraction_prompt_result,
                                                                                   temperature = MODEL_TEMPERATURE,
                                                                                   seed        = SEED,
                                                                                   max_tokens  = MAX_TOKENS,
                                                                                  )
                # If successful, break out of the retry loop
                break  
            
            except Exception as AttemptException:
                if (("429" in repr(AttemptException)) and (attempt < (MAX_RETRIES - 1))):
                    # Exponential backoff with jitter when encountering rate limit errors
                    exponential_delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    
                    # Give a warning of rate limit error
                    logger.warning(f"Rate limited. Retrying in {exponential_delay:.2f} seconds...")
                    
                    # Sleep for the calculated delay
                    await asyncio.sleep(delay = exponential_delay)
                
                else:
                    raise

        # Close the OpenAI client
        openai_client_instance.close()
        
        logger.info(msg   = 'Successfully closed the AsyncOpenAI API client', 
                    extra = {"request_id": "gpt_data_extractor"}
                   )
        
        # Extract only the text part from the raw response
        response_text            = raw_gpt_response.choices[0].text.strip()
        
        # Parse the response text into a JSON object
        extracted_info           = json.loads(s = response_text)

        # Apply post-processing for deleting unnecessary information, if present
        post_processing_result   = await post_process_extracted_info(extracted_data = extracted_info.get('extracted_info', []))

        # Check if post processing result is correct or not
        if (not isinstance(post_processing_result, dict)):
            logger.warning(msg   = "Post-processing failed", 
                           extra = {"request_id": "data_extraction"})
            
            return {"poster_name"    : poster_name,
                    "post_category"  : "5",
                    "change_count"   : 0,
                    "relevant"       : False,
                    "extracted_info" : [],
                    "error"          : post_processing_result,
                   }

        # Replace the post processed information in final response
        extracted_info['extracted_info'] = post_processing_result['extracted_info']
        extracted_info['change_count']   = post_processing_result['change_count']
        extracted_info['relevant']       = post_processing_result['relevant']
        
        # Prepare final output data
        final_output                     = {"poster_name"    : extracted_info.get("poster_name"),
                                            "post_category"  : extracted_info.get("post_category"),
                                            "change_count"   : extracted_info.get("change_count"),
                                            "relevant"       : extracted_info.get("relevant"),
                                            "extracted_info" : extracted_info.get("extracted_info", []),
                                           }
        
        logger.info(msg   = 'Successfully got data extraction results', 
                    extra = {"request_id": "data_extraction"})
        
        return final_output

    except Exception as DataExtractionError:
        exception_message = f"DataExtractionError: While extracting data from LinkedIn post, got: {repr(DataExtractionError)}"
        
        logger.error(msg      = exception_message, 
                     extra    = {"request_id": "data_extraction"}, 
                     exc_info = True)
        
        return {"poster_name"    : linkedin_post.get('name', ''),
                "post_category"  : "5",
                "change_count"   : 0,
                "relevant"       : False,
                "extracted_info" : [],
                "error"          : exception_message,
               }
