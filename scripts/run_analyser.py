"""
RUN CONSULTATION ANALYSER

This script shows how easy it is to use the consult_ai package 
to create themes for answers
"""

import json
from langchain_aws import BedrockLLM
from consult_ai.models.public_schema import ConsultationWithResponses
from consult_ai.backends.theme.theme_backend_bert import ThemeBackendBert
from consult_ai.backends.summarise_themes.summarise_themes_langchain import (
    SummariseThemesLangchain,
)
from consult_ai.analyser.question_analyser import QuestionAnalyser

import logging

logging.getLogger("pipeline").setLevel(logging.INFO)

### Load data ==============

input_json = "tests/examples/chocolate.json"

with open(input_json) as f:
    data = json.load(f)

consultation_with_responses = ConsultationWithResponses(**data)

# Define backends ==========
theme_backend = ThemeBackendBert(
    embedding_model="sentence-transformers-testing/stsb-bert-tiny-safetensors"
)

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

# Setup analyser for a specific question ============
consulation_name = consultation_with_responses.consultation.name
question = consultation_with_responses.consultation.sections[0].questions[0]
responses = [
    response for response in consultation_with_responses.consultation_responses
]
answers = [
    answer
    for response in responses
    for answer in response.answers
    if answer.question_id == question.id
]

analyser = QuestionAnalyser(
    consultation_name=consulation_name, question=question, answers=answers
)

### Run analyser ==========
analyser.get_themes(theme_backend=theme_backend)
analyser.summarise_themes(summarise_theme_backend=summary_backend)

### Explore results ==========
print(analyser.themes)
