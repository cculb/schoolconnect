"""Unit tests for analysis and insight skills.

These tests validate the skill files structure, YAML frontmatter,
and interpretation guidance without requiring external dependencies.
"""

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit


# Get the project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"


# Expected skill files
SKILL_FILES = [
    "weekly-report.md",
    "analyze-attendance.md",
    "grade-trends.md",
    "action-items.md",
]


class TestSkillFilesExist:
    """Test that all required skill files exist."""

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_skill_file_exists(self, skill_file):
        """Test that skill file exists."""
        skill_path = SKILLS_DIR / skill_file
        assert skill_path.exists(), f"Skill file {skill_file} does not exist at {skill_path}"

    def test_skills_directory_exists(self):
        """Test that .claude/skills directory exists."""
        assert SKILLS_DIR.exists(), f".claude/skills directory does not exist at {SKILLS_DIR}"
        assert SKILLS_DIR.is_dir(), f"{SKILLS_DIR} is not a directory"


class TestSkillFrontmatter:
    """Test YAML frontmatter structure and required fields."""

    @pytest.fixture
    def parse_skill_file(self):
        """Helper to parse skill file frontmatter and content."""

        def _parse(skill_file):
            skill_path = SKILLS_DIR / skill_file
            content = skill_path.read_text()

            # Extract frontmatter
            pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
            match = re.match(pattern, content, re.DOTALL)
            assert match, f"No frontmatter found in {skill_file}"

            frontmatter_text = match.group(1)
            body = match.group(2)

            # Parse YAML
            frontmatter = yaml.safe_load(frontmatter_text)
            return frontmatter, body

        return _parse

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_has_description(self, skill_file, parse_skill_file):
        """Test that skill has a description in frontmatter."""
        frontmatter, _ = parse_skill_file(skill_file)
        assert "description" in frontmatter, f"{skill_file} missing 'description' field"
        assert frontmatter["description"], f"{skill_file} has empty description"
        assert (
            len(frontmatter["description"]) >= 20
        ), f"{skill_file} description too short (min 20 chars)"

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_description_is_string(self, skill_file, parse_skill_file):
        """Test that description is a string."""
        frontmatter, _ = parse_skill_file(skill_file)
        assert isinstance(
            frontmatter["description"], str
        ), f"{skill_file} description is not a string"

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_frontmatter_is_valid_yaml(self, skill_file):
        """Test that frontmatter is valid YAML."""
        skill_path = SKILLS_DIR / skill_file
        content = skill_path.read_text()

        # Extract frontmatter
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, content, re.DOTALL)
        assert match, f"No frontmatter found in {skill_file}"

        frontmatter_text = match.group(1)

        # Should not raise
        try:
            yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            pytest.fail(f"{skill_file} has invalid YAML frontmatter: {e}")


class TestSkillContent:
    """Test skill content structure and required sections."""

    @pytest.fixture
    def get_skill_content(self):
        """Helper to get skill file content."""

        def _get(skill_file):
            skill_path = SKILLS_DIR / skill_file
            return skill_path.read_text()

        return _get

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_has_markdown_content(self, skill_file, get_skill_content):
        """Test that skill has substantial markdown content."""
        content = get_skill_content(skill_file)

        # Extract body (after frontmatter)
        pattern = r"^---\s*\n.*?\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        assert match, f"Could not extract body from {skill_file}"

        body = match.group(1).strip()
        assert len(body) >= 100, f"{skill_file} has insufficient content (min 100 chars)"

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_has_example_section(self, skill_file, get_skill_content):
        """Test that skill has an example section."""
        content = get_skill_content(skill_file)

        # Look for example-related headings or keywords
        has_example = any(
            keyword in content.lower()
            for keyword in ["## example", "### example", "**example**:", "for example"]
        )
        assert has_example, f"{skill_file} does not have an example section"

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_markdown_structure(self, skill_file, get_skill_content):
        """Test that skill has proper markdown structure with headings."""
        content = get_skill_content(skill_file)

        # Should have at least one heading
        has_heading = re.search(r"^#{1,3}\s+.+", content, re.MULTILINE)
        assert has_heading, f"{skill_file} has no markdown headings"


class TestMCPToolReferences:
    """Test that skills reference correct MCP tools."""

    # Map skill files to expected MCP tools they should reference
    EXPECTED_TOOLS = {
        "weekly-report.md": [
            "generate_weekly_report",
            "get_student_summary",
            "get_current_grades",
            "get_missing_assignments",
            "get_attendance_summary",
        ],
        "analyze-attendance.md": [
            "get_attendance_patterns",
            "get_attendance_summary",
            "get_daily_attendance",
        ],
        "grade-trends.md": ["get_grade_trends", "get_current_grades"],
        "action-items.md": ["get_action_items", "get_missing_assignments"],
    }

    @pytest.fixture
    def get_skill_content(self):
        """Helper to get skill file content."""

        def _get(skill_file):
            skill_path = SKILLS_DIR / skill_file
            return skill_path.read_text()

        return _get

    @pytest.mark.parametrize(
        "skill_file,expected_tools",
        [
            (skill, tools)
            for skill, tools in EXPECTED_TOOLS.items()
        ],
    )
    def test_references_mcp_tools(self, skill_file, expected_tools, get_skill_content):
        """Test that skill references expected MCP tools."""
        content = get_skill_content(skill_file)

        for tool in expected_tools:
            assert (
                tool in content
            ), f"{skill_file} should reference MCP tool '{tool}'"


class TestInterpretationGuidance:
    """Test that analysis skills provide interpretation guidance."""

    # Skills that require interpretation guidance
    ANALYSIS_SKILLS = [
        "weekly-report.md",
        "analyze-attendance.md",
        "grade-trends.md",
        "action-items.md",
    ]

    @pytest.fixture
    def get_skill_content(self):
        """Helper to get skill file content."""

        def _get(skill_file):
            skill_path = SKILLS_DIR / skill_file
            return skill_path.read_text()

        return _get

    @pytest.mark.parametrize("skill_file", ANALYSIS_SKILLS)
    def test_has_interpretation_section(self, skill_file, get_skill_content):
        """Test that skill has interpretation guidance section."""
        content = get_skill_content(skill_file)

        # Look for interpretation-related sections
        has_interpretation = any(
            keyword in content.lower()
            for keyword in [
                "interpretation",
                "threshold",
                "warning",
                "alert",
                "indicates",
                "suggests",
                "concern",
            ]
        )
        assert (
            has_interpretation
        ), f"{skill_file} missing interpretation guidance (thresholds, alerts, etc.)"

    @pytest.mark.parametrize("skill_file", ANALYSIS_SKILLS)
    def test_has_numeric_thresholds(self, skill_file, get_skill_content):
        """Test that skill includes numeric thresholds for interpretation."""
        content = get_skill_content(skill_file)

        # Look for percentage or numeric thresholds
        has_threshold = re.search(
            r"(\d+%|below \d+|above \d+|more than \d+|less than \d+|\d+\+)", content
        )
        assert (
            has_threshold
        ), f"{skill_file} should include numeric thresholds for interpretation"


class TestSkillSpecificContent:
    """Test skill-specific requirements."""

    @pytest.fixture
    def get_skill_content(self):
        """Helper to get skill file content."""

        def _get(skill_file):
            skill_path = SKILLS_DIR / skill_file
            return skill_path.read_text()

        return _get

    def test_weekly_report_has_comprehensive_coverage(self, get_skill_content):
        """Test that weekly-report skill covers all key areas."""
        content = get_skill_content("weekly-report.md")

        # Should mention key areas
        key_areas = ["grades", "attendance", "missing", "action"]
        for area in key_areas:
            assert (
                area.lower() in content.lower()
            ), f"weekly-report should mention '{area}'"

    def test_attendance_skill_has_pattern_analysis(self, get_skill_content):
        """Test that analyze-attendance skill covers pattern analysis."""
        content = get_skill_content("analyze-attendance.md")

        # Should mention pattern analysis
        pattern_keywords = ["pattern", "day of week", "streak"]
        has_pattern = any(keyword in content.lower() for keyword in pattern_keywords)
        assert (
            has_pattern
        ), "analyze-attendance should include pattern analysis guidance"

    def test_grade_trends_mentions_terms(self, get_skill_content):
        """Test that grade-trends skill mentions academic terms."""
        content = get_skill_content("grade-trends.md")

        # Should mention terms (quarters, semesters)
        has_terms = re.search(r"(Q[1-4]|S[1-2]|quarter|semester|term)", content, re.IGNORECASE)
        assert has_terms, "grade-trends should mention academic terms (Q1, Q2, etc.)"

    def test_action_items_has_prioritization(self, get_skill_content):
        """Test that action-items skill mentions prioritization."""
        content = get_skill_content("action-items.md")

        # Should mention priority levels
        priority_keywords = ["priority", "high", "critical", "urgent"]
        has_priority = any(keyword in content.lower() for keyword in priority_keywords)
        assert has_priority, "action-items should include prioritization guidance"


class TestSkillQuality:
    """Test overall quality of skill files."""

    @pytest.fixture
    def get_skill_content(self):
        """Helper to get skill file content."""

        def _get(skill_file):
            skill_path = SKILLS_DIR / skill_file
            return skill_path.read_text()

        return _get

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_no_placeholder_text(self, skill_file, get_skill_content):
        """Test that skill doesn't contain placeholder text."""
        content = get_skill_content(skill_file)

        # Common placeholder patterns
        placeholders = [
            "TODO",
            "FIXME",
            "[add details]",
            "[to be added]",
            "lorem ipsum",
        ]
        for placeholder in placeholders:
            assert (
                placeholder.lower() not in content.lower()
            ), f"{skill_file} contains placeholder text: {placeholder}"

    @pytest.mark.parametrize("skill_file", SKILL_FILES)
    def test_has_sufficient_detail(self, skill_file, get_skill_content):
        """Test that skill has sufficient detail (word count)."""
        content = get_skill_content(skill_file)

        # Extract body
        pattern = r"^---\s*\n.*?\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        body = match.group(1) if match else content

        # Count words
        words = len(re.findall(r"\b\w+\b", body))
        assert (
            words >= 150
        ), f"{skill_file} has insufficient detail ({words} words, min 150)"
