import logging

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models.llms import LLM
from typing import List

from consult_ai.models.public_schema import Theme, Answer
from consult_ai.models.schemas_for_querying import ThemeSummary
from consult_ai.backends.summarise_themes.summarise_themes_base import (
    SummariseThemesBase,
)

logger = logging.getLogger("pipeline")


class SummariseThemesLangchain(SummariseThemesBase):
    def __init__(self, llm: LLM):
        self.llm = llm
        self.max_tokens = 2000

    def summarise_theme(
        self,
        theme: Theme,
        sample_responses: List[Answer],
        consultation_name: str,
        question: str,
    ) -> Theme:
        prompt_template = self.__get_prompt_template()

        prompt_inputs = {
            "consultation_name": consultation_name,
            "question": question,
            "keywords": ", ".join(theme.topic_keywords),
            "responses": sample_responses,
        }

        parser = PydanticOutputParser(pydantic_object=ThemeSummary)
        errors = (OutputParserException, ValueError)
        try:
            llm_chain = prompt_template | self.llm | parser
            # TODO - are the outputs of this as good as the RetryWithErrorOutputParser?
            llm_chain = llm_chain.with_retry(
                retry_if_exception_type=errors,
                wait_exponential_jitter=False,
                stop_after_attempt=10,
            )
            parsed_output = llm_chain.invoke(prompt_inputs)
            output = {
                "short_description": parsed_output.short_description,
                "summary": parsed_output.summary,
            }
            theme.short_description = output["short_description"]
            theme.summary = output["summary"]

            return theme
        except errors as e:
            logger.info(
                f"Failed to summarise theme with keywords: {theme.topic_keywords}."
            )
            error_message = e.args[0] if e.args else ""
            logger.info(error_message)
            return theme

    def __get_prompt_template(self):
        # TODO - what is the best way to get info about the policy area into the prompt.
        # TODO - this might need tweaking on the first run.
        prompt_template = """
        <s>[INST] You are serving as an expert AI assisting UK government policy officers in analyzing public opinions on new policies.

        We conducted a consultation, and answers to a specific question have been grouped under a single common theme.
        We have provided a sample of answers for the theme and frequently occurring keywords.
        We want you to distill key arguments expressed in the answers.

        Your task is to generate a valid JSON object containing "short_description" and "summary" fields based on the given information.

        IT IS ESSENTIAL THAT YOU FORMAT YOUR RESPONSE AS JSON. INCLUDE NO OTHER MATERIAL.

        For example, given the following information in CONSULTATION NAME, QUESTION, KEYWORDS and SAMPLE ANSWERS TO THE QUESTION blocks:

        == CONSULTATION NAME ==
        Consultation on changing the recipe of Cadbury's chocolate bars
        == CONSULTATION NAME ENDS ==

        == QUESTION ==
        What is the most important quality of Dairy Milk?
        == QUESTION ENDS ==

        == KEYWORDS ==
        creamy,sweet,delicious,flavourful,mouthfeel
        == KEYWORDS END ==

        == SAMPLE ANSWERS TO THE QUESTION ==
        I find Dairy Milk to be creamy and delicious.

        Just the right balance of sweetness and creamy texture.

        For me the creaminess of Dairy Milk gives it the edge
        == SAMPLE ANSWERS END ==

        Would become: [/INST]
        {{
            "short_description": 'The creaminess of Dairy Milk',
            "summary": 'Answers emphasised how creamy Dairy Milk is',
        }}</s>
        [INST] == CONSULTATION NAME ==
        {consultation_name}
        == CONSULTATION NAME ENDS ==

        == QUESTION ==
        {question}
        == QUESTION ENDS ==

        == KEYWORDS ==
        {keywords}
        == KEYWORDS END ==

        == SAMPLE ANSWERS TO THE QUESTION ==
        {responses}
        == SAMPLE ANSWERS END == [/INST]
        """

        return PromptTemplate.from_template(template=prompt_template)


if __name__ == "__main__":
    from langchain_aws import BedrockLLM

    llm = BedrockLLM(
        # hardcoding this because the kwargs and model
        # are coupled - can generalise later
        model_id="mistral.mistral-large-2402-v1:0",
        region_name="eu-west-2",
        model_kwargs={
            "temperature": 0.8,
            "stop": ["###", "</s>"],
        },
    )
    summary_backend = SummariseThemesLangchain(llm=llm)

    theme = Theme(topic_id=0, topic_keywords=["apples", "bananas", "limes"])
    sample_responses = ["I really like apples"]
    conultation_name = "Views on food"
    question = "What's your favourite food?"

    test = summary_backend.summarise_theme(
        theme=theme,
        sample_responses=sample_responses,
        consultation_name=conultation_name,
        question=question,
    )

    print(test)
