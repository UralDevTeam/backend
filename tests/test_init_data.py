from __future__ import annotations

import re
import unittest
from pathlib import Path


SQL_PATH = Path("src/res/init-db.sql")


def _load_block(sql_text: str, table: str) -> str:
    marker = f"INSERT INTO {table}"
    start = sql_text.index(marker)
    end = sql_text.index("ON CONFLICT", start)
    return sql_text[start:end]


def _extract_rows(block: str) -> list[list[str]]:
    """Extract rows from INSERT block, handling multi-line records."""
    rows: list[list[str]] = []
    current_row = []
    in_record = False
    
    for raw_line in block.splitlines():
        line = raw_line.strip()
        
        # Check if this line contains the start of a record (has opening parenthesis)
        if "(" in line and not in_record:
            in_record = True
            # Extract the part after the first (
            line = line[line.index("("):]
        
        # Skip if not in a record
        if not in_record:
            continue
        
        # Check if record ends on this line (before removing trailing comma)
        record_ends = line.rstrip().endswith("),") or (line.rstrip().endswith(")") and "," not in line.rstrip()[-3:])
        
        # Remove trailing comma and comments
        line = line.rstrip(",")
        if "--" in line:
            line = line.split("--", 1)[0].rstrip()
        
        # Extract quoted values from this line
        values = re.findall(r"'([^']*)'", line)
        current_row.extend(values)
        
        # If record ends on this line
        if record_ends:
            if current_row:
                rows.append(current_row)
            current_row = []
            in_record = False
    
    # Don't forget the last row if it wasn't saved
    if in_record and current_row:
        rows.append(current_row)
    
    return rows


class InitDataTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sql_text = SQL_PATH.read_text(encoding="utf-8")

        cls.position_rows = _extract_rows(_load_block(sql_text, "positions"))
        cls.team_rows = _extract_rows(_load_block(sql_text, "teams"))
        cls.employee_rows = _extract_rows(_load_block(sql_text, "employees"))
        cls.status_rows = _extract_rows(_load_block(sql_text, "status_history"))

        cls.position_ids = {row[0] for row in cls.position_rows}
        cls.team_ids = {row[0] for row in cls.team_rows}
        cls.employee_ids = {row[0] for row in cls.employee_rows}

    def test_positions_count(self) -> None:
        self.assertEqual(len(self.position_ids), 25)

    def test_teams_reference_existing_leaders(self) -> None:
        for row in self.team_rows:
            leader_id = row[-1]
            self.assertIn(leader_id, self.employee_ids)

    def test_teams_reference_existing_parents(self) -> None:
        for row in self.team_rows:
            if len(row) == 4:
                parent_id = row[2]
                self.assertIn(parent_id, self.team_ids)

    def test_employees_reference_existing_teams_and_positions(self) -> None:
        for row in self.employee_rows:
            team_id = row[-2]
            position_id = row[-1]
            self.assertIn(team_id, self.team_ids)
            self.assertIn(position_id, self.position_ids)

    def test_status_history_references_existing_employees(self) -> None:
        for row in self.status_rows:
            employee_id = row[1]
            self.assertIn(employee_id, self.employee_ids)


if __name__ == "__main__":
    unittest.main()