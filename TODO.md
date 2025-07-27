# TODO: Database Verification Steps for Ingest Script

## Overview
This document outlines various methods to verify that the ingest script has successfully imported consultation data, including the new cross-cutting themes functionality.

## 1. Database Models Populated by Ingest Script

The ingest script populates these models in order:

1. **Consultation** - The main consultation record
2. **Respondent** - Survey participants with demographics  
3. **DemographicOption** - Normalized demographic field values
4. **Question** - Survey questions (free text and/or multiple choice)
5. **Response** - Respondent answers to questions
6. **Theme** - AI-generated themes for free text questions
7. **ResponseAnnotation** - AI outputs (sentiment, evidence_rich)
8. **ResponseAnnotationTheme** - Theme assignments to responses
9. **CrossCuttingTheme** - Themes that span multiple questions (NEW)
10. **CrossCuttingThemeAssignment** - Links themes to cross-cutting themes (NEW)

## 2. Django Shell Commands to Check Data

### Quick count checks:
```python
# Run with: python manage.py shell

from consultation_analyser.consultations.models import *

# Check main table counts
print(f"Consultations: {Consultation.objects.count()}")
print(f"Questions: {Question.objects.count()}")
print(f"Respondents: {Respondent.objects.count()}")
print(f"Responses: {Response.objects.count()}")
print(f"Themes: {Theme.objects.count()}")
print(f"Response Annotations: {ResponseAnnotation.objects.count()}")
print(f"Cross-cutting Themes: {CrossCuttingTheme.objects.count()}")
print(f"Cross-cutting Assignments: {CrossCuttingThemeAssignment.objects.count()}")
```

### Check cross-cutting themes details:
```python
# List all cross-cutting themes with their assignments
for cct in CrossCuttingTheme.objects.all():
    print(f"\n{cct.name}: {cct.description}")
    print(f"  Assigned themes: {cct.theme_assignments.count()}")
    for assignment in cct.theme_assignments.all():
        print(f"    - Question {assignment.theme.question.number}: {assignment.theme.name} (key: {assignment.theme.key})")
```

### Verify relationships:
```python
# Check a sample consultation's structure
c = Consultation.objects.first()
if c:
    print(f"Consultation: {c.title}")
    print(f"  Questions: {c.questions.count()}")
    print(f"  Respondents: {c.respondents.count()}")
    print(f"  Cross-cutting themes: {c.cross_cutting_themes.count()}")
    
    # Check first question
    q = c.questions.first()
    if q:
        print(f"\n  Question {q.number}: {q.text[:50]}...")
        print(f"    Responses: {q.responses.count()}")
        print(f"    Themes: {q.themes.count()}")
```

## 3. Direct SQL Queries

### Count all tables:
```sql
-- Run with: python manage.py dbshell

SELECT 'Consultations' as table_name, COUNT(*) as count FROM consultations_consultation
UNION ALL
SELECT 'Questions', COUNT(*) FROM consultations_question  
UNION ALL
SELECT 'Respondents', COUNT(*) FROM consultations_respondent
UNION ALL
SELECT 'Responses', COUNT(*) FROM consultations_response
UNION ALL
SELECT 'Themes', COUNT(*) FROM consultations_theme
UNION ALL
SELECT 'Response Annotations', COUNT(*) FROM consultations_responseannotation
UNION ALL
SELECT 'Cross-cutting Themes', COUNT(*) FROM consultations_crosscuttingtheme
UNION ALL
SELECT 'Cross-cutting Assignments', COUNT(*) FROM consultations_crosscuttingthemeassignment;
```

### Check cross-cutting themes:
```sql
-- List cross-cutting themes with assignment counts
SELECT 
    cct.name,
    cct.description,
    COUNT(ccta.id) as assignment_count
FROM consultations_crosscuttingtheme cct
LEFT JOIN consultations_crosscuttingthemeassignment ccta ON cct.id = ccta.cross_cutting_theme_id
GROUP BY cct.id, cct.name, cct.description;
```

## 4. Django Management Command (To Implement)

Create `consultation_analyser/consultations/management/commands/check_ingest.py`:

```python
# Command outline - TO BE IMPLEMENTED
# Usage: python manage.py check_ingest [consultation_id]

# Should check:
# - All expected tables have data
# - Relationships are properly linked
# - No orphaned records
# - Cross-cutting themes are properly assigned
# - Display summary statistics
# - Flag any potential issues
```

## 5. Django Admin Setup (To Implement)

Add to `consultation_analyser/consultations/admin.py`:

```python
# TO BE IMPLEMENTED
# Register CrossCuttingTheme and CrossCuttingThemeAssignment models
# This will allow visual inspection via /admin/
```

## 6. Validation Checklist

After running the ingest script, verify:

- [ ] **Consultation created** - Check title matches import
- [ ] **Respondents imported** - Count matches expected, demographics populated
- [ ] **Questions created** - Correct number, types (free_text/multiple_choice)
- [ ] **Responses linked** - Each response has respondent & question
- [ ] **Themes generated** - Only for free-text questions
- [ ] **Annotations created** - Sentiment and evidence_rich populated
- [ ] **Theme assignments** - Responses mapped to themes via ResponseAnnotationTheme
- [ ] **Cross-cutting themes** - Created from cross_cutting_themes.json
- [ ] **Cross-cutting assignments** - Themes correctly linked to cross-cutting themes

## 7. Common Issues to Check

1. **Missing embeddings** - Response.embedding should be populated for free text
2. **Missing search vectors** - Response.search_vector should be set
3. **Orphaned themes** - All themes should belong to a question
4. **Invalid theme keys** - Cross-cutting theme assignments should match existing theme keys
5. **Missing question totals** - Question.total_responses should be updated

## 8. Sample Test Data Location

The cross_cutting_themes.json file created for testing contains:
- 2 cross-cutting themes
- References to questions 4 and 7
- Theme keys using alphabetical labels (A, B, C, F)