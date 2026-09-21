from app.models.example import MovieRecommendation
from app.services.llm_client import LLMClient


def test_generate_returns_valid_object_on_first_success(mocker):
    fake_response_content = (
        '{"title": "Dune", "year": 2021, "genre": "Sci-Fi", '
        '"one_line_reason": "Great visuals."}'
    )

    mock_groq_client = mocker.patch("app.services.llm_client.Groq")
    mock_create = mock_groq_client.return_value.chat.completions.create
    mock_create.return_value.choices = [
        mocker.Mock(message=mocker.Mock(content=fake_response_content))
    ]

    client = LLMClient()
    result = client.generate(
        schema=MovieRecommendation,
        system_prompt="You recommend movies.",
        user_prompt="Recommend a sci-fi movie.",
    )

    assert isinstance(result, MovieRecommendation)
    assert result.title == "Dune"
    assert result.year == 2021
    mock_create.assert_called_once()
