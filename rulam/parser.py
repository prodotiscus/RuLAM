from enum import Enum
from .udpipe_glue_connector import make_discourse_tester
import nltk


class IntegrationTypes(Enum):
    WEB_UDPIPE_GLUE = 1
    LOCAL_UDPIPE_GLUE = 2  # not ready yet


def get_parser(sentences, integration_type: IntegrationTypes = IntegrationTypes.WEB_UDPIPE_GLUE):
    if integration_type == IntegrationTypes.LOCAL_UDPIPE_GLUE:
        raise NotImplementedError("Local UDPipe integration is not yet available.")
    
    if integration_type == IntegrationTypes.WEB_UDPIPE_GLUE:
        return make_discourse_tester(sentences)

    raise ValueError(f"Unknown integration type provided: {integration_type}")
