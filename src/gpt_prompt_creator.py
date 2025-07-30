# DEPENDENCIES
import logging
import warnings


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# LOGGING 
logger = logging.getLogger(__name__)


async def create_prompt(poster_name:str, about:str, description:str) -> str:
    """
    Create the prompt for GPT model to instruct it how to classify LinkedIn posts and
    exactly what all information are required to be extracted from the LinkedIn post

    Arguments:
    ----------
        poster_name { str }   : Name key in the LinkedIn post, as per scraped data

        about       { str }   : A brief information about the LinkedIn poster, as per scraped data

        description { str }   : The main post, which is of main interest, as per scraped data
    
    Errors:
    -------
        InputError            : If required arguments are not of valid data type

        PromptCreationError   : If any exception occurs while formatting and creating the prompt

    Returns:
    --------
               { str }        : A python string, which is the final and formatted with proper 
                                inputs for OpenAI client 
    """
    # Input type checking 
    if (not isinstance(poster_name, str)):
        poster_name_error = f"InputError: Expected a string for poster_name, got: {type(poster_name)} instead"
        
        logger.error(msg   = poster_name_error, 
                     extra = {"request_id": "prompt_creation"})
        
        return poster_name_error
    
    if (not isinstance(about, str)):
        about_poster_error = f"InputError: Expected a string for about, got: {type(about)} instead"
        
        logger.error(msg   = about_poster_error, 
                     extra = {"request_id": "prompt_creation"})
        
        return about_poster_error

    if (not isinstance(description, str)):
        description_error = f"InputError: Expected a string for description, got: {type(description)} instead"
        
        logger.error(msg   = description_error, 
                     extra = {"request_id": "prompt_creation"})
        
        return description_error

    try:
        # Define the prompt
        data_extraction_prompt = f"""
                                     Analyze the following LinkedIn post throughly and classify it based on job-related announcements:
                                            
                                     Post by: {poster_name}
                                     About: {about}
                                     Description: {description}

                                     Step 1: Classification
                                     Determine if this post is about any of the following:
                                     1. New job joining (either within the same company or a new company)
                                     2. Job change or transition
                                     3. Promotion within the same company
                                     4. Leadership change or appointment
                                     5. Other (not related to the above categories)

                                     Step 2: Information Extraction
                                     If the post falls into categories 1-4, extract the following information for each relevant mention:
                                     - Remove any solutions eg: Mr. Mrs. Dr. Prof. or title or degree or something rather than the name
                                       itself only, present after or before the name : {poster_name}
                                     - Full name of the person mentioned (who got the new job, promotion, or new role), but exclude any 
                                       solutions eg: Mr. Mrs. Dr. Prof.  or title or degree or something rather than the name itself only, 
                                       present after or before the name
                                     - Full name of the organization (current or new)
                                     - New job title or role

                                     Important:
                                     - Ignore all kinds of hiring announcements for positions that are not filled yet or do not mention a
                                       specific individual's job change. For example, if the post says "I am hiring for a Finance Manager," 
                                       this should be ignored.
                                     - Ignore those individuals or persons who are retiring or leaving job
                                     - Include those who are leaving a role or position but joining another role or position.
                                     - Ignore positions like "Shareholder", "Owner", "Proprietor", "Insider", or similar titles. 
                                     - Specifically, exclude roles that do not indicate a significant change in responsibilities or title.

                                     Format the response as a JSON object with the following structure:
                                     {{
                                            "poster_name": "[modified poster_name]",
                                            "post_category": "[Category number from Step 1]",
                                            "change_count": [number of changes],
                                            "relevant": [true/false],
                                            "extracted_info": [
                                                {{
                                                    "person_name": "[Full Name of the person mentioned]",
                                                    "organization": "[Full Name of the Organization]",
                                                    "new_role": "[New Job Title or Role]"
                                                }},
                                                ...
                                            ]
                                     }}

                                     Ensure high accuracy in classification and information extraction. If any information is
                                     uncertain or not explicitly mentioned, use "Unknown" as the value.

                                     Provide only the JSON object as your response, with no additional text before or after.
                                  """
        
        logger.info(msg   = "Successfully created the prompt for data extraction", 
                    extra = {"request_id": "prompt_creation"})
        
        return data_extraction_prompt
    
    except Exception as PromptCreationError:
        exception_message = f"PromptCreationError: While creating data extraction prompt, got: {repr(PromptCreationError)}"
        
        logger.error(msg      = exception_message, 
                     extra    = {"request_id": "prompt_creation"}, 
                     exc_info = True)
        
        return exception_message