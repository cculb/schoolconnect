"""Tests for student data skills validation.

Tests validate:
- YAML frontmatter is valid and parseable
- Required fields exist: name, description, whenToUse, tags
- MCP tool references match actual tools in server.py
- Markdown structure is correct
"""

import re
from pathlib import Path

import pytest
import yaml

# Path to skills directory
SKILLS_DIR = Path(__file__).parent.parent.parent / ".claude" / "skills"

# Expected skills
EXPECTED_SKILLS = [
    "student-summary.md",
    "check-grades.md",
    "missing-work.md",
    "check-attendance.md",
]

# Valid MCP tools from server.py
VALID_MCP_TOOLS = {
    "list_students",
    "get_student_summary",
    "get_current_grades",
    "get_grade_trends",
    "get_missing_assignments",
    "get_upcoming_assignments",
    "get_assignment_completion_rates",
    "get_course_score_details",
    "get_attendance_summary",
    "get_attendance_alerts",
    "get_daily_attendance",
    "get_attendance_patterns",
    "get_action_items",
    "generate_weekly_report",
    "prepare_teacher_meeting",
    "get_teacher_comments",
    "list_teachers",
    "get_teacher_profile",
    "draft_teacher_email",
    "get_communication_suggestions",
    "save_communication_draft",
    "list_communication_drafts",
    "run_custom_query",
    "get_database_status",
}


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and markdown content from skill file."""
    # Match YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not match:
        raise ValueError("No valid YAML frontmatter found")

    frontmatter_str = match.group(1)
    markdown_content = match.group(2)

    frontmatter = yaml.safe_load(frontmatter_str)
    return frontmatter, markdown_content


def extract_mcp_tools(content: str) -> set[str]:
    """Extract MCP tool names referenced in the skill content."""
    # Look for tool names in backticks or code blocks
    # Common patterns: `get_student_summary`, get_student_summary()
    tool_pattern = r"`?([a-z_]+(?:_[a-z]+)*)`?"
    matches = re.findall(tool_pattern, content)

    # Filter to only those that are valid MCP tools
    return {match for match in matches if match in VALID_MCP_TOOLS}


@pytest.fixture
def skill_files():
    """Get all skill markdown files."""
    return [SKILLS_DIR / skill for skill in EXPECTED_SKILLS]


class TestSkillFiles:
    """Test that all expected skill files exist."""

    def test_skills_directory_exists(self):
        """Skills directory should exist."""
        assert SKILLS_DIR.exists(), f"Skills directory not found: {SKILLS_DIR}"
        assert SKILLS_DIR.is_dir(), f"Skills path is not a directory: {SKILLS_DIR}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_file_exists(self, skill_name):
        """Each expected skill file should exist."""
        skill_path = SKILLS_DIR / skill_name
        assert skill_path.exists(), f"Skill file not found: {skill_path}"
        assert skill_path.is_file(), f"Skill path is not a file: {skill_path}"


class TestSkillFrontmatter:
    """Test YAML frontmatter in skill files."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_frontmatter_is_valid_yaml(self, skill_name):
        """Frontmatter should be valid YAML."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()

        # Should not raise
        frontmatter, _ = extract_frontmatter(content)
        assert isinstance(frontmatter, dict), "Frontmatter should be a dictionary"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_frontmatter_has_required_fields(self, skill_name):
        """Frontmatter should have all required fields."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        frontmatter, _ = extract_frontmatter(content)

        required_fields = ["name", "description", "whenToUse", "tags"]
        for field in required_fields:
            assert field in frontmatter, f"Missing required field '{field}' in {skill_name}"
            assert frontmatter[field], f"Field '{field}' is empty in {skill_name}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_frontmatter_name_is_string(self, skill_name):
        """Name field should be a non-empty string."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        frontmatter, _ = extract_frontmatter(content)

        assert isinstance(frontmatter["name"], str), f"name should be string in {skill_name}"
        assert len(frontmatter["name"]) > 0, f"name should not be empty in {skill_name}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_frontmatter_description_length(self, skill_name):
        """Description should be 1-2 sentences (reasonable length)."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        frontmatter, _ = extract_frontmatter(content)

        description = frontmatter["description"]
        assert isinstance(description, str), f"description should be string in {skill_name}"
        # Between 10 and 300 characters is reasonable for 1-2 sentences
        assert 10 <= len(description) <= 300, (
            f"description length unreasonable in {skill_name}: {len(description)}"
        )

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_frontmatter_tags_include_required(self, skill_name):
        """Tags should include 'student-data' and 'schoolconnect'."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        frontmatter, _ = extract_frontmatter(content)

        tags = frontmatter["tags"]
        assert isinstance(tags, list), f"tags should be a list in {skill_name}"
        assert "student-data" in tags, f"tags should include 'student-data' in {skill_name}"
        assert "schoolconnect" in tags, f"tags should include 'schoolconnect' in {skill_name}"


class TestSkillContent:
    """Test markdown content structure."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_markdown_content(self, skill_name):
        """Skill should have markdown content after frontmatter."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        _, markdown = extract_frontmatter(content)

        assert len(markdown.strip()) > 0, f"No markdown content in {skill_name}"
        assert len(markdown) > 100, f"Markdown content too short in {skill_name}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_section_headers(self, skill_name):
        """Skill should have standard section headers."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        _, markdown = extract_frontmatter(content)

        # Should have at least some headers
        headers = re.findall(r"^##?\s+(.+)$", markdown, re.MULTILINE)
        assert len(headers) >= 2, f"Should have at least 2 section headers in {skill_name}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_mcp_tools_section(self, skill_name):
        """Skill should document which MCP tools it uses."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        _, markdown = extract_frontmatter(content)

        # Should mention MCP tools somewhere
        assert "MCP" in markdown or "tool" in markdown.lower(), (
            f"Should mention MCP tools in {skill_name}"
        )


class TestMCPToolReferences:
    """Test that skills reference valid MCP tools."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_references_valid_tools(self, skill_name):
        """Skills should only reference valid MCP tools."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()

        # Extract all tool references
        tools = extract_mcp_tools(content)

        # All referenced tools should be valid
        invalid_tools = tools - VALID_MCP_TOOLS
        assert not invalid_tools, f"Invalid MCP tool references in {skill_name}: {invalid_tools}"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_references_at_least_one_tool(self, skill_name):
        """Skills should reference at least one MCP tool."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()

        tools = extract_mcp_tools(content)
        assert len(tools) >= 1, f"Should reference at least one MCP tool in {skill_name}"


class TestSkillSpecificContent:
    """Test skill-specific requirements."""

    def test_student_summary_uses_correct_tool(self):
        """student-summary should use get_student_summary tool."""
        skill_path = SKILLS_DIR / "student-summary.md"
        content = skill_path.read_text()

        tools = extract_mcp_tools(content)
        assert "get_student_summary" in tools, "Should reference get_student_summary"

    def test_check_grades_uses_correct_tool(self):
        """check-grades should use get_current_grades tool."""
        skill_path = SKILLS_DIR / "check-grades.md"
        content = skill_path.read_text()

        tools = extract_mcp_tools(content)
        assert "get_current_grades" in tools, "Should reference get_current_grades"

    def test_missing_work_uses_correct_tool(self):
        """missing-work should use get_missing_assignments tool."""
        skill_path = SKILLS_DIR / "missing-work.md"
        content = skill_path.read_text()

        tools = extract_mcp_tools(content)
        assert "get_missing_assignments" in tools, "Should reference get_missing_assignments"

    def test_check_attendance_uses_correct_tool(self):
        """check-attendance should use get_attendance_summary tool."""
        skill_path = SKILLS_DIR / "check-attendance.md"
        content = skill_path.read_text()

        tools = extract_mcp_tools(content)
        assert "get_attendance_summary" in tools, "Should reference get_attendance_summary"


class TestSkillExamples:
    """Test that skills include examples."""

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_has_example_section(self, skill_name):
        """Skill should include example usage."""
        skill_path = SKILLS_DIR / skill_name
        content = skill_path.read_text()
        _, markdown = extract_frontmatter(content)

        # Should have "Example" or "Usage" section
        has_example = bool(re.search(r"##?\s+(Example|Usage|How to Use)", markdown, re.IGNORECASE))
        assert has_example, f"Should have Example/Usage section in {skill_name}"
