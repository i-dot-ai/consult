"""
Use LLMs to generate summaries for themes. More to follow!
"""
import random
from django.conf import settings
from pydantic import BaseModel

from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.output_parsers import PydanticOutputParser, RetryWithErrorOutputParser
from consultation_analyser.consultations.decorators.sagemaker_endpoint_status_check import check_and_launch_sagemaker
from consultation_analyser.consultations.models import Theme
import tiktoken


# Pydantic output parser for the LLM
class Output(BaseModel):
    phrase: str
    summary: str


def dummy_generate_theme_summary(theme: Theme) -> str:
    made_up_summary = (", ").join(theme.keywords)
    return made_up_summary


def get_llm_chain(llm):

    _prompt_template = """
    You are serving as an expert AI assisting UK government \
    policy officers in analyzing public opinions on new policies affecting UK veterans. \
    We want you to distill key sentiments and arguments expressed in the responses. \
    We conducted a survey, and responses to a specific question have been categorized under a single common theme.\
    We have provided a sample of responses for the theme and frequently occurring key words. \
    We have also provided some background information about the chapter of the survey in which the question was asked. \
    Instead of general agreement/disagreement, focus on capturing specific perspectives. \
    Your task is to generate ONLY:
    1) A very concise phrase, NO MORE THAN 10 WORDS, that encapsulates both the prevalent keywords and the nuanced opinions conveyed in the responses.
    2) A summary of the opinions expressed in the responses.
    You should generate a phrase and summary that reflects the MOST COMMON opinion expressed in the responses. \
    DO NOT prefix your phrase with "Most responses" or words like that. SUMMARISE the responses themselves. \
    You MUST return your answer in JSON format. DO NOT DEVIATE FROM THIS FORMAT. \
    The response MUST be formatted with two fields: "phrase" and "summary". \
    IT IS ESSENTIAL THAT YOU FORMAT YOUR RESPONSE LIKE THIS.

    == QUESTION ==
    {question}

    == KEYWORDS ==
    {keywords}

    == SAMPLE RESPONSES ==
    {responses}

    Ensure that the phrase you generate does not include any of the following phrases or their equivalents: "Support for ...", "Agreement with the policy", "Disagreement with the policy", "Policies", "Opinions on ...", "Agreement with proposed policy", "Disagreement with proposed policy".
    """
    DEFAULT_PROMPT = PromptTemplate.from_template(_prompt_template)

    llm_chain = LLMChain(llm=llm, prompt=DEFAULT_PROMPT)

    return llm_chain, DEFAULT_PROMPT


def token_count(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def get_docs_str(docs, max_tokens):
    random.shuffle(docs)
    docs_str = "\n".join(docs)
    frac = max_tokens / token_count(docs_str)
    if frac > 1 :
        return docs_str
    else:
        return "\n".join(f"<doc{i+1}> {doc} </doc{i+1}>" for i, doc in enumerate(docs[:int(len(docs) * frac)]))


def get_label_and_summary_for_theme(theme, llm_chain, retry_parser, parser, prompt):
    answers = [a.free_text for a in theme.answer_set.all()]
    docs_str = get_docs_str(answers, max_tokens=2000)
    keywords = theme.keywords
    question_text = theme.question.text

    llm_response = llm_chain(
        {
            "question": question_text,
            "keywords": keywords,
            "responses": docs_str,
        }

    )["text"]

    try:
        parsed_output = parser.parse(llm_response)
        return parsed_output.phrase, parsed_output.summary
    except:
        try:
            parsed_output = retry_parser.parse_with_prompt(
                llm_response,
                prompt.format_prompt(
                    question_text,
                    keywords,
                    docs_str,
                ),
            )
            return parsed_output.phrase, parsed_output.summary
        except:
            print(f"Cannot parse LLM response: {llm_response}")
            return "blank", "blank"


def get_llm():
    return OpenAI()
    # return gpt3.5
    pass

def run_llm(theme):
    llm = get_llm()
    parser = PydanticOutputParser(pydantic_object=Output)
    retry_parser = RetryWithErrorOutputParser.from_llm(
        parser=parser, llm=llm, max_retries=3,
    )
    llm_chain, prompt = get_llm_chain(llm)

    label, summary = get_label_and_summary_for_theme(theme, llm_chain, retry_parser, parser, prompt)

    theme.summary = summary
    theme.save()


def create_llm_summaries_for_consultation(consultation):
    themes = Theme.objects.filter(question__section__consultation=consultation).filter(question__has_free_text=True)
    for theme in themes:
        run_llm(theme)
