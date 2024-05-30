"""
Use LLMs to generate summaries for themes.
"""

import json
import logging

import boto3
import tiktoken
from django.conf import settings
from langchain.chains.llm import LLMChain
from langchain.output_parsers import PydanticOutputParser, RetryWithErrorOutputParser
from langchain.prompts import PromptTemplate
from langchain.pydantic_v1 import BaseModel
from langchain_community.llms import SagemakerEndpoint
from langchain_community.llms.sagemaker_endpoint import LLMContentHandler
from langchain_core.exceptions import OutputParserException
from langchain_core.prompt_values import StringPromptValue

from consultation_analyser.consultations.models import Answer, Theme
from consultation_analyser.pipeline.decorators import check_and_launch_sagemaker

logger = logging.getLogger("django.server")


MODEL_ENCODING = tiktoken.get_encoding(
    "cl100k_base"
)  # TODO - where does this encoding come from, how do we associate it with model

# TODO - what should this be, should we save in DB a flag if we can't generate summary?
NO_SUMMARY_STR = "Unable to generate summary for this theme"


def get_prompt_template():
    # TODO - what is the best way to get info about the policy area into the prompt.
    # TODO - this might need tweaking on the first run.
    prompt_template = """
    <s>[INST]
    You are serving as an expert AI assisting UK government \
    policy officers in analyzing public opinions on new policies. \
    The topic of the new policy is {consultation_name}. \
    We want you to distill key sentiments and arguments expressed in the responses. \
    We conducted a survey, and responses to a specific question have been categorized under a single common theme.\
    We have provided a sample of responses for the theme and frequently occurring key words. \
    We have also provided some background information about the chapter of the survey in which the question was asked. \
    Instead of general agreement/disagreement, focus on capturing specific perspectives. \
    Your task is to generate ONLY:
    1) A concise phrase that encapsulates both the prevalent keywords and the nuanced opinions conveyed in the responses.
    2) A summary of the opinions expressed in the responses.
    You should generate a short description (a phrase) and summary that reflects the MOST COMMON opinion expressed in the responses. \
    You MUST return your answer in JSON format. DO NOT DEVIATE FROM THIS FORMAT. \
    The response MUST be formatted with two fields: 'short_description' and 'summary'. \
    IT IS ESSENTIAL THAT YOU FORMAT YOUR RESPONSE LIKE THIS.

    == QUESTION ==
    {question}

    == KEYWORDS ==
    {keywords}

    == SAMPLE RESPONSES ==
    {responses}

    Ensure that the phrase you generate does not include any of the following phrases or their equivalents: "Support for ...", "Agreement with the policy", "Disagreement with the policy", "Policies", "Opinions on ...", "Agreement with proposed policy", "Disagreement with proposed policy".

    [/INST]
    """

    return PromptTemplate.from_template(template=prompt_template)


class ContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, inputs: str, model_kwargs: dict) -> bytes:
        input_str = json.dumps({"inputs": inputs, "parameters": model_kwargs})
        return input_str.encode("utf-8")

    def transform_output(self, output) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]


class ThemeSummaryOutput(BaseModel):
    short_description: str
    summary: str


def token_count(text: str, encoding: tiktoken.Encoding) -> int:
    return len(encoding.encode(text))


# TODO - max tokens also to be associated with model
def get_random_sample_of_responses_for_theme(
    theme: Theme, encoding: tiktoken.Encoding, max_tokens: int
) -> str:
    responses_for_theme = Answer.objects.filter(theme=theme).order_by("?")
    free_text_responses_for_theme = responses_for_theme.values_list("free_text", flat=True)
    number_responses = responses_for_theme.count()
    combined_responses_string = ""
    i = 0
    append_more_results = True
    # TODO - how else might we want to separate documents (aka responses)?
    separator = "\n"
    while append_more_results:
        new_combined_responses_string = separator.join(
            [combined_responses_string, free_text_responses_for_theme[i]]
        )
        under_token_limit = (
            token_count(text=new_combined_responses_string, encoding=encoding) < max_tokens
        )
        if under_token_limit:
            combined_responses_string = new_combined_responses_string
        i = i + 1
        append_more_results = under_token_limit and (i < number_responses)
    return combined_responses_string


def get_sagemaker_endpoint() -> SagemakerEndpoint:
    content_handler = ContentHandler()
    client = boto3.client("sagemaker-runtime", region_name=settings.AWS_REGION)
    # TODO - What should these parameters be?
    model_kwargs = {
        "temperature": 0.8,
        "max_new_tokens": 2048,
        "repetition_penalty": 1.03,
        "stop": ["###", "</s>"],
    }
    sagemaker_endpoint = SagemakerEndpoint(
        endpoint_name=settings.SAGEMAKER_ENDPOINT_NAME,
        content_handler=content_handler,
        model_kwargs=model_kwargs,
        client=client,
    )
    return sagemaker_endpoint


def generate_theme_summary(theme: Theme) -> dict:
    """For a given theme, generate a summary using an LLM."""
    logger.info(f"Starting LLM summarisation for theme with keywords: {theme.keywords} ")
    prompt_template = get_prompt_template()
    sagemaker_endpoint = get_sagemaker_endpoint()
    # TODO - where is this max tokens coming from?
    # max_tokens=2000 in original code
    sample_responses = get_random_sample_of_responses_for_theme(
        theme, encoding=MODEL_ENCODING, max_tokens=2000
    )
    prompt_inputs = {
        "consultation_name": theme.question.section.consultation.name,
        "question": theme.question.text,
        "keywords": ", ".join(theme.keywords),
        "responses": sample_responses,
    }
    parser = PydanticOutputParser(pydantic_object=ThemeSummaryOutput)
    errors = (OutputParserException, ValueError)
    try:
        llm_chain = prompt_template | sagemaker_endpoint | parser
        # TODO - are the outputs of this as good as the RetryWithErrorOutputParser?
        llm_chain = llm_chain.with_retry(
            retry_if_exception_type=errors, wait_exponential_jitter=False, stop_after_attempt=10
        )
        parsed_output = llm_chain.invoke(prompt_inputs)
        parsed_output = {
            "short_description": parsed_output.short_description,
            "summary": parsed_output.summary,
        }
    except errors as e:
        parsed_output = {"short_description": NO_SUMMARY_STR, "summary": NO_SUMMARY_STR}
    return parsed_output


def dummy_generate_theme_summary(theme: Theme) -> dict[str, str]:
    concatenated_keywords = (", ").join(theme.keywords)
    made_up_short_description = f"Short description: {concatenated_keywords}"
    made_up_summary = f"Longer summary: {concatenated_keywords}"
    output = {"short_description": made_up_short_description, "summary": made_up_summary}
    return output


# TODO - actually do this at the start of the process consultation,
# but check that it's ready at the start of the LLM summariser method
@check_and_launch_sagemaker
def create_llm_summaries_for_consultation(consultation):
    logger.info(f"Starting LLM summarisation for consultation: {consultation.name}")
    themes = Theme.objects.filter(question__section__consultation=consultation).filter(
        question__has_free_text=True
    )
    for theme in themes:
        if settings.USE_SAGEMAKER_LLM:
            theme_summary_data = generate_theme_summary(theme)
        else:
            theme_summary_data = dummy_generate_theme_summary(theme)
        theme.summary = theme_summary_data["summary"]
        theme.short_description = theme_summary_data["short_description"]
        logger.info(f"Theme description: {theme.short_description}")
        theme.save()
