"""Values shared between the code that writes eval results and the code that reads them."""

# Evaluators record exceptions as 0.0 scores with this comment prefix, so readers must
# match it to tell a failed evaluator from a genuinely low score.
EVALUATOR_ERROR_PREFIX = "Error:"
