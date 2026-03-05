import logging
import structlog
import contextvars
import os
from datetime import datetime

request_id_ctx = contextvars.ContextVar("request_id", default=None)

def add_context_vars(_, __, event_dict):
    event_dict['request_id'] = request_id_ctx.get()
    return event_dict

def config_logger(name: str, file_name: str|None = None, backup: bool|None = None) -> None:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Handlers
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO) # Dont flood console with debug logs
    c_handler.setFormatter(logging.Formatter(fmt='%(levelname)s - %(asctime)s: %(message)s', 
                                             datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(c_handler)

    if file_name:
        # If dir doesnt exist create it
        if not os.path.exists('logs'): 
            os.makedirs('logs')
        # If file already exists move it to a backup or overwrite
        if os.path.exists(f'logs/{file_name}'):
            if backup:
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                backup_name = f'logs/{file_name}-{timestamp}.bkp'
                os.rename(f'logs/{file_name}', backup_name)
            else:
                open(f'logs/{file_name}', 'w').close()

        f_handler = logging.FileHandler(f'logs/{file_name}', mode='a')
        f_handler.setLevel(logging.DEBUG) # All logs go to log file
        f_handler.setFormatter(logging.Formatter(fmt='%(levelname)s - %(asctime)s: %(message)s'))
        logger.addHandler(f_handler)

    structlog.configure(
        processors = [
            structlog.processors.TimeStamper(fmt="iso"),
            add_context_vars,
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class = structlog.make_filtering_bound_logger(logging.DEBUG),
        logger_factory = structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
    )

def get_struct_logger(name: str):
    return structlog.get_logger(name)