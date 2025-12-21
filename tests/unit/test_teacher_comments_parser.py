"""Unit tests for teacher comments HTML parser.

These tests use static HTML fixtures and don't require
external dependencies or network access.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


# Sample HTML matching real PowerSchool teacher comments page structure
SAMPLE_TEACHER_COMMENTS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Teacher Comments</title></head>
<body>
<h1>Teacher Comments: Student, Test</h1>
<table class="grid linkDescList">
<tbody><tr align="center">
<th>Exp.</th>
<th>Course #</th>
<th>Course</th>
<th>Teacher</th>
<th>Comment</th>
</tr>

    <tr>
    <td align="center">1/6(A-B)</td>
    <td>54436</td>
    <td>Social Studies (grade 6)</td>
    <td>
        <a href="teacherinfo.html?frn=0051089" title="Details about Miller, Stephen J" class="button mini dialogM"></a>
        <a href="mailto:stephen.miller@school.net" target="_top">Email Miller, Stephen J</a>
    </td>
    <td><pre>Test Student has shown excellent progress this quarter. Keep up the great work!</pre></td>
    </tr>

    <tr>
    <td align="center">2/6(A-B)</td>
    <td>52036</td>
    <td>Mathematics (grade 6)</td>
    <td>
        <a href="teacherinfo.html?frn=00514844" title="Details about Koskinen, Elizabeth" class="button mini dialogM"></a>
        <a href="mailto:elizabeth.koskinen@school.net" target="_top">Email Koskinen, Elizabeth</a>
    </td>
    <td><pre></pre></td>
    </tr>

    <tr>
    <td align="center">3/6(A-B)</td>
    <td>51034</td>
    <td>Language Arts (grade 6)</td>
    <td>
        <a href="teacherinfo.html?frn=0056532" title="Details about Jones, Mary Ann" class="button mini dialogM"></a>
        <a href="mailto:mary.jones@school.net" target="_top">Email Jones, Mary Ann</a>
    </td>
    <td><pre>Needs improvement in reading comprehension. Please encourage daily reading at home.</pre></td>
    </tr>

    <tr>
    <td align="center">4/6(A-B)</td>
    <td>55101</td>
    <td>Science (grade 6)</td>
    <td>
        <a href="teacherinfo.html?frn=0052590" title="Details about Smith, John" class="button mini dialogM"></a>
        <a href="mailto:john.smith@school.net" target="_top">Email Smith, John</a>
    </td>
    <td><pre>Great participation in class discussions!</pre></td>
    </tr>

</tbody></table>
</body>
</html>
"""

EMPTY_COMMENTS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Teacher Comments</title></head>
<body>
<h1>Teacher Comments: Student, Test</h1>
<table class="grid linkDescList">
<tbody><tr align="center">
<th>Exp.</th>
<th>Course #</th>
<th>Course</th>
<th>Teacher</th>
<th>Comment</th>
</tr>

    <tr>
    <td align="center">1/6(A-B)</td>
    <td>54436</td>
    <td>Social Studies (grade 6)</td>
    <td>
        <a href="mailto:teacher@school.net" target="_top">Email Teacher, Name</a>
    </td>
    <td><pre></pre></td>
    </tr>

    <tr>
    <td align="center">2/6(A-B)</td>
    <td>52036</td>
    <td>Mathematics (grade 6)</td>
    <td>
        <a href="mailto:teacher2@school.net" target="_top">Email Teacher, Two</a>
    </td>
    <td><pre></pre></td>
    </tr>

</tbody></table>
</body>
</html>
"""


@pytest.fixture
def sample_comments_html() -> str:
    """Provide sample teacher comments HTML."""
    return SAMPLE_TEACHER_COMMENTS_HTML


@pytest.fixture
def empty_comments_html() -> str:
    """Provide HTML with empty comments."""
    return EMPTY_COMMENTS_HTML


class TestTeacherCommentsParser:
    """Tests for teacher comments HTML parsing."""

    def test_parse_teacher_comments_returns_list(self, sample_comments_html: str):
        """Parser returns a list of comment dictionaries."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_extracts_course_name(self, sample_comments_html: str):
        """Parser extracts course names correctly."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        course_names = [c["course_name"] for c in result]
        assert "Social Studies (grade 6)" in course_names
        assert "Mathematics (grade 6)" in course_names

    def test_parse_extracts_teacher_name(self, sample_comments_html: str):
        """Parser extracts teacher names from email links."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        # Find Social Studies entry
        social_studies = next(c for c in result if "Social Studies" in c["course_name"])
        assert social_studies["teacher_name"] == "Miller, Stephen J"

    def test_parse_extracts_teacher_email(self, sample_comments_html: str):
        """Parser extracts teacher email addresses."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        social_studies = next(c for c in result if "Social Studies" in c["course_name"])
        assert social_studies["teacher_email"] == "stephen.miller@school.net"

    def test_parse_extracts_comment_text(self, sample_comments_html: str):
        """Parser extracts comment text from pre tags."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        # Find entry with comment
        social_studies = next(c for c in result if "Social Studies" in c["course_name"])
        assert "excellent progress" in social_studies["comment"]

    def test_parse_handles_empty_comments(self, sample_comments_html: str):
        """Parser handles rows with empty comment fields."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        # Math should have empty comment
        math = next(c for c in result if "Mathematics" in c["course_name"])
        assert math["comment"] == "" or math["comment"] is None

    def test_parse_extracts_course_number(self, sample_comments_html: str):
        """Parser extracts course numbers."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        social_studies = next(c for c in result if "Social Studies" in c["course_name"])
        assert social_studies["course_number"] == "54436"

    def test_parse_extracts_expression(self, sample_comments_html: str):
        """Parser extracts period/expression field."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        social_studies = next(c for c in result if "Social Studies" in c["course_name"])
        assert social_studies["expression"] == "1/6(A-B)"

    def test_parse_filters_comments_only(self, sample_comments_html: str):
        """Parser can filter to only return rows with actual comments."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html, comments_only=True)

        # Should only have entries with non-empty comments
        assert len(result) == 3  # Social Studies, Language Arts, Science have comments
        for item in result:
            assert item["comment"] and len(item["comment"].strip()) > 0

    def test_parse_includes_all_by_default(self, sample_comments_html: str):
        """Parser includes all courses by default, even without comments."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        # Should have all 4 courses
        assert len(result) == 4

    def test_parse_empty_html_returns_empty_list(self):
        """Parser handles empty or minimal HTML gracefully."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments("")
        assert result == []

        result = parse_teacher_comments("<html></html>")
        assert result == []

    def test_parse_all_empty_comments(self, empty_comments_html: str):
        """Parser handles HTML where all comments are empty."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(empty_comments_html, comments_only=True)
        assert result == []

        result = parse_teacher_comments(empty_comments_html, comments_only=False)
        assert len(result) == 2  # Both rows should be included

    def test_parse_strips_whitespace(self, sample_comments_html: str):
        """Parser strips whitespace from extracted values."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        for item in result:
            if item.get("comment"):
                assert item["comment"] == item["comment"].strip()
            assert item["course_name"] == item["course_name"].strip()


class TestTeacherCommentsWithRealHTML:
    """Tests using real HTML files from raw_html directory."""

    def test_parse_q1_html_file(self, raw_html_dir: Path):
        """Parser can handle real Q1 comments HTML file."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        html_path = raw_html_dir / "comments_q1.html"
        if not html_path.exists():
            pytest.skip("comments_q1.html not found in raw_html directory")

        html = html_path.read_text(encoding="utf-8")
        result = parse_teacher_comments(html)

        # Should extract at least some entries
        assert isinstance(result, list)
        assert len(result) >= 1

        # Each entry should have required fields
        for item in result:
            assert "course_name" in item
            assert "teacher_name" in item
            assert "comment" in item

    def test_parse_q2_html_file(self, raw_html_dir: Path):
        """Parser can handle real Q2 comments HTML file."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        html_path = raw_html_dir / "comments_q2.html"
        if not html_path.exists():
            pytest.skip("comments_q2.html not found in raw_html directory")

        html = html_path.read_text(encoding="utf-8")
        result = parse_teacher_comments(html)

        # Should extract at least some entries
        assert isinstance(result, list)
        assert len(result) >= 1


class TestTeacherCommentsDataStructure:
    """Tests for the structure of parsed data."""

    def test_comment_dict_has_all_fields(self, sample_comments_html: str):
        """Each parsed comment has all expected fields."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        required_fields = [
            "expression",
            "course_number",
            "course_name",
            "teacher_name",
            "teacher_email",
            "comment",
        ]

        for item in result:
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_comment_dict_values_are_strings(self, sample_comments_html: str):
        """All parsed values are strings (or None for optional fields)."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        result = parse_teacher_comments(sample_comments_html)

        for item in result:
            for key, value in item.items():
                assert value is None or isinstance(value, str), (
                    f"Field {key} should be str or None, got {type(value)}"
                )
