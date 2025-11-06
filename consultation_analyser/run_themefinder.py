import asyncio

import pandas as pd
from django.conf import settings
from langchain_openai import ChatOpenAI
from simple_history.utils import bulk_create_with_history
from themefinder import (
    detail_detection,
    theme_condensation,
    theme_generation,
    theme_mapping,
    theme_refinement,
)
from themefinder.models import HierarchicalClusteringResponse, ThemeNode
from themefinder.theme_clustering_agent import ThemeClusteringAgent

from consultation_analyser.consultations.models import (
    CandidateTheme,
    Question,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)

logger = settings.LOGGER

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


def theme_identifier(question: Question):
    responses_df = get_responses_df(question)

    theme_df, _ = asyncio.run(
        theme_generation(responses_df, llm, question=question.text, partition_key=None)
    )

    condensed_theme_df, _ = asyncio.run(
        theme_condensation(
            theme_df,
            llm,
            question=question.text,
        )
    )
    refined_themes_df, _ = asyncio.run(
        theme_refinement(
            condensed_theme_df,
            llm,
            question=question.text,
        )
    )

    if len(refined_themes_df) > 20:
        _, all_themes_df = agentic_theme_selection(refined_themes_df)
    else:
        all_themes_df = refined_themes_df.copy()
        all_themes_df["parent_id"] = "0"

    records = {}
    for _, row in all_themes_df.iterrows():
        if row["topic_id"] != "0":
            name, description = row["topic"].split(":", 1)
            source_topic_count = 0

            records[row["topic_id"]] = CandidateTheme.objects.create(
                question=question,
                name=name,
                description=description,
                approximate_frequency=source_topic_count,
            )

    for _, row in all_themes_df.iterrows():
        if parent := records.get(row["parent_id"]):
            if child := records.get(row["topic_id"]):
                child.parent = parent
                child.save()


def agentic_theme_selection(
    refined_themes_df,
    min_selected_themes=10,
    max_selected_themes=20,
    max_cluster_iterations=0,
    n_target_themes=10,
):
    """
    Iteratively select themes using clustering with adaptive significance threshold.
    Will retry a fixed number of times before defaulting to top 20 themes.

    Parameters:
    -----------
    refined_themes_df : pd.DataFrame
        DataFrame containing themes with 'topic' column
    llm : object
        Language model object for theme clustering
    min_selected_themes : int, default=10
        Minimum number of themes to select
    max_selected_themes : int, default=20
        Maximum number of themes to select
    max_cluster_iterations : int, default=0
        Maximum number of clustering iterations to attempt
    n_target_themes : int, default=10
        Number of themes to target

    Returns:
    --------
    pd.DataFrame
        Selected themes with 'Theme Name', 'Theme Description', and 'topic' columns
    """
    refined_themes_df[["topic_label", "topic_description"]] = refined_themes_df["topic"].str.split(
        ":", n=1, expand=True
    )
    selected_themes = pd.DataFrame()

    initial_themes = [
        ThemeNode(
            topic_id=row["topic_id"],
            topic_label=row["topic_label"],
            topic_description=row["topic_description"],
            source_topic_count=row["source_topic_count"],
        )
        for _, row in refined_themes_df.iterrows()
    ]
    agent = ThemeClusteringAgent(
        llm.with_structured_output(HierarchicalClusteringResponse),
        initial_themes,
    )
    logger.info(
        f"Clustering themes with max_iterations={max_cluster_iterations}, target_themes={n_target_themes}"
    )
    for i in range(3):
        try:
            all_themes_df = agent.cluster_themes(
                max_iterations=max_cluster_iterations, target_themes=n_target_themes
            )
            if len(all_themes_df) > 0:
                break
        except:  # noqa: E722
            logger.info(f"Error when clustering, attempt {i}, retrying")

    selected_themes = pd.DataFrame()
    significance_percentage = 1
    while (
        len(selected_themes) < min_selected_themes or len(selected_themes) > max_selected_themes
    ) and (significance_percentage < 20):
        selected_themes = agent.select_themes(significance_percentage)
        significance_percentage += 1
    selected_themes["topic"] = (
        selected_themes["topic_label"] + ": " + selected_themes["topic_description"]
    )
    selected_themes.rename(
        columns={"topic_label": "Theme Name", "topic_description": "Theme Description"},
        inplace=True,
    )

    return selected_themes, all_themes_df
