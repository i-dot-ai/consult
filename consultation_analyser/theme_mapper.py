import asyncio

import pandas as pd
from django.conf import settings
from langchain_openai import ChatOpenAI
from simple_history.utils import bulk_create_with_history
from themefinder import detail_detection, theme_mapping

from consultation_analyser.consultations.models import (
    Question,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_base=settings.LLM_GATEWAY_URL,
    openai_api_key=settings.LITELLM_CONSULT_OPENAI_API_KEY,
)


def model_to_dict(objects, key, value) -> dict[str, str]:
    return {record[key]: record[value] for record in objects.values(key, value)}


def get_responses_df(question: Question):
    return pd.DataFrame(
        [
            {
                "response_id": response["respondent__themefinder_id"],
                "response": response["free_text"],
            }
            for response in Response.objects.filter(question=question).values(
                "respondent__themefinder_id", "free_text"
            )
        ]
    )


def sync_detail_detection(question: Question):
    responses_df = get_responses_df(question)

    detail_df, _ = asyncio.run(
        detail_detection(
            responses_df,
            llm,
            question=question.text,
        )
    )

    themefinder_id_mapping = model_to_dict(
        Response.objects.filter(question=question), "respondent__themefinder_id", "id"
    )

    detail_df["response_id"] = detail_df["response_id"].map(themefinder_id_mapping)
    detail_df["evidence_rich"] = detail_df["evidence_rich"] == "YES"
    detail_df = detail_df[~detail_df["response_id"].isna()]

    detail_dict = detail_df.set_index("response_id")["evidence_rich"].to_dict()

    annotations_to_save = [
        ResponseAnnotation(
            response_id=response_id,
            sentiment=ResponseAnnotation.Sentiment.UNCLEAR,
            evidence_rich=evidence_rich,
            human_reviewed=False,
        )
        for response_id, evidence_rich in detail_dict.items()
    ]

    bulk_create_with_history(annotations_to_save, ResponseAnnotation, batch_size=1000)


def sync_theme_mapping(question: Question):
    responses_df = get_responses_df(question)

    themes_df = pd.DataFrame(
        [
            {"topic_id": theme.key, "topic": f"{theme.name}: {theme.description}"}
            for theme in SelectedTheme.objects.filter(question=question)
        ]
    )

    if themes_df.empty:
        raise ValueError("no themes found")

    mapped_df, _ = asyncio.run(
        theme_mapping(
            responses_df,
            llm,
            refined_themes_df=themes_df,
            question=question.text,
        )
    )

    mapped_df = mapped_df.explode("labels")

    themefinder_id_mapping = model_to_dict(
        ResponseAnnotation.objects.filter(response__question=question),
        "response__respondent__themefinder_id",
        "id",
    )

    theme_key_mapping = model_to_dict(SelectedTheme.objects.filter(question=question), "key", "id")

    mapped_df["response_annotation_id"] = mapped_df["response_id"].map(themefinder_id_mapping)
    mapped_df["theme_id"] = mapped_df["labels"].map(theme_key_mapping)

    mapped_df = mapped_df[["response_annotation_id", "theme_id"]].drop_duplicates()

    response_annotation_theme_to_save = [
        ResponseAnnotationTheme(
            response_annotation_id=row.response_annotation_id,
            theme_id=row.theme_id,
        )
        for _, row in mapped_df.iterrows()
    ]

    bulk_create_with_history(
        response_annotation_theme_to_save, ResponseAnnotationTheme, batch_size=1000
    )
