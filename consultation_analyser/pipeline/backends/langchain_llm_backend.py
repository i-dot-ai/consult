import logging

import tiktoken
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models.llms import LLM

from consultation_analyser.consultations import models

from .llm_backend import LLMBackend
from .types import NO_SUMMARY_STR, ThemeSummary

logger = logging.getLogger("pipeline")


class LangchainLLMBackend(LLMBackend):
    def __init__(self, llm: LLM):
        self.llm = llm
        self.model_encoding = tiktoken.get_encoding(
            "cl100k_base"
        )  # TODO - where does this encoding come from, how do we associate it with model
        self.max_tokens = 2000

    def summarise_theme(self, theme: models.Theme) -> ThemeSummary:
        prompt_template = self.__get_prompt_template()

        sample_responses = get_random_sample_of_responses_for_theme(
            theme, encoding=self.model_encoding, max_tokens=self.max_tokens
        )

        prompt_inputs = {
            "consultation_name": theme.question.section.consultation.name,
            "question": theme.question.text,
            "keywords": ", ".join(theme.topic_keywords),
            "responses": sample_responses,
        }

        parser = PydanticOutputParser(pydantic_object=ThemeSummary)
        errors = (OutputParserException, ValueError)
        try:
            llm_chain = prompt_template | self.llm | parser
            # TODO - are the outputs of this as good as the RetryWithErrorOutputParser?
            llm_chain = llm_chain.with_retry(
                retry_if_exception_type=errors, wait_exponential_jitter=False, stop_after_attempt=10
            )
            parsed_output = llm_chain.invoke(prompt_inputs)
            output = {
                "short_description": parsed_output.short_description,
                "summary": parsed_output.summary,
            }

            return ThemeSummary(**output)
        except errors as e:
            logger.info(f"Failed to summarise theme with keywords: {theme.topic_keywords}.")
            error_message = e.args[0] if e.args else ""
            logger.info(error_message)
            return ThemeSummary(
                **{
                    "short_description": NO_SUMMARY_STR,
                    "summary": NO_SUMMARY_STR,
                }
            )

    def __get_prompt_template(self):
        # TODO - what is the best way to get info about the policy area into the prompt.
        # TODO - this might need tweaking on the first run.
        prompt_template = """
        [INST]You are serving as an expert AI assisting UK government
        policy officers in analyzing public opinions on new policies.
        The topic of the new policy is {consultation_name}.
        We conducted a survey, and answers to a specific question have been categorized under a single common theme.
        We have provided a sample of answers for the theme and frequently occurring key words.
        We want you to distill key sentiments and arguments expressed in the answers.
        We have also provided some background information about the chapter of the survey in which the question was asked.
        Instead of general agreement/disagreement, focus on capturing specific perspectives.
        You should generate a short description (a phrase) and summary that reflects the MOST COMMON opinion expressed
        in the answers.
        1) 'short_description': A concise phrase that encapsulates both the prevalent keywords and the nuanced opinions
        conveyed in the answers.
        2) 'summary': A summary of the opinions expressed in the answers.
        Ensure that the short_description does not include any of the following phrases or their equivalents: "Support for ...", "Agreement with the policy", "Disagreement with the policy", "Policies", "Opinions on ...", "Agreement with proposed policy", "Disagreement with proposed policy".


        == QUESTION ==
        {question}
        == QUESTION ENDS ==

        == KEYWORDS ==
        {keywords}
        == KEYWORDS END ==

        == SAMPLE ANSWERS TO THE QUESTION ==
        {responses}
        == SAMPLE ANSWERS END ==

        You MUST return your answer in JSON format. DO NOT DEVIATE FROM THIS FORMAT.
        The response should include two fields: 'short_description' and 'summary'.

        Example JSON:

        {{
            "short_description": 'the short_description you have generated',
            "summary": 'the summary you have generated',
        }}

        IT IS ESSENTIAL THAT YOU FORMAT YOUR RESPONSE AS JSON. INCLUDE NO OTHER MATERIAL.

        The JSON:
        [/INST]
        """

        return PromptTemplate.from_template(template=prompt_template)


def get_random_sample_of_responses_for_theme(
    theme: models.Theme, encoding: tiktoken.Encoding, max_tokens: int
) -> str:
    responses_for_theme = models.Answer.objects.filter(theme=theme).order_by("?")
    free_text_responses_for_theme = responses_for_theme.values_list("free_text", flat=True)

    # TWILIGHT ZONE: https://code.djangoproject.com/ticket/30655
    len(free_text_responses_for_theme)  # calling this prevents dupes in the output!
    # ENDS

    number_responses = responses_for_theme.count()
    combined_responses_string = ""
    i = 0
    append_more_results = True
    # TODO - how else might we want to separate documents (aka responses)?
    separator = "\n\n"
    while append_more_results:
        new_combined_responses_string = separator.join(
            [combined_responses_string, free_text_responses_for_theme[i]]
        )
        under_token_limit = len(encoding.encode(new_combined_responses_string)) < max_tokens
        if under_token_limit:
            combined_responses_string = new_combined_responses_string
        i = i + 1
        append_more_results = under_token_limit and (i < number_responses)
    return combined_responses_string
