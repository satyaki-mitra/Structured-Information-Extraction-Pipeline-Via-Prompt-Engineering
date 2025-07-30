# DEPENDENCIES
import os
import signal
import asyncio
import uvicorn
import warnings
from typing import List
from config import WORKERS
from fastapi import FastAPI
from fastapi import Request
from config import BATCH_SIZE
from config import APPLICATION_HOST
from config import APPLICATION_PORT
from src.logging_config import setup_logging
from src.pydantic_input_classes import InputItemGpt
from src.pydantic_output_classes import OutputItemGpt
from src.processing_functions import process_item_gpt
from src.shutdown_handler import handle_shutdown_event
from src.shutdown_middleware import ShutdownMiddleware
from src.shutdown_handler import handle_shutdown_signal
from src.request_id_middleware import RequestIDMiddleware


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING
logger = setup_logging()


# INITIALIZING FASTAPI APPLICATION
data_extractor_application = FastAPI()


# ADD CUSTOM MIDDLEWARES
data_extractor_application.add_middleware(ShutdownMiddleware)


# ADD MIDDLEWARE FOR REQUEST ID
data_extractor_application.add_middleware(RequestIDMiddleware)


# REGISTER THE SHUTDOWN EVENT HANDLER
@data_extractor_application.on_event(event_type = "shutdown")
async def shutdown():
    logger.info(msg   = "Shutting down application", 
                extra = {"request_id": "shutdown"})
    
    await handle_shutdown_event()


######################### FASTAPI APPLICATION ENDPOINTS #########################

# END POINT FOR HOME PAGE / STARTUP PAGE
@data_extractor_application.get("/")
async def home(request: Request):
    """
    Home endpoint for the Data Extractor API

    Returns:
    --------
        { dict } : Welcome message
    """
    logger.info(msg   = "Home endpoint accessed", 
                extra = {"request_id": request.state.request_id})
    
    return {"message": "Welcome to the Data Extractor API !"}



# ENDPOINT FOR THE DATA EXTRACTION TASK BY GPT MODEL
@data_extractor_application.post("/extract_information_gpt", response_model=List[OutputItemGpt], response_model_exclude_none=True)
async def extract_data_gpt(input_data: List[InputItemGpt], request: Request):
    """
    This endpoint processes multiple input items concurrently, extracting relevant information
    from each. It uses asynchronous processing to handle multiple items efficiently

    Arguments:
    ----------
        input_data      { List[InputItemGpt] } : A list of input items to process

    Returns:
    --------
              { List[OutputItemGpt] }          : A flattened list of OutputItems containing the 
                                                 extracted information or error messages for each
                                                 input item.

    Note:
    -----
        - This function processes all items concurrently using asyncio.gather
        - The results are flattened to handle both single and multiple job postings per input item
        - Returns an empty list for any invalid input or processing errors
    """
    request_id = request.state.request_id

    logger.info(msg   = f"Processing {len(input_data)} input items in extract_data_gpt endpoint", 
                extra = {"request_id"    : request_id, 
                         "batch_id"      : "N/A", 
                         "batch_item_id" : "N/A"}
               )
    
    
    logger.debug(msg   = f"Raw data: {input_data}", 
                 extra = {"request_id": request_id})

    if (not isinstance(input_data, list)):
        logger.warning(msg   = "Invalid input: expected a list of InputItemGpt", 
                       extra = {"request_id": request_id})
        return []
  
    if (len(input_data) == 0):
        logger.warning(msg   = "Empty input: the list of InputItemGpt is empty", 
                       extra = {"request_id": request_id})
        return []

    try:
        # Define an empty list to dump all batch's processed results
        all_processed_results = list()

        for batch_id, i in enumerate(range(0, len(input_data), BATCH_SIZE), start=1):
            # Create a batch of defined size from input data 
            batch         = input_data[i:i+BATCH_SIZE]
            
            logger.info(msg   = f"Processing batch {batch_id} with {len(batch)} items", 
                        extra = {"request_id"    : request_id, 
                                 "batch_id"      : batch_id, 
                                 "batch_item_id" : "N/A"
                                }
                       )

            # Create a list of tasks, one for each input item in the batch
            tasks         = [process_item_gpt(item          = input_item, 
                                              index         = idx+i, 
                                              total_count   = len(input_data),
                                              batch_id      = batch_id,
                                              batch_item_id = idx+1,
                                              request_id    = request.state.request_id,
                                             )
                             for idx, input_item in enumerate(batch)]
            
            # Execute batch tasks concurrently
            batch_results = await asyncio.gather(*tasks)
           
            # Append batch's results in a list for further processing
            all_processed_results.extend(batch_results)

        # Flatten the results, handling both single items and lists
        flattened_results = [item for sublist in all_processed_results for item in (sublist if isinstance(sublist, list) else [sublist])]
        
        logger.info(msg   = f"Successfully processed {len(flattened_results)} items", 
                    extra = {"request_id"    : request_id, 
                             "batch_id"      : "All"}
                   )
        
        return flattened_results
    
    except Exception as ErrorGpt:
        # Return an empty list in case of any processing error
        logger.error(msg      = f"An error occurred while processing the input data: {repr(ErrorGpt)}", 
                     extra    = {"request_id"    : request_id, 
                                 "batch_id"      : "N/A", 
                                 "batch_item_id" : "N/A"}, 
                     exc_info = True)
        return []  





# RUN THE SERVER
if __name__ == '__main__':
    # Configure the Uvicorn server with application settings
    config = uvicorn.Config(app     = data_extractor_application, 
                            host    = APPLICATION_HOST, 
                            port    = APPLICATION_PORT,
                            workers = WORKERS
                           )
    
    # Set the configurations of Uvicorn server
    server = uvicorn.Server(config = config)

    # Register signal handlers for graceful shutdown
    signal.signal(signalnum = signal.SIGINT, 
                  handler   = handle_shutdown_signal)
    
    signal.signal(signalnum = signal.SIGTERM, 
                  handler   = handle_shutdown_signal)

    # Start the server
    server.run()