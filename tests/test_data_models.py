from datetime import date as Date
import json
import pathlib
import os
import shutil

import pydantic
import pytest
import time_machine
import ruamel.yaml

from rendercv import data_models as dm

from .test_renderer import update_auxiliary_files


@pytest.mark.parametrize(
    "date, expected_date_object, expected_error",
    [
        ("2020-01-01", Date(2020, 1, 1), None),
        ("2020-01", Date(2020, 1, 1), None),
        ("2020", Date(2020, 1, 1), None),
        (2020, Date(2020, 1, 1), None),
        ("present", Date(2024, 1, 1), None),
        ("invalid", None, ValueError),
        ("20222", None, ValueError),
        ("202222-20200", None, ValueError),
        ("202222-12-20", None, ValueError),
        ("2022-20-20", None, ValueError),
    ],
)
@time_machine.travel("2024-01-01")
def test_get_date_object(date, expected_date_object, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            dm.get_date_object(date)
    else:
        assert dm.get_date_object(date) == expected_date_object


@pytest.mark.parametrize(
    "date, expected_date_string",
    [
        (Date(2020, 1, 1), "Jan. 2020"),
        (Date(2020, 2, 1), "Feb. 2020"),
        (Date(2020, 3, 1), "Mar. 2020"),
        (Date(2020, 4, 1), "Apr. 2020"),
        (Date(2020, 5, 1), "May 2020"),
        (Date(2020, 6, 1), "June 2020"),
        (Date(2020, 7, 1), "July 2020"),
        (Date(2020, 8, 1), "Aug. 2020"),
        (Date(2020, 9, 1), "Sept. 2020"),
        (Date(2020, 10, 1), "Oct. 2020"),
        (Date(2020, 11, 1), "Nov. 2020"),
        (Date(2020, 12, 1), "Dec. 2020"),
    ],
)
def test_format_date(date, expected_date_string):
    assert dm.format_date(date) == expected_date_string


def test_read_input_file(input_file_path):
    # Update the auxiliary files if update_auxiliary_files is True
    if update_auxiliary_files:
        input_dictionary = {
            "cv": {
                "name": "John Doe",
            },
            "design": {
                "theme": "classic",
            },
        }

        # dump the dictionary to a yaml file
        yaml = ruamel.yaml.YAML()
        yaml.dump(input_dictionary, input_file_path)

    data_model = dm.read_input_file(input_file_path)

    assert isinstance(data_model, dm.RenderCVDataModel)


def test_read_input_file_not_found():
    with pytest.raises(FileNotFoundError):
        invalid_path = pathlib.Path("doesntexist.yaml")
        dm.read_input_file(invalid_path)


def test_read_input_file_invalid_file(tmp_path):
    invalid_file_path = tmp_path / "invalid.extension"
    invalid_file_path.write_text("dummy content", encoding="utf-8")
    with pytest.raises(ValueError):
        dm.read_input_file(invalid_file_path)


def test_get_a_sample_data_model():
    data_model = dm.get_a_sample_data_model("John Doe")
    assert isinstance(data_model, dm.RenderCVDataModel)


def test_generate_json_schema():
    schema = dm.generate_json_schema()
    assert isinstance(schema, dict)


def test_generate_json_schema_file(tmp_path):
    schema_file_path = tmp_path / "schema.json"
    dm.generate_json_schema_file(schema_file_path)

    assert schema_file_path.exists()

    schema_text = schema_file_path.read_text(encoding="utf-8")
    schema = json.loads(schema_text)

    assert isinstance(schema, dict)


def test_if_the_schema_is_the_latest(root_directory_path):
    original_schema_file_path = root_directory_path / "schema.json"
    original_schema_text = original_schema_file_path.read_text()
    original_schema = json.loads(original_schema_text)

    new_schema = dm.generate_json_schema()

    assert original_schema == new_schema


@pytest.mark.parametrize(
    "start_date, end_date, date, expected_date_string, expected_date_string_only_years,"
    " expected_time_span",
    [
        (
            "2020-01-01",
            "2021-01-01",
            None,
            "Jan. 2020 to Jan. 2021",
            "2020 to 2021",
            "1 year 1 month",
        ),
        (
            "2020-01",
            "2021-01",
            None,
            "Jan. 2020 to Jan. 2021",
            "2020 to 2021",
            "1 year 1 month",
        ),
        (
            "2020-01",
            "2021-01-01",
            None,
            "Jan. 2020 to Jan. 2021",
            "2020 to 2021",
            "1 year 1 month",
        ),
        (
            "2020-01-01",
            "2021-01",
            None,
            "Jan. 2020 to Jan. 2021",
            "2020 to 2021",
            "1 year 1 month",
        ),
        (
            "2020-01-01",
            None,
            None,
            "Jan. 2020 to present",
            "2020 to present",
            "4 years 1 month",
        ),
        (
            "2020-02-01",
            "present",
            None,
            "Feb. 2020 to present",
            "2020 to present",
            "3 years 11 months",
        ),
        ("2020-01-01", "2021-01-01", "2023-02-01", "Feb. 2023", "Feb. 2023", ""),
        ("2020", "2021", None, "2020 to 2021", "2020 to 2021", "1 year"),
        ("2020", None, None, "2020 to present", "2020 to present", "4 years"),
        ("2020-10-10", "2022", None, "Oct. 2020 to 2022", "2020 to 2022", "2 years"),
        (
            "2020-10-10",
            "2020-11-05",
            None,
            "Oct. 2020 to Nov. 2020",
            "2020 to 2020",
            "1 month",
        ),
        ("2022", "2023-10-10", None, "2022 to Oct. 2023", "2022 to 2023", "1 year"),
        (
            "2020-01-01",
            "present",
            "My Custom Date",
            "My Custom Date",
            "My Custom Date",
            "",
        ),
        (
            "2020-01-01",
            None,
            "My Custom Date",
            "My Custom Date",
            "My Custom Date",
            "",
        ),
        (
            None,
            None,
            "My Custom Date",
            "My Custom Date",
            "My Custom Date",
            "",
        ),
        (
            None,
            "2020-01-01",
            "My Custom Date",
            "My Custom Date",
            "My Custom Date",
            "",
        ),
        (None, None, "2020-01-01", "Jan. 2020", "Jan. 2020", ""),
        (None, None, None, "", "", ""),
    ],
)
@time_machine.travel("2024-01-01")
def test_dates(
    start_date,
    end_date,
    date,
    expected_date_string,
    expected_date_string_only_years,
    expected_time_span,
):
    entry_base = dm.EntryBase(start_date=start_date, end_date=end_date, date=date)

    assert entry_base.date_string == expected_date_string
    assert entry_base.date_string_only_years == expected_date_string_only_years
    assert entry_base.time_span_string == expected_time_span


@pytest.mark.parametrize(
    "date, expected_date_string",
    [
        ("2020-01-01", "Jan. 2020"),
        ("2020-01", "Jan. 2020"),
        ("2020", "2020"),
    ],
)
def test_publication_dates(publication_entry, date, expected_date_string):
    publication_entry["date"] = date
    publication_entry = dm.PublicationEntry(**publication_entry)
    assert publication_entry.date_string == expected_date_string


@pytest.mark.parametrize("date", ["aaa", None, "2025"])
def test_invalid_publication_dates(publication_entry, date):
    with pytest.raises(pydantic.ValidationError):
        publication_entry["date"] = date
        dm.PublicationEntry(**publication_entry)


@pytest.mark.parametrize(
    "start_date, end_date, date",
    [
        ("aaa", "2021-01-01", None),
        ("2020-01-01", "aaa", None),
        (None, "2020-01-01", None),
        ("2023-01-01", "2021-01-01", None),
        ("2999-01-01", None, None),
        ("2020-01-01", "2999-01-01", None),
        ("2022", "2021", None),
        ("2021", "2060", None),
        ("2025", "2021", None),
        (None, None, "2028"),
        ("2020-01-01", "invalid_end_date", None),
        ("invalid_start_date", "2021-01-01", None),
        ("2020-99-99", "2021-01-01", None),
        ("2020-10-12", "2020-99-99", None),
    ],
)
def test_invalid_dates(start_date, end_date, date):
    with pytest.raises(pydantic.ValidationError):
        dm.EntryBase(start_date=start_date, end_date=end_date, date=date)


@pytest.mark.parametrize(
    "doi, expected_doi_url",
    [
        ("10.1109/TASC.2023.3340648", "https://doi.org/10.1109/TASC.2023.3340648"),
    ],
)
def test_doi_url(publication_entry, doi, expected_doi_url):
    publication_entry["doi"] = doi
    publication_entry = dm.PublicationEntry(**publication_entry)
    assert publication_entry.doi_url == expected_doi_url


@pytest.mark.parametrize(
    "doi",
    ["aaa10.1109/TASC.2023.3340648", "aaa"],
)
def test_invalid_doi(publication_entry, doi):
    with pytest.raises(pydantic.ValidationError):
        publication_entry["doi"] = doi
        dm.PublicationEntry(**publication_entry)


@pytest.mark.parametrize(
    "network, username",
    [("Mastodon", "invalidmastodon"), ("Mastodon", "@inva@l@id")],
)
def test_invalid_social_networks(network, username):
    with pytest.raises(pydantic.ValidationError):
        dm.SocialNetwork(network=network, username=username)


@pytest.mark.parametrize(
    "network, username, expected_url",
    [
        ("LinkedIn", "myusername", "https://linkedin.com/in/myusername"),
        ("GitHub", "myusername", "https://github.com/myusername"),
        ("Instagram", "myusername", "https://instagram.com/myusername"),
        ("Orcid", "myusername", "https://orcid.org/myusername"),
        ("Twitter", "myusername", "https://twitter.com/myusername"),
        ("Mastodon", "@myusername", "https://mastodon.social/@myusername"),
    ],
)
def test_social_network_url(network, username, expected_url):
    social_network = dm.SocialNetwork(network=network, username=username)
    assert str(social_network.url) == expected_url


@pytest.mark.parametrize(
    "entry, expected_entry_type, expected_section_type",
    [
        (
            "publication_entry",
            "PublicationEntry",
            dm.SectionWithPublicationEntries,
        ),
        (
            "experience_entry",
            "ExperienceEntry",
            dm.SectionWithExperienceEntries,
        ),
        (
            "education_entry",
            "EducationEntry",
            dm.SectionWithEducationEntries,
        ),
        (
            "normal_entry",
            "NormalEntry",
            dm.SectionWithNormalEntries,
        ),
        ("one_line_entry", "OneLineEntry", dm.SectionWithOneLineEntries),
        ("text_entry", "TextEntry", dm.SectionWithTextEntries),
    ],
)
def test_get_entry_and_section_type(
    entry, expected_entry_type, expected_section_type, request
):
    entry = request.getfixturevalue(entry)
    entry_type, section_type = dm.get_entry_and_section_type(entry)
    assert entry_type == expected_entry_type
    assert section_type == expected_section_type

    # initialize the entry with the entry type
    if not entry_type == "TextEntry":
        entry = eval(f"dm.{entry_type}(**entry)")
        entry_type, section_type = dm.get_entry_and_section_type(entry)
        assert entry_type == expected_entry_type
        assert section_type == expected_section_type


def test_sections(
    education_entry,
    experience_entry,
    publication_entry,
    normal_entry,
    one_line_entry,
    text_entry,
):
    input = {
        "name": "John Doe",
        "sections": {
            "arbitrary_title": [
                education_entry,
                education_entry,
            ],
            "arbitrary_title_2": [
                experience_entry,
                experience_entry,
            ],
            "arbitrary_title_3": [
                publication_entry,
                publication_entry,
            ],
            "arbitrary_title_4": [
                normal_entry,
                normal_entry,
            ],
            "arbitrary_title_5": [
                one_line_entry,
                one_line_entry,
            ],
            "arbitrary_title_6": [
                text_entry,
                text_entry,
            ],
        },
    }

    cv = dm.CurriculumVitae(**input)
    assert len(cv.sections) == 6
    for section in cv.sections:
        assert len(section.entries) == 2


def test_sections_with_invalid_entries():
    input = {"name": "John Doe", "sections": dict()}
    input["sections"]["section_title"] = [
        {
            "this": "is",
            "an": "invalid",
            "entry": 10,
        }
    ]
    with pytest.raises(pydantic.ValidationError):
        dm.CurriculumVitae(**input)


@pytest.mark.parametrize(
    "invalid_custom_theme_name",
    [
        "pathdoesntexist",
        "invalid_theme_name",
    ],
)
def test_invalid_custom_theme(invalid_custom_theme_name):
    with pytest.raises(pydantic.ValidationError):
        dm.RenderCVDataModel(
            **{
                "cv": {"name": "John Doe"},
                "design": {"theme": invalid_custom_theme_name},
            }
        )


def test_custom_theme_with_missing_files(tmp_path):
    custom_theme_path = tmp_path / "customtheme"
    custom_theme_path.mkdir()
    with pytest.raises(pydantic.ValidationError):
        os.chdir(tmp_path)
        dm.RenderCVDataModel(
            **{  # type: ignore
                "cv": {"name": "John Doe"},
                "design": {"theme": "customtheme"},
            }
        )


def test_custom_theme(auxiliary_files_directory_path):
    os.chdir(
        auxiliary_files_directory_path
        / "test_copy_theme_files_to_output_directory_custom_theme"
    )
    data_model = dm.RenderCVDataModel(
        **{  # type: ignore
            "cv": {"name": "John Doe"},
            "design": {"theme": "dummytheme"},
        }
    )

    assert data_model.design.theme == "dummytheme"


def test_custom_theme_without_init_file(tmp_path, auxiliary_files_directory_path):
    reference_custom_theme_path = (
        auxiliary_files_directory_path
        / "test_copy_theme_files_to_output_directory_custom_theme"
        / "dummytheme"
    )

    # copy the directory to tmp_path:
    custom_theme_path = tmp_path / "dummytheme"
    shutil.copytree(reference_custom_theme_path, custom_theme_path, dirs_exist_ok=True)

    # remove the __init__.py file:
    init_file = custom_theme_path / "__init__.py"
    init_file.unlink()

    os.chdir(tmp_path)
    data_model = dm.RenderCVDataModel(
        **{  # type: ignore
            "cv": {"name": "John Doe"},
            "design": {"theme": "dummytheme"},
        }
    )

    assert data_model.design.theme == "dummytheme"
