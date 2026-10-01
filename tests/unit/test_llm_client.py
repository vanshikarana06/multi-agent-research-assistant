import pytest

from app.core.exceptions import LLMValidationError
from app.models.example import MovieRecommendation
from app.services.llm_client import LLMClient


def test_generate_returns_valid_object_on_first_success(mocker):
    fake_response_content = (
        '{"title": "Dune", "year": 2021, "genre": "Sci-Fi", "one_line_reason": "Great visuals."}'
    )

    mock_groq_client = mocker.patch(
        "app.services.llm_client.Groq"
    )  # temporarily replace a real thing with a fake,
    # A MagicMock can automatically
    # create fake children when you access them.
    mock_create = mock_groq_client.return_value.chat.completions.create
    mock_create.return_value.choices = [
        mocker.Mock(message=mocker.Mock(content=fake_response_content))
    ]  # fake response returned when create() is called

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


def test_generate_retries_after_validation_failure_then_succeeds(mocker):
    bad_json = (
        '{"title": "Dune", "year": "not a number", "genre": "Sci-Fi", "one_line_reason": "x"}'
    )
    good_json = (
        '{"title": "Dune", "year": 2021, "genre": "Sci-Fi", "one_line_reason": "Great visuals."}'
    )

    mock_groq_client = mocker.patch("app.services.llm_client.Groq")
    mock_create = mock_groq_client.return_value.chat.completions.create
    mock_create.side_effect = [
        mocker.Mock(choices=[mocker.Mock(message=mocker.Mock(content=bad_json))]),
        mocker.Mock(choices=[mocker.Mock(message=mocker.Mock(content=good_json))]),
    ]

    client = LLMClient()
    result = client.generate(
        schema=MovieRecommendation,
        system_prompt="You recommend movies.",
        user_prompt="Recommend a sci-fi movie.",
    )

    assert result.year == 2021
    assert mock_create.call_count == 2


def test_generate_raises_after_exhausting_validation_retries(mocker):
    always_bad_json = (
        '{"title": "Dune", "year": "not a number", "genre": "Sci-Fi", "one_line_reason": "x"}'
    )

    mock_groq_client = mocker.patch("app.services.llm_client.Groq")
    mock_create = mock_groq_client.return_value.chat.completions.create
    mock_create.return_value.choices = [mocker.Mock(message=mocker.Mock(content=always_bad_json))]

    client = LLMClient()

    with pytest.raises(LLMValidationError) as exc_info:
        client.generate(
            schema=MovieRecommendation,
            system_prompt="You recommend movies.",
            user_prompt="Recommend a sci-fi movie.",
            max_validation_retries=2,
        )

    assert exc_info.value.raw_output == always_bad_json
    assert mock_create.call_count == 3
