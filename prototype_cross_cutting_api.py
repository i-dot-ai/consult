#!/usr/bin/env python
"""
Prototype script for cross-cutting themes API endpoint
Run with: python manage.py shell < prototype_cross_cutting_api.py
"""

import json

from consultation_analyser.consultations import models

# Configuration - change these to match your test data
CONSULTATION_SLUG = "cross_cutting_test"  # Replace with actual consultation slug


def get_cross_cutting_themes_for_consultation(consultation_slug):
    """
    Main function to get cross-cutting themes data
    This simulates what our API endpoint will do
    """
    
    # Step 1: Get the consultation
    try:
        consultation = models.Consultation.objects.get(slug=consultation_slug)
        print(f"✓ Found consultation: {consultation.title}")
    except models.Consultation.DoesNotExist:
        print(f"✗ Consultation with slug '{consultation_slug}' not found")
        print("\nAvailable consultations:")
        for c in models.Consultation.objects.all():
            print(f"  - {c.slug}: {c.title}")
        return None
    
    # Step 2: Get all cross-cutting themes for this consultation
    cross_cutting_themes = models.CrossCuttingTheme.objects.filter(
        consultation=consultation
    ).prefetch_related(
        'theme_assignments__theme__question'
    )
    
    print(f"\n✓ Found {cross_cutting_themes.count()} cross-cutting themes")
    
    # Step 3: Build the response data structure
    response_data = {
        "consultation_id": str(consultation.id),
        "consultation_title": consultation.title,
        "cross_cutting_themes": []
    }
    
    for cct in cross_cutting_themes:
        # Build theme data
        theme_data = {
            "id": str(cct.id),
            "name": cct.name,
            "description": cct.description,
            "themes": []
        }
        
        # Get all theme assignments
        for assignment in cct.theme_assignments.all():
            theme = assignment.theme
            theme_info = {
                "theme_id": str(theme.id),
                "theme_name": theme.name,
                "theme_key": theme.key,
                "theme_description": theme.description,
                "question_number": theme.question.number,
                "question_text": theme.question.text[:100] + "..." if len(theme.question.text) > 100 else theme.question.text
            }
            theme_data["themes"].append(theme_info)
        
        response_data["cross_cutting_themes"].append(theme_data)
    
    return response_data


def get_theme_response_counts(theme_id):
    """
    Helper function to get response counts for a specific theme
    This demonstrates how to reuse existing query logic
    """
    # Count responses that have this theme assigned
    count = models.Response.objects.filter(
        annotation__themes__id=theme_id
    ).distinct().count()
    
    return count


def enhance_with_response_counts(cross_cutting_data):
    """
    Enhance the cross-cutting themes data with response counts
    This shows how we can combine data from different sources
    """
    if not cross_cutting_data:
        return None
        
    print("\n📊 Adding response counts...")
    
    for cct in cross_cutting_data["cross_cutting_themes"]:
        cct["total_responses"] = 0
        
        for theme in cct["themes"]:
            # Get response count for this theme
            theme_id = theme["theme_id"]
            response_count = get_theme_response_counts(theme_id)
            theme["response_count"] = response_count
            cct["total_responses"] += response_count
            
            print(f"  - {theme['theme_name']}: {response_count} responses")
    
    return cross_cutting_data


def main():
    """
    Main execution function
    """
    print("="*60)
    print("Cross-Cutting Themes API Prototype")
    print("="*60)
    
    # Get basic cross-cutting themes data
    data = get_cross_cutting_themes_for_consultation(CONSULTATION_SLUG)
    
    if data:
        # Enhance with additional data
        enhanced_data = enhance_with_response_counts(data)
        
        # Pretty print the final result
        print("\n📄 Final API Response:")
        print("-"*60)
        print(json.dumps(enhanced_data, indent=2))
        
        # Summary statistics
        print("\n📈 Summary:")
        print(f"  - Total cross-cutting themes: {len(enhanced_data['cross_cutting_themes'])}")
        total_assignments = sum(len(cct['themes']) for cct in enhanced_data['cross_cutting_themes'])
        print(f"  - Total theme assignments: {total_assignments}")
        
        # Show which questions are involved
        questions_involved = set()
        for cct in enhanced_data['cross_cutting_themes']:
            for theme in cct['themes']:
                questions_involved.add(theme['question_number'])
        print(f"  - Questions involved: {sorted(questions_involved)}")


# Run the script
if __name__ == "__main__":
    main()
else:
    # When run in Django shell
    print("\n💡 To run the prototype, call: main()")
    print("   Or change CONSULTATION_SLUG and call individual functions")
    print("   Example: data = get_cross_cutting_themes_for_consultation('my-consultation')")
    
# Always run main() when the script is executed
main()