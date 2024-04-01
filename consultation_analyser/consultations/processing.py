from abc import ABC, abstractmethod
import environ
from uuid import uuid4

env = environ.Env()

class LabellingLLM(ABC):
    @abstractmethod
    def assign_label(themes):
        return

class SagemakerLabellingLLM(LabellingLLM):
    def __init__(self):
        # do some sagemaker waking up
        pass

    def assign_label(self, themes):
        # make a sagemaker call with the themes
        pass

class DummyLabellingLLM(LabellingLLM):
    # no __init__ because there's no setup

    # this is the same method as above with different impl
    def assign_label(self, themes):
        return ",".join(themes) # or whatever

class ConsultationProcessingRun: # dummy django model for illustration process
    def __init__(self, slug, start_time):
        pass

    def find(pk):
        pass

    def save(self):
        pass

    def mark_completed(self):
        pass

# function for the view to call. will return the uuid of the ConsultationProcessingRun
def send_consultation_to_be_processed(consultation_slug: str) -> uuid4:
    # this would have a foreign key to the consultation and a start time
    processing_run = ConsultationProcessingRun(consultation_slug, start_time='current time').save()
    if env.str("CONSULTATION_PROCESSING_BACKEND").upper() == 'AWS_BATCH':
        send_consultation_processing_to_aws_batch(processing_run.id)
        return processing_run.id # the view can redirect us to the run's show page which will be "in progess"
    else:
        # the view can redirect us to the run's show page which will be
        # done by the time we get there
        return process_consultation(processing_run.id)

def send_consultation_processing_to_aws_batch(processing_run_id: uuid4) -> None:
    # effectful function sending the API call to batch
    pass

def assign_themes(consultation_slug) -> None:
    pass

def assign_labels(consultation_slug, llm) -> None:
    pass

def process_consultation(processing_run_id) -> None:
    if env.str("LABELLING_BACKEND").upper() == "SAGEMAKER":
        llm = SagemakerLabellingLLM()
    else:
        llm = DummyLabellingLLM()

    do the actual work, e.g.
    assign_themes(consultation_slug)
    assign_labels(consultation_slug, llm)

    run = ConsultationProcessingRun.find(pk=processing_run_id)
    run.mark_completed()
