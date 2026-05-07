"""Static dummy content used to pre-populate the Responses sheet of
``consult_data_template.xlsx``.

Kept in a separate module so ``build_consult_data_template.py`` stays
focused on workbook construction. Each list is a small pool of
plausible values for a given column; the builder samples from them
to produce ~40 dummy rows so the template's validation rules can be
exercised end-to-end without real consultation data.
"""

DUMMY_HEADERS = [
    "respondent_id",
    "Which region of the UK do you live in?",
    "Which age band are you in?",
    "What type of organisation are you responding on behalf of?",
    "Q1: To what extent do you support the proposal set out in chapter 3?",
    "Q1: Please explain the reasoning behind your level of support for the proposal.",
    "Q2: How important is this issue to you personally?",
    "Q2: Please explain why you rated the importance of this issue the way you did.",
    "Q3: Do you have any other suggestions or comments you would like to share with us?",
    "Q4: Would you recommend this approach to others working in a similar context?",
]
DUMMY_REGIONS = ["North", "South", "East", "West", "London", "Scotland", "Wales"]
DUMMY_AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
DUMMY_ORG_TYPES = ["Individual", "Charity", "Business", "Public sector"]
DUMMY_AGREE = [
    "Strongly agree",
    "Agree",
    "Neutral",
    "Disagree",
    "Strongly disagree",
]
DUMMY_PRIORITY = ["High", "Medium", "Low"]
DUMMY_REASONS = [
    "I think this would help vulnerable groups in my community.",
    "The proposal is unclear and I am not sure what it would change.",
    "Cost is the main concern — there should be more detail on funding.",
    "It aligns with what other countries are doing successfully.",
    "I am worried about the impact on small businesses like mine.",
    "More consultation with frontline staff is needed before deciding.",
    "The timeline feels unrealistic given current resource pressures.",
    "I welcome the focus on accessibility but it could go further.",
]
DUMMY_EXPLANATIONS = [
    "Local authorities need clearer guidance and a longer lead-in time.",
    "Without ringfenced funding none of this will be deliverable.",
    "Digital-only delivery would exclude many of the people we support.",
    "Clear performance metrics and public reporting would help.",
    "It should be piloted in two or three regions first.",
    "Existing schemes already cover most of this — avoid duplication.",
]
DUMMY_SUGGESTIONS = [
    "Add a transitional protection period for current beneficiaries.",
    "Publish an equality impact assessment alongside the final policy.",
    "Engage charities that work directly with affected groups.",
    "Provide template materials in plain English and Welsh.",
    "Set up a feedback channel that stays open after rollout.",
    "Use independent evaluators to monitor early outcomes.",
]
DUMMY_RECOMMEND = ["Yes", "No", "Unsure"]
