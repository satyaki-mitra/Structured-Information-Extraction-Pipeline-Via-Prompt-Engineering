# DEPENDENCIES
import logging
import asyncio
import warnings


# IGNORE ALL WARNINGS 
warnings.filterwarnings(action = 'ignore')


# CONFIGURE THE LOGGING 
logger = logging.getLogger(__name__)


def handle_shutdown_signal(signal, frame):
    """
    Handles OS shutdown signals (SIGINT, SIGTERM)
    
    """
    logger.info(msg   = "Shutdown signal received", 
                extra = {"request_id": "shutdown"})
    
    # Get the current event loop
    loop = asyncio.get_event_loop()

    if loop.is_running():
        loop.create_task(handle_shutdown_event())
    
    else:
        loop.run_until_complete(handle_shutdown_event())


async def handle_shutdown_event():
    """
    Asynchronous handler for FastAPI shutdown event

    This function ensures that any asynchronous cleanup or shutdown operations are performed
    
    """
    logger.info(msg   = "Running shutdown event handler", 
                extra = {"request_id": "shutdown"})
    
     # Perform any necessary cleanup here and 
     # give some time to perform the cleanup process properly
    await asyncio.sleep(delay = 5)  
    #handle_shutdown_signal()

    logger.info(msg   = "Shutdown complete", 
                extra = {"request_id": "shutdown"})

