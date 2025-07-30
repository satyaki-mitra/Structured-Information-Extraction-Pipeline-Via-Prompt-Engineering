# DEPENDENCIES
import logging
import warnings
from .pydantic_input_classes import InputItemGpt
from .pydantic_output_classes import OutputItemGpt
from .gpt_data_extractor import extract_information


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING 
logger = logging.getLogger(__name__)


async def process_item_gpt(item: InputItemGpt, index:int, total_count:int, batch_id: int, batch_item_id: int, request_id: str) -> OutputItemGpt:
    """
    Process a single input item asynchronously for GPT model by performing the following steps:
    1. Extracts relevant information using GPT model for classified data
    2. Formats the extracted data into OutputItemGpt(s)

    Arguments:
    ----------
        item     { InputItemGpt }  : The input item to process
        
        index         { int }      : The index of the input item in total input array

        total_count   { int }      : The total count of input array in current request 

        batch_id      { int }      : The id of the current batch

        batch_item_id { int }      : The item id of the current batch

        request_id    { str }      : The request id which is currently getting processed
        
    Returns:
    --------
        { OutputItemGpt }     : A single OutputItemGpt if processing a single job posting or
                                a list of OutputItemGpt if processing multiple job postings or
                                an OutputItemGpt with an error message if any step fails

    Raises:
    -------
        No exceptions has been raised; all are caught and returned as error messages in OutputItem
    """
    logger.info(msg   = f"Processing item {index + 1} of {total_count}", 
                extra = {"request_id"    : request_id, 
                         "batch_id"      : batch_id, 
                         "batch_item_id" : batch_item_id}
               )
    try:
        # Log the item index which is getting processed
        logger.info(msg   = f'Processing input item: {index+1} / {total_count}', 
                    extra = {"request_id": request_id})

        # Extract information
        extraction_result = await extract_information(linkedin_post = item.dict())
        
        # If any error occurs in extracting information, catch it and return
        if isinstance(extraction_result, str):
            logger.warning(msg   = f"Extraction failed for item {index+1}", 
                           extra = {"request_id": request_id})
            
            return [OutputItemGpt(**item.dict(), error = extraction_result)]

        # Define a base structure to align with OutputItem class
        base_output       = OutputItemGpt(name           = item.name,
                                          about          = item.about,
                                          description    = item.description,
                                          userProfileUrl = item.userProfileUrl,
                                          source         = item.source,
                                          searchJobTitle = item.searchJobTitle,
                                          companyLinks   = item.companyLinks if item.companyLinks != None else [],
                                          classification = 'Relevant' if extraction_result.get('relevant') else 'Irrelevant',
                                          error          = f"IrrelevantData: LinkedIn post is Irrelevant in this context, \
                                                             hence no data has been extracted".replace('  ', '') 
                                                             if not extraction_result.get('relevant') else None,
                                         )
        
        # Capture extraction results and populate with objects of OutputItem class
        extracted_info    = extraction_result.get('extracted_info', [])
        
        # If any error occurs in getting extracted_info key, catch it and return
        if not extracted_info:
            logger.info(msg   = f"No relevant information extracted for item {index+1}", 
                        extra = {"request_id": request_id})
            
            return [base_output.dict(exclude_none = True)]
        
        # Define an empty list to dump all results
        output_items = list()

        # Iteratively collect all unit results in output_item
        for info in extracted_info:
            output_item                = base_output.copy(deep = True)
            output_item.jobPosterName  = extraction_result.get('poster_name')
            output_item.jobStarterName = info.get('person_name')
            output_item.companyName    = info.get('organization') or item.companyName
            output_item.currentRole    = info.get('new_role')
            output_items.append(output_item)
        
        logger.info(msg   = f'Successfully created response data for item {index+1}', 
                    extra = {"request_id": request_id})
        
        return output_items
    
    except Exception as ProcessItemError:
        logger.error(msg      = f"Error processing item {index+1}: {repr(ProcessItemError)}", 
                     extra    = {"request_id": request_id}, 
                     exc_info = True)
        
        return [OutputItemGpt(**item.dict(), error = f"ProcessItemError: Got error while processing item: {repr(ProcessItemError)}")]
