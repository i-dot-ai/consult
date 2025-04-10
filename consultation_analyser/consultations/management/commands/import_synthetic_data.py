import json

from django.core.management.base import BaseCommand

from consultation_analyser.consultations import models


class Command(BaseCommand):
    help = "Import synthetic data from the 'downloads' folder"

    def get_theme(self, theme_data, response_theme_data, framework):
        search_string = list(response_theme_data)[0]
        theme_dict = theme_data["Agreement"] | theme_data["Disagreement"]

        try:
            key = next(filter(lambda k: search_string in str(theme_dict[k]), theme_dict.keys()))
            return models.Theme.objects.get(framework=framework, key=key)
        except StopIteration:
            return None
        except models.Theme.DoesNotExist:
            return None

    def import_question(self, index, consultation):
        self.stdout.write(f"Creating question {index}")

        with open(f"synthetic_data/question_{index}/expanded_question.json") as f:
            question_data = json.load(f)

        question = models.Question.objects.create(
            consultation=consultation,
            text=question_data["text"],
            number=index,
        )

        if question_data["has_free_text"]:
            free_text_qp = models.QuestionPart.objects.create(
                question=question,
                number=0,
                type=models.QuestionPart.QuestionType.FREE_TEXT,
            )
            execution_run = models.ExecutionRun.objects.create(
                type=models.ExecutionRun.TaskType.THEME_GENERATION,
            )
            framework = models.Framework.create_initial_framework(
                theme_generation_execution_run=execution_run, question_part=free_text_qp
            )

            with open(f"synthetic_data/question_{index}/framework_topics.json") as f:
                theme_data = json.load(f)

            for key, value in (theme_data["Agreement"] | theme_data["Disagreement"]).items():
                models.Theme.create_initial_theme(
                    framework=framework,
                    # The synthetic data topics have several synonyms, but we're only using the first one
                    name=value["topics"][0]["topic_name"],
                    description=value["topics"][0]["rationale"],
                    key=key,
                )

        if question_data["multiple_choice"]:
            multi_choice_qp = models.QuestionPart.objects.create(
                question=question,
                number=1 if question_data["has_free_text"] else 0,
                type=models.QuestionPart.QuestionType.MULTIPLE_OPTIONS,
                # The synthetic data only has one multiple choice set
                options=json.loads(json.dumps(question_data["multiple_choice"][0]["options"])),
            )

        # respondents = models.Respondent.objects.filter(consultation=consultation)
        with open(f"synthetic_data/question_{index}/responses.json") as f:
            responses = json.load(f)

        for i, response in enumerate(responses):
            self.stdout.write(f"Creating responses for {i}")

            respondent = models.Respondent.objects.get(
                consultation=consultation,
                themefinder_respondent_id=(response["response_id"] + 1),
            )

            if models.Answer.objects.filter(
                respondent=respondent, question_part__question=question
            ).exists():
                continue
            if response.get("free_text"):
                self.stdout.write(f"Creating free-text response for {i}")
                answer = models.Answer.objects.create(
                    question_part=free_text_qp,
                    respondent=respondent,
                    text=response["free_text"],
                )

                if response.get("overall_agreement") == "Agreement":
                    position = models.SentimentMapping.Position.AGREEMENT
                elif response.get("overall_agreement") == "Disagreement":
                    position = models.SentimentMapping.Position.DISAGREEMENT
                elif response.get("overall_agreement") == "Conflicted (Undecided)":
                    position = models.SentimentMapping.Position.UNCLEAR

                if position:
                    # TODO: fix the execution run type here
                    models.SentimentMapping.objects.create(
                        answer=answer,
                        sentiment_analysis_execution_run=execution_run,
                        position=position,
                    )

                for topic in response["agreed_topics"]:
                    # TODO: fix the execution run type here
                    if theme := self.get_theme(theme_data, topic, framework):
                        models.ThemeMapping.objects.create(
                            answer=answer,
                            theme=theme,
                            theme_mapping_execution_run=execution_run,
                            stance=models.ThemeMapping.Stance.POSITIVE,
                        )

                for topic in response["counter_topics"]:
                    if theme := self.get_theme(theme_data, topic, framework):
                        models.ThemeMapping.objects.create(
                            answer=answer,
                            theme=theme,
                            theme_mapping_execution_run=execution_run,
                            stance=models.ThemeMapping.Stance.NEGATIVE,
                        )

            if response.get("multiple_choice_option"):
                self.stdout.write(f"Creating multiple choice response for {i}")
                models.Answer.objects.create(
                    question_part=multi_choice_qp,
                    respondent=respondent,
                    chosen_options=[response["multiple_choice_option"]],
                )

    def handle(self, *args, **options):
        self.stdout.write("Importing synthetic data")

        consultation = models.Consultation.objects.create(title="Synthetic Data Consultation")

        # Generating respondents. In the synthetic data, the respondents were regenerated for each question, but as we're only using this for local testing, we'll just use the first batch.
        with open("synthetic_data/question_3/responses.json") as f:
            responses = json.load(f)

        for response in responses:
            if models.Respondent.objects.filter(
                consultation=consultation,
                themefinder_respondent_id=(response["response_id"] + 1),
            ).exists():
                continue

            models.Respondent.objects.create(
                consultation=consultation,
                themefinder_respondent_id=(response["response_id"] + 1),
                data={
                    "individual": response["demographic_individual"],
                    "region": response["demographic_region"],
                },
            )

        for i in range(1, 10):
            self.import_question(i, consultation)

        self.stdout.write("Successfully imported synthetic data")
