# DEPENDENCIES
import logging
import warnings

# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# LOGGING 
logger = logging.getLogger(__name__)


# HELPER : POST PROCESS RAW RESPONSES BY GPT INSTRUCT MODEL
async def post_process_extracted_info(extracted_data: list) -> dict:
    """
    Post process the extracted data by GPT model and returns cleaned data

    Arguments:
    ----------
        extracted_data { list } : A python list containing raw data extracted by 
                                  GPT model from the LinkedIn post

    Errors:
    -------
        InputError              : If required arguments are not of valid data type
        
        PostProcessingError     : If any exception occurs during post-processing of 
                                  the raw extracted data 

    Returns:
    --------
              { dict }          : A python dictionary, containing the cleaned information 
                                  after post processing as key : value pairs
    """
    # Input type checking 
    if (not isinstance(extracted_data, list)):
        input_error_message = f"InputError: Expected a python list for extracted_info, got: {type(extracted_data)} instead"
        
        logger.error(msg   = input_error_message, 
                     extra = {"request_id": "post_processing"})
        
        return input_error_message
    
    try:
        # Remove any entries where any of the three key fields is "Unknown"
        cleaned_info        = [info for info in extracted_data if all(info[key] != "Unknown" for key in info.keys())]

        # Update new_role to "Unknown" if it contains keywords like retiring or leaving
        for info in cleaned_info:
            if (('retiring' in info['new_role'].lower()) or ('leaving' in info['new_role'].lower())):
                info['new_role'] = 'Unknown'

        # Perform another cleaning step to remove entries where new_role is "Unknown" after the update
        final_cleaned_info  = [info for info in cleaned_info if info['new_role'] != 'Unknown']

        # Update change_count
        change_count        = len(final_cleaned_info)

        # Determine relevance based on the final cleaned info
        relevant            = (change_count > 0)

        # Dump all the post-processing results in a python dictionary
        post_processed_dict = {'extracted_info' : final_cleaned_info,
                               'change_count'   : change_count,
                               'relevant'       : relevant}
        
        logger.info(msg   = 'Successfully post-processed the extracted data from LinkedIn post', 
                    extra = {"request_id": "post_processing"})
        
        return post_processed_dict
    
    except Exception as PostProcessingError:
        error_message = f"PostProcessingError: While post-processing the extracted data, got: {repr(PostProcessingError)}"
        
        logger.error(msg      = error_message, 
                     extra    = {"request_id": "post_processing"}, 
                     exc_info = True)
        
        return error_message