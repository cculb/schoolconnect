"""Main MCP server for PowerSchool data access."""

import asyncio
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tools import (
    register_assignment_tools,
    register_attendance_tools,
    register_grade_tools,
    register_insight_tools,
    register_student_tools,
)


def create_server(db_path: str | None = None) -> Server:
    """Create and configure the MCP server with all tools.

    Args:
        db_path: Path to the SQLite database. If not provided, uses
                 DATABASE_PATH env var or defaults to data/powerschool.db

    Returns:
        Configured MCP Server instance
    """
    # Determine database path
    if db_path is None:
        db_path = os.environ.get("DATABASE_PATH", "data/powerschool.db")

    # Ensure path is absolute
    db_path = str(Path(db_path).resolve())

    # Create server
    mcp = Server("powerschool-mcp")

    # Register all tools
    register_student_tools(mcp, db_path)
    register_grade_tools(mcp, db_path)
    register_assignment_tools(mcp, db_path)
    register_attendance_tools(mcp, db_path)
    register_insight_tools(mcp, db_path)

    return mcp


async def run_server(db_path: str | None = None) -> None:
    """Run the MCP server using stdio transport.

    Args:
        db_path: Optional path to the SQLite database
    """
    mcp = create_server(db_path)

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


def main(db_path: str | None = None) -> None:
    """Main entry point for the MCP server."""
    asyncio.run(run_server(db_path))


if __name__ == "__main__":
    main()
