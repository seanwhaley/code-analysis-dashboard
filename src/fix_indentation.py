#!/usr/bin/env python3
"""
Quick script to fix indentation issues in sqlite_backend.py
"""


def fix_indentation():
    file_path = "api/sqlite_backend.py"

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Fix indentation in _create_schema method
    in_create_schema = False
    fixed_lines = []

    for i, line in enumerate(lines):
        if "def _create_schema(self, cursor) -> None:" in line:
            in_create_schema = True
            fixed_lines.append(line)
        elif in_create_schema and line.strip().startswith(
            "async def _create_schema_async"
        ):
            in_create_schema = False
            fixed_lines.append(line)
        elif in_create_schema:
            # Fix indentation - remove extra spaces
            if line.startswith("            "):  # 12 spaces
                # Convert to 8 spaces (2 levels of indentation)
                fixed_line = "        " + line[12:]
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    # Write back the fixed content
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(fixed_lines)

    print("Fixed indentation issues in sqlite_backend.py")


if __name__ == "__main__":
    fix_indentation()
