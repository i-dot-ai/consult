# 2. Database design for consultation data and AI pipeline outputs

Date: 2025-01-27

## Status

Accepted

## Context

For a given consultation, Consult needs to store the questions, responses and all outputs of the AI pipeline. The pipeline generates themes for free-text responses, and assigns them to each response. Additionally we need to store some of the intermediate outputs.

The theme mapping pipeline outputs we need to store are: 
- Sentiment analysis
- Themes
- Theme mapping (mapping themes to each response)

For audit we need to store the outputs, but also the changes users have made.


## Decision

Use `django-simple-history` to record changes to the models that record mapping of responses to themes/sentiment (`ThemeMapping` and `SentimentMapping`). This will store a history of all changes with the user that made them.

To record the history of changes to `Theme` and `Framework` tables, create a new row everytime there is a change (storing the theme that it has been changed from and the user that made the change). Add helper methods, constraints and override `save()` method to enforce these rules. The reason we can't use `django-simple-history` is because in the mapping tables, we need to store the theme exactly at the point of mapping.


## Consequences
 
This change will enable us to store all of the AI pipeline outputs, ie assigning themes to free-text consultation responses and intermediate outputs. It will also enable us to track the history of all themes and theme assignments, and who made those changes.

A risk is that these models and their interactions are difficult to understand, but this is partially mitigated by adding logic in the model methods, and adding constraints in the model