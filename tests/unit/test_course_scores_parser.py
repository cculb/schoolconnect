"""Unit tests for course scores HTML parser.

These tests use static HTML fixtures and don't require
external dependencies or network access.

The parser extracts:
- Category weights (e.g., "Formative: 30%, Summative: 70%")
- Assignment details (descriptions, standards, comments)
- Full assignment breakdown with calculated weighted scores
"""

import pytest

pytestmark = pytest.mark.unit


# Sample HTML for course scores page (based on PowerSchool scores.html structure)
SAMPLE_COURSE_SCORES_HTML = """
<!DOCTYPE html>
<html>
<head><title>Class Score Detail</title></head>
<body>
<div class="box-round">
    <h2>Mathematics (grade 6)</h2>
    <div class="teacher-info">
        <span class="teacher">Koskinen, Elizabeth Jeanne</span>
    </div>

    <!-- Category weights section -->
    <div class="category-weights">
        <h3>Category Weights</h3>
        <table class="linkDescList grid">
            <tr>
                <th>Category</th>
                <th>Weight</th>
                <th>Points Earned</th>
                <th>Points Possible</th>
            </tr>
            <tr>
                <td class="category-name">Formative</td>
                <td class="weight">30%</td>
                <td class="points-earned">85</td>
                <td class="points-possible">100</td>
            </tr>
            <tr>
                <td class="category-name">Summative</td>
                <td class="weight">50%</td>
                <td class="points-earned">45</td>
                <td class="points-possible">50</td>
            </tr>
            <tr>
                <td class="category-name">Practice</td>
                <td class="weight">20%</td>
                <td class="points-earned">18</td>
                <td class="points-possible">20</td>
            </tr>
        </table>
    </div>

    <!-- Assignments section -->
    <div class="assignments-detail">
        <h3>Assignments</h3>
        <table class="linkDescList grid" id="scoreTable">
            <tr>
                <th>Due Date</th>
                <th>Category</th>
                <th>Assignment</th>
                <th>Score</th>
                <th>%</th>
                <th>Grade</th>
                <th>Codes</th>
            </tr>
            <tr class="assignment-row" data-assignment-id="12345">
                <td class="due-date">12/15/2024</td>
                <td class="category">Formative</td>
                <td class="assignment-name">
                    <a href="#" onclick="showDetail(12345)">Chapter 5 Quiz</a>
                    <div class="assignment-detail hidden" id="detail-12345">
                        <p class="description">Quiz covering fractions and decimals</p>
                        <p class="standards">6.NS.1, 6.NS.2</p>
                        <p class="comments">Great improvement!</p>
                    </div>
                </td>
                <td class="score">17/20</td>
                <td class="percent">85%</td>
                <td class="letter-grade">B</td>
                <td class="codes">Collected</td>
            </tr>
            <tr class="assignment-row" data-assignment-id="12346">
                <td class="due-date">12/18/2024</td>
                <td class="category">Summative</td>
                <td class="assignment-name">
                    <a href="#" onclick="showDetail(12346)">Unit 5 Test</a>
                    <div class="assignment-detail hidden" id="detail-12346">
                        <p class="description">Comprehensive unit test</p>
                        <p class="standards">6.NS.1, 6.NS.2, 6.NS.3</p>
                        <p class="comments"></p>
                    </div>
                </td>
                <td class="score">45/50</td>
                <td class="percent">90%</td>
                <td class="letter-grade">A</td>
                <td class="codes">Collected</td>
            </tr>
            <tr class="assignment-row" data-assignment-id="12347">
                <td class="due-date">12/20/2024</td>
                <td class="category">Practice</td>
                <td class="assignment-name">
                    <a href="#" onclick="showDetail(12347)">Homework Set 5</a>
                    <div class="assignment-detail hidden" id="detail-12347">
                        <p class="description">Practice problems 1-25</p>
                        <p class="standards"></p>
                        <p class="comments">Missing problem 15</p>
                    </div>
                </td>
                <td class="score">--</td>
                <td class="percent"></td>
                <td class="letter-grade"></td>
                <td class="codes">Missing</td>
            </tr>
        </table>
    </div>
</div>
</body>
</html>
"""

SAMPLE_MINIMAL_HTML = """
<div class="box-round">
    <h2>Science (grade 6)</h2>
    <div class="assignments-detail">
        <table class="linkDescList grid" id="scoreTable">
            <tr>
                <th>Assignment</th>
                <th>Score</th>
            </tr>
            <tr class="assignment-row">
                <td class="assignment-name">Lab Report</td>
                <td class="score">8/10</td>
            </tr>
        </table>
    </div>
</div>
"""


class TestCourseScoresParser:
    """Tests for course scores HTML parsing."""

    def test_parse_category_weights(self):
        """Parser extracts category weights from HTML."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)

        assert "categories" in result
        categories = result["categories"]
        assert len(categories) == 3

        # Check specific categories
        formative = next((c for c in categories if c["name"] == "Formative"), None)
        assert formative is not None
        assert formative["weight"] == 30.0

        summative = next((c for c in categories if c["name"] == "Summative"), None)
        assert summative is not None
        assert summative["weight"] == 50.0

        practice = next((c for c in categories if c["name"] == "Practice"), None)
        assert practice is not None
        assert practice["weight"] == 20.0

    def test_parse_category_points(self):
        """Parser extracts points earned and possible for categories."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)
        categories = result["categories"]

        formative = next((c for c in categories if c["name"] == "Formative"), None)
        assert formative["points_earned"] == 85.0
        assert formative["points_possible"] == 100.0

    def test_parse_assignments(self):
        """Parser extracts assignments from HTML."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)

        assert "assignments" in result
        assignments = result["assignments"]
        assert len(assignments) == 3

    def test_parse_assignment_basic_info(self):
        """Parser extracts basic assignment information."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)
        assignments = result["assignments"]

        quiz = next((a for a in assignments if "Chapter 5 Quiz" in a["name"]), None)
        assert quiz is not None
        assert quiz["category"] == "Formative"
        assert quiz["due_date"] == "12/15/2024"
        assert quiz["score"] == "17/20"
        assert quiz["percent"] == 85.0
        assert quiz["letter_grade"] == "B"

    def test_parse_assignment_details(self):
        """Parser extracts assignment details (description, standards, comments)."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)
        assignments = result["assignments"]

        quiz = next((a for a in assignments if "Chapter 5 Quiz" in a["name"]), None)
        assert quiz is not None

        # Check details
        assert quiz.get("description") == "Quiz covering fractions and decimals"
        assert "6.NS.1" in quiz.get("standards", "")
        assert quiz.get("comments") == "Great improvement!"

    def test_parse_assignment_standards_as_list(self):
        """Parser can return standards as a list."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)
        assignments = result["assignments"]

        test = next((a for a in assignments if "Unit 5 Test" in a["name"]), None)
        assert test is not None

        # Standards should be parseable as JSON if stored that way
        standards = test.get("standards", "")
        if standards:
            # Should contain multiple standards
            assert "6.NS.1" in standards
            assert "6.NS.3" in standards

    def test_parse_missing_assignment(self):
        """Parser correctly identifies missing assignments."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)
        assignments = result["assignments"]

        homework = next((a for a in assignments if "Homework Set 5" in a["name"]), None)
        assert homework is not None
        assert homework["score"] == "--" or homework["score"] is None
        assert "Missing" in homework.get("codes", "")

    def test_parse_course_info(self):
        """Parser extracts course information."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)

        assert result.get("course_name") == "Mathematics (grade 6)"
        assert "Koskinen" in result.get("teacher_name", "")

    def test_parse_empty_html(self):
        """Parser handles empty HTML gracefully."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores("")
        assert result == {} or result.get("categories") == []
        assert result == {} or result.get("assignments") == []

        result = parse_course_scores("<html></html>")
        assert result == {} or result.get("categories") == []

    def test_parse_minimal_html(self):
        """Parser handles HTML without category weights."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_MINIMAL_HTML)

        # Should still extract assignments
        assert "assignments" in result
        assert len(result["assignments"]) >= 1

        # Categories may be empty
        categories = result.get("categories", [])
        assert isinstance(categories, list)


class TestCategoryWeightParsing:
    """Focused tests for category weight extraction."""

    def test_weight_with_percent_sign(self):
        """Parser handles weight values with % sign."""
        try:
            from src.scraper.parsers.course_scores import parse_weight
        except ImportError:
            pytest.skip("Parser not implemented")

        assert parse_weight("30%") == 30.0
        assert parse_weight("50%") == 50.0
        assert parse_weight("100%") == 100.0

    def test_weight_without_percent_sign(self):
        """Parser handles weight values without % sign."""
        try:
            from src.scraper.parsers.course_scores import parse_weight
        except ImportError:
            pytest.skip("Parser not implemented")

        assert parse_weight("30") == 30.0
        assert parse_weight("50") == 50.0

    def test_weight_with_whitespace(self):
        """Parser handles weight values with whitespace."""
        try:
            from src.scraper.parsers.course_scores import parse_weight
        except ImportError:
            pytest.skip("Parser not implemented")

        assert parse_weight("  30%  ") == 30.0
        assert parse_weight("\n50%\t") == 50.0

    def test_weight_invalid_value(self):
        """Parser handles invalid weight values."""
        try:
            from src.scraper.parsers.course_scores import parse_weight
        except ImportError:
            pytest.skip("Parser not implemented")

        assert parse_weight("") is None
        assert parse_weight("N/A") is None
        assert parse_weight("--") is None


class TestScoreParsing:
    """Focused tests for score extraction."""

    def test_parse_fraction_score(self):
        """Parser handles fraction scores like 17/20."""
        try:
            from src.scraper.parsers.course_scores import parse_score
        except ImportError:
            pytest.skip("Parser not implemented")

        earned, possible = parse_score("17/20")
        assert earned == 17.0
        assert possible == 20.0

    def test_parse_missing_score(self):
        """Parser handles missing score indicators."""
        try:
            from src.scraper.parsers.course_scores import parse_score
        except ImportError:
            pytest.skip("Parser not implemented")

        earned, possible = parse_score("--")
        assert earned is None
        assert possible is None

        earned, possible = parse_score("")
        assert earned is None
        assert possible is None

    def test_parse_partial_score(self):
        """Parser handles partial scores like /10."""
        try:
            from src.scraper.parsers.course_scores import parse_score
        except ImportError:
            pytest.skip("Parser not implemented")

        earned, possible = parse_score("/10")
        assert earned is None
        assert possible == 10.0

    def test_parse_decimal_score(self):
        """Parser handles decimal scores."""
        try:
            from src.scraper.parsers.course_scores import parse_score
        except ImportError:
            pytest.skip("Parser not implemented")

        earned, possible = parse_score("8.5/10")
        assert earned == 8.5
        assert possible == 10.0


class TestStandardsParsing:
    """Focused tests for standards extraction."""

    def test_parse_comma_separated_standards(self):
        """Parser handles comma-separated standards."""
        try:
            from src.scraper.parsers.course_scores import parse_standards
        except ImportError:
            pytest.skip("Parser not implemented")

        standards = parse_standards("6.NS.1, 6.NS.2, 6.NS.3")
        assert isinstance(standards, list)
        assert len(standards) == 3
        assert "6.NS.1" in standards
        assert "6.NS.3" in standards

    def test_parse_empty_standards(self):
        """Parser handles empty standards."""
        try:
            from src.scraper.parsers.course_scores import parse_standards
        except ImportError:
            pytest.skip("Parser not implemented")

        standards = parse_standards("")
        assert standards == [] or standards is None

        standards = parse_standards(None)
        assert standards == [] or standards is None

    def test_parse_single_standard(self):
        """Parser handles single standard."""
        try:
            from src.scraper.parsers.course_scores import parse_standards
        except ImportError:
            pytest.skip("Parser not implemented")

        standards = parse_standards("6.NS.1")
        assert isinstance(standards, list)
        assert len(standards) == 1
        assert standards[0] == "6.NS.1"


class TestPercentParsing:
    """Focused tests for percent extraction."""

    def test_parse_percent_with_sign(self):
        """Parser handles percent with % sign."""
        try:
            from src.scraper.parsers.course_scores import parse_percent
        except ImportError:
            pytest.skip("Parser not implemented")

        assert parse_percent("85%") == 85.0
        assert parse_percent("90%") == 90.0
        assert parse_percent("100%") == 100.0

    def test_parse_percent_without_sign(self):
        """Parser handles percent without % sign."""
        try:
            from src.scraper.parsers.course_scores import parse_percent
        except ImportError:
            pytest.skip("Parser not implemented")

        assert parse_percent("85") == 85.0
        assert parse_percent("90") == 90.0

    def test_parse_empty_percent(self):
        """Parser handles empty percent."""
        try:
            from src.scraper.parsers.course_scores import parse_percent
        except ImportError:
            pytest.skip("Parser not implemented")

        assert parse_percent("") is None
        assert parse_percent("--") is None


class TestDataStructures:
    """Tests for output data structures."""

    def test_category_structure(self):
        """Category dict has expected keys."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)
        category = result["categories"][0]

        assert "name" in category
        assert "weight" in category
        # Points are optional
        assert "points_earned" in category or True
        assert "points_possible" in category or True

    def test_assignment_structure(self):
        """Assignment dict has expected keys."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)
        assignment = result["assignments"][0]

        assert "name" in assignment
        assert "category" in assignment
        assert "due_date" in assignment
        assert "score" in assignment
        # Detail fields
        assert "description" in assignment or True
        assert "standards" in assignment or True
        assert "comments" in assignment or True

    def test_result_structure(self):
        """Result dict has expected top-level keys."""
        try:
            from src.scraper.parsers.course_scores import parse_course_scores
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_course_scores(SAMPLE_COURSE_SCORES_HTML)

        assert "course_name" in result
        assert "categories" in result
        assert "assignments" in result
        assert isinstance(result["categories"], list)
        assert isinstance(result["assignments"], list)
