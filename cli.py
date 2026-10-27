from __future__ import annotations

import sys
from pathlib import Path

from pykd.executor import QueryExecutor
from pykd.lexer import Lexer, LexerError
from pykd.optimizer import QueryOptimizer
from pykd.parser import Parser, ParserError
from pykd.planner import QueryPlanner, PlannerError
from pykd.storage import StorageEngine


def run_cli(db_path: str = "pykd_live.db") -> None:
    storage = StorageEngine(Path(db_path))
    storage.open()
    
    executor = QueryExecutor(storage)

    print("=" * 50)
    print("       Welcome to PyKD Interactive Shell       ")
    print("=" * 50)
    print(f"Connected to database storage: {db_path}")
    print("Type your SQL statements ending with a semicolon (;)")
    print("Type EXIT; or QUIT; to exit the shell.\n")

    buffer = []

    while True:
        try:
            prompt = "pykd> " if not buffer else "   -> "
            line = input(prompt)
            
            # Check for direct quit commands if buffer is empty
            if not buffer and line.strip().upper() in ("EXIT;", "QUIT;", "EXIT", "QUIT"):
                print("Closing database and exiting PyKD Shell. Goodbye!")
                break

            buffer.append(line)
            full_input = " ".join(buffer).strip()

            if not full_input:
                buffer.clear()
                continue

            # Statements require a semicolon to execute
            if not full_input.endswith(";"):
                continue

            sql_statement = full_input[:-1].strip()
            buffer.clear()

            if sql_statement.upper() in ("EXIT", "QUIT"):
                print("Closing database and exiting PyKD Shell. Goodbye!")
                break

            # Pipeline execution: Lexer -> Parser -> Planner -> Optimizer -> Executor
            tokens = Lexer(sql_statement).tokenize()
            query = Parser(tokens).parse()
            result = executor.execute(query)

            # Format and display output if result contains rows/columns
            if result is not None and hasattr(result, "columns") and hasattr(result, "rows"):
                columns = result.columns
                rows = result.rows
                
                if not columns:
                    print("Query executed successfully. (No columns returned)\n")
                    continue

                # Calculate column widths for nice formatting
                col_widths = [len(str(col)) for col in columns]
                for row in rows:
                    for i, val in enumerate(row):
                        col_widths[i] = max(col_widths[i], len(str(val)))

                header_str = " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(columns))
                separator_str = "-+-".join("-" * w for w in col_widths)

                print("\n" + header_str)
                print(separator_str)
                for row in rows:
                    print(" | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)))
                print(f"\n({result.row_count} row{'s' if result.row_count != 1 else ''})\n")
            else:
                print("Query executed successfully.\n")

        except (LexerError, ParserError, PlannerError, Exception) as e:
            print(f"Error: {e}\n")
            buffer.clear()
        except KeyboardInterrupt:
            print("\nUse EXIT; or QUIT; to exit.")
            buffer.clear()
        except EOFError:
            break

    storage.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "pykd_live.db"
    run_cli(db_file)