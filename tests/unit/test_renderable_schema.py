from consultation_analyser.consultations import public_schema
from consultation_analyser.consultations.decorators.renderable_schema import RenderableSchema


def test_renderable_schema():
    renderable = RenderableSchema(public_schema.Consultation)

    assert renderable.name() == "Consultation"
    assert "the top-level object describing a consultation" in renderable.description()

    assert renderable.rows()[0]["name"] == "name"
    assert renderable.rows()[0]["description"] == "The name of the consultation"
